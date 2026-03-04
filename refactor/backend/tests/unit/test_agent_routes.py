from fastapi.testclient import TestClient

from app.main import create_app


def test_agent_routes_register_list_and_invoke() -> None:
    client = TestClient(create_app())

    listed_before = client.get("/api/v2/agent/tools")
    assert listed_before.status_code == 200
    assert listed_before.json()["count"] >= 3

    registered = client.post(
        "/api/v2/agent/tools/register",
        json={
            "name": "custom.echo",
            "version": "v1",
            "description": "echo static payload",
            "timeout_sec": 2,
            "max_retries": 0,
            "keywords": ["echo"],
            "static_response": {"message": "ok"},
            "degrade_payload": {"message": "degraded"},
            "overwrite": True,
        },
    )
    assert registered.status_code == 201
    assert registered.json()["name"] == "custom.echo"

    invoked = client.post(
        "/api/v2/agent/invoke",
        json={
            "intent": "run echo",
            "payload": {"query": "test"},
            "context": {"session_id": "s1"},
            "force_tools": ["custom.echo"],
        },
    )
    assert invoked.status_code == 200
    payload = invoked.json()
    assert payload["results"]["custom.echo"]["message"] == "ok"
    assert payload["trace"][0]["tool_name"] == "custom.echo"
    assert payload["trace"][0]["status"] == "succeeded"


def test_agent_routes_reject_unknown_tool() -> None:
    client = TestClient(create_app())
    invoked = client.post(
        "/api/v2/agent/invoke",
        json={
            "intent": "unknown",
            "payload": {"query": "test"},
            "force_tools": ["tool.missing"],
        },
    )
    assert invoked.status_code == 404
    assert "AGT-TOOL-002" in str(invoked.json()["detail"])
