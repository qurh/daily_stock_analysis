from fastapi.testclient import TestClient

from app.llm.provider import LLMProviderError
from app.main import create_app


def test_chat_multi_turn_with_rag_citations() -> None:
    client = TestClient(create_app())

    uploaded = client.post(
        "/api/v2/knowledge/documents/upload",
        json={
            "title": "volume playbook",
            "markdown": "# Volume\nVolume expansion confirms momentum breakout.",
            "tags": ["volume"],
        },
    )
    assert uploaded.status_code == 201
    doc_id = uploaded.json()["doc_id"]

    ingested = client.post(f"/api/v2/knowledge/documents/{doc_id}/ingest")
    assert ingested.status_code == 202

    created_session = client.post(
        "/api/v2/chat/sessions",
        json={"user_id": "u001", "memory_policy": "summary_v1"},
    )
    assert created_session.status_code == 201
    session_id = created_session.json()["session_id"]

    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "How to confirm momentum with volume?"},
    )
    assert replied.status_code == 200
    reply_payload = replied.json()
    assert reply_payload["session_id"] == session_id
    assert reply_payload["assistant"]["role"] == "assistant"
    assert len(reply_payload["assistant"]["citations"]) >= 1
    assert reply_payload["assistant"]["citations"][0]["source_type"] == "knowledge"
    assert reply_payload["assistant"]["citations"][0]["doc_id"] == doc_id

    messages = client.get(f"/api/v2/chat/sessions/{session_id}/messages")
    assert messages.status_code == 200
    message_payload = messages.json()
    assert len(message_payload["messages"]) >= 2
    assert message_payload["messages"][-2]["role"] == "user"
    assert message_payload["messages"][-1]["role"] == "assistant"


def test_chat_maps_llm_provider_error(monkeypatch) -> None:
    def fake_generate(self, prompt: str) -> str:  # noqa: ARG001
        raise LLMProviderError(
            provider="dashscope",
            status_code=400,
            error_code="InvalidParameter",
            error_message="Model not exist.",
            category="model_config",
            retryable=False,
        )

    monkeypatch.setattr("app.llm.provider.MockLLMProvider.generate", fake_generate)
    client = TestClient(create_app())

    created_session = client.post(
        "/api/v2/chat/sessions",
        json={"user_id": "u002", "memory_policy": "summary_v1"},
    )
    assert created_session.status_code == 201
    session_id = created_session.json()["session_id"]

    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "test llm failure"},
    )
    assert replied.status_code == 502
    payload = replied.json()
    assert payload["detail"]["provider"] == "dashscope"
    assert payload["detail"]["category"] == "model_config"
    assert payload["detail"]["retryable"] is False


def test_chat_maps_circuit_open_error_to_503(monkeypatch) -> None:
    def fake_generate(self, prompt: str) -> str:  # noqa: ARG001
        raise LLMProviderError(
            provider="dashscope",
            status_code=None,
            error_code="CircuitOpen",
            error_message="Circuit breaker open.",
            category="circuit_open",
            retryable=True,
        )

    monkeypatch.setattr("app.llm.provider.MockLLMProvider.generate", fake_generate)
    client = TestClient(create_app())
    created_session = client.post("/api/v2/chat/sessions", json={"user_id": "u003"})
    session_id = created_session.json()["session_id"]

    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "trigger circuit open"},
    )
    assert replied.status_code == 503
    payload = replied.json()
    assert payload["detail"]["category"] == "circuit_open"
    assert payload["detail"]["retryable"] is True
