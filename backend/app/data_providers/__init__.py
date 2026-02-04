"""Data Providers Package."""

from app.data_providers.base import BaseFetcher, FetchResult
from app.data_providers.efinance_fetcher import EfinanceFetcher
from app.data_providers.akshare_fetcher import AkshareFetcher
from app.data_providers.tushare_fetcher import TushareFetcher
from app.data_providers.baostock_fetcher import BaostockFetcher
from app.data_providers.yfinance_fetcher import YFinanceFetcher
from app.data_providers.manager import DataFetcherManager

__all__ = [
    "BaseFetcher",
    "FetchResult",
    "EfinanceFetcher",
    "AkshareFetcher",
    "TushareFetcher",
    "BaostockFetcher",
    "YFinanceFetcher",
    "DataFetcherManager",
]
