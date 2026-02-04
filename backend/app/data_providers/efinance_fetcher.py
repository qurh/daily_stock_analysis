"""Efinance Data Fetcher."""

import logging
from datetime import date
from typing import List, Dict, Any, Optional

from app.data_providers.base import BaseFetcher, FetchResult

logger = logging.getLogger(__name__)


class EfinanceFetcher(BaseFetcher):
    """Efinance data fetcher for A-shares."""

    priority = 1  # Highest priority for A-shares

    def __init__(self):
        try:
            import efinance as ef
            self.ef = ef
            self._initialized = True
        except ImportError:
            logger.warning("efinance not installed")
            self._initialized = False

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
                return FetchResult(success=False, error="efinance not installed", source="EfinanceFetcher")

            df = self.ef.stock.get_quote([code])
            if df.empty:
                return FetchResult(success=False, error="No data", source="EfinanceFetcher")

            row = df.iloc[0]
            return FetchResult(
                success=True,
                data={
                    "code": code,
                    "name": str(row.get("股票名称", "")),
                    "price": float(row.get("最新价", 0)),
                    "pct_chg": float(row.get("涨跌幅", 0)),
                    "open": float(row.get("开盘价", 0)),
                    "high": float(row.get("最高价", 0)),
                    "low": float(row.get("最低价", 0)),
                    "close": float(row.get("收盘价", 0)),
                    "volume": int(row.get("成交量(手)", 0) * 100),
                    "turnover_rate": float(row.get("换手率", 0)),
                    "pe_ratio": float(row.get("市盈率", 0)),
                    "pb_ratio": float(row.get("市净率", 0)),
                },
                source="EfinanceFetcher",
            )
        except Exception as e:
            logger.error(f"Efinance error: {e}")
            return FetchResult(success=False, error=str(e), source="EfinanceFetcher")

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
                return FetchResult(success=False, error="efinance not installed", source="EfinanceFetcher")

            # Convert to string format
            start = start_date.strftime("%Y%m%d")
            end = end_date.strftime("%Y%m%d")

            df = self.ef.stock.get_bars(
                code,
                start_date=start,
                end_date=end,
                freq="日" if period == "daily" else ("周" if period == "weekly" else "月"),
            )

            if df is None or df.empty:
                return FetchResult(success=False, error="No data", source="EfinanceFetcher")

            # Convert to list of dicts
            data = []
            for _, row in df.iterrows():
                data.append({
                    "date": row["日期"] if isinstance(row["日期"], date) else date.fromisoformat(str(row["日期"])[:10]),
                    "open": float(row.get("开盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "close": float(row.get("收盘", 0)),
                    "volume": int(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                    "pct_chg": float(row.get("涨跌幅", 0)),
                })

            return FetchResult(success=True, data=data, source="EfinanceFetcher")
        except Exception as e:
            logger.error(f"Efinance history error: {e}")
            return FetchResult(success=False, error=str(e), source="EfinanceFetcher")

    async def get_name(self, code: str) -> str:
        """Get stock name."""
        try:
            if not self._initialized:
                return ""

            df = self.ef.stock.get_quote([code])
            if df.empty:
                return ""
            return str(df.iloc[0].get("股票名称", ""))
        except Exception as e:
            logger.error(f"Error getting name: {e}")
            return ""

    async def health_check(self) -> bool:
        """Check if fetcher is healthy."""
        return self._initialized
