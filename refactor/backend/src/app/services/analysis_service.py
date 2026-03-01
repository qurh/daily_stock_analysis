from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase
from app.services.notification_service import NotificationHub, NotificationMessage
from app.services.prompt_lock_audit_service import PromptLockAuditService
from app.services.prompt_routing import (
    PromptLockError,
    normalize_lock_mode,
    normalize_prompt_refs,
    resolve_binding_prompt,
)
from app.services.prompt_service import PromptService
from app.services.strategy_service import StrategyService
from app.services.task_queue_service import TaskQueueService
from app.services.workflow_service import WorkflowService


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalysisService:
    """Analysis orchestration service backed by persistent storage."""

    def __init__(
        self,
        database: SQLiteDatabase,
        workflow_service: WorkflowService,
        task_queue: TaskQueueService,
        strategy_service: StrategyService | None = None,
        prompt_service: PromptService | None = None,
        prompt_lock_audit_service: PromptLockAuditService | None = None,
        notification_service: NotificationHub | None = None,
        default_prompt_lock_mode: str = "lenient",
        queue_auto_process: bool = True,
        auto_notify_enabled: bool = False,
        auto_notify_channels: list[str] | None = None,
    ) -> None:
        self._database = database
        self._workflow_service = workflow_service
        self._task_queue = task_queue
        self._strategy_service = strategy_service
        self._prompt_service = prompt_service
        self._prompt_lock_audit_service = prompt_lock_audit_service
        self._notification_service = notification_service
        self._default_prompt_lock_mode = normalize_lock_mode(default_prompt_lock_mode)
        self._queue_auto_process = queue_auto_process
        self._auto_notify_enabled = bool(auto_notify_enabled)
        self._auto_notify_channels = [item.strip().lower() for item in (auto_notify_channels or []) if item.strip()]
        self._task_queue.register_handler("analysis.run", self._handle_analysis_task)

    def submit_job(self, symbol: str, report_type: str) -> dict[str, str]:
        job_id = str(uuid4())
        now = _utc_now()
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_jobs (
                    job_id, symbol, report_type, status, result_json, execution_id, created_at, updated_at
                )
                VALUES (?, ?, ?, 'pending', NULL, NULL, ?, ?)
                """,
                (job_id, symbol, report_type, now, now),
            )

        self._task_queue.enqueue(
            task_type="analysis.run",
            payload={"job_id": job_id, "symbol": symbol, "report_type": report_type},
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
                SELECT job_id, status, result_json, execution_id
                FROM analysis_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            if row is None:
                return None

        execution_id = row["execution_id"]
        trace = {"flow_id": "stock_analysis_v1", "nodes": []}
        if execution_id:
            execution = self._workflow_service.get_execution(execution_id)
            if execution is not None:
                trace = execution["trace"]

        result = self._database.json_load(row["result_json"], {})
        return {
            "job_id": row["job_id"],
            "status": row["status"],
            "result": result,
            "trace": trace,
        }

    def _handle_analysis_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        symbol = payload["symbol"]
        report_type = payload["report_type"]
        now = _utc_now()
        execution_id: str | None = None
        try:
            execution_ref = self._workflow_service.start_execution(
                flow_id="stock_analysis_v1",
                flow_input={"symbol": symbol, "report_type": report_type},
                enqueue=False,
            )
            execution_id = execution_ref["execution_id"]
            strategy_context = self._resolve_strategy_context(symbol=symbol, report_type=report_type)
            prompt_resolution = self._resolve_prompt(
                symbol=symbol,
                report_type=report_type,
                strategy_context=strategy_context,
            )
            meta = {
                "stock_code": symbol,
                "report_type": report_type,
                "prompt_ref": prompt_resolution["prompt_ref"],
            }
            if strategy_context is not None:
                meta["strategy_context"] = strategy_context
            result = {
                "report": {
                    "meta": meta,
                    "dashboard": {
                        "signals": [],
                        "risk_flags": [],
                    },
                }
            }
            self._notify_analysis_result(
                job_id=job_id,
                symbol=symbol,
                report_type=report_type,
                prompt_ref=prompt_resolution["prompt_ref"],
                meta=meta,
            )
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = 'succeeded', result_json = ?, execution_id = ?, updated_at = ?
                    WHERE job_id = ?
                    """,
                    (self._database.json_dump(result), execution_id, now, job_id),
                )
            return {"job_id": job_id, "execution_id": execution_id}
        except PromptLockError as exc:
            if self._prompt_lock_audit_service is not None:
                self._prompt_lock_audit_service.record_event(
                    flow_id=exc.flow_id,
                    lock_mode=exc.lock_mode,
                    source_type="analysis",
                    source_id=job_id,
                    requested_prompt_refs=exc.requested_prompt_refs,
                    failures=exc.failures,
                )
            error_payload = {"error": exc.to_detail()}
            with self._database.connection() as conn:
                conn.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = 'failed', result_json = ?, execution_id = ?, updated_at = ?
                    WHERE job_id = ?
                    """,
                    (self._database.json_dump(error_payload), execution_id, now, job_id),
                )
            return {"job_id": job_id, "execution_id": execution_id}
        except Exception:
            with self._database.connection() as conn:
                conn.execute(
                    "UPDATE analysis_jobs SET status = 'failed', updated_at = ? WHERE job_id = ?",
                    (now, job_id),
                )
            raise

    def _notify_analysis_result(
        self,
        job_id: str,
        symbol: str,
        report_type: str,
        prompt_ref: str,
        meta: dict[str, Any],
    ) -> None:
        if not self._auto_notify_enabled or self._notification_service is None:
            return
        title = f"Analysis {symbol} ({report_type})"
        content = (
            f"job_id: {job_id}\n"
            f"symbol: {symbol}\n"
            f"report_type: {report_type}\n"
            f"prompt_ref: {prompt_ref}\n"
            "status: succeeded"
        )
        try:
            report = self._notification_service.send(
                message=NotificationMessage(title=title, content=content),
                channels=self._auto_notify_channels or None,
                source_type="analysis_job",
                source_id=job_id,
            )
            meta["notification_delivery"] = {
                "message_id": report.get("message_id"),
                "summary": report.get("summary"),
            }
        except Exception as exc:
            meta["notification_delivery"] = {"error": str(exc)}

    def _resolve_strategy_context(self, symbol: str, report_type: str) -> dict[str, Any] | None:
        if self._strategy_service is None:
            return None
        return self._strategy_service.resolve_active_binding(
            flow_id="stock_analysis_v1",
            symbol=symbol,
            report_type=report_type,
        )

    def _resolve_prompt(
        self,
        symbol: str,
        report_type: str,
        strategy_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        if self._prompt_service is None:
            return {
                "prompt_ref": "builtin.analysis.reply@0",
                "rendered_prompt": f"Analyze symbol={symbol}, report_type={report_type}.",
            }

        variables = {
            "symbol": symbol,
            "report_type": report_type,
        }
        lock_mode = self._resolve_prompt_lock_mode(strategy_context=strategy_context)
        binding_prompt_refs = normalize_prompt_refs(strategy_context=strategy_context)
        binding_rendered, failures = resolve_binding_prompt(
            prompt_service=self._prompt_service,
            prompt_refs=binding_prompt_refs,
            variables=variables,
            lock_mode=lock_mode,
        )
        if binding_rendered is not None:
            return binding_rendered
        if lock_mode == "strict" and binding_prompt_refs:
            raise PromptLockError(
                flow_id="stock_analysis_v1",
                lock_mode=lock_mode,
                requested_prompt_refs=binding_prompt_refs,
                failures=failures,
            )

        for prompt_id in ["prompt.analysis.reply", "prompt.analysis.merge"]:
            try:
                rendered = self._prompt_service.render_active_prompt(
                    prompt_id=prompt_id,
                    variables=variables,
                )
                return {
                    "prompt_ref": rendered["prompt_ref"],
                    "rendered_prompt": rendered["rendered_prompt"],
                }
            except (KeyError, ValueError):
                continue
        return {
            "prompt_ref": "builtin.analysis.reply@0",
            "rendered_prompt": f"Analyze symbol={symbol}, report_type={report_type}.",
        }

    def _resolve_prompt_lock_mode(self, strategy_context: dict[str, Any] | None) -> str:
        if strategy_context is None:
            return self._default_prompt_lock_mode
        return normalize_lock_mode(strategy_context.get("prompt_lock_mode"), self._default_prompt_lock_mode)
