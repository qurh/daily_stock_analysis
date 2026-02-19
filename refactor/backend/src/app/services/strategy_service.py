from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase
from app.services.knowledge_service import KnowledgeService


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrategyService:
    """Strategy domain service for cognition distill, extraction, and version lifecycle."""

    def __init__(self, database: SQLiteDatabase, knowledge_service: KnowledgeService) -> None:
        self._database = database
        self._knowledge_service = knowledge_service

    def distill_cognition(
        self,
        session_id: str,
        start_index: int | None = None,
        end_index: int | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        with self._database.connection() as conn:
            session_row = conn.execute(
                "SELECT session_id FROM conversation_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if session_row is None:
                raise KeyError(f"Session not found: {session_id}")
            rows = conn.execute(
                """
                SELECT message_id, role, content, created_at
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        if not rows:
            raise ValueError("No conversation messages found for distill")

        range_start = max(start_index or 1, 1)
        range_end = min(end_index or len(rows), len(rows))
        if range_start > range_end:
            raise ValueError("Invalid message range")
        selected = rows[range_start - 1 : range_end]
        if not selected:
            raise ValueError("No conversation messages selected")

        resolved_title = (title or "").strip() or f"Cognition Memo {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        markdown = self._build_memo_markdown(selected_rows=selected, title=resolved_title, session_id=session_id)
        memo_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO cognition_memos (
                    memo_id, title, markdown, source_sessions_json, source_message_ids_json,
                    status, reviewer, review_notes, knowledge_doc_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'review_pending', NULL, NULL, NULL, ?, ?)
                """,
                (
                    memo_id,
                    resolved_title,
                    markdown,
                    self._database.json_dump([session_id]),
                    self._database.json_dump([item["message_id"] for item in selected]),
                    now,
                    now,
                ),
            )
        return self.get_memo(memo_id=memo_id)

    def review_cognition(
        self,
        memo_id: str,
        action: str,
        reviewer: str,
        editor_notes: str | None = None,
        edited_markdown: str | None = None,
    ) -> dict[str, Any]:
        normalized_action = (action or "").strip().lower()
        if normalized_action not in {"approve", "reject", "edit"}:
            raise ValueError(f"Unsupported review action: {action}")

        normalized_reviewer = (reviewer or "").strip()
        if not normalized_reviewer:
            raise ValueError("reviewer is required")

        with self._database.connection() as conn:
            row = self._require_memo(conn=conn, memo_id=memo_id)
            if row["status"] not in {"review_pending", "generated"}:
                raise RuntimeError(f"Memo state conflict: {row['status']}")

            current_markdown = row["markdown"]
            next_markdown = (edited_markdown or "").strip() or current_markdown
            if normalized_action == "edit":
                conn.execute(
                    """
                    UPDATE cognition_memos
                    SET markdown = ?, reviewer = ?, review_notes = ?, updated_at = ?
                    WHERE memo_id = ?
                    """,
                    (next_markdown, normalized_reviewer, editor_notes, _utc_now(), memo_id),
                )
                return self.get_memo(memo_id=memo_id)

        if normalized_action == "reject":
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE cognition_memos
                    SET status = 'rejected', reviewer = ?, review_notes = ?, updated_at = ?
                    WHERE memo_id = ?
                    """,
                    (normalized_reviewer, editor_notes, _utc_now(), memo_id),
                )
            return self.get_memo(memo_id=memo_id)

        # approve path: create knowledge doc and index it.
        memo = self.get_memo(memo_id=memo_id)
        final_markdown = (edited_markdown or "").strip() or memo["markdown"]
        uploaded = self._knowledge_service.upload_document(
            title=memo["title"],
            markdown=final_markdown,
            tags=["cognition_memo", "strategy_source"],
        )
        doc_id = uploaded["doc_id"]
        self._knowledge_service.ingest_document(doc_id=doc_id)

        with self._database.connection() as conn:
            conn.execute(
                """
                UPDATE cognition_memos
                SET markdown = ?, status = 'indexed', reviewer = ?,
                    review_notes = ?, knowledge_doc_id = ?, updated_at = ?
                WHERE memo_id = ?
                """,
                (final_markdown, normalized_reviewer, editor_notes, doc_id, _utc_now(), memo_id),
            )
        return self.get_memo(memo_id=memo_id)

    def extract_strategy(
        self,
        strategy_type: str,
        source_scope: str = "indexed_memos",
        prompt_ref: str | None = None,
    ) -> dict[str, Any]:
        normalized_type = (strategy_type or "").strip().lower()
        if normalized_type not in {"analysis", "trading"}:
            raise ValueError(f"Unsupported strategy_type: {strategy_type}")

        with self._database.connection() as conn:
            memo_rows = conn.execute("""
                SELECT memo_id, markdown, title
                FROM cognition_memos
                WHERE status = 'indexed'
                ORDER BY updated_at DESC
                LIMIT 20
                """).fetchall()
        if not memo_rows:
            raise RuntimeError("STR-EXTRACT-003: no indexed cognition memo available")

        rules = self._extract_rules(memo_rows=memo_rows, strategy_type=normalized_type)
        thresholds = self._build_thresholds(strategy_type=normalized_type)
        conditions = {
            "source_scope": source_scope,
            "prompt_ref": prompt_ref,
            "memo_count": len(memo_rows),
        }

        with self._database.connection() as conn:
            version_row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS max_version FROM strategy_artifacts WHERE strategy_type = ?",
                (normalized_type,),
            ).fetchone()
            next_version = int(version_row["max_version"]) + 1

            strategy_id = str(uuid4())
            now = _utc_now()
            conn.execute(
                """
                INSERT INTO strategy_artifacts (
                    strategy_id, strategy_type, version, rules_json, thresholds_json,
                    conditions_json, source_memo_ids_json, status, gate_result_json,
                    backtest_job_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'candidate', NULL, NULL, ?, ?)
                """,
                (
                    strategy_id,
                    normalized_type,
                    next_version,
                    self._database.json_dump(rules),
                    self._database.json_dump(thresholds),
                    self._database.json_dump(conditions),
                    self._database.json_dump([row["memo_id"] for row in memo_rows]),
                    now,
                    now,
                ),
            )
        return self.get_strategy(strategy_id=strategy_id)

    def list_versions(
        self,
        strategy_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        safe_limit = max(min(int(limit), 200), 1)
        query = """
            SELECT
                strategy_id, strategy_type, version, rules_json, thresholds_json, conditions_json,
                source_memo_ids_json, status, gate_result_json, backtest_job_id, created_at, updated_at
            FROM strategy_artifacts
            WHERE 1 = 1
        """
        params: list[Any] = []
        if strategy_type:
            query += " AND strategy_type = ?"
            params.append(strategy_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY strategy_type ASC, version DESC LIMIT ?"
        params.append(safe_limit)

        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return {"items": [self._serialize_strategy_row(row) for row in rows], "count": len(rows)}

    def publish_strategy(
        self,
        strategy_id: str,
        backtest_job_id: str | None,
        proposal_id: str | None = None,
        require_proposal_id: bool = False,
    ) -> dict[str, Any]:
        if not backtest_job_id:
            raise RuntimeError("STR-GATE-005: backtest_job_id is required before publish")

        with self._database.connection() as conn:
            strategy_row = self._require_strategy(conn=conn, strategy_id=strategy_id)
            if strategy_row["status"] not in {"candidate", "approved", "rolled_back"}:
                raise RuntimeError(f"Strategy state conflict: {strategy_row['status']}")

            normalized_proposal_id = (proposal_id or "").strip() or None
            if require_proposal_id and normalized_proposal_id is None:
                raise RuntimeError("STR-GATE-009: proposal_id is required in strict publish mode")
            if normalized_proposal_id is not None:
                linked_proposal = self._load_proposal_by_id(
                    conn=conn,
                    proposal_id=normalized_proposal_id,
                )
                linked_strategy_id = self._extract_linked_strategy_id(
                    self._database.json_load(linked_proposal["diff_json"], {}),
                )
                if linked_strategy_id != strategy_id:
                    raise RuntimeError("STR-GATE-008: explicit proposal is not linked to strategy")
                if linked_proposal["status"] != "approved":
                    raise RuntimeError("STR-GATE-007: explicit proposal must be approved before publish")
                linked_chatbot_proposal = {
                    "proposal_id": linked_proposal["proposal_id"],
                    "source": linked_proposal["source"],
                    "target": linked_proposal["target"],
                    "status": linked_proposal["status"],
                    "updated_at": linked_proposal["updated_at"],
                }
            else:
                linked_chatbot_proposal = self._find_latest_linked_chatbot_proposal(
                    conn=conn,
                    strategy_id=strategy_id,
                )
                if linked_chatbot_proposal is not None and linked_chatbot_proposal["status"] != "approved":
                    raise RuntimeError("STR-GATE-006: linked chatbot proposal must be approved before publish")

            backtest_row = conn.execute(
                "SELECT status, metrics_json FROM backtest_jobs WHERE job_id = ?",
                (backtest_job_id,),
            ).fetchone()
            if backtest_row is None:
                raise RuntimeError("STR-GATE-005: backtest job missing")

            metrics = self._database.json_load(backtest_row["metrics_json"], {})
            sample_size = int(metrics.get("sample_size") or 0)
            win_rate_pct = float(metrics.get("win_rate_pct") or 0.0)
            is_passed = (
                backtest_row["status"] in {"completed", "partial_completed"}
                and sample_size >= 5
                and win_rate_pct >= 50.0
            )
            gate_result = {
                "gate": "backtest",
                "passed": is_passed,
                "sample_size": sample_size,
                "win_rate_pct": win_rate_pct,
                "backtest_job_id": backtest_job_id,
            }
            if linked_chatbot_proposal is not None:
                gate_result["proposal_id"] = linked_chatbot_proposal["proposal_id"]
                gate_result["proposal_source"] = linked_chatbot_proposal["source"]
                gate_result["proposal_status"] = linked_chatbot_proposal["status"]
            if not is_passed:
                raise RuntimeError("STR-GATE-005: strategy did not pass backtest gate")

            # Keep only one active strategy version per strategy type.
            conn.execute(
                """
                UPDATE strategy_artifacts
                SET status = 'rolled_back', updated_at = ?
                WHERE strategy_type = ? AND status = 'active'
                """,
                (_utc_now(), strategy_row["strategy_type"]),
            )
            conn.execute(
                """
                UPDATE strategy_artifacts
                SET status = 'active', gate_result_json = ?, backtest_job_id = ?, updated_at = ?
                WHERE strategy_id = ?
                """,
                (self._database.json_dump(gate_result), backtest_job_id, _utc_now(), strategy_id),
            )
        return self.get_strategy(strategy_id=strategy_id)

    def bind_strategy(
        self,
        strategy_id: str,
        flow_id: str,
        prompt_refs: list[str] | None = None,
        prompt_lock_mode: str | None = None,
        effective_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_flow_id = (flow_id or "").strip()
        if not normalized_flow_id:
            raise ValueError("flow_id is required")
        resolved_scope = dict(effective_scope or {})
        normalized_lock_mode = (prompt_lock_mode or "").strip().lower()
        if normalized_lock_mode:
            if normalized_lock_mode not in {"strict", "lenient"}:
                raise ValueError(f"Unsupported prompt_lock_mode: {prompt_lock_mode}")
            resolved_scope["prompt_lock_mode"] = normalized_lock_mode
        elif "prompt_lock_mode" in resolved_scope:
            scope_lock_mode = str(resolved_scope.get("prompt_lock_mode") or "").strip().lower()
            if scope_lock_mode not in {"strict", "lenient"}:
                raise ValueError(f"Unsupported prompt_lock_mode: {scope_lock_mode}")
            resolved_scope["prompt_lock_mode"] = scope_lock_mode

        with self._database.connection() as conn:
            strategy_row = self._require_strategy(conn=conn, strategy_id=strategy_id)
            if strategy_row["status"] != "active":
                raise RuntimeError("STR-BIND-004: strategy must be active before binding")

            # Single active binding per flow for MVP phase.
            conn.execute(
                """
                UPDATE strategy_bindings
                SET status = 'inactive', updated_at = ?
                WHERE flow_id = ? AND status = 'active'
                """,
                (_utc_now(), normalized_flow_id),
            )

            binding_id = str(uuid4())
            now = _utc_now()
            conn.execute(
                """
                INSERT INTO strategy_bindings (
                    binding_id, strategy_id, flow_id, prompt_refs_json,
                    effective_scope_json, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    binding_id,
                    strategy_id,
                    normalized_flow_id,
                    self._database.json_dump(prompt_refs or []),
                    self._database.json_dump(resolved_scope or {"scope": "global"}),
                    now,
                    now,
                ),
            )
        return self.get_binding(binding_id=binding_id)

    def list_bindings(
        self,
        flow_id: str | None = None,
        strategy_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        safe_limit = max(min(int(limit), 500), 1)
        query = """
            SELECT
                binding_id, strategy_id, flow_id, prompt_refs_json,
                effective_scope_json, status, created_at, updated_at
            FROM strategy_bindings
            WHERE 1 = 1
        """
        params: list[Any] = []
        if flow_id:
            query += " AND flow_id = ?"
            params.append(flow_id)
        if strategy_id:
            query += " AND strategy_id = ?"
            params.append(strategy_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(safe_limit)

        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return {"items": [self._serialize_binding_row(row) for row in rows], "count": len(rows)}

    def get_binding(self, binding_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = self._require_binding(conn=conn, binding_id=binding_id)
        return self._serialize_binding_row(row)

    def resolve_active_binding(
        self,
        flow_id: str,
        symbol: str | None = None,
        report_type: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_flow_id = (flow_id or "").strip()
        if not normalized_flow_id:
            return None

        with self._database.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    b.binding_id,
                    b.strategy_id,
                    b.flow_id,
                    b.prompt_refs_json,
                    b.effective_scope_json,
                    b.status AS binding_status,
                    b.created_at,
                    b.updated_at,
                    s.strategy_type,
                    s.version,
                    s.rules_json,
                    s.thresholds_json,
                    s.status AS strategy_status
                FROM strategy_bindings b
                INNER JOIN strategy_artifacts s ON s.strategy_id = b.strategy_id
                WHERE b.flow_id = ? AND b.status = 'active'
                ORDER BY b.updated_at DESC
                """,
                (normalized_flow_id,),
            ).fetchall()

        for row in rows:
            if row["strategy_status"] != "active":
                continue
            scope = self._database.json_load(row["effective_scope_json"], {})
            if not self._scope_matches(scope=scope, symbol=symbol, report_type=report_type):
                continue
            return {
                "binding_id": row["binding_id"],
                "strategy_id": row["strategy_id"],
                "flow_id": row["flow_id"],
                "prompt_refs": self._database.json_load(row["prompt_refs_json"], []),
                "effective_scope": scope,
                "prompt_lock_mode": scope.get("prompt_lock_mode"),
                "strategy_type": row["strategy_type"],
                "strategy_version": row["version"],
                "rules": self._database.json_load(row["rules_json"], []),
                "thresholds": self._database.json_load(row["thresholds_json"], {}),
            }
        return None

    def rollback_strategy(self, strategy_id: str, reason: str | None = None) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = self._require_strategy(conn=conn, strategy_id=strategy_id)
            if row["status"] != "active":
                raise RuntimeError(f"Strategy state conflict: {row['status']}")
            gate_result = self._database.json_load(row["gate_result_json"], {})
            gate_result["rollback_reason"] = reason
            gate_result["rolled_back_at"] = _utc_now()
            now = _utc_now()
            conn.execute(
                """
                UPDATE strategy_artifacts
                SET status = 'rolled_back', gate_result_json = ?, updated_at = ?
                WHERE strategy_id = ?
                """,
                (self._database.json_dump(gate_result), now, strategy_id),
            )
            conn.execute(
                """
                UPDATE strategy_bindings
                SET status = 'inactive', updated_at = ?
                WHERE strategy_id = ? AND status = 'active'
                """,
                (now, strategy_id),
            )
        return self.get_strategy(strategy_id=strategy_id)

    def get_memo(self, memo_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = self._require_memo(conn=conn, memo_id=memo_id)
        return {
            "memo_id": row["memo_id"],
            "title": row["title"],
            "markdown": row["markdown"],
            "source_sessions": self._database.json_load(row["source_sessions_json"], []),
            "source_message_ids": self._database.json_load(row["source_message_ids_json"], []),
            "status": row["status"],
            "reviewer": row["reviewer"],
            "review_notes": row["review_notes"],
            "knowledge_doc_id": row["knowledge_doc_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_strategy(self, strategy_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = self._require_strategy(conn=conn, strategy_id=strategy_id)
        return self._serialize_strategy_row(row=row)

    def _build_memo_markdown(self, selected_rows: list[Any], title: str, session_id: str) -> str:
        insights = self._derive_insights(selected_rows=selected_rows)
        evidence_lines = [
            f"- [{row['created_at']}] {row['role']}: {self._trim_text(row['content'], 160)}"
            for row in selected_rows[:10]
        ]
        lines = [
            f"# {title}",
            "",
            f"- session_id: {session_id}",
            f"- generated_at: {_utc_now()}",
            "",
            "## Core Insights",
            *[f"- {item}" for item in insights],
            "",
            "## Source Evidence",
            *evidence_lines,
        ]
        return "\n".join(lines).strip()

    def _derive_insights(self, selected_rows: list[Any]) -> list[str]:
        user_text = " ".join(row["content"] for row in selected_rows if row["role"] == "user")
        assistant_text = " ".join(row["content"] for row in selected_rows if row["role"] == "assistant")
        candidates = [
            self._trim_text(user_text, 120),
            self._trim_text(assistant_text, 120),
            f"Total messages considered: {len(selected_rows)}",
        ]
        return [item for item in candidates if item]

    def _extract_rules(self, memo_rows: list[Any], strategy_type: str) -> list[str]:
        bullets: list[str] = []
        for row in memo_rows:
            for line in str(row["markdown"]).splitlines():
                content = line.strip()
                if content.startswith("- "):
                    bullets.append(content[2:].strip())
        cleaned = [self._trim_text(item, 140) for item in bullets if item]
        if not cleaned:
            cleaned = [f"Use distilled {strategy_type} cognition as primary decision context."]
        if strategy_type == "analysis":
            cleaned.insert(0, "Prioritize evidence-backed trend and risk interpretation.")
        else:
            cleaned.insert(0, "Control position sizing and stop conditions before entry.")
        # Keep deterministic small rule set for MVP phase.
        deduped: list[str] = []
        for item in cleaned:
            if item not in deduped:
                deduped.append(item)
        return deduped[:8]

    def _build_thresholds(self, strategy_type: str) -> dict[str, Any]:
        if strategy_type == "analysis":
            return {
                "signal_confidence_min": 0.6,
                "risk_alert_max": 0.4,
            }
        return {
            "max_position_pct": 0.3,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.12,
        }

    def _serialize_strategy_row(self, row: Any) -> dict[str, Any]:
        return {
            "strategy_id": row["strategy_id"],
            "strategy_type": row["strategy_type"],
            "version": row["version"],
            "rules": self._database.json_load(row["rules_json"], []),
            "thresholds": self._database.json_load(row["thresholds_json"], {}),
            "conditions": self._database.json_load(row["conditions_json"], {}),
            "source_memo_ids": self._database.json_load(row["source_memo_ids_json"], []),
            "status": row["status"],
            "gate_result": self._database.json_load(row["gate_result_json"], {}),
            "backtest_job_id": row["backtest_job_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _serialize_binding_row(self, row: Any) -> dict[str, Any]:
        effective_scope = self._database.json_load(row["effective_scope_json"], {})
        return {
            "binding_id": row["binding_id"],
            "strategy_id": row["strategy_id"],
            "flow_id": row["flow_id"],
            "prompt_refs": self._database.json_load(row["prompt_refs_json"], []),
            "effective_scope": effective_scope,
            "prompt_lock_mode": effective_scope.get("prompt_lock_mode"),
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _scope_matches(scope: dict[str, Any], symbol: str | None, report_type: str | None) -> bool:
        resolved_scope = scope or {}
        if resolved_scope.get("scope") == "global":
            return True

        symbols = resolved_scope.get("symbols")
        if symbols is not None:
            normalized_symbols = {str(item) for item in symbols if item is not None}
            if not symbol or symbol not in normalized_symbols:
                return False

        constrained_report_type = resolved_scope.get("report_type")
        if constrained_report_type is not None and report_type != constrained_report_type:
            return False

        return True

    @staticmethod
    def _trim_text(text: str, max_len: int) -> str:
        compact = re.sub(r"\s+", " ", (text or "").strip())
        if len(compact) <= max_len:
            return compact
        return f"{compact[: max_len - 3]}..."

    def _find_latest_linked_chatbot_proposal(self, conn: Any, strategy_id: str) -> dict[str, Any] | None:
        rows = conn.execute("""
            SELECT proposal_id, source, target, diff_json, status, updated_at
            FROM change_proposals
            WHERE source = 'chatbot'
            ORDER BY updated_at DESC
            LIMIT 200
            """).fetchall()
        normalized_strategy_id = (strategy_id or "").strip()
        for row in rows:
            diff = self._database.json_load(row["diff_json"], {})
            linked_strategy_id = self._extract_linked_strategy_id(diff=diff)
            if linked_strategy_id == normalized_strategy_id:
                return {
                    "proposal_id": row["proposal_id"],
                    "source": row["source"],
                    "target": row["target"],
                    "status": row["status"],
                    "updated_at": row["updated_at"],
                }
        return None

    def _load_proposal_by_id(self, conn: Any, proposal_id: str) -> Any:
        row = conn.execute(
            """
            SELECT proposal_id, source, target, diff_json, status, updated_at
            FROM change_proposals
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Proposal not found: {proposal_id}")
        return row

    @staticmethod
    def _extract_linked_strategy_id(diff: Any) -> str | None:
        if not isinstance(diff, dict):
            return None
        direct_value = diff.get("strategy_id")
        if direct_value is not None:
            normalized = str(direct_value).strip()
            return normalized or None
        nested_strategy = diff.get("strategy")
        if isinstance(nested_strategy, dict):
            nested_value = nested_strategy.get("strategy_id")
            if nested_value is not None:
                normalized_nested = str(nested_value).strip()
                return normalized_nested or None
        return None

    @staticmethod
    def _require_memo(conn: Any, memo_id: str) -> Any:
        row = conn.execute(
            """
            SELECT
                memo_id, title, markdown, source_sessions_json, source_message_ids_json,
                status, reviewer, review_notes, knowledge_doc_id, created_at, updated_at
            FROM cognition_memos
            WHERE memo_id = ?
            """,
            (memo_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Cognition memo not found: {memo_id}")
        return row

    @staticmethod
    def _require_strategy(conn: Any, strategy_id: str) -> Any:
        row = conn.execute(
            """
            SELECT
                strategy_id, strategy_type, version, rules_json, thresholds_json, conditions_json,
                source_memo_ids_json, status, gate_result_json, backtest_job_id, created_at, updated_at
            FROM strategy_artifacts
            WHERE strategy_id = ?
            """,
            (strategy_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Strategy not found: {strategy_id}")
        return row

    @staticmethod
    def _require_binding(conn: Any, binding_id: str) -> Any:
        row = conn.execute(
            """
            SELECT
                binding_id, strategy_id, flow_id, prompt_refs_json,
                effective_scope_json, status, created_at, updated_at
            FROM strategy_bindings
            WHERE binding_id = ?
            """,
            (binding_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Strategy binding not found: {binding_id}")
        return row
