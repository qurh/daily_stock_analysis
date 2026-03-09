from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Protocol
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

FactorFetcher = Callable[[str, dict[str, str], float], dict[str, Any]]


def _seed_int(seed: str) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _scale(seed: str, minimum: float, maximum: float) -> float:
    raw = _seed_int(seed) % 10000
    ratio = raw / 10000.0
    return round(minimum + (maximum - minimum) * ratio, 4)


def _http_fetch_json(url: str, headers: dict[str, str], timeout_sec: float) -> dict[str, Any]:
    request = Request(url=url, headers=headers, method="GET")
    with urlopen(request, timeout=timeout_sec) as response:
        payload_bytes = response.read()
    if not payload_bytes:
        raise ValueError("empty response payload")
    payload = json.loads(payload_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("response payload must be a JSON object")
    return payload


def _format_source_url(template: str, symbol: str, report_type: str) -> str:
    return template.format(symbol=quote_plus(symbol), report_type=quote_plus(report_type))


def _to_float(payload: dict[str, Any], key: str) -> float:
    return float(payload[key])


def _to_int(payload: dict[str, Any], key: str) -> int:
    return int(round(float(payload[key])))


def _credit_risk_level(cds_bps: int, bond_spread_bps: int) -> str:
    if cds_bps >= 240 or bond_spread_bps >= 260:
        return "high"
    if cds_bps >= 180 or bond_spread_bps >= 200:
        return "medium"
    return "low"


def _sentiment_level(score: float) -> str:
    if score >= 0.25:
        return "positive"
    if score <= -0.25:
        return "negative"
    return "neutral"


def _coerce_headlines(raw: Any) -> list[str]:
    if raw is None:
        return []

    values: list[str] = []
    if isinstance(raw, list):
        iterable = raw
    else:
        iterable = [raw]

    for item in iterable:
        if isinstance(item, dict):
            text = str(item.get("title") or item.get("headline") or "").strip()
        else:
            text = str(item).strip()
        if text and text not in values:
            values.append(text)
    return values


def _fallback_headlines(symbol: str, sentiment_level: str) -> list[str]:
    direction = sentiment_level.lower()
    if direction == "positive":
        tone = "Risk appetite improves on policy support."
    elif direction == "negative":
        tone = "Market concerns rise amid short-term volatility."
    else:
        tone = "Market sentiment stays mixed with limited conviction."
    return [
        f"{symbol}: {tone}",
        f"{symbol}: Institutional flow and liquidity are being monitored.",
        f"{symbol}: Macro and credit context remain key watch points.",
    ]


def _degraded_quality_flag(factor_key: str, reason: str) -> dict[str, str]:
    return {
        "factor": factor_key,
        "status": "degraded",
        "reason": reason,
        "source": "fallback",
    }


class FactorProvider(Protocol):
    factor_key: str

    def fetch(self, symbol: str, report_type: str) -> dict[str, Any]:
        ...


class TechnicalFactorProvider:
    factor_key = "technical"

    def fetch(self, symbol: str, report_type: str) -> dict[str, Any]:
        trend_score = _scale(f"technical:trend:{symbol}:{report_type}", -1.0, 1.0)
        volume_ratio = _scale(f"technical:volume:{symbol}:{report_type}", 0.6, 2.0)
        chip_concentration = _scale(f"technical:chip:{symbol}:{report_type}", 0.3, 0.9)
        if trend_score > 0.2:
            ma_alignment = "bullish"
        elif trend_score < -0.2:
            ma_alignment = "bearish"
        else:
            ma_alignment = "neutral"
        return {
            "trend_score": trend_score,
            "ma_alignment": ma_alignment,
            "volume_ratio": round(volume_ratio, 3),
            "chip_concentration": round(chip_concentration, 3),
        }


@dataclass
class MacroFactorProvider:
    source_url: str | None = None
    auth_token: str | None = None
    timeout_sec: float = 5.0
    fetcher: FactorFetcher | None = None
    factor_key = "macro"

    def fetch(self, symbol: str, report_type: str) -> dict[str, Any]:
        if self.source_url:
            try:
                payload = self._fetch_external(symbol=symbol, report_type=report_type)
                return {
                    "gdp_growth_pct": round(_to_float(payload, "gdp_growth_pct"), 2),
                    "unemployment_rate_pct": round(_to_float(payload, "unemployment_rate_pct"), 2),
                    "liquidity_index": round(_to_float(payload, "liquidity_index"), 2),
                }
            except Exception as exc:
                fallback = self._fallback(symbol=symbol, report_type=report_type)
                fallback["_quality_flag"] = _degraded_quality_flag(
                    factor_key=self.factor_key,
                    reason=f"external source failed: {exc}",
                )
                return fallback
        return self._fallback(symbol=symbol, report_type=report_type)

    def _fetch_external(self, symbol: str, report_type: str) -> dict[str, Any]:
        fetcher = self.fetcher or _http_fetch_json
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        timeout_sec = max(self.timeout_sec, 0.1)
        url = _format_source_url(self.source_url or "", symbol=symbol, report_type=report_type)
        return fetcher(url, headers, timeout_sec)

    def _fallback(self, symbol: str, report_type: str) -> dict[str, Any]:
        gdp_growth_pct = _scale(f"macro:gdp:{symbol}:{report_type}", 2.0, 6.5)
        unemployment_rate_pct = _scale(f"macro:unemployment:{symbol}:{report_type}", 3.0, 7.0)
        liquidity_index = _scale(f"macro:liquidity:{symbol}:{report_type}", 35.0, 75.0)
        return {
            "gdp_growth_pct": round(gdp_growth_pct, 2),
            "unemployment_rate_pct": round(unemployment_rate_pct, 2),
            "liquidity_index": round(liquidity_index, 2),
        }


@dataclass
class CreditFactorProvider:
    source_url: str | None = None
    auth_token: str | None = None
    timeout_sec: float = 5.0
    fetcher: FactorFetcher | None = None
    factor_key = "credit"

    def fetch(self, symbol: str, report_type: str) -> dict[str, Any]:
        if self.source_url:
            try:
                payload = self._fetch_external(symbol=symbol, report_type=report_type)
                cds_bps = _to_int(payload, "cds_bps")
                bond_spread_bps = _to_int(payload, "bond_spread_bps")
                risk_level = str(payload.get("risk_level", _credit_risk_level(cds_bps, bond_spread_bps))).lower()
                if risk_level not in {"low", "medium", "high"}:
                    risk_level = _credit_risk_level(cds_bps, bond_spread_bps)
                return {
                    "cds_bps": cds_bps,
                    "bond_spread_bps": bond_spread_bps,
                    "risk_level": risk_level,
                }
            except Exception as exc:
                fallback = self._fallback(symbol=symbol, report_type=report_type)
                fallback["_quality_flag"] = _degraded_quality_flag(
                    factor_key=self.factor_key,
                    reason=f"external source failed: {exc}",
                )
                return fallback
        return self._fallback(symbol=symbol, report_type=report_type)

    def _fetch_external(self, symbol: str, report_type: str) -> dict[str, Any]:
        fetcher = self.fetcher or _http_fetch_json
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        timeout_sec = max(self.timeout_sec, 0.1)
        url = _format_source_url(self.source_url or "", symbol=symbol, report_type=report_type)
        return fetcher(url, headers, timeout_sec)

    def _fallback(self, symbol: str, report_type: str) -> dict[str, Any]:
        cds_bps = int(round(_scale(f"credit:cds:{symbol}:{report_type}", 80.0, 300.0)))
        bond_spread_bps = int(round(_scale(f"credit:spread:{symbol}:{report_type}", 90.0, 320.0)))
        risk_level = _credit_risk_level(cds_bps, bond_spread_bps)
        return {
            "cds_bps": cds_bps,
            "bond_spread_bps": bond_spread_bps,
            "risk_level": risk_level,
        }


@dataclass
class SentimentFactorProvider:
    source_url: str | None = None
    auth_token: str | None = None
    timeout_sec: float = 5.0
    fetcher: FactorFetcher | None = None
    factor_key = "sentiment"

    def fetch(self, symbol: str, report_type: str) -> dict[str, Any]:
        if self.source_url:
            try:
                payload = self._fetch_external(symbol=symbol, report_type=report_type)
                score = round(_to_float(payload, "sentiment_score"), 3)
                headline_count = _to_int(payload, "headline_count")
                level = str(payload.get("sentiment_level", _sentiment_level(score))).lower()
                if level not in {"positive", "neutral", "negative"}:
                    level = _sentiment_level(score)
                headlines = _coerce_headlines(payload.get("headlines"))
                if not headlines:
                    headlines = _fallback_headlines(symbol=symbol, sentiment_level=level)
                return {
                    "sentiment_score": score,
                    "headline_count": headline_count,
                    "sentiment_level": level,
                    "headlines": headlines,
                }
            except Exception as exc:
                fallback = self._fallback(symbol=symbol, report_type=report_type)
                fallback["_quality_flag"] = _degraded_quality_flag(
                    factor_key=self.factor_key,
                    reason=f"external source failed: {exc}",
                )
                return fallback
        return self._fallback(symbol=symbol, report_type=report_type)

    def _fetch_external(self, symbol: str, report_type: str) -> dict[str, Any]:
        fetcher = self.fetcher or _http_fetch_json
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        timeout_sec = max(self.timeout_sec, 0.1)
        url = _format_source_url(self.source_url or "", symbol=symbol, report_type=report_type)
        return fetcher(url, headers, timeout_sec)

    def _fallback(self, symbol: str, report_type: str) -> dict[str, Any]:
        score = _scale(f"sentiment:score:{symbol}:{report_type}", -1.0, 1.0)
        headline_count = int(round(_scale(f"sentiment:count:{symbol}:{report_type}", 10.0, 120.0)))
        level = _sentiment_level(score)
        return {
            "sentiment_score": round(score, 3),
            "headline_count": headline_count,
            "sentiment_level": level,
            "headlines": _fallback_headlines(symbol=symbol, sentiment_level=level),
        }


@dataclass
class FactorService:
    providers: list[FactorProvider] | None = None

    def __post_init__(self) -> None:
        if self.providers is None:
            self.providers = [
                TechnicalFactorProvider(),
                MacroFactorProvider(),
                CreditFactorProvider(),
                SentimentFactorProvider(),
            ]

    def collect(self, symbol: str, report_type: str) -> dict[str, Any]:
        factor_pack = self.empty_factor_pack()
        for provider in self.providers or []:
            factor_key = provider.factor_key
            try:
                provider_data, quality_flag = self.collect_factor(
                    symbol=symbol,
                    report_type=report_type,
                    factor_key=factor_key,
                )
                factor_pack[factor_key] = provider_data
                if quality_flag is not None:
                    factor_pack["quality_flags"].append(quality_flag)
            except Exception as exc:
                factor_pack["quality_flags"].append(
                    {
                        "factor": factor_key,
                        "status": "degraded",
                        "reason": str(exc),
                    }
                )
        return factor_pack

    def collect_factor(
        self,
        symbol: str,
        report_type: str,
        factor_key: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        provider_map = {provider.factor_key: provider for provider in (self.providers or [])}
        provider = provider_map.get(factor_key)
        if provider is None:
            raise KeyError(f"Unknown factor provider: {factor_key}")
        provider_data = provider.fetch(symbol=symbol, report_type=report_type)
        quality_flag = provider_data.pop("_quality_flag", None)
        return provider_data, quality_flag

    @staticmethod
    def empty_factor_pack() -> dict[str, Any]:
        return {
            "technical": {},
            "macro": {},
            "credit": {},
            "sentiment": {},
            "quality_flags": [],
        }

    def build_dashboard(self, factor_pack: dict[str, Any]) -> dict[str, Any]:
        technical = factor_pack.get("technical", {})
        macro = factor_pack.get("macro", {})
        credit = factor_pack.get("credit", {})
        sentiment = factor_pack.get("sentiment", {})
        quality_flags = list(factor_pack.get("quality_flags", []))

        trend_score = float(technical.get("trend_score", 0.0))
        sentiment_score = float(sentiment.get("sentiment_score", 0.0))
        gdp_growth_pct = float(macro.get("gdp_growth_pct", 0.0))
        unemployment_rate_pct = float(macro.get("unemployment_rate_pct", 0.0))
        credit_risk_level = str(credit.get("risk_level", "unknown")).lower()

        signals: list[str] = []
        risk_flags: list[str] = []
        rationale: list[str] = []

        if trend_score > 0.2:
            signals.append("technical_uptrend")
            rationale.append("Technical trend remains positive.")
        elif trend_score < -0.2:
            signals.append("technical_downtrend")
            rationale.append("Technical trend turns weak.")
        else:
            signals.append("technical_sideways")
            rationale.append("Technical trend is mixed.")

        if gdp_growth_pct < 3.0:
            risk_flags.append("macro_growth_soft")
            rationale.append("Macro growth momentum is soft.")
        if unemployment_rate_pct >= 6.0:
            risk_flags.append("macro_employment_pressure")
            rationale.append("Employment pressure is elevated.")
        if credit_risk_level == "high":
            risk_flags.append("credit_risk_high")
            rationale.append("Credit spread and CDS imply elevated risk.")
        elif credit_risk_level == "medium":
            risk_flags.append("credit_risk_medium")
            rationale.append("Credit conditions are moderately tight.")
        if sentiment_score <= -0.25:
            risk_flags.append("sentiment_negative")
            rationale.append("News sentiment is negative.")
        elif sentiment_score >= 0.25:
            signals.append("sentiment_positive")
            rationale.append("News sentiment is supportive.")

        credit_modifier = {"low": 0.2, "medium": -0.1, "high": -0.35}.get(credit_risk_level, 0.0)
        directional_score = (
            trend_score * 0.45
            + sentiment_score * 0.3
            + ((gdp_growth_pct - unemployment_rate_pct) / 10.0) * 0.2
            + credit_modifier * 0.05
        )
        if directional_score >= 0.2:
            direction = "long"
        elif directional_score <= -0.2:
            direction = "short"
        else:
            direction = "hold"
        confidence = round(min(0.95, max(0.35, abs(directional_score) + 0.35)), 2)

        return {
            "signals": signals,
            "risk_flags": risk_flags,
            "decision": {
                "direction": direction,
                "confidence": confidence,
                "rationale": rationale,
            },
            "factors": {
                "technical": technical,
                "macro": macro,
                "credit": credit,
                "sentiment": sentiment,
            },
            "quality_flags": quality_flags,
        }
