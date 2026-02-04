"""Data Provider Base Classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Dict, Any


@dataclass
class FetchResult:
    """Generic fetch result."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    source: str = ""


class BaseFetcher(ABC):
    """Base class for data fetchers."""

    priority: int = 100  # Lower = higher priority

    @abstractmethod
    async def get_realtime(self, code: str) -> FetchResult:
        """Get real-time quote for a stock."""
        pass

    @abstractmethod
    async def get_history(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = "daily",
    ) -> FetchResult:
        """Get historical price data."""
        pass

    @abstractmethod
    async def get_name(self, code: str) -> str:
        """Get stock name."""
        pass

    async def get_chip_distribution(self, code: str) -> FetchResult:
        """Get chip distribution data."""
        return FetchResult(success=False, error="Not implemented", source=self.__class__.__name__)

    async def health_check(self) -> bool:
        """Check if fetcher is healthy."""
        return True
