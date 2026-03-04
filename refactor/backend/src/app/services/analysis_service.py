from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
import time
from typing import Any, Callable
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase
from app.services.factor_service import FactorService
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


_DEFAULT_ANALYSIS_FLOW_TEMPLATE = [
    "resolve_strategy_context",
    "resolve_prompt",
    "collect_factors",
    "build_dashboard",
    "finalize_report",
]

_FACTOR_COLLECTION_NODE_MAP = {
    "collect_technical_factor": "technical",
    "collect_macro_factor": "macro",
    "collect_credit_factor": "credit",
    "collect_sentiment_factor": "sentiment",
}


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
        factor_service: FactorService | None = None,
        analysis_flow_template: list[str] | None = None,
        analysis_node_max_retries: int = 0,
        analysis_node_retry_backoff_ms: int = 0,
        analysis_orchestrator_engine: str = "local",
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
        self._factor_service = factor_service or FactorService()
        self._default_prompt_lock_mode = normalize_lock_mode(default_prompt_lock_mode)
        self._queue_auto_process = queue_auto_process
        self._auto_notify_enabled = bool(auto_notify_enabled)
        self._auto_notify_channels = [item.strip().lower() for item in (auto_notify_channels or []) if item.strip()]
        self._analysis_node_max_retries = max(int(analysis_node_max_retries), 0)
        self._analysis_node_retry_backoff_ms = max(int(analysis_node_retry_backoff_ms), 0)
        self._analysis_orchestrator_engine = self._normalize_analysis_orchestrator_engine(analysis_orchestrator_engine)
        self._analysis_node_handlers: dict[str, Callable[[dict[str, Any]], None]] = {
            "resolve_strategy_context": self._node_resolve_strategy_context,
            "resolve_prompt": self._node_resolve_prompt,
            "collect_factors": self._node_collect_factors,
            "collect_technical_factor": self._node_collect_technical_factor,
            "collect_macro_factor": self._node_collect_macro_factor,
            "collect_credit_factor": self._node_collect_credit_factor,
            "collect_sentiment_factor": self._node_collect_sentiment_factor,
            "build_dashboard": self._node_build_dashboard,
            "finalize_report": self._node_finalize_report,
        }
        self._analysis_flow_stages = self._normalize_analysis_flow_template(analysis_flow_template)
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
        trace_nodes: list[dict[str, Any]] = []
        try:
            execution_ref = self._workflow_service.start_execution(
                flow_id="stock_analysis_v1",
                flow_input={"symbol": symbol, "report_type": report_type},
                enqueue=False,
                defer_run=True,
            )
            execution_id = execution_ref["execution_id"]
            context: dict[str, Any] = {
                "symbol": symbol,
                "report_type": report_type,
            }
            orchestrator = self._execute_flow(context=context, trace_nodes=trace_nodes)

            result = context["result"]
            meta = context["meta"]
            meta["orchestrator"] = orchestrator
            prompt_resolution = context["prompt_resolution"]
            self._workflow_service.complete_execution(
                execution_id=execution_id,
                trace_nodes=trace_nodes,
                output={
                    "summary": "Flow stock_analysis_v1 completed",
                    "node_count": len(trace_nodes),
                },
            )
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
            if execution_id is not None:
                self._workflow_service.fail_execution(
                    execution_id=execution_id,
                    trace_nodes=trace_nodes,
                    output=error_payload,
                )
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
            error_payload = {"error": "analysis_task_failed"}
            if execution_id is not None:
                self._workflow_service.fail_execution(
                    execution_id=execution_id,
                    trace_nodes=trace_nodes,
                    output=error_payload,
                )
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

    def _normalize_analysis_orchestrator_engine(self, engine: str) -> str:
        normalized = (engine or "local").strip().lower()
        if normalized not in {"local", "langgraph"}:
            raise ValueError(f"Invalid analysis orchestrator engine: {engine}")
        return normalized

    def _execute_flow(
        self,
        context: dict[str, Any],
        trace_nodes: list[dict[str, Any]],
    ) -> dict[str, str]:
        requested_engine = self._analysis_orchestrator_engine
        if requested_engine == "langgraph":
            try:
                self._execute_flow_with_langgraph(context=context, trace_nodes=trace_nodes)
                return {
                    "requested": "langgraph",
                    "effective": "langgraph",
                }
            except ImportError as exc:
                self._execute_flow_local(context=context, trace_nodes=trace_nodes)
                return {
                    "requested": "langgraph",
                    "effective": "local",
                    "warning_code": "langgraph_import_error",
                    "warning_message": str(exc),
                }
        self._execute_flow_local(context=context, trace_nodes=trace_nodes)
        return {
            "requested": "local",
            "effective": "local",
        }

    def _execute_flow_local(self, context: dict[str, Any], trace_nodes: list[dict[str, Any]]) -> None:
        for stage in self._analysis_flow_stages:
            if len(stage) > 1:
                self._execute_parallel_stage(context=context, stage=stage, trace_nodes=trace_nodes)
                continue
            node_id = stage[0]
            self._execute_node_with_retry(context=context, node_id=node_id, trace_nodes=trace_nodes)

    def _execute_flow_with_langgraph(self, context: dict[str, Any], trace_nodes: list[dict[str, Any]]) -> None:
        from langgraph.graph import END, StateGraph

        builder = StateGraph(dict)
        stage_node_ids: list[str] = []
        for idx, stage in enumerate(self._analysis_flow_stages):
            stage_node_id = f"stage_{idx}"
            stage_node_ids.append(stage_node_id)
            builder.add_node(stage_node_id, self._build_langgraph_stage_node(stage=stage))
        if not stage_node_ids:
            raise ValueError("Empty analysis flow stages")
        builder.set_entry_point(stage_node_ids[0])
        for left, right in zip(stage_node_ids, stage_node_ids[1:]):
            builder.add_edge(left, right)
        builder.add_edge(stage_node_ids[-1], END)
        graph = builder.compile()
        output_state = graph.invoke(
            {
                "context": context,
                "trace_nodes": trace_nodes,
            }
        )
        context.clear()
        context.update(output_state.get("context", {}))
        trace_nodes.clear()
        trace_nodes.extend(output_state.get("trace_nodes", []))

    def _build_langgraph_stage_node(self, stage: list[str]) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def _runner(state: dict[str, Any]) -> dict[str, Any]:
            stage_context = state["context"]
            stage_trace_nodes = state["trace_nodes"]
            if len(stage) > 1:
                self._execute_parallel_stage(
                    context=stage_context,
                    stage=stage,
                    trace_nodes=stage_trace_nodes,
                )
            else:
                self._execute_node_with_retry(
                    context=stage_context,
                    node_id=stage[0],
                    trace_nodes=stage_trace_nodes,
                )
            return {
                "context": stage_context,
                "trace_nodes": stage_trace_nodes,
            }

        return _runner

    def _normalize_analysis_flow_template(self, template: list[str] | None) -> list[list[str]]:
        normalized = [item.strip() for item in (template or []) if item.strip()]
        if not normalized:
            normalized = list(_DEFAULT_ANALYSIS_FLOW_TEMPLATE)

        stages: list[list[str]] = []
        for raw_stage in normalized:
            nodes = [item.strip() for item in raw_stage.split("+") if item.strip()]
            if not nodes:
                continue
            invalid_nodes = [item for item in nodes if item not in self._analysis_node_handlers]
            if invalid_nodes:
                raise ValueError(f"Invalid analysis flow nodes: {', '.join(invalid_nodes)}")
            if len(nodes) > 1 and not all(item in _FACTOR_COLLECTION_NODE_MAP for item in nodes):
                raise ValueError("Parallel analysis stage supports only factor collection nodes")
            stages.append(nodes)

        flattened_nodes = [item for stage in stages for item in stage]
        if "finalize_report" not in flattened_nodes:
            raise ValueError("ANALYSIS_FLOW_TEMPLATE must include finalize_report node")
        if not flattened_nodes or flattened_nodes[-1] != "finalize_report":
            raise ValueError("ANALYSIS_FLOW_TEMPLATE must end with finalize_report")
        return stages

    def _execute_node_with_retry(
        self,
        context: dict[str, Any],
        node_id: str,
        trace_nodes: list[dict[str, Any]],
    ) -> None:
        handler = self._analysis_node_handlers[node_id]
        attempt = 0
        started_at = time.perf_counter()
        while True:
            try:
                handler(context)
                attempts = attempt + 1
                trace_nodes.append(
                    self._build_trace_node(
                        node_id=node_id,
                        status="succeeded",
                        attempts=attempts,
                        duration_ms=self._elapsed_ms(started_at),
                        degraded=attempts > 1,
                        degrade_reason="retry_recovered" if attempts > 1 else None,
                    )
                )
                return
            except Exception as exc:
                attempts = attempt + 1
                if isinstance(exc, PromptLockError):
                    trace_nodes.append(
                        self._build_trace_node(
                            node_id=node_id,
                            status="failed",
                            attempts=attempts,
                            duration_ms=self._elapsed_ms(started_at),
                            degraded=attempts > 1,
                            failure_code="prompt_lock_error",
                            degrade_reason="retry_exhausted" if attempts > 1 else None,
                            failure_context=self._sanitize_failure_context(exc),
                        )
                    )
                    raise
                if attempt >= self._analysis_node_max_retries:
                    trace_nodes.append(
                        self._build_trace_node(
                            node_id=node_id,
                            status="failed",
                            attempts=attempts,
                            duration_ms=self._elapsed_ms(started_at),
                            degraded=attempts > 1,
                            failure_code=self._resolve_failure_code(exc, default_code="node_execution_error"),
                            degrade_reason="retry_exhausted" if attempts > 1 else None,
                            failure_context=self._sanitize_failure_context(exc),
                        )
                    )
                    raise
                attempt += 1
                self._sleep_before_retry(attempt=attempt)

    def _execute_parallel_stage(
        self,
        context: dict[str, Any],
        stage: list[str],
        trace_nodes: list[dict[str, Any]],
    ) -> None:
        symbol = context["symbol"]
        report_type = context["report_type"]
        futures_by_node: dict[
            str, Future[tuple[dict[str, Any] | None, dict[str, Any] | None, int, int, Exception | None]]
        ] = {}
        with ThreadPoolExecutor(max_workers=len(stage)) as executor:
            for node_id in stage:
                factor_key = _FACTOR_COLLECTION_NODE_MAP[node_id]
                futures_by_node[node_id] = executor.submit(
                    self._collect_factor_with_retry,
                    symbol,
                    report_type,
                    factor_key,
                )

            failed = False
            first_exception: Exception | None = None
            for node_id in stage:
                factor_key = _FACTOR_COLLECTION_NODE_MAP[node_id]
                factor_data, quality_flag, attempts, duration_ms, error = futures_by_node[node_id].result()
                if error is None and factor_data is not None:
                    self._merge_factor_result(
                        context=context,
                        factor_key=factor_key,
                        factor_data=factor_data,
                        quality_flag=quality_flag,
                    )
                    trace_nodes.append(
                        self._build_trace_node(
                            node_id=node_id,
                            status="succeeded",
                            attempts=attempts,
                            duration_ms=duration_ms,
                            degraded=attempts > 1 or quality_flag is not None,
                            degrade_reason=self._resolve_degrade_reason(attempts=attempts, quality_flag=quality_flag),
                        )
                    )
                    continue

                failed = True
                if first_exception is None and error is not None:
                    first_exception = error
                trace_nodes.append(
                    self._build_trace_node(
                        node_id=node_id,
                        status="failed",
                        attempts=attempts,
                        duration_ms=duration_ms,
                        degraded=attempts > 1,
                        failure_code=self._resolve_failure_code(error, default_code="factor_collection_error"),
                        degrade_reason="retry_exhausted" if attempts > 1 else None,
                        failure_context=self._sanitize_failure_context(error),
                    )
                )

            if failed and first_exception is not None:
                raise first_exception

    def _collect_factor_with_retry(
        self,
        symbol: str,
        report_type: str,
        factor_key: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, int, int, Exception | None]:
        attempt = 0
        started_at = time.perf_counter()
        while True:
            try:
                factor_data, quality_flag = self._factor_service.collect_factor(
                    symbol=symbol,
                    report_type=report_type,
                    factor_key=factor_key,
                )
                return factor_data, quality_flag, attempt + 1, self._elapsed_ms(started_at), None
            except Exception as exc:
                if attempt >= self._analysis_node_max_retries:
                    return None, None, attempt + 1, self._elapsed_ms(started_at), exc
                attempt += 1
                self._sleep_before_retry(attempt=attempt)

    def _sleep_before_retry(self, attempt: int) -> None:
        if self._analysis_node_retry_backoff_ms <= 0:
            return
        backoff_sec = (self._analysis_node_retry_backoff_ms / 1000.0) * (2 ** max(attempt - 1, 0))
        time.sleep(backoff_sec)

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return max(int(round((time.perf_counter() - started_at) * 1000)), 0)

    @staticmethod
    def _build_trace_node(
        node_id: str,
        status: str,
        attempts: int,
        duration_ms: int,
        degraded: bool,
        failure_code: str | None = None,
        degrade_reason: str | None = None,
        failure_context: str | None = None,
    ) -> dict[str, Any]:
        return {
            "node_id": node_id,
            "status": status,
            "attempts": max(int(attempts), 1),
            "duration_ms": max(int(duration_ms), 0),
            "degraded": bool(degraded),
            "failure_code": failure_code,
            "degrade_reason": degrade_reason,
            "failure_context": failure_context,
        }

    @staticmethod
    def _resolve_failure_code(exc: Exception | None, default_code: str) -> str:
        if isinstance(exc, PromptLockError):
            return "prompt_lock_error"
        return default_code

    @staticmethod
    def _resolve_degrade_reason(attempts: int, quality_flag: dict[str, Any] | None) -> str | None:
        has_retry = attempts > 1
        has_quality_degraded = quality_flag is not None
        if has_retry and has_quality_degraded:
            return "retry_recovered_and_factor_quality_degraded"
        if has_retry:
            return "retry_recovered"
        if has_quality_degraded:
            return "factor_quality_degraded"
        return None

    @staticmethod
    def _sanitize_failure_context(exc: Exception | None, max_length: int = 240) -> str | None:
        if exc is None:
            return None
        raw = str(exc).strip()
        if not raw:
            raw = exc.__class__.__name__
        normalized = " ".join(raw.split())
        if len(normalized) <= max_length:
            return normalized
        return normalized[: max_length - 3] + "..."

    def _merge_factor_result(
        self,
        context: dict[str, Any],
        factor_key: str,
        factor_data: dict[str, Any],
        quality_flag: dict[str, Any] | None,
    ) -> None:
        factor_pack = context.setdefault("factor_pack", self._factor_service.empty_factor_pack())
        factor_pack[factor_key] = factor_data
        if quality_flag is not None:
            factor_pack.setdefault("quality_flags", [])
            factor_pack["quality_flags"].append(quality_flag)

    def _node_resolve_strategy_context(self, context: dict[str, Any]) -> None:
        context["strategy_context"] = self._resolve_strategy_context(
            symbol=context["symbol"],
            report_type=context["report_type"],
        )

    def _node_resolve_prompt(self, context: dict[str, Any]) -> None:
        strategy_context = context.get("strategy_context")
        if strategy_context is None:
            strategy_context = self._resolve_strategy_context(
                symbol=context["symbol"],
                report_type=context["report_type"],
            )
            context["strategy_context"] = strategy_context
        context["prompt_resolution"] = self._resolve_prompt(
            symbol=context["symbol"],
            report_type=context["report_type"],
            strategy_context=strategy_context,
        )

    def _node_collect_factors(self, context: dict[str, Any]) -> None:
        context["factor_pack"] = self._factor_service.collect(
            symbol=context["symbol"],
            report_type=context["report_type"],
        )

    def _node_collect_technical_factor(self, context: dict[str, Any]) -> None:
        self._node_collect_single_factor(context=context, factor_key="technical")

    def _node_collect_macro_factor(self, context: dict[str, Any]) -> None:
        self._node_collect_single_factor(context=context, factor_key="macro")

    def _node_collect_credit_factor(self, context: dict[str, Any]) -> None:
        self._node_collect_single_factor(context=context, factor_key="credit")

    def _node_collect_sentiment_factor(self, context: dict[str, Any]) -> None:
        self._node_collect_single_factor(context=context, factor_key="sentiment")

    def _node_collect_single_factor(self, context: dict[str, Any], factor_key: str) -> None:
        factor_data, quality_flag = self._factor_service.collect_factor(
            symbol=context["symbol"],
            report_type=context["report_type"],
            factor_key=factor_key,
        )
        self._merge_factor_result(
            context=context,
            factor_key=factor_key,
            factor_data=factor_data,
            quality_flag=quality_flag,
        )

    def _node_build_dashboard(self, context: dict[str, Any]) -> None:
        factor_pack = context.get("factor_pack")
        if factor_pack is None:
            self._node_collect_factors(context)
            factor_pack = context["factor_pack"]
        else:
            full_factor_pack = self._factor_service.empty_factor_pack()
            for key in ["technical", "macro", "credit", "sentiment"]:
                if key in factor_pack:
                    full_factor_pack[key] = factor_pack[key]
            full_factor_pack["quality_flags"] = list(factor_pack.get("quality_flags", []))
            factor_pack = full_factor_pack
            context["factor_pack"] = factor_pack
        context["dashboard"] = self._factor_service.build_dashboard(factor_pack=factor_pack)

    def _node_finalize_report(self, context: dict[str, Any]) -> None:
        prompt_resolution = context.get("prompt_resolution")
        if prompt_resolution is None:
            self._node_resolve_prompt(context)
            prompt_resolution = context["prompt_resolution"]
        dashboard = context.get("dashboard")
        if dashboard is None:
            self._node_build_dashboard(context)
            dashboard = context["dashboard"]

        meta = {
            "stock_code": context["symbol"],
            "report_type": context["report_type"],
            "prompt_ref": prompt_resolution["prompt_ref"],
            "factor_quality_flags": dashboard.get("quality_flags", []),
        }
        strategy_context = context.get("strategy_context")
        if strategy_context is not None:
            meta["strategy_context"] = strategy_context

        context["meta"] = meta
        context["result"] = {
            "report": {
                "meta": meta,
                "dashboard": dashboard,
            }
        }

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
