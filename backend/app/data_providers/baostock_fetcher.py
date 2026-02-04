"""Baostock Data Fetcher."""

import logging
from datetime import date
from typing import List, Dict, Any

from app.data_providers.base import BaseFetcher, FetchResult

logger = logging.getLogger(__name__)


class BaostockFetcher(BaseFetcher):
    """Baostock data fetcher (brokerage API)."""

    priority = 3

    def __init__(self):
        self._initialized = False
        self._login()

    def _login(self):
        """Login to Baostock."""
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == "0":
                self._initialized = True
                logger.info("Baostock login successful")
            else:
                logger.error(f"Baostock login failed: {lg.error_msg}")
        except ImportError:
            logger.warning("baostock not installed")

    def supports_code(self, code: str) -> bool:
        """Check if fetcher supports this code."""
        if not self._initialized:
            return False
        return len(code) == 6 and code.isdigit()

    async def get_realtime(self, code: str) -> FetchResult:
        """Get real-time quote."""
        try:
            import baostock as bs

            # Format code for Baostock
            bs_code = f"sh.{code}" if code.startswith("6") else f"sz.{code}"
            rs = bs.query_sh_dquot(bs_code)

            data = []
            while rs.next():
                data.append(rs.get_row_data())

            if not data:
                return FetchResult(success=False, error="No data", source="BaostockFetcher")

            row = data[0]
            return FetchResult(
                success=True,
                data={
                    "code": code,
                    "name": row[1] if len(row) > 1 else "",
                    "price": float(row[3]) if row[3] else 0,
                    "pct_chg": float(row[32]) if row[32] else 0,
                },
                source="BaostockFetcher",
            )
        except Exception as e:
            logger.error(f"Baostock error: {e}")
            return FetchResult(success=False, error=str(e), source="BaostockFetcher")

    async def get_history(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = "daily",
    ) -> FetchResult:
        """Get historical price data."""
        try:
            import baostock as bs

            bs_code = f"sh.{code}" if code.startswith("6") else f"sz.{code}"

            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,preclose",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                frequency="d" if period == "daily" else "w",
                adjustflag="2",  # Forward adjusted
            )

            data = []
            while rs.next():
                row = rs.get_row_data()
                if row[0]:
                    data.append({
                        "date": date.fromisoformat(row[0]),
                        "open": float(row[1]) if row[1] else 0,
                        "high": float(row[2]) if row[2] else 0,
                        "low": float(row[3]) if row[3] else 0,
                        "close": float(row[4]) if row[4] else 0,
                        "volume": int(float(row[5])) if row[5] else 0,
                        "amount": float(row[6]) if row[6] else 0,
                    })

            if not data:
                return FetchResult(success=False, error="No data", source="BaostockFetcher")

            return FetchResult(success=True, data=data, source="BaostockFetcher")
        except Exception as e:
            logger.error(f"Baostock history error: {e}")
            return FetchResult(success=False, error=str(e), source="BaostockFetcher")

    async def get_name(self, code: str) -> str:
        """Get stock name."""
        # Baostock doesn't provide easy name lookup
        return ""

    async def health_check(self) -> bool:
        """Check if fetcher is healthy."""
        return self._initialized


class YFinanceFetcher(BaseFetcher):
    """Yahoo Finance data fetcher (HK/US stocks)."""

    priority = 4

    def __init__(self):
        self._initialized = True

    def supports_code(self, code: str) -> bool:
        """Check if fetcher supports this code."""
        # Support HK stocks (.HK) and US stocks
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
            logger.error(f"YFinance error: {e}")
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
            logger.error(f"YFinance history error: {e}")
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
