from __future__ import annotations

from typing import Any

from app.services.news_service import NewsService


def test_news_service_uses_external_source_and_filters_query() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []

    def fetcher(url: str, headers: dict[str, str], timeout_sec: float) -> dict[str, Any]:
        calls.append((url, headers, timeout_sec))
        return {
            "headlines": [
                {"title": "Policy support strengthens consumption recovery"},
                {"headline": "Liquidity concern persists in short term"},
                "Policy path remains data-dependent",
            ],
            "sentiment_score": 0.33,
            "headline_count": 3,
            "sentiment_level": "positive",
            "summary": "Policy tone improves but liquidity risk remains.",
        }

    service = NewsService(
        source_url="https://example.test/news?symbol={symbol}&report={report_type}&q={query}&k={top_k}",
        auth_token="token-x",
        timeout_sec=3.5,
        fetcher=fetcher,
    )

    result = service.search(symbol="600519", report_type="detailed", query="policy", top_k=2)

    assert result["symbol"] == "600519"
    assert result["top_k"] == 2
    assert len(result["headlines"]) == 2
    assert all("policy" in headline.lower() for headline in result["headlines"])
    assert result["sentiment"]["sentiment_level"] == "positive"
    assert "quality_flag" not in result
    assert len(calls) == 1
    assert calls[0][1].get("Authorization") == "Bearer token-x"


def test_news_service_falls_back_when_external_source_fails() -> None:
    def failing_fetcher(url: str, headers: dict[str, str], timeout_sec: float) -> dict[str, Any]:  # noqa: ARG001
        raise RuntimeError("news upstream timeout")

    service = NewsService(
        source_url="https://example.test/news?symbol={symbol}",
        fetcher=failing_fetcher,
    )
    result = service.search(symbol="000001", report_type="summary", query="risk", top_k=2)

    assert result["symbol"] == "000001"
    assert len(result["headlines"]) == 2
    assert result["sentiment"]["sentiment_level"] in {"positive", "neutral", "negative"}
    assert result["quality_flag"]["status"] == "degraded"
    assert "news upstream timeout" in result["quality_flag"]["reason"]
