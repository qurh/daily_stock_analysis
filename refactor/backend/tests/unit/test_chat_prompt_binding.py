from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_uses_active_prompt_version_and_llm_provider_trace() -> None:
    client = TestClient(create_app())

    created_template = client.post(
        "/api/v2/prompts/templates",
        json={"prompt_id": "prompt.chat.reply", "name": "chat reply", "module": "chat"},
    )
    assert created_template.status_code == 201

    version_1 = client.post(
        "/api/v2/prompts/templates/prompt.chat.reply/versions",
        json={
            "content": "Q={{question}}; K={{knowledge_hint}}; M={{memory_hint}}",
            "variables": ["question", "knowledge_hint", "memory_hint"],
            "output_schema": "chat_reply_v1",
        },
    )
    assert version_1.status_code == 201
    assert version_1.json()["version"] == 1

    published = client.post("/api/v2/prompts/templates/prompt.chat.reply/versions/1/publish")
    assert published.status_code == 200
    assert published.json()["active_version"] == 1

    uploaded = client.post(
        "/api/v2/knowledge/documents/upload",
        json={
            "title": "breakout",
            "markdown": "# Breakout\nVolume breakout confirms trend continuation.",
            "tags": ["breakout"],
        },
    )
    assert uploaded.status_code == 201
    doc_id = uploaded.json()["doc_id"]
    ingested = client.post(f"/api/v2/knowledge/documents/{doc_id}/ingest")
    assert ingested.status_code == 202

    created_session = client.post("/api/v2/chat/sessions", json={"user_id": "u-prompt"})
    assert created_session.status_code == 201
    session_id = created_session.json()["session_id"]

    replied = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "How to verify breakout?"},
    )
    assert replied.status_code == 200
    assistant = replied.json()["assistant"]

    assert assistant["content"].startswith("[mock-llm]")
    assert assistant["tool_trace"]["prompt_ref"] == "prompt.chat.reply@1"
    assert assistant["tool_trace"]["llm_provider"] == "mock-llm"
    assert "How to verify breakout?" in assistant["content"]
