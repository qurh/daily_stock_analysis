from fastapi.testclient import TestClient

from app.main import create_app
from app.services.agent_service import ToolSpec


def test_agent_service_lists_builtin_tools() -> None:
    client = TestClient(create_app())
    service = client.app.state.agent_service

    tools = service.list_tools()
    tool_names = {item["name"] for item in tools}
    assert "knowledge.search" in tool_names
    assert "memory.search" in tool_names
    assert "backtest.performance" in tool_names


def test_agent_service_retries_and_degrades_on_failure() -> None:
    client = TestClient(create_app())
    service = client.app.state.agent_service
    attempts = {"count": 0}

    def always_fail(payload, context):  # noqa: ARG001
        attempts["count"] += 1
        raise RuntimeError("boom")

    service.register_tool(
        ToolSpec(
            name="custom.fail",
            version="v1",
            description="fail tool",
            timeout_sec=2,
            max_retries=2,
            keywords=["fail"],
            degrade_payload={"fallback": "partial"},
        ),
        always_fail,
        overwrite=True,
    )

    bundle = service.invoke(
        intent="force custom fail",
        payload={"query": "x"},
        context={},
        force_tools=["custom.fail"],
    )
    assert bundle["degraded"] is True
    assert bundle["failed_tools"] == []
    assert bundle["results"]["custom.fail"]["fallback"] == "partial"
    assert attempts["count"] == 3
    assert bundle["trace"][0]["status"] == "degraded"
    assert bundle["trace"][0]["attempts"] == 3
