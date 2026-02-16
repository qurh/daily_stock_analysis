import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app


def _create_chat_session_with_messages(client: TestClient) -> str:
    created = client.post("/api/v2/chat/sessions", json={"user_id": "u-bind", "memory_policy": "summary_v1"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]
    m1 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "趋势上行时分批买入，回撤控制仓位"},
    )
    assert m1.status_code == 200
    m2 = client.post(
        f"/api/v2/chat/sessions/{session_id}/messages",
        json={"content": "放量突破且风险可控时再加仓"},
    )
    assert m2.status_code == 200
    return session_id


def _create_strategy_candidate(client: TestClient, strategy_type: str = "analysis") -> str:
    session_id = _create_chat_session_with_messages(client)
    distilled = client.post("/api/v2/strategy/cognition/distill", json={"session_id": session_id})
    assert distilled.status_code == 201
    memo_id = distilled.json()["memo_id"]
    reviewed = client.post(
        f"/api/v2/strategy/cognition/{memo_id}/review", json={"action": "approve", "reviewer": "qrh"}
    )
    assert reviewed.status_code == 200
    extracted = client.post("/api/v2/strategy/extract", json={"strategy_type": strategy_type})
    assert extracted.status_code == 201
    return extracted.json()["strategy_id"]


def _create_passing_backtest_job(client: TestClient) -> str:
    now = datetime.now(timezone.utc).isoformat()
    backtest_job_id = str(uuid4())
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
                backtest_job_id,
                json.dumps({"sample_size": 12, "win_rate_pct": 72.5}, ensure_ascii=False),
                now,
                now,
                now,
                now,
            ),
        )
    return backtest_job_id


def _create_active_strategy(client: TestClient, strategy_type: str = "analysis") -> str:
    strategy_id = _create_strategy_candidate(client, strategy_type=strategy_type)
    backtest_job_id = _create_passing_backtest_job(client)
    published = client.post(
        f"/api/v2/strategy/{strategy_id}/publish",
        json={"backtest_job_id": backtest_job_id},
    )
    assert published.status_code == 200
    return strategy_id


def test_bind_active_strategy_and_list_bindings() -> None:
    client = TestClient(create_app())
    strategy_id = _create_active_strategy(client, strategy_type="analysis")

    bound = client.post(
        f"/api/v2/strategy/{strategy_id}/bind",
        json={
            "flow_id": "stock_analysis_v1",
            "prompt_refs": ["prompt.chat.reply@1"],
            "effective_scope": {"symbols": ["600519"], "report_type": "detailed"},
        },
    )
    assert bound.status_code == 201
    binding_payload = bound.json()
    assert binding_payload["binding_id"]
    assert binding_payload["status"] == "active"
    assert binding_payload["strategy_id"] == strategy_id
    assert binding_payload["flow_id"] == "stock_analysis_v1"

    queried = client.get("/api/v2/strategy/bindings", params={"flow_id": "stock_analysis_v1"})
    assert queried.status_code == 200
    queried_payload = queried.json()
    assert queried_payload["count"] >= 1
    assert any(item["binding_id"] == binding_payload["binding_id"] for item in queried_payload["items"])


def test_bind_requires_active_strategy() -> None:
    client = TestClient(create_app())
    candidate_id = _create_strategy_candidate(client, strategy_type="trading")
    bound = client.post(
        f"/api/v2/strategy/{candidate_id}/bind",
        json={"flow_id": "stock_analysis_v1", "prompt_refs": ["prompt.chat.reply@1"]},
    )
    assert bound.status_code == 409


def test_rebind_same_flow_deactivates_previous_binding() -> None:
    client = TestClient(create_app())
    strategy_id_1 = _create_active_strategy(client, strategy_type="analysis")

    first = client.post(
        f"/api/v2/strategy/{strategy_id_1}/bind",
        json={"flow_id": "stock_analysis_v1", "prompt_refs": ["prompt.chat.reply@1"]},
    )
    assert first.status_code == 201

    strategy_id_2 = _create_active_strategy(client, strategy_type="analysis")
    second = client.post(
        f"/api/v2/strategy/{strategy_id_2}/bind",
        json={"flow_id": "stock_analysis_v1", "prompt_refs": ["prompt.chat.reply@2"]},
    )
    assert second.status_code == 201

    queried = client.get("/api/v2/strategy/bindings", params={"flow_id": "stock_analysis_v1"})
    assert queried.status_code == 200
    items = queried.json()["items"]
    active_items = [item for item in items if item["status"] == "active"]
    assert len(active_items) == 1
    assert active_items[0]["strategy_id"] == strategy_id_2
    assert any(item["strategy_id"] == strategy_id_1 and item["status"] == "inactive" for item in items)
