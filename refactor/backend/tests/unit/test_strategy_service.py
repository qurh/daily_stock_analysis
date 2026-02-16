import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app


def _create_chat_session_with_messages(client: TestClient) -> str:
    created = client.post("/api/v2/chat/sessions", json={"user_id": "u-strategy", "memory_policy": "summary_v1"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]

    m1 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "我希望趋势向上时分批买入，回撤时控制仓位"},
    )
    assert m1.status_code == 200
    m2 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "如果放量突破并且风险可控，再增加仓位"},
    )
    assert m2.status_code == 200
    return session_id


def _distill_and_approve_memo(client: TestClient) -> dict:
    session_id = _create_chat_session_with_messages(client)
    distilled = client.post(
        "/api/v2/strategy/cognition/distill",
        json={"session_id": session_id},
    )
    assert distilled.status_code == 201
    memo_id = distilled.json()["memo_id"]

    reviewed = client.post(
        f"/api/v2/strategy/cognition/{memo_id}/review",
        json={"action": "approve", "reviewer": "qrh"},
    )
    assert reviewed.status_code == 200
    return reviewed.json()


def test_cognition_distill_and_review_to_knowledge_doc() -> None:
    client = TestClient(create_app())
    session_id = _create_chat_session_with_messages(client)

    distilled = client.post(
        "/api/v2/strategy/cognition/distill",
        json={"session_id": session_id},
    )
    assert distilled.status_code == 201
    payload = distilled.json()
    assert payload["status"] == "review_pending"
    assert payload["memo_id"]
    assert "Cognition Memo" in payload["title"]
    assert "Core Insights" in payload["markdown"]

    reviewed = client.post(
        f"/api/v2/strategy/cognition/{payload['memo_id']}/review",
        json={"action": "approve", "reviewer": "qrh", "editor_notes": "approved for indexing"},
    )
    assert reviewed.status_code == 200
    reviewed_payload = reviewed.json()
    assert reviewed_payload["status"] == "indexed"
    assert reviewed_payload["knowledge_doc_id"]

    doc_id = reviewed_payload["knowledge_doc_id"]
    doc_info = client.get(f"/api/v2/knowledge/documents/{doc_id}")
    assert doc_info.status_code == 200
    assert doc_info.json()["status"] == "COMPLETED"


def test_strategy_extract_and_list_versions() -> None:
    client = TestClient(create_app())
    _distill_and_approve_memo(client)

    extracted = client.post(
        "/api/v2/strategy/extract",
        json={"strategy_type": "analysis"},
    )
    assert extracted.status_code == 201
    extracted_payload = extracted.json()
    assert extracted_payload["strategy_id"]
    assert extracted_payload["strategy_type"] == "analysis"
    assert extracted_payload["status"] == "candidate"
    assert extracted_payload["version"] >= 1

    queried = client.get("/api/v2/strategy/versions", params={"strategy_type": "analysis"})
    assert queried.status_code == 200
    items = queried.json()["items"]
    assert len(items) >= 1
    assert any(item["strategy_id"] == extracted_payload["strategy_id"] for item in items)


def test_strategy_publish_gate_and_rollback() -> None:
    client = TestClient(create_app())
    _distill_and_approve_memo(client)
    extracted = client.post(
        "/api/v2/strategy/extract",
        json={"strategy_type": "trading"},
    )
    strategy_id = extracted.json()["strategy_id"]

    publish_without_gate = client.post(f"/api/v2/strategy/{strategy_id}/publish", json={})
    assert publish_without_gate.status_code == 409

    now = datetime.now(timezone.utc).isoformat()
    low_job_id = str(uuid4())
    high_job_id = str(uuid4())
    with client.app.state.database.connection() as conn:
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            )
            VALUES (?, 'market', NULL, 10, 'completed', 100, ?, 'v1', ?, ?, ?, ?)
            """,
            (
                low_job_id,
                json.dumps({"sample_size": 10, "win_rate_pct": 30.0}, ensure_ascii=False),
                now,
                now,
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO backtest_jobs (
                job_id, scope, symbol, eval_window_days, status, progress, metrics_json,
                engine_version, started_at, ended_at, created_at, updated_at
            )
            VALUES (?, 'market', NULL, 10, 'completed', 100, ?, 'v1', ?, ?, ?, ?)
            """,
            (
                high_job_id,
                json.dumps({"sample_size": 12, "win_rate_pct": 72.5}, ensure_ascii=False),
                now,
                now,
                now,
                now,
            ),
        )

    low_gate = client.post(
        f"/api/v2/strategy/{strategy_id}/publish",
        json={"backtest_job_id": low_job_id},
    )
    assert low_gate.status_code == 409

    published = client.post(
        f"/api/v2/strategy/{strategy_id}/publish",
        json={"backtest_job_id": high_job_id},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "active"
    assert published.json()["backtest_job_id"] == high_job_id

    rolled_back = client.post(
        f"/api/v2/strategy/{strategy_id}/rollback",
        json={"reason": "manual rollback"},
    )
    assert rolled_back.status_code == 200
    assert rolled_back.json()["status"] == "rolled_back"
