from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def test_real_llm_chat_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if not _is_enabled(os.getenv("ENABLE_REAL_LLM_SMOKE", "0")):
        pytest.skip("Real LLM smoke disabled. Set ENABLE_REAL_LLM_SMOKE=1 to run.")

    provider_name = (os.getenv("LLM_PROVIDER") or "openai-compatible").strip() or "openai-compatible"
    if provider_name == "mock-llm":
        provider_name = "openai-compatible"

    default_key_name = "DASHSCOPE_API_KEY" if provider_name in {"dashscope", "dashscope-sdk"} else "LLM_API_KEY"
    api_key = (
        os.getenv(default_key_name)
        or os.getenv("LLM_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or ""
    ).strip()
    if not api_key:
        pytest.skip(f"{default_key_name} is not set.")

    model_name = (os.getenv("LLM_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    base_url = (os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").strip() or "https://api.openai.com/v1"
    timeout_sec = (os.getenv("LLM_TIMEOUT_SEC") or "30").strip() or "30"
    dashscope_base_http_api_url = (
        os.getenv("DASHSCOPE_BASE_HTTP_API_URL") or "https://dashscope.aliyuncs.com/api/v1"
    ).strip()
    dashscope_enable_thinking = os.getenv("DASHSCOPE_ENABLE_THINKING", "false").strip()

    db_file = tmp_path / "real-llm-smoke.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("QUEUE_AUTO_PROCESS", "true")
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("CHROMA_COLLECTION", "smoke_knowledge")
    monkeypatch.setenv("MEMORY_COLLECTION", "smoke_memory")
    monkeypatch.setenv("LLM_PROVIDER", provider_name)
    monkeypatch.setenv("LLM_MODEL", model_name)
    monkeypatch.setenv("LLM_API_KEY", api_key)
    monkeypatch.setenv("LLM_BASE_URL", base_url)
    monkeypatch.setenv("LLM_TIMEOUT_SEC", timeout_sec)
    monkeypatch.setenv("DASHSCOPE_API_KEY", api_key)
    monkeypatch.setenv("DASHSCOPE_BASE_HTTP_API_URL", dashscope_base_http_api_url)
    monkeypatch.setenv("DASHSCOPE_ENABLE_THINKING", dashscope_enable_thinking)

    from app.main import create_app

    client = TestClient(create_app())
    created_session = client.post(
        "/api/v2/chat/sessions",
        json={"user_id": "smoke-user", "memory_policy": "summary_v1"},
    )
    assert created_session.status_code == 201
    session_id = created_session.json()["session_id"]

    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "Reply with one short sentence about trend and risk."},
    )
    assert replied.status_code == 200
    payload = replied.json()
    assert payload["session_id"] == session_id
    assistant = payload["assistant"]
    assert assistant["role"] == "assistant"
    assert isinstance(assistant["content"], str)
    assert assistant["content"].strip() != ""
    assert assistant["tool_trace"]["llm_provider"] == provider_name
    assert assistant["tool_trace"]["llm_model"] == model_name
