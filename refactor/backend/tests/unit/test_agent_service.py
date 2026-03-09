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
    assert "market.quote" in tool_names
    assert "macro.snapshot" in tool_names
    assert "credit.snapshot" in tool_names
    assert "sentiment.snapshot" in tool_names
    assert "news.search" in tool_names


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


def test_agent_service_returns_normalized_entity_context() -> None:
    client = TestClient(create_app())
    service = client.app.state.agent_service

    service.register_static_tool(
        ToolSpec(
            name="custom.echo",
            version="v1",
            description="echo tool",
            timeout_sec=2,
            max_retries=0,
            keywords=["echo"],
        ),
        {"ok": True},
        overwrite=True,
    )

    bundle = service.invoke(
        intent="echo",
        payload={
            "query": "回测情况",
            "symbol": "600519",
            "resolved_name": "贵州茅台",
            "aliases": ["Moutai"],
        },
        context={
            "session_id": "s-1",
            "entity_context": {
                "symbol": "600519",
                "resolved_name": "贵州茅台",
                "aliases": ["Kweichow Moutai", "Moutai"],
            },
        },
        force_tools=["custom.echo"],
    )

    assert bundle["entity_context"]["symbol"] == "600519"
    assert bundle["entity_context"]["resolved_name"] == "贵州茅台"
    aliases = bundle["entity_context"]["aliases"]
    assert "600519" in aliases
    assert "贵州茅台" in aliases
    assert "Kweichow Moutai" in aliases


def test_agent_service_factor_tools_return_symbol_scoped_snapshots() -> None:
    client = TestClient(create_app())
    service = client.app.state.agent_service

    bundle = service.invoke(
        intent="查看宏观和信用风险，还有舆情",
        payload={"symbol": "600519", "report_type": "detailed"},
        context={},
        force_tools=["market.quote", "macro.snapshot", "credit.snapshot", "sentiment.snapshot", "news.search"],
    )

    results = bundle["results"]
    assert results["market.quote"]["symbol"] == "600519"
    assert "technical" in results["market.quote"]
    assert "trend_score" in results["market.quote"]["technical"]

    assert results["macro.snapshot"]["symbol"] == "600519"
    assert "gdp_growth_pct" in results["macro.snapshot"]["macro"]

    assert results["credit.snapshot"]["symbol"] == "600519"
    assert "risk_level" in results["credit.snapshot"]["credit"]

    assert results["sentiment.snapshot"]["symbol"] == "600519"
    assert "sentiment_level" in results["sentiment.snapshot"]["sentiment"]

    assert results["news.search"]["symbol"] == "600519"
    assert "headlines" in results["news.search"]
    assert isinstance(results["news.search"]["headlines"], list)
    assert len(results["news.search"]["headlines"]) >= 1
    assert "sentiment" in results["news.search"]
    assert "sentiment_level" in results["news.search"]["sentiment"]


def test_agent_service_news_search_prefers_news_service_when_available() -> None:
    client = TestClient(create_app())
    service = client.app.state.agent_service

    class _FakeNewsService:
        @staticmethod
        def search(symbol: str, report_type: str, query: str | None, top_k: int) -> dict[str, object]:
            return {
                "symbol": symbol,
                "report_type": report_type,
                "query": query,
                "top_k": top_k,
                "headlines": ["custom-news-1", "custom-news-2"],
                "sentiment": {
                    "sentiment_score": -0.2,
                    "headline_count": 2,
                    "sentiment_level": "negative",
                },
            }

    service._news_service = _FakeNewsService()  # type: ignore[attr-defined]

    bundle = service.invoke(
        intent="查新闻",
        payload={"symbol": "600519", "report_type": "detailed", "query": "custom", "top_k": 2},
        context={},
        force_tools=["news.search"],
    )

    result = bundle["results"]["news.search"]
    assert result["headlines"] == ["custom-news-1", "custom-news-2"]
    assert result["sentiment"]["sentiment_level"] == "negative"
