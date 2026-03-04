from __future__ import annotations

from typing import Any

from app.services.factor_service import (
    CreditFactorProvider,
    FactorService,
    MacroFactorProvider,
    SentimentFactorProvider,
    TechnicalFactorProvider,
)


def test_factor_service_uses_external_sources_when_configured() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []

    def fetcher(url: str, headers: dict[str, str], timeout_sec: float) -> dict[str, Any]:
        calls.append((url, headers, timeout_sec))
        if "macro" in url:
            return {"gdp_growth_pct": 5.8, "unemployment_rate_pct": 4.2, "liquidity_index": 66.0}
        if "credit" in url:
            return {"cds_bps": 110, "bond_spread_bps": 145, "risk_level": "low"}
        if "sentiment" in url:
            return {"sentiment_score": 0.46, "headline_count": 78, "sentiment_level": "positive"}
        raise AssertionError(f"unexpected url: {url}")

    service = FactorService(
        providers=[
            TechnicalFactorProvider(),
            MacroFactorProvider(
                source_url="https://example.test/macro?symbol={symbol}&report={report_type}",
                auth_token="token-x",
                timeout_sec=3.5,
                fetcher=fetcher,
            ),
            CreditFactorProvider(
                source_url="https://example.test/credit?symbol={symbol}&report={report_type}",
                auth_token="token-x",
                timeout_sec=3.5,
                fetcher=fetcher,
            ),
            SentimentFactorProvider(
                source_url="https://example.test/sentiment?symbol={symbol}&report={report_type}",
                auth_token="token-x",
                timeout_sec=3.5,
                fetcher=fetcher,
            ),
        ]
    )

    factor_pack = service.collect(symbol="600519", report_type="detailed")

    assert factor_pack["macro"]["gdp_growth_pct"] == 5.8
    assert factor_pack["credit"]["cds_bps"] == 110
    assert factor_pack["sentiment"]["sentiment_score"] == 0.46
    assert factor_pack["quality_flags"] == []
    assert len(calls) == 3
    assert all(item[1].get("Authorization") == "Bearer token-x" for item in calls)


def test_factor_service_falls_back_when_external_source_fails() -> None:
    def failing_fetcher(url: str, headers: dict[str, str], timeout_sec: float) -> dict[str, Any]:
        raise RuntimeError("upstream timeout")

    service = FactorService(
        providers=[
            TechnicalFactorProvider(),
            MacroFactorProvider(
                source_url="https://example.test/macro?symbol={symbol}&report={report_type}",
                fetcher=failing_fetcher,
            ),
            CreditFactorProvider(
                source_url="https://example.test/credit?symbol={symbol}&report={report_type}",
                fetcher=failing_fetcher,
            ),
            SentimentFactorProvider(
                source_url="https://example.test/sentiment?symbol={symbol}&report={report_type}",
                fetcher=failing_fetcher,
            ),
        ]
    )

    factor_pack = service.collect(symbol="000001", report_type="summary")

    assert factor_pack["macro"]["gdp_growth_pct"] > 0.0
    assert factor_pack["credit"]["risk_level"] in {"low", "medium", "high"}
    assert factor_pack["sentiment"]["sentiment_level"] in {"positive", "neutral", "negative"}
    assert len(factor_pack["quality_flags"]) == 3
    assert sorted(item["factor"] for item in factor_pack["quality_flags"]) == ["credit", "macro", "sentiment"]
    assert all(item["status"] == "degraded" for item in factor_pack["quality_flags"])
    assert all("upstream timeout" in item["reason"] for item in factor_pack["quality_flags"])

    dashboard = service.build_dashboard(factor_pack=factor_pack)
    assert dashboard["decision"]["direction"] in {"long", "hold", "short"}
