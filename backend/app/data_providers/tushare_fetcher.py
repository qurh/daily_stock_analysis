"""Tushare Data Fetcher."""

import logging
from datetime import date
from typing import List, Dict, Any

from app.data_providers.base import BaseFetcher, FetchResult

logger = logging.getLogger(__name__)


class TushareFetcher(BaseFetcher):
    """Tushare data fetcher (official A-shares API)."""

    priority = 0  # Highest if configured

    def __init__(self):
        self._initialized = False
        self._token = None
        self._init_from_config()

    def _init_from_config(self):
        """Initialize from configuration."""
        from app.config import get_settings
        settings = get_settings()

        if settings.TUSHARE_TOKEN:
            try:
                import tushare as ts
                self._token = settings.TUSHARE_TOKEN
                self._pro = ts.pro_api(self._token)
                self._initialized = True
                logger.info("Tushare configured successfully")
            except Exception as e:
                logger.error(f"Tushare init error: {e}")

    def is_configured(self) -> bool:
        """Check if fetcher is configured."""
        return self._initialized

    def supports_code(self, code: str) -> bool:
        """Check if fetcher supports this code."""
        if not self._initialized:
            return False
        return len(code) == 6 and code.isdigit()

    async def get_realtime(self, code: str) -> FetchResult:
        """Get real-time quote."""
        try:
            if not self._initialized:
                return FetchResult(success=False, error="Tushare not configured", source="TushareFetcher")

            df = self._pro.daily_basic(
                ts_code=f"{code}.SSE",
                fields="ts_code,close,pct_chg,vol,turnover_rate,pe,pb"
            )

            if df.empty:
                return FetchResult(success=False, error="No data", source="TushareFetcher")

            row = df.iloc[0]
            return FetchResult(
                success=True,
                data={
                    "code": code,
                    "price": float(row.get("close", 0)),
                    "pct_chg": float(row.get("pct_chg", 0)),
                    "volume": int(row.get("vol", 0)),
                    "turnover_rate": float(row.get("turnover_rate", 0)),
                    "pe_ratio": float(row.get("pe", 0)),
                    "pb_ratio": float(row.get("pb", 0)),
                },
                source="TushareFetcher",
            )
        except Exception as e:
            logger.error(f"Tushare error: {e}")
            return FetchResult(success=False, error=str(e), source="TushareFetcher")

    async def get_history(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = "daily",
    ) -> FetchResult:
        """Get historical price data."""
        try:
            if not self._initialized:
                return FetchResult(success=False, error="Tushare not configured", source="TushareFetcher")

            df = self._pro.daily(
                ts_code=f"{code}.SSE",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )

            if df is None or df.empty:
                return FetchResult(success=False, error="No data", source="TushareFetcher")

            data = []
            for _, row in df.iterrows():
                data.append({
                    "date": date.fromisoformat(str(row["trade_date"])[:4] + "-" +
                                               str(row["trade_date"])[4:6] + "-" +
                                               str(row["trade_date"])[6:8]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["vol"]),
                    "amount": float(row["amount"]) if "amount" in row else 0,
                    "pct_chg": float(row["pct_chg"]) if "pct_chg" in row else 0,
                })

            return FetchResult(success=True, data=data, source="TushareFetcher")
        except Exception as e:
            logger.error(f"Tushare history error: {e}")
            return FetchResult(success=False, error=str(e), source="TushareFetcher")

    async def get_name(self, code: str) -> str:
        """Get stock name."""
        try:
            if not self._initialized:
                return ""

            df = self._pro.stock_basic(
                ts_code=f"{code}.SSE",
                fields="ts_code,name"
            )

            if df.empty:
                return ""
            return str(df.iloc[0].get("name", ""))
        except Exception as e:
            logger.error(f"Error getting name: {e}")
            return ""

    async def health_check(self) -> bool:
        """Check if fetcher is healthy."""
        return self._initialized
