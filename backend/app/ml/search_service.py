"""News Search Service.

This module provides news and information search capabilities:
- Stock news search via Tavily/Bocha/SerpAPI
- Official announcements retrieval
- Research reports fetching
- Sentiment analysis
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class Sentiment(Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class NewsItem:
    """News item for stock."""
    title: str
    url: str
    source: str
    published_at: datetime
    sentiment: Optional[Sentiment] = None
    summary: Optional[str] = None
    relevance_score: float = 1.0


@dataclass
class Announcement:
    """Stock announcement."""
    code: str
    title: str
    url: str
    published_at: datetime
    announcement_type: str
    summary: Optional[str] = None


class SearchService:
    """News and information search service."""

    def __init__(self):
        self.settings = get_settings()
        self.tavily_api_key = self.settings.TAVILY_API_KEY
        self.bocha_api_key = self.settings.BOCHA_API_KEY
        self.serpapi_key = self.settings.SERPAPI_API_KEY

    async def search_news(
        self, query: str, limit: int = 10
    ) -> List[NewsItem]:
        """Search for news related to a query."""
        results = []

        # Try Tavily first
        if self.tavily_api_key:
            tavily_results = await self._search_with_tavily(query, limit)
            results.extend(tavily_results)

        # Try Bocha if not enough results
        if len(results) < limit and self.bocha_api_key:
            bocha_results = await self._search_with_bocha(query, limit - len(results))
            results.extend(bocha_results)

        # Fall back to mock data for demo
        if not results:
            results = self._get_mock_news(query)

        # Limit and sort by relevance
        results = sorted(results, key=lambda x: x.relevance_score, reverse=True)[:limit]

        return results

    async def search_stock_news(
        self, code: str, limit: int = 10
    ) -> List[NewsItem]:
        """Search for news about a specific stock."""
        # Get stock name for better search results
        stock_name = await self._get_stock_name(code)
        query = f"{code} {stock_name} 股票 财经"

        return await self.search_news(query, limit)

    async def search_market_news(
        self, limit: int = 20
    ) -> List[NewsItem]:
        """Search for general market news."""
        return await self.search_news("A股市场 股市 财经", limit)

    async def get_announcements(self, code: str) -> List[Announcement]:
        """Get stock announcements."""
        try:
            # Try to fetch from Eastmoney or similar
            announcements = await self._fetch_announcements_from_eastmoney(code)
            if announcements:
                return announcements

            # Fallback mock data
            return self._get_mock_announcements(code)
        except Exception as e:
            logger.error(f"Error fetching announcements for {code}: {e}")
            return self._get_mock_announcements(code)

    async def get_research_reports(self, code: str) -> List[Dict[str, Any]]:
        """Get research reports for a stock."""
        try:
            # This would typically fetch from professional data sources
            # For now, return mock data
            return self._get_mock_reports(code)
        except Exception as e:
            logger.error(f"Error fetching research reports for {code}: {e}")
            return []

    async def analyze_sentiment(self, text: str) -> Sentiment:
        """Analyze sentiment of text using keyword matching."""
        # Simple keyword-based sentiment analysis
        positive_words = [
            "上涨", "突破", "大涨", "看好", "利好", "增持", "推荐",
            "超预期", "业绩增长", "订单饱满", "景气", "高增长",
        ]
        negative_words = [
            "下跌", "破位", "大跌", "看跌", "利空", "减持", "下调",
            "不及预期", "业绩下滑", "风险", "亏损", "警告",
        ]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    async def _search_with_tavily(
        self, query: str, limit: int = 10
    ) -> List[NewsItem]:
        """Search using Tavily API."""
        if not self.tavily_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": limit,
                        "include_answer": False,
                        "include_images": False,
                    },
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    # Analyze sentiment
                    sentiment = await self.analyze_sentiment(item.get("title", ""))

                    results.append(NewsItem(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        source=self._extract_source(item.get("url", "")),
                        published_at=datetime.now(),
                        sentiment=sentiment,
                        summary=item.get("content", "")[:200],
                        relevance_score=item.get("score", 0.5),
                    ))

                return results
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    async def _search_with_bocha(
        self, query: str, limit: int = 10
    ) -> List[NewsItem]:
        """Search using Bocha API."""
        if not self.bocha_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.bochaai.com/v1/web-search",
                    json={
                        "apiKey": self.bocha_api_key,
                        "query": query,
                        "count": limit,
                    },
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("data", []):
                    sentiment = await self.analyze_sentiment(item.get("title", ""))

                    results.append(NewsItem(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        source=item.get("source", ""),
                        published_at=datetime.fromisoformat(
                            item.get("publish_time", datetime.now().isoformat())
                        ),
                        sentiment=sentiment,
                        relevance_score=item.get("score", 0.5),
                    ))

                return results
        except Exception as e:
            logger.error(f"Bocha search error: {e}")
            return []

    async def _fetch_announcements_from_eastmoney(
        self, code: str
    ) -> List[Announcement]:
        """Fetch announcements from Eastmoney."""
        try:
            # Eastmoney API endpoint
            url = f"http://datacenter.eastmoney.com/api/data/v1/get"

            params = {
                "reportName": "RPT_ANNOUNCEMENT",
                "columns": "ALL",
                "filter": f"(SECURITY_CODE='{code}')",
                "pageNumber": 1,
                "pageSize": 10,
                "source": "WEB",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                announcements = []
                for item in data.get("result", {}).get("data", []):
                    announcements.append(Announcement(
                        code=code,
                        title=item.get("ANN_TITLE", ""),
                        url=f"http://www.cninfo.com.cn/new/disclosure/detail?plate=szse&orgId={code}&stockCode={code}",
                        published_at=datetime.fromisoformat(
                            item.get("ANN_PUBLISH_DATETIME", datetime.now().isoformat())
                        ),
                        announcement_type=item.get("ANN_TYPE", ""),
                        summary=item.get("DISCLOSURE_CONTENT", "")[:500],
                    ))

                return announcements
        except Exception as e:
            logger.error(f"Eastmoney API error: {e}")
            return []

    async def _get_stock_name(self, code: str) -> str:
        """Get stock name from code."""
        # This would typically fetch from a data provider
        # For now, return empty
        return ""

    def _extract_source(self, url: str) -> str:
        """Extract source name from URL."""
        if "sina" in url:
            return "新浪财经"
        elif "eastmoney" in url:
            return "东方财富"
        elif "ifeng" in url:
            return "凤凰财经"
        elif "163" in url:
            return "网易财经"
        elif "qq" in url:
            return "腾讯财经"
        elif "xinhua" in url:
            return "新华网"
        elif "cninfo" in url:
            return "巨潮资讯"
        else:
            return "其他"

    def _get_mock_news(self, query: str) -> List[NewsItem]:
        """Get mock news for demo."""
        return [
            NewsItem(
                title=f"{query}相关重大利好消息",
                url="https://example.com/news1",
                source="新浪财经",
                published_at=datetime.now() - timedelta(hours=2),
                sentiment=Sentiment.POSITIVE,
                relevance_score=0.9,
            ),
            NewsItem(
                title=f"{query}行业发展趋势分析",
                url="https://example.com/news2",
                source="东方财富",
                published_at=datetime.now() - timedelta(hours=5),
                sentiment=Sentiment.NEUTRAL,
                relevance_score=0.8,
            ),
            NewsItem(
                title=f"{query}需关注的风险因素",
                url="https://example.com/news3",
                source="凤凰财经",
                published_at=datetime.now() - timedelta(hours=8),
                sentiment=Sentiment.NEGATIVE,
                relevance_score=0.7,
            ),
        ]

    def _get_mock_announcements(self, code: str) -> List[Announcement]:
        """Get mock announcements for demo."""
        return [
            Announcement(
                code=code,
                title=f"{code} 2024年度业绩预告",
                url=f"http://www.cninfo.com.cn/{code}",
                published_at=datetime.now() - timedelta(days=1),
                announcement_type="业绩预告",
                summary="公司预计2024年度实现净利润同比增长...",
            ),
            Announcement(
                code=code,
                title=f"{code} 关于重大合同的公告",
                url=f"http://www.cninfo.com.cn/{code}",
                published_at=datetime.now() - timedelta(days=3),
                announcement_type="重大合同",
                summary="公司近日与某大型企业签订战略合作...",
            ),
        ]

    def _get_mock_reports(self, code: str) -> List[Dict[str, Any]]:
        """Get mock research reports for demo."""
        return [
            {
                "title": f"{code} 深度研究报告",
                "institution": "中金公司",
                "rating": "买入",
                "target_price": 150.00,
                "summary": "公司基本面优良，行业发展前景广阔...",
                "published_at": datetime.now() - timedelta(days=2),
            },
            {
                "title": f"{code} 投资价值分析报告",
                "institution": "华泰证券",
                "rating": "增持",
                "target_price": 140.00,
                "summary": "业绩增长确定性高，估值合理...",
                "published_at": datetime.now() - timedelta(days=5),
            },
        ]
