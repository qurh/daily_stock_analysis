from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase
from app.services.task_queue_service import TaskQueueService
from app.shared.error_codes import ErrorCode


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BacktestService:
    """Backtest domain service for job execution, records, and performance summary."""

    def __init__(
        self,
        database: SQLiteDatabase,
        task_queue: TaskQueueService,
        queue_auto_process: bool = True,
        default_eval_window_days: int = 10,
        engine_version: str = "v1",
        neutral_band_pct: float = 2.0,
    ) -> None:
        self._database = database
        self._task_queue = task_queue
        self._queue_auto_process = queue_auto_process
        self._default_eval_window_days = default_eval_window_days
        self._engine_version = engine_version
        self._neutral_band_pct = neutral_band_pct
        self._task_queue.register_handler("backtest.run", self._handle_backtest_task)

    def submit_job(self, scope: str, symbol: str | None, eval_window_days: int | None = None) -> dict[str, str]:
        normalized_scope = (scope or "market").strip().lower()
        if normalized_scope not in {"market", "symbol"}:
            raise ValueError(f"Unsupported backtest scope: {scope}")

        normalized_symbol = (symbol or "").strip() or None
        if normalized_scope == "symbol" and normalized_symbol is None:
            raise ValueError("symbol is required when scope=symbol")
        if normalized_scope == "market":
            normalized_symbol = None

        resolved_days = eval_window_days or self._default_eval_window_days
        if resolved_days <= 0:
            raise ValueError("eval_window_days must be positive")

        job_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO backtest_jobs (
                    job_id, scope, symbol, eval_window_days, status, progress,
                    metrics_json, engine_version, started_at, ended_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 'created', 0, NULL, ?, NULL, NULL, ?, ?)
                """,
                (job_id, normalized_scope, normalized_symbol, resolved_days, self._engine_version, now, now),
            )

        self._task_queue.enqueue(
            task_type="backtest.run",
            payload={"job_id": job_id},
        )
        with self._database.connection() as conn:
            conn.execute(
                "UPDATE backtest_jobs SET status = 'queued', updated_at = ? WHERE job_id = ?",
                (_utc_now(), job_id),
            )

        if self._queue_auto_process:
            self._task_queue.process_all()

        job = self.get_job(job_id=job_id)
        if job is None:
            return {"job_id": job_id, "status": "failed"}
        return {"job_id": job_id, "status": job["status"]}

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT
                    job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                    engine_version, started_at, ended_at, created_at, updated_at
                FROM backtest_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            if row is None:
                return None

        return {
            "job_id": row["job_id"],
            "scope": row["scope"],
            "symbol": row["symbol"],
            "eval_window_days": row["eval_window_days"],
            "status": row["status"],
            "progress": row["progress"],
            "metrics": self._database.json_load(row["metrics_json"], self._empty_metrics()),
            "engine_version": row["engine_version"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_results(
        self,
        job_id: str | None = None,
        symbol: str | None = None,
        outcome: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        safe_limit = max(min(limit, 500), 1)
        query = """
            SELECT
                record_id, job_id, analysis_job_id, symbol, direction, outcome, return_pct,
                direction_correct, flags_json, created_at
            FROM backtest_records
            WHERE 1 = 1
        """
        params: list[Any] = []
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if outcome:
            query += " AND outcome = ?"
            params.append(outcome)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(safe_limit)

        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()

        items = [
            {
                "record_id": row["record_id"],
                "job_id": row["job_id"],
                "analysis_job_id": row["analysis_job_id"],
                "symbol": row["symbol"],
                "direction": row["direction"],
                "outcome": row["outcome"],
                "return_pct": row["return_pct"],
                "direction_correct": None if row["direction_correct"] is None else bool(row["direction_correct"]),
                "flags": self._database.json_load(row["flags_json"], []),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
        return {"items": items, "count": len(items)}

    def aggregate(self, job_id: str | None = None, symbol: str | None = None) -> dict[str, Any]:
        query = """
            SELECT outcome, return_pct, direction_correct
            FROM backtest_records
            WHERE 1 = 1
        """
        params: list[Any] = []
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()

        scope = "symbol" if symbol else "market"
        return {
            "scope": scope,
            "symbol": symbol,
            "job_id": job_id,
            "engine_version": self._engine_version,
            "metrics": self._aggregate_rows(rows),
        }

    def evaluate_report(
        self,
        analysis_job_id: str,
        symbol: str,
        report_payload: Any,
        eval_window_days: int,
    ) -> dict[str, Any]:
        if not isinstance(report_payload, dict):
            return self._build_insufficient_eval(reason=ErrorCode.BT_COMPAT_003.value)

        report = report_payload.get("report")
        if not isinstance(report, dict):
            return self._build_insufficient_eval(reason=ErrorCode.BT_COMPAT_003.value)

        direction = self._extract_direction(report)
        realized_change_pct = self._deterministic_change_pct(
            analysis_job_id=analysis_job_id,
            symbol=symbol,
            eval_window_days=eval_window_days,
        )
        expected_direction = self._expected_direction(realized_change_pct)
        direction_correct = direction == expected_direction

        if direction == "long":
            return_pct = round(realized_change_pct, 2)
        elif direction == "short":
            return_pct = round(-realized_change_pct, 2)
        else:
            return_pct = 0.0 if direction_correct else round(-abs(realized_change_pct), 2)

        outcome = "win" if direction_correct else "loss"
        return {
            "direction": direction,
            "outcome": outcome,
            "return_pct": return_pct,
            "direction_correct": direction_correct,
            "flags": [],
        }

    def _handle_backtest_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        started_at = _utc_now()
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT scope, symbol, eval_window_days
                FROM backtest_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Backtest job not found: {job_id}")
            conn.execute(
                """
                UPDATE backtest_jobs
                SET status = 'running', progress = 0, started_at = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (started_at, started_at, job_id),
            )

        scope = row["scope"]
        symbol = row["symbol"]
        eval_window_days = int(row["eval_window_days"])
        try:
            query = """
                SELECT job_id, symbol, result_json
                FROM analysis_jobs
                WHERE status = 'succeeded'
            """
            params: list[Any] = []
            if scope == "symbol" and symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            query += " ORDER BY created_at ASC"

            with self._database.connection() as conn:
                analysis_rows = conn.execute(query, params).fetchall()
                conn.execute("DELETE FROM backtest_records WHERE job_id = ?", (job_id,))

            total = len(analysis_rows)
            for index, analysis_row in enumerate(analysis_rows, start=1):
                evaluation = self.evaluate_report(
                    analysis_job_id=analysis_row["job_id"],
                    symbol=analysis_row["symbol"],
                    report_payload=self._database.json_load(analysis_row["result_json"], None),
                    eval_window_days=eval_window_days,
                )
                with self._database.connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO backtest_records (
                            record_id, job_id, analysis_job_id, symbol, direction, outcome,
                            return_pct, direction_correct, flags_json, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid4()),
                            job_id,
                            analysis_row["job_id"],
                            analysis_row["symbol"],
                            evaluation["direction"],
                            evaluation["outcome"],
                            evaluation["return_pct"],
                            None if evaluation["direction_correct"] is None else int(evaluation["direction_correct"]),
                            self._database.json_dump(evaluation["flags"]),
                            _utc_now(),
                        ),
                    )
                    progress = 100 if total == 0 else int(index * 100 / total)
                    conn.execute(
                        "UPDATE backtest_jobs SET progress = ?, updated_at = ? WHERE job_id = ?",
                        (progress, _utc_now(), job_id),
                    )

            with self._database.connection() as conn:
                conn.execute(
                    "UPDATE backtest_jobs SET status = 'summarizing', updated_at = ? WHERE job_id = ?",
                    (_utc_now(), job_id),
                )
                rows = conn.execute(
                    """
                    SELECT outcome, return_pct, direction_correct
                    FROM backtest_records
                    WHERE job_id = ?
                    """,
                    (job_id,),
                ).fetchall()

            metrics = self._aggregate_rows(rows)
            status = "partial_completed" if metrics["insufficient_size"] > 0 else "completed"
            ended_at = _utc_now()
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE backtest_jobs
                    SET status = ?, progress = 100, metrics_json = ?, ended_at = ?, updated_at = ?
                    WHERE job_id = ?
                    """,
                    (status, self._database.json_dump(metrics), ended_at, ended_at, job_id),
                )
            return {"job_id": job_id, "status": status, "sample_size": metrics["sample_size"]}
        except Exception:
            failed_at = _utc_now()
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE backtest_jobs
                    SET status = 'failed', ended_at = ?, updated_at = ?
                    WHERE job_id = ?
                    """,
                    (failed_at, failed_at, job_id),
                )
            raise

    def _deterministic_change_pct(self, analysis_job_id: str, symbol: str, eval_window_days: int) -> float:
        seed = f"{analysis_job_id}:{symbol}:{eval_window_days}".encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()
        raw_value = int(digest[:8], 16)
        return ((raw_value % 2001) - 1000) / 100.0

    def _expected_direction(self, change_pct: float) -> str:
        if abs(change_pct) <= self._neutral_band_pct:
            return "hold"
        return "long" if change_pct > 0 else "short"

    @staticmethod
    def _build_insufficient_eval(reason: str) -> dict[str, Any]:
        return {
            "direction": "hold",
            "outcome": "insufficient_data",
            "return_pct": None,
            "direction_correct": None,
            "flags": ["insufficient_data", reason],
        }

    def _extract_direction(self, report: dict[str, Any]) -> str:
        direction_candidates: list[Any] = [
            report.get("decision", {}).get("direction") if isinstance(report.get("decision"), dict) else None,
            (
                report.get("recommendation", {}).get("direction")
                if isinstance(report.get("recommendation"), dict)
                else None
            ),
            (
                report.get("dashboard", {}).get("decision", {}).get("direction")
                if isinstance(report.get("dashboard"), dict)
                and isinstance(report.get("dashboard", {}).get("decision"), dict)
                else None
            ),
            report.get("meta", {}).get("direction") if isinstance(report.get("meta"), dict) else None,
            report.get("operation_advice"),
        ]
        for candidate in direction_candidates:
            if candidate is None:
                continue
            text = str(candidate).strip().lower()
            if not text:
                continue
            if any(token in text for token in ["buy", "long", "bull", "看多", "买", "增持", "加仓"]):
                return "long"
            if any(token in text for token in ["sell", "short", "bear", "看空", "卖", "减仓", "清仓"]):
                return "short"
            if any(token in text for token in ["hold", "neutral", "观望", "等待", "持有"]):
                return "hold"
        return "hold"

    @staticmethod
    def _aggregate_rows(rows: list[Any]) -> dict[str, Any]:
        sample_size = len(rows)
        insufficient_size = sum(1 for row in rows if row["outcome"] == "insufficient_data")
        valid_rows = [row for row in rows if row["outcome"] != "insufficient_data"]
        win_count = sum(1 for row in valid_rows if row["outcome"] == "win")
        loss_count = sum(1 for row in valid_rows if row["outcome"] == "loss")
        valid_direction_rows = [row for row in valid_rows if row["direction_correct"] is not None]
        correct_count = sum(1 for row in valid_direction_rows if int(row["direction_correct"]) == 1)
        return_rows = [float(row["return_pct"]) for row in valid_rows if row["return_pct"] is not None]

        direction_accuracy_pct = (
            round(correct_count / len(valid_direction_rows) * 100, 2) if valid_direction_rows else None
        )
        win_rate_pct = round(win_count / (win_count + loss_count) * 100, 2) if (win_count + loss_count) > 0 else None
        avg_return_pct = round(sum(return_rows) / len(return_rows), 4) if return_rows else None
        return {
            "sample_size": sample_size,
            "valid_size": len(valid_rows),
            "insufficient_size": insufficient_size,
            "win_count": win_count,
            "loss_count": loss_count,
            "direction_accuracy_pct": direction_accuracy_pct,
            "win_rate_pct": win_rate_pct,
            "avg_return_pct": avg_return_pct,
        }

    @staticmethod
    def _empty_metrics() -> dict[str, Any]:
        return {
            "sample_size": 0,
            "valid_size": 0,
            "insufficient_size": 0,
            "win_count": 0,
            "loss_count": 0,
            "direction_accuracy_pct": None,
            "win_rate_pct": None,
            "avg_return_pct": None,
        }
