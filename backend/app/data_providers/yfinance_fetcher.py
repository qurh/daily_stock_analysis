"""YFinance Data Fetcher - Placeholder for yfinance."""

from datetime import date
from typing import List, Dict, Any

from app.data_providers.base import BaseFetcher, FetchResult


class YFinanceFetcher(BaseFetcher):
    """Yahoo Finance data fetcher (HK/US stocks)."""

    priority = 4

    def __init__(self):
        self._initialized = True

    def supports_code(self, code: str) -> bool:
        """Check if fetcher supports this code."""
        if not self._initialized:
            return False
        return code.endswith(".HK") or len(code) <= 5

    async def get_realtime(self, code: str) -> FetchResult:
        """Get real-time quote."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(code)
            info = ticker.info

            return FetchResult(
                success=True,
                data={
                    "code": code,
                    "name": info.get("shortName", ""),
                    "price": info.get("currentPrice", 0),
                    "pct_chg": info.get("regularMarketChangePercent", 0) * 100,
                },
                source="YFinanceFetcher",
            )
        except Exception as e:
            return FetchResult(success=False, error=str(e), source="YFinanceFetcher")

    async def get_history(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = "daily",
    ) -> FetchResult:
        """Get historical price data."""
        try:
            import yfinance as yf
            import pandas as pd

            ticker = yf.Ticker(code)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval="1d" if period == "daily" else "1wk",
            )

            if df.empty:
                return FetchResult(success=False, error="No data", source="YFinanceFetcher")

            data = []
            for idx, row in df.iterrows():
                data.append({
                    "date": idx.date() if hasattr(idx, "date") else idx,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "amount": float(row["Close"]) * row["Volume"],
                })

            return FetchResult(success=True, data=data, source="YFinanceFetcher")
        except Exception as e:
            return FetchResult(success=False, error=str(e), source="YFinanceFetcher")

    async def get_name(self, code: str) -> str:
        """Get stock name."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(code)
            return ticker.info.get("shortName", "")
        except Exception:
            return ""

    async def health_check(self) -> bool:
        """Check if fetcher is healthy."""
        return self._initialized
