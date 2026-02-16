from fastapi.testclient import TestClient

from app.main import create_app


def test_memory_summarize_and_search_flow() -> None:
    client = TestClient(create_app())

    created_session = client.post(
        "/api/v2/chat/sessions",
        json={"user_id": "u002", "memory_policy": "summary_v1"},
    )
    assert created_session.status_code == 201
    session_id = created_session.json()["session_id"]

    sent = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "My core strategy is momentum follow with strict risk control."},
    )
    assert sent.status_code == 200

    summarized = client.post(f"/api/v2/memory/sessions/{session_id}/summarize")
    assert summarized.status_code == 200
    summary_payload = summarized.json()
    assert summary_payload["session_id"] == session_id
    assert summary_payload["summary_id"] != ""
    assert summary_payload["long_term_entry_id"] != ""

    memory_view = client.get(f"/api/v2/memory/sessions/{session_id}")
    assert memory_view.status_code == 200
    memory_payload = memory_view.json()
    assert memory_payload["session_id"] == session_id
    assert len(memory_payload["summaries"]) >= 1

    searched = client.post(
        "/api/v2/memory/search",
        json={"query": "momentum risk control", "top_k": 3},
    )
    assert searched.status_code == 200
    search_payload = searched.json()
    assert len(search_payload["hits"]) >= 1
    assert search_payload["hits"][0]["source_session_id"] == session_id


def test_memory_delete_session_cleans_data() -> None:
    client = TestClient(create_app())

    created_session = client.post("/api/v2/chat/sessions", json={"user_id": "u003"})
    assert created_session.status_code == 201
    session_id = created_session.json()["session_id"]

    sent = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "Unique phrase for cleanup verification."},
    )
    assert sent.status_code == 200

    summarized = client.post(f"/api/v2/memory/sessions/{session_id}/summarize")
    assert summarized.status_code == 200

    deleted = client.delete(f"/api/v2/memory/sessions/{session_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    messages = client.get(f"/api/v2/chat/sessions/{session_id}/messages")
    assert messages.status_code == 404

    searched = client.post(
        "/api/v2/memory/search",
        json={"query": "cleanup verification", "top_k": 3},
    )
    assert searched.status_code == 200
    assert searched.json()["hits"] == []
