from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase
from app.services.feedback_service import FeedbackService
from app.services.task_queue_service import TaskQueueService


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OptimizationService:
    """Optimization service for trigger jobs and proposal review lifecycle."""

    def __init__(
        self,
        database: SQLiteDatabase,
        task_queue: TaskQueueService,
        feedback_service: FeedbackService,
        queue_auto_process: bool = True,
    ) -> None:
        self._database = database
        self._task_queue = task_queue
        self._feedback_service = feedback_service
        self._queue_auto_process = queue_auto_process
        self._task_queue.register_handler("optimization.run", self._handle_optimization_task)

    def trigger_job(
        self,
        trigger_source: str,
        reason: str | None = None,
        backtest_job_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_source = (trigger_source or "").strip().lower()
        if normalized_source not in {"event", "manual", "chatbot"}:
            raise ValueError(f"Unsupported trigger_source: {trigger_source}")

        if backtest_job_id:
            with self._database.connection() as conn:
                row = conn.execute(
                    "SELECT job_id FROM backtest_jobs WHERE job_id = ?",
                    (backtest_job_id,),
                ).fetchone()
                if row is None:
                    raise ValueError(f"Backtest job not found: {backtest_job_id}")

        job_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO optimization_jobs (
                    job_id, trigger_source, reason, backtest_job_id, status,
                    feature_set_json, result_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 'queued', NULL, NULL, ?, ?)
                """,
                (job_id, normalized_source, reason, backtest_job_id, now, now),
            )
        self._task_queue.enqueue("optimization.run", {"job_id": job_id})
        if self._queue_auto_process:
            self._task_queue.process_all()
        return self.get_job(job_id=job_id)

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = conn.execute(
                """
                SELECT
                    job_id, trigger_source, reason, backtest_job_id, status,
                    feature_set_json, result_json, created_at, updated_at
                FROM optimization_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Optimization job not found: {job_id}")
        return {
            "job_id": row["job_id"],
            "trigger_source": row["trigger_source"],
            "reason": row["reason"],
            "backtest_job_id": row["backtest_job_id"],
            "status": row["status"],
            "feature_set": self._database.json_load(row["feature_set_json"], {}),
            "result": self._database.json_load(row["result_json"], {}),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def create_proposal(
        self,
        source: str,
        target: str,
        diff: dict[str, Any],
        summary: str | None = None,
    ) -> dict[str, Any]:
        normalized_source = (source or "").strip().lower()
        normalized_target = (target or "").strip()
        if normalized_source not in {"event", "manual", "chatbot"}:
            raise ValueError(f"Unsupported proposal source: {source}")
        if not normalized_target:
            raise ValueError("target is required")
        if not diff:
            raise ValueError("diff is required")

        proposal_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO change_proposals (
                    proposal_id, source, target, summary, diff_json, status,
                    gate_result_json, reviewer, review_note, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'review_pending', NULL, NULL, NULL, ?, ?)
                """,
                (proposal_id, normalized_source, normalized_target, summary, self._database.json_dump(diff), now, now),
            )
        return self.get_proposal(proposal_id=proposal_id)

    def approve_proposal(self, proposal_id: str, reviewer: str, note: str | None = None) -> dict[str, Any]:
        normalized_reviewer = (reviewer or "").strip()
        if not normalized_reviewer:
            raise ValueError("reviewer is required")
        with self._database.connection() as conn:
            row = self._require_proposal(conn=conn, proposal_id=proposal_id)
            if row["status"] != "review_pending":
                raise RuntimeError(f"Proposal state conflict: {row['status']}")
            gate_result = {"decision": "approved", "note": note}
            now = _utc_now()
            conn.execute(
                """
                UPDATE change_proposals
                SET status = 'approved', gate_result_json = ?, reviewer = ?, review_note = ?, updated_at = ?
                WHERE proposal_id = ?
                """,
                (self._database.json_dump(gate_result), normalized_reviewer, note, now, proposal_id),
            )
        return self.get_proposal(proposal_id=proposal_id)

    def reject_proposal(self, proposal_id: str, reviewer: str, reason: str | None = None) -> dict[str, Any]:
        normalized_reviewer = (reviewer or "").strip()
        if not normalized_reviewer:
            raise ValueError("reviewer is required")
        with self._database.connection() as conn:
            row = self._require_proposal(conn=conn, proposal_id=proposal_id)
            if row["status"] != "review_pending":
                raise RuntimeError(f"Proposal state conflict: {row['status']}")
            gate_result = {"decision": "rejected", "reason": reason}
            now = _utc_now()
            conn.execute(
                """
                UPDATE change_proposals
                SET status = 'rejected', gate_result_json = ?, reviewer = ?, review_note = ?, updated_at = ?
                WHERE proposal_id = ?
                """,
                (self._database.json_dump(gate_result), normalized_reviewer, reason, now, proposal_id),
            )
        return self.get_proposal(proposal_id=proposal_id)

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        with self._database.connection() as conn:
            row = self._require_proposal(conn=conn, proposal_id=proposal_id)
        return {
            "proposal_id": row["proposal_id"],
            "source": row["source"],
            "target": row["target"],
            "summary": row["summary"],
            "diff": self._database.json_load(row["diff_json"], {}),
            "status": row["status"],
            "gate_result": self._database.json_load(row["gate_result_json"], {}),
            "reviewer": row["reviewer"],
            "review_note": row["review_note"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _handle_optimization_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        started = _utc_now()
        with self._database.connection() as conn:
            row = conn.execute(
                "SELECT trigger_source, reason, backtest_job_id FROM optimization_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Optimization job not found: {job_id}")
            conn.execute(
                "UPDATE optimization_jobs SET status = 'running', updated_at = ? WHERE job_id = ?",
                (started, job_id),
            )
        try:
            feature_set = self._build_feature_set(backtest_job_id=row["backtest_job_id"])
            result = self._evaluate_features(feature_set=feature_set)
            finished = _utc_now()
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE optimization_jobs
                    SET status = 'completed', feature_set_json = ?, result_json = ?, updated_at = ?
                    WHERE job_id = ?
                    """,
                    (self._database.json_dump(feature_set), self._database.json_dump(result), finished, job_id),
                )
            return {"job_id": job_id, "status": "completed"}
        except Exception as exc:
            failed = _utc_now()
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE optimization_jobs
                    SET status = 'failed', result_json = ?, updated_at = ?
                    WHERE job_id = ?
                    """,
                    (self._database.json_dump({"error": str(exc)}), failed, job_id),
                )
            raise

    def _build_feature_set(self, backtest_job_id: str | None) -> dict[str, Any]:
        feedback = self._feedback_service.build_feature_snapshot(limit=200)
        backtest = self._load_backtest_snapshot(backtest_job_id=backtest_job_id)
        return {"feedback": feedback, "backtest": backtest}

    def _load_backtest_snapshot(self, backtest_job_id: str | None) -> dict[str, Any]:
        with self._database.connection() as conn:
            if backtest_job_id:
                row = conn.execute(
                    """
                    SELECT job_id, status, metrics_json
                    FROM backtest_jobs
                    WHERE job_id = ?
                    """,
                    (backtest_job_id,),
                ).fetchone()
            else:
                row = conn.execute("""
                    SELECT job_id, status, metrics_json
                    FROM backtest_jobs
                    WHERE status IN ('completed', 'partial_completed')
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """).fetchone()
        if row is None:
            return {"job_id": None, "status": "missing", "metrics": {}}
        return {
            "job_id": row["job_id"],
            "status": row["status"],
            "metrics": self._database.json_load(row["metrics_json"], {}),
        }

    @staticmethod
    def _evaluate_features(feature_set: dict[str, Any]) -> dict[str, Any]:
        feedback = feature_set.get("feedback", {})
        backtest = feature_set.get("backtest", {})
        feedback_avg = feedback.get("avg_score")
        feedback_score = (float(feedback_avg) / 5.0 * 100.0) if feedback_avg is not None else 50.0
        backtest_metrics = backtest.get("metrics", {})
        backtest_score = float(backtest_metrics.get("win_rate_pct") or 50.0)
        sample_size = int(backtest_metrics.get("sample_size") or 0)
        stability_score = min(sample_size, 50) / 50.0 * 100.0 if sample_size > 0 else 50.0
        quality_score = round(0.45 * backtest_score + 0.35 * feedback_score + 0.20 * stability_score, 2)
        recommendation = "promote_candidate" if quality_score >= 70 else "optimize_prompt_or_flow"
        return {
            "quality_score": quality_score,
            "feedback_score": round(feedback_score, 2),
            "backtest_score": round(backtest_score, 2),
            "stability_score": round(stability_score, 2),
            "recommendation": recommendation,
        }

    @staticmethod
    def _require_proposal(conn: Any, proposal_id: str) -> Any:
        row = conn.execute(
            """
            SELECT
                proposal_id, source, target, summary, diff_json, status, gate_result_json,
                reviewer, review_note, created_at, updated_at
            FROM change_proposals
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Proposal not found: {proposal_id}")
        return row
