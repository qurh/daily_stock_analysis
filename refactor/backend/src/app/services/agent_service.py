from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable
from uuid import uuid4


ToolExecutor = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    version: str
    description: str
    timeout_sec: int
    max_retries: int
    keywords: tuple[str, ...]
    degrade_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "timeout_sec": self.timeout_sec,
            "max_retries": self.max_retries,
            "keywords": list(self.keywords),
            "degrade_payload": self.degrade_payload,
        }


class ToolNotFoundError(KeyError):
    """Raised when a requested tool is not registered."""


class AgentService:
    """Tool registry, intent planning and runtime execution with retry/degrade trace."""

    def __init__(
        self,
        knowledge_service: Any,
        memory_service: Any,
        backtest_service: Any,
        workflow_service: Any,
        default_max_retries: int = 0,
        retry_backoff_ms: int = 0,
    ) -> None:
        self._knowledge_service = knowledge_service
        self._memory_service = memory_service
        self._backtest_service = backtest_service
        self._workflow_service = workflow_service
        self._default_max_retries = max(int(default_max_retries), 0)
        self._retry_backoff_ms = max(int(retry_backoff_ms), 0)
        self._registry: dict[str, tuple[ToolSpec, ToolExecutor]] = {}
        self._register_builtin_tools()

    def register_tool(self, tool_spec: ToolSpec, executor: ToolExecutor, overwrite: bool = False) -> dict[str, Any]:
        normalized_name = self._normalize_tool_name(tool_spec.name)
        if not normalized_name:
            raise ValueError("Tool name is required")

        if normalized_name in self._registry and not overwrite:
            raise ValueError(f"Tool already registered: {normalized_name}")

        normalized_spec = ToolSpec(
            name=normalized_name,
            version=(tool_spec.version or "v1").strip() or "v1",
            description=(tool_spec.description or "").strip() or normalized_name,
            timeout_sec=max(int(tool_spec.timeout_sec), 1),
            max_retries=max(int(tool_spec.max_retries), 0),
            keywords=self._normalize_keywords(tool_spec.keywords),
            degrade_payload=None if tool_spec.degrade_payload is None else dict(tool_spec.degrade_payload),
        )
        self._registry[normalized_name] = (normalized_spec, executor)
        return normalized_spec.to_dict()

    def register_static_tool(
        self,
        tool_spec: ToolSpec,
        static_response: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        static_payload = dict(static_response)

        def _executor(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
            response = dict(static_payload)
            if payload:
                response.setdefault("payload", payload)
            if context:
                response.setdefault("context", context)
            return response

        return self.register_tool(tool_spec=tool_spec, executor=_executor, overwrite=overwrite)

    def list_tools(self) -> list[dict[str, Any]]:
        items = [item[0].to_dict() for item in self._registry.values()]
        return sorted(items, key=lambda item: item["name"])

    def plan(self, intent: str, context: dict[str, Any] | None = None, force_tools: list[str] | None = None) -> list[str]:
        if force_tools:
            planned_tools = []
            for raw_name in force_tools:
                normalized_name = self._normalize_tool_name(raw_name)
                if normalized_name not in self._registry:
                    raise ToolNotFoundError(f"AGT-TOOL-002: tool not registered: {normalized_name}")
                if normalized_name not in planned_tools:
                    planned_tools.append(normalized_name)
            return planned_tools

        normalized_intent = (intent or "").strip().lower()
        planned_tools: list[str] = []
        for tool_name, (spec, _) in self._registry.items():
            if not spec.keywords:
                continue
            if any(keyword in normalized_intent for keyword in spec.keywords):
                planned_tools.append(tool_name)

        if planned_tools:
            return planned_tools

        fallback_tools: list[str] = []
        for fallback_name in ["knowledge.search", "memory.search"]:
            if fallback_name in self._registry:
                fallback_tools.append(fallback_name)
        return fallback_tools

    def invoke(
        self,
        intent: str,
        payload: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        force_tools: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_payload = dict(payload or {})
        resolved_context = dict(context or {})
        planned_tools = self.plan(intent=intent, context=resolved_context, force_tools=force_tools)

        results: dict[str, Any] = {}
        failed_tools: list[str] = []
        trace: list[dict[str, Any]] = []
        degraded = False
        for tool_name in planned_tools:
            spec, executor = self._registry[tool_name]
            call_trace, result = self._execute_tool(
                tool_spec=spec,
                executor=executor,
                payload=resolved_payload,
                context=resolved_context,
            )
            trace.append(call_trace)
            if call_trace["status"] == "failed":
                failed_tools.append(tool_name)
            elif result is not None:
                results[tool_name] = result
            if call_trace["status"] == "degraded":
                degraded = True

        return {
            "intent": intent,
            "planned_tools": planned_tools,
            "results": results,
            "degraded": degraded,
            "failed_tools": failed_tools,
            "trace": trace,
        }

    def invoke_with_intent(
        self,
        intent: str,
        payload: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.invoke(intent=intent, payload=payload, context=context)

    def _execute_tool(
        self,
        tool_spec: ToolSpec,
        executor: ToolExecutor,
        payload: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        max_retries = max(tool_spec.max_retries, self._default_max_retries)
        max_attempts = max_retries + 1
        started_at = time.perf_counter()
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = executor(dict(payload), dict(context))
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                return (
                    {
                        "call_id": str(uuid4()),
                        "tool_name": tool_spec.name,
                        "status": "succeeded",
                        "latency_ms": latency_ms,
                        "attempts": attempt,
                        "error_code": None,
                        "error_message": None,
                    },
                    result,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < max_attempts:
                    self._sleep_with_backoff(attempt)
                    continue

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        error_code = self._map_call_error(last_error)
        if tool_spec.degrade_payload is not None:
            return (
                {
                    "call_id": str(uuid4()),
                    "tool_name": tool_spec.name,
                    "status": "degraded",
                    "latency_ms": latency_ms,
                    "attempts": max_attempts,
                    "error_code": error_code,
                    "error_message": str(last_error) if last_error is not None else None,
                },
                dict(tool_spec.degrade_payload),
            )

        return (
            {
                "call_id": str(uuid4()),
                "tool_name": tool_spec.name,
                "status": "failed",
                "latency_ms": latency_ms,
                "attempts": max_attempts,
                "error_code": "AGT-FALLBACK-004",
                "error_message": str(last_error) if last_error is not None else None,
            },
            None,
        )

    def _sleep_with_backoff(self, attempt: int) -> None:
        if self._retry_backoff_ms <= 0:
            return
        delay_ms = self._retry_backoff_ms * (2 ** max(attempt - 1, 0))
        time.sleep(min(delay_ms / 1000.0, 1.0))

    @staticmethod
    def _map_call_error(error: Exception | None) -> str:
        if isinstance(error, TimeoutError):
            return "AGT-CALL-003"
        return "AGT-CALL-003"

    @staticmethod
    def _normalize_tool_name(name: str) -> str:
        return (name or "").strip().lower()

    @staticmethod
    def _normalize_keywords(keywords: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        normalized = [str(item).strip().lower() for item in keywords if str(item).strip()]
        return tuple(normalized)

    def _register_builtin_tools(self) -> None:
        self.register_tool(
            ToolSpec(
                name="knowledge.search",
                version="v1",
                description="Search vectorized knowledge chunks",
                timeout_sec=5,
                max_retries=self._default_max_retries,
                keywords=("知识", "文档", "knowledge", "memo", "资料", "citation"),
                degrade_payload={"hits": [], "degraded": True, "reason": "knowledge_search_unavailable"},
            ),
            self._run_knowledge_search,
            overwrite=True,
        )
        self.register_tool(
            ToolSpec(
                name="memory.search",
                version="v1",
                description="Search long-term memory entries",
                timeout_sec=5,
                max_retries=self._default_max_retries,
                keywords=("记忆", "历史", "memory", "之前", "回忆"),
                degrade_payload={"hits": [], "degraded": True, "reason": "memory_search_unavailable"},
            ),
            self._run_memory_search,
            overwrite=True,
        )
        self.register_tool(
            ToolSpec(
                name="backtest.performance",
                version="v1",
                description="Get backtest aggregate performance",
                timeout_sec=5,
                max_retries=self._default_max_retries,
                keywords=("回测", "收益", "胜率", "backtest", "performance"),
                degrade_payload={"metrics": {}, "degraded": True, "reason": "backtest_performance_unavailable"},
            ),
            self._run_backtest_performance,
            overwrite=True,
        )
        self.register_tool(
            ToolSpec(
                name="workflow.execution.get",
                version="v1",
                description="Get workflow execution details",
                timeout_sec=5,
                max_retries=self._default_max_retries,
                keywords=("流程", "工作流", "执行", "trace", "workflow"),
                degrade_payload={"status": "missing", "degraded": True, "reason": "workflow_lookup_unavailable"},
            ),
            self._run_workflow_lookup,
            overwrite=True,
        )

    def _run_knowledge_search(self, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG002
        query = str(payload.get("query") or "").strip()
        if not query:
            raise ValueError("query is required for knowledge.search")
        top_k = int(payload.get("top_k") or 3)
        top_k = max(min(top_k, 20), 1)
        doc_id = payload.get("doc_id")
        normalized_doc_id = str(doc_id).strip() if doc_id is not None else None
        return self._knowledge_service.search_chunks(query=query, top_k=top_k, doc_id=normalized_doc_id or None)

    def _run_memory_search(self, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG002
        query = str(payload.get("query") or "").strip()
        if not query:
            raise ValueError("query is required for memory.search")
        top_k = int(payload.get("top_k") or 2)
        top_k = max(min(top_k, 20), 1)
        return self._memory_service.search_long_term(query=query, top_k=top_k)

    def _run_backtest_performance(self, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG002
        job_id = self._optional_str(payload.get("job_id"))
        symbol = self._optional_str(payload.get("symbol"))
        return self._backtest_service.aggregate(job_id=job_id, symbol=symbol)

    def _run_workflow_lookup(self, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        execution_id = self._optional_str(payload.get("execution_id")) or self._optional_str(context.get("execution_id"))
        if not execution_id:
            raise ValueError("execution_id is required for workflow.execution.get")
        execution = self._workflow_service.get_execution(execution_id=execution_id)
        if execution is None:
            return {"execution_id": execution_id, "status": "missing"}
        return execution

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
