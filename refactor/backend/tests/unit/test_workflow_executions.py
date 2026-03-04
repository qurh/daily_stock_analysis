from fastapi.testclient import TestClient

from app.main import create_app


def test_workflow_execution_lifecycle_and_cancel_response() -> None:
    client = TestClient(create_app())

    started = client.post(
        "/api/v2/workflows/executions",
        json={"flow_id": "stock_analysis_v1", "input": {"symbol": "000001"}},
    )
    assert started.status_code == 202
    started_payload = started.json()
    assert "execution_id" in started_payload

    execution_id = started_payload["execution_id"]
    queried = client.get(f"/api/v2/workflows/executions/{execution_id}")
    assert queried.status_code == 200
    queried_payload = queried.json()
    assert queried_payload["execution_id"] == execution_id
    assert queried_payload["status"] == "succeeded"
    assert len(queried_payload["trace"]["nodes"]) >= 2
    first_node = queried_payload["trace"]["nodes"][0]
    assert first_node["attempts"] == 1
    assert isinstance(first_node["duration_ms"], int)
    assert first_node["duration_ms"] >= 0
    assert first_node["degraded"] is False
    assert first_node["failure_code"] is None
    assert first_node["degrade_reason"] is None
    assert first_node["failure_context"] is None

    cancelled = client.post(f"/api/v2/workflows/executions/{execution_id}/cancel")
    assert cancelled.status_code == 200
    cancelled_payload = cancelled.json()
    assert cancelled_payload["execution_id"] == execution_id
    assert cancelled_payload["cancelled"] is False
