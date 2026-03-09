from __future__ import annotations

import json
import re
from typing import Any

from app.llm.provider import LLMProvider
from app.services.agent_service import AgentService
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.prompt_lock_audit_service import PromptLockAuditService
from app.services.prompt_routing import (
    PromptLockError,
    normalize_lock_mode,
    normalize_prompt_refs,
    resolve_binding_prompt,
)
from app.services.prompt_service import PromptService
from app.services.strategy_service import StrategyService


class ChatService:
    """Chat application service for multi-turn conversation and RAG citations."""

    def __init__(
        self,
        memory_service: MemoryService,
        knowledge_service: KnowledgeService,
        prompt_service: PromptService,
        llm_provider: LLMProvider,
        strategy_service: StrategyService | None = None,
        prompt_lock_audit_service: PromptLockAuditService | None = None,
        default_prompt_lock_mode: str = "lenient",
        agent_service: AgentService | None = None,
    ) -> None:
        self._memory_service = memory_service
        self._knowledge_service = knowledge_service
        self._prompt_service = prompt_service
        self._llm_provider = llm_provider
        self._strategy_service = strategy_service
        self._prompt_lock_audit_service = prompt_lock_audit_service
        self._default_prompt_lock_mode = normalize_lock_mode(default_prompt_lock_mode)
        self._agent_service = agent_service

    def create_session(self, user_id: str, memory_policy: str = "summary_v1") -> dict[str, Any]:
        return self._memory_service.create_session(user_id=user_id, memory_policy=memory_policy)

    def handle_message(self, session_id: str, content: str) -> dict[str, Any]:
        self._memory_service.append_message(
            session_id=session_id,
            role="user",
            content=content,
            citations=[],
            tool_trace={},
        )

        knowledge_hits = self._knowledge_service.search_chunks(query=content, top_k=3)["hits"]
        memory_hits = self._memory_service.search_long_term(query=content, top_k=2)["hits"]
        citations = _build_citations(knowledge_hits=knowledge_hits, memory_hits=memory_hits)

        knowledge_hint = knowledge_hits[0].get("summary", "") if knowledge_hits else ""
        memory_hint = memory_hits[0].get("content", "") if memory_hits else ""
        symbol_context = self._extract_symbol_context(content=content)
        agent_trace = self._invoke_agent(session_id=session_id, content=content, symbol_context=symbol_context)
        agent_hint = self._build_agent_hint(agent_trace=agent_trace)
        strategy_context = self._resolve_strategy_context()
        try:
            prompt_resolution = self._resolve_prompt(
                question=content,
                knowledge_hint=knowledge_hint,
                memory_hint=memory_hint,
                agent_hint=agent_hint,
                strategy_context=strategy_context,
            )
        except PromptLockError as exc:
            if self._prompt_lock_audit_service is not None:
                self._prompt_lock_audit_service.record_event(
                    flow_id=exc.flow_id,
                    lock_mode=exc.lock_mode,
                    source_type="chat",
                    source_id=session_id,
                    requested_prompt_refs=exc.requested_prompt_refs,
                    failures=exc.failures,
                )
            raise
        assistant_content = self._llm_provider.generate(prompt_resolution["rendered_prompt"])
        tool_trace = {
            "knowledge_hit_count": len(knowledge_hits),
            "memory_hit_count": len(memory_hits),
            "prompt_ref": prompt_resolution["prompt_ref"],
            "llm_provider": self._llm_provider.provider_name,
            "llm_model": self._llm_provider.model_name,
        }
        if agent_trace is not None:
            tool_trace["agent_trace"] = agent_trace
        merged_symbol_context = self._merge_symbol_context(symbol_context=symbol_context, agent_trace=agent_trace)
        if merged_symbol_context is not None:
            tool_trace["symbol_context"] = merged_symbol_context
        if strategy_context is not None:
            tool_trace["strategy_id"] = strategy_context["strategy_id"]
            tool_trace["strategy_binding_id"] = strategy_context["binding_id"]
            tool_trace["strategy_flow_id"] = strategy_context["flow_id"]
        assistant = self._memory_service.append_message(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            citations=citations,
            tool_trace=tool_trace,
        )
        return {"session_id": session_id, "assistant": assistant}

    def list_messages(self, session_id: str) -> dict[str, Any]:
        return self._memory_service.list_messages(session_id=session_id)

    def _resolve_prompt(
        self,
        question: str,
        knowledge_hint: str,
        memory_hint: str,
        agent_hint: str = "",
        strategy_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        variables = {
            "question": question,
            "knowledge_hint": knowledge_hint,
            "memory_hint": memory_hint,
            "agent_hint": agent_hint,
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
                flow_id="chat_reply_v1",
                lock_mode=lock_mode,
                requested_prompt_refs=binding_prompt_refs,
                failures=failures,
            )

        for prompt_id in ["prompt.chat.reply"]:
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

        fallback_prompt = (
            f"Q={question}\n"
            f"K={knowledge_hint}\n"
            f"M={memory_hint}\n"
            f"A={agent_hint}\n"
            "Return concise answer with actionable next step."
        )
        return {
            "prompt_ref": "builtin.chat.reply@0",
            "rendered_prompt": fallback_prompt,
        }

    def _resolve_strategy_context(self) -> dict[str, Any] | None:
        if self._strategy_service is None:
            return None
        return self._strategy_service.resolve_active_binding(flow_id="chat_reply_v1")

    def _resolve_prompt_lock_mode(self, strategy_context: dict[str, Any] | None) -> str:
        if strategy_context is None:
            return self._default_prompt_lock_mode
        return normalize_lock_mode(strategy_context.get("prompt_lock_mode"), self._default_prompt_lock_mode)

    def _invoke_agent(
        self,
        session_id: str,
        content: str,
        symbol_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if self._agent_service is None:
            return None

        payload: dict[str, Any] = {"query": content, "top_k": 3}
        context: dict[str, Any] = {"session_id": session_id}
        if symbol_context is not None:
            payload["symbol"] = symbol_context["symbol"]
            payload["resolved_name"] = symbol_context["resolved_name"]
            payload["aliases"] = list(symbol_context.get("aliases", []))
            context["entity_context"] = {
                "symbol": symbol_context["symbol"],
                "resolved_name": symbol_context["resolved_name"],
                "aliases": list(symbol_context.get("aliases", [])),
            }
        try:
            return self._agent_service.invoke_with_intent(
                intent=content,
                payload=payload,
                context=context,
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "intent": content,
                "planned_tools": [],
                "results": {},
                "degraded": True,
                "failed_tools": ["agent.runtime"],
                "entity_context": context.get("entity_context"),
                "trace": [
                    {
                        "call_id": "agent-runtime",
                        "tool_name": "agent.runtime",
                        "status": "failed",
                        "latency_ms": 0,
                        "attempts": 1,
                        "error_code": "AGT-ROUTE-001",
                        "error_message": str(exc),
                    }
                ],
            }

    @staticmethod
    def _build_agent_hint(agent_trace: dict[str, Any] | None) -> str:
        if agent_trace is None:
            return ""
        payload = {
            "planned_tools": agent_trace.get("planned_tools", []),
            "degraded": bool(agent_trace.get("degraded", False)),
            "results": agent_trace.get("results", {}),
            "entity_context": agent_trace.get("entity_context"),
        }
        serialized = json.dumps(payload, ensure_ascii=False)
        return serialized if len(serialized) <= 320 else f"{serialized[:317]}..."

    @staticmethod
    def _extract_symbol_context(content: str) -> dict[str, Any] | None:
        cn_match = re.search(r"(?P<symbol>(?:0|3|6)\d{5})", content or "")
        if cn_match is not None:
            symbol = cn_match.group("symbol")
            prefix_window = (content or "")[max(0, cn_match.start() - 24) : cn_match.start()]
            name_match = re.search(r"([A-Za-z\u4e00-\u9fff]{2,20})\s*$", prefix_window)
            resolved_name = symbol
            if name_match is not None:
                resolved_name = ChatService._clean_name_token(name_match.group(1), fallback=symbol)
            aliases = []
            for alias in [symbol, resolved_name]:
                if alias not in aliases:
                    aliases.append(alias)
            return {
                "symbol": symbol,
                "resolved_name": resolved_name,
                "aliases": aliases,
                "market": "cn",
                "parser": "chat_symbol_parser_v1",
            }

        us_match = re.search(r"\$(?P<symbol>[A-Z]{1,5})\b", content or "")
        if us_match is not None:
            symbol = us_match.group("symbol")
            return {
                "symbol": symbol,
                "resolved_name": symbol,
                "aliases": [symbol],
                "market": "us",
                "parser": "chat_symbol_parser_v1",
            }
        return None

    @staticmethod
    def _clean_name_token(raw: str, fallback: str) -> str:
        value = (raw or "").strip()
        if not value:
            return fallback
        for prefix in ["请分析", "分析", "请问", "请帮我", "帮我", "看看", "看下", "请"]:
            if value.startswith(prefix) and len(value) > len(prefix):
                value = value[len(prefix) :].strip()
        if not value:
            return fallback
        return value

    @staticmethod
    def _merge_symbol_context(
        symbol_context: dict[str, Any] | None,
        agent_trace: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        merged: dict[str, Any] = {}
        if symbol_context is not None:
            merged.update(symbol_context)
        if agent_trace is not None and isinstance(agent_trace.get("entity_context"), dict):
            merged.update(agent_trace["entity_context"])
        if "symbol" not in merged:
            return None
        aliases = merged.get("aliases")
        if not isinstance(aliases, list):
            aliases = []
        deduped_aliases: list[str] = []
        for alias in aliases + [merged.get("symbol"), merged.get("resolved_name")]:
            text = str(alias).strip() if alias is not None else ""
            if not text or text in deduped_aliases:
                continue
            deduped_aliases.append(text)
        merged["aliases"] = deduped_aliases
        if "resolved_name" not in merged or not str(merged["resolved_name"]).strip():
            merged["resolved_name"] = merged["symbol"]
        return merged


def _build_citations(knowledge_hits: list[dict[str, Any]], memory_hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for item in knowledge_hits[:3]:
        citations.append(
            {
                "source_type": "knowledge",
                "doc_id": item.get("doc_id", ""),
                "chunk_id": item.get("chunk_id", ""),
                "section_path": item.get("section_path", ""),
                "score": item.get("score", 0.0),
            }
        )
    for item in memory_hits[:2]:
        citations.append(
            {
                "source_type": "memory",
                "entry_id": item.get("entry_id", ""),
                "source_session_id": item.get("source_session_id", ""),
                "topic": item.get("topic", ""),
                "score": item.get("score", 0.0),
            }
        )
    return citations
