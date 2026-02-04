"""AkShare Data Fetcher."""

import logging
from datetime import date
from typing import List, Dict, Any

from app.data_providers.base import BaseFetcher, FetchResult

logger = logging.getLogger(__name__)


class AkshareFetcher(BaseFetcher):
    """AkShare data fetcher (A-shares data)."""

    priority = 2

    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self._initialized = True
        except ImportError:
            logger.warning("akshare not installed")
            self._initialized = False

    def supports_code(self, code: str) -> bool:
        """Check if fetcher supports this code."""
        if not self._initialized:
            return False
        return len(code) == 6 and code.isdigit()

    async def get_realtime(self, code: str) -> FetchResult:
        """Get real-time quote."""
        try:
            if not self._initialized:
                return FetchResult(success=False, error="akshare not installed", source="AkshareFetcher")

            df = self.ak.stock_zh_a_spot_em()
            stock = df[df["代码"] == code]
            if stock.empty:
                return FetchResult(success=False, error="Stock not found", source="AkshareFetcher")

            row = stock.iloc[0]
            return FetchResult(
                success=True,
                data={
                    "code": code,
                    "name": str(row.get("名称", "")),
                    "price": float(row.get("最新价", 0)),
                    "pct_chg": float(row.get("涨跌幅", 0)),
                    "open": float(row.get("开盘价", 0)),
                    "high": float(row.get("最高价", 0)),
                    "low": float(row.get("最低价", 0)),
                    "close": float(row.get("收盘价", 0)),
                    "volume": int(row.get("成交量(手)", 0) * 100),
                    "turnover_rate": float(row.get("换手率", 0)),
                    "pe_ratio": float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态", 0) != "-" else 0,
                    "pb_ratio": float(row.get("市净率", 0)) if row.get("市净率", 0) != "-" else 0,
                },
                source="AkshareFetcher",
            )
        except Exception as e:
            logger.error(f"Akshare error: {e}")
            return FetchResult(success=False, error=str(e), source="AkshareFetcher")

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
                return FetchResult(success=False, error="akshare not installed", source="AkshareFetcher")

            df = self.ak.stock_zh_a_hist(
                symbol=code,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )

            if df is None or df.empty:
                return FetchResult(success=False, error="No data", source="AkshareFetcher")

            data = []
            for _, row in df.iterrows():
                data.append({
                    "date": date.fromisoformat(str(row["日期"])),
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"]) if "成交额" in row else 0,
                    "pct_chg": float(row["涨跌幅"]) if "涨跌幅" in row else 0,
                })

            return FetchResult(success=True, data=data, source="AkshareFetcher")
        except Exception as e:
            logger.error(f"Akshare history error: {e}")
            return FetchResult(success=False, error=str(e), source="AkshareFetcher")

    async def get_name(self, code: str) -> str:
        """Get stock name."""
        try:
            if not self._initialized:
                return ""

            df = self.ak.stock_zh_a_spot_em()
            stock = df[df["代码"] == code]
            if stock.empty:
                return ""
            return str(stock.iloc[0].get("名称", ""))
        except Exception as e:
            logger.error(f"Error getting name: {e}")
            return ""

    async def health_check(self) -> bool:
        """Check if fetcher is healthy."""
        return self._initialized
