"""Data Fetcher Manager with Auto-Failover."""

import logging
from datetime import date
from typing import List, Optional, Dict, Any

from app.data_providers.base import BaseFetcher, FetchResult
from app.data_providers.efinance_fetcher import EfinanceFetcher
from app.data_providers.akshare_fetcher import AkshareFetcher
from app.data_providers.tushare_fetcher import TushareFetcher
from app.data_providers.baostock_fetcher import BaostockFetcher
from app.data_providers.yfinance_fetcher import YFinanceFetcher

logger = logging.getLogger(__name__)


class DataFetcherManager:
    """Manages data fetchers with automatic failover."""

    def __init__(self):
        self.fetchers: List[BaseFetcher] = []
        self._init_fetchers()

    def _init_fetchers(self):
        """Initialize available fetchers."""
        # Add fetchers in priority order
        # Efinance (highest priority for A-shares)
        self.fetchers.append(EfinanceFetcher())

        # AkShare (good fallback)
        self.fetchers.append(AkshareFetcher())

        # Tushare (if token configured)
        tushare = TushareFetcher()
        if tushare.is_configured():
            self.fetchers.insert(0, tushare)  # Highest priority if configured

        # Baostock (backup)
        self.fetchers.append(BaostockFetcher())

        # YFinance (for HK/US stocks)
        self.fetchers.append(YFinanceFetcher())

    def _get_working_fetcher(self, code: str) -> Optional[BaseFetcher]:
        """Find first working fetcher for a code."""
        for fetcher in self.fetchers:
            if fetcher.supports_code(code):
                if fetcher.priority < 100 or self._test_fetcher(fetcher):
                    return fetcher
        return None

    def _test_fetcher(self, fetcher: BaseFetcher) -> bool:
        """Test if fetcher is working."""
        try:
            import asyncio
            return asyncio.run(fetcher.health_check())
        except Exception as e:
            logger.warning(f"Fetcher {fetcher.__class__.__name__} health check failed: {e}")
            return False

    async def get_realtime(self, code: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote with failover."""
        fetcher = self._get_working_fetcher(code)
        if not fetcher:
            logger.error(f"No working fetcher for {code}")
            return None

        result = await fetcher.get_realtime(code)
        if result.success:
            return result.data
        return None

    async def get_history(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = "daily",
    ) -> List[Dict[str, Any]]:
        """Get historical data with failover."""
        fetcher = self._get_working_fetcher(code)
        if not fetcher:
            logger.error(f"No working fetcher for {code}")
            return []

        result = await fetcher.get_history(code, start_date, end_date, period)
        if result.success:
            return result.data or []
        return []

    async def get_name(self, code: str) -> str:
        """Get stock name."""
        fetcher = self._get_working_fetcher(code)
        if not fetcher:
            return ""
        return await fetcher.get_name(code)

    async def get_chip_distribution(self, code: str) -> Optional[Dict[str, Any]]:
        """Get chip distribution."""
        for fetcher in self.fetchers:
            if fetcher.supports_code(code):
                result = await fetcher.get_chip_distribution(code)
                if result.success:
                    return result.data
        return None
