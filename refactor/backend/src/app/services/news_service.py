from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

NewsFetcher = Callable[[str, dict[str, str], float], dict[str, Any]]


def _seed_int(seed: str) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _scale(seed: str, minimum: float, maximum: float) -> float:
    raw = _seed_int(seed) % 10000
    ratio = raw / 10000.0
    return minimum + (maximum - minimum) * ratio


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


def _format_source_url(template: str, symbol: str, report_type: str, query: str | None, top_k: int) -> str:
    return template.format(
        symbol=quote_plus(symbol),
        report_type=quote_plus(report_type),
        query=quote_plus(query or ""),
        top_k=top_k,
    )


def _normalize_headlines(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        items = raw
    else:
        items = [raw]

    headlines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = str(item.get("title") or item.get("headline") or "").strip()
        else:
            text = str(item).strip()
        if text and text not in headlines:
            headlines.append(text)
    return headlines


def _sentiment_level(score: float) -> str:
    if score >= 0.25:
        return "positive"
    if score <= -0.25:
        return "negative"
    return "neutral"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


@dataclass
class NewsService:
    source_url: str | None = None
    auth_token: str | None = None
    timeout_sec: float = 5.0
    fetcher: NewsFetcher | None = None

    def search(self, symbol: str, report_type: str, query: str | None = None, top_k: int = 5) -> dict[str, Any]:
        normalized_symbol = _optional_str(symbol)
        if normalized_symbol is None:
            raise ValueError("symbol is required")
        normalized_report_type = _optional_str(report_type) or "standard"
        normalized_query = _optional_str(query)
        safe_top_k = max(min(int(top_k), 20), 1)

        if self.source_url:
            try:
                payload = self._fetch_external(
                    symbol=normalized_symbol,
                    report_type=normalized_report_type,
                    query=normalized_query,
                    top_k=safe_top_k,
                )
                return self._from_payload(
                    payload=payload,
                    symbol=normalized_symbol,
                    report_type=normalized_report_type,
                    query=normalized_query,
                    top_k=safe_top_k,
                )
            except Exception as exc:  # noqa: BLE001
                fallback = self._fallback(
                    symbol=normalized_symbol,
                    report_type=normalized_report_type,
                    query=normalized_query,
                    top_k=safe_top_k,
                )
                fallback["quality_flag"] = {
                    "source": "news",
                    "status": "degraded",
                    "reason": f"external source failed: {exc}",
                }
                return fallback

        return self._fallback(
            symbol=normalized_symbol,
            report_type=normalized_report_type,
            query=normalized_query,
            top_k=safe_top_k,
        )

    def _fetch_external(self, symbol: str, report_type: str, query: str | None, top_k: int) -> dict[str, Any]:
        fetcher = self.fetcher or _http_fetch_json
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        url = _format_source_url(
            template=self.source_url or "",
            symbol=symbol,
            report_type=report_type,
            query=query,
            top_k=top_k,
        )
        return fetcher(url, headers, max(self.timeout_sec, 0.1))

    def _from_payload(
        self,
        payload: dict[str, Any],
        symbol: str,
        report_type: str,
        query: str | None,
        top_k: int,
    ) -> dict[str, Any]:
        raw_headlines = _normalize_headlines(payload.get("headlines"))
        filtered = self._filter_headlines(raw_headlines, query=query)
        selected = filtered[:top_k]

        score = round(_safe_float(payload.get("sentiment_score"), 0.0), 3)
        level = _optional_str(payload.get("sentiment_level")) or _sentiment_level(score)
        normalized_level = level.lower()
        if normalized_level not in {"positive", "neutral", "negative"}:
            normalized_level = _sentiment_level(score)
        headline_count = _safe_int(payload.get("headline_count"), len(raw_headlines))
        summary = _optional_str(payload.get("summary")) or self._build_summary(selected)

        return {
            "symbol": symbol,
            "report_type": report_type,
            "query": query,
            "top_k": top_k,
            "headlines": selected,
            "summary": summary,
            "sentiment": {
                "sentiment_score": score,
                "headline_count": headline_count,
                "sentiment_level": normalized_level,
            },
        }

    def _fallback(self, symbol: str, report_type: str, query: str | None, top_k: int) -> dict[str, Any]:
        score = round(_scale(f"news:sentiment:{symbol}:{report_type}", -0.6, 0.6), 3)
        level = _sentiment_level(score)
        base = [
            f"{symbol}: Policy and liquidity remain the key market drivers.",
            f"{symbol}: Earnings expectation and valuation gap stay in focus.",
            f"{symbol}: Macro and credit conditions may change short-term risk appetite.",
        ]
        filtered = self._filter_headlines(base, query=query)
        selected = filtered[:top_k]
        summary = self._build_summary(selected)
        return {
            "symbol": symbol,
            "report_type": report_type,
            "query": query,
            "top_k": top_k,
            "headlines": selected,
            "summary": summary,
            "sentiment": {
                "sentiment_score": score,
                "headline_count": len(base),
                "sentiment_level": level,
            },
        }

    @staticmethod
    def _filter_headlines(headlines: list[str], query: str | None) -> list[str]:
        if not query:
            return [item for item in headlines if item]
        lowered = query.lower()
        matched = [item for item in headlines if lowered in item.lower()]
        if not matched:
            return [item for item in headlines if item]
        remaining = [item for item in headlines if item and item not in matched]
        return matched + remaining

    @staticmethod
    def _build_summary(headlines: list[str]) -> str:
        if not headlines:
            return "No relevant headlines found."
        top = headlines[:2]
        return " ".join(top)
