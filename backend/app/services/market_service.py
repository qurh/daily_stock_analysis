"""Market Data Service."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.market import (
    QuoteResponse,
    HistoryResponse,
    OHLCV,
    IndicatorResponse,
    AnalysisRequest,
    AnalysisResponse,
    DailyReviewRequest,
    DailyReviewResponse,
)
from app.data_providers import DataFetcherManager

logger = logging.getLogger(__name__)


class MarketService:
    """Market data service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fetcher = DataFetcherManager()

    async def get_quotes(self, codes: List[str]) -> List[QuoteResponse]:
        """Get real-time quotes for specified stocks."""
        results = []
        for code in codes:
            try:
                data = await self.fetcher.get_realtime(code)
                if data:
                    results.append(QuoteResponse(
                        code=code,
                        name=data.get("name"),
                        price=Decimal(str(data.get("price", 0))),
                        pct_chg=Decimal(str(data.get("pct_chg", 0))),
                        volume=data.get("volume"),
                        turnover_rate=Decimal(str(data.get("turnover_rate", 0))),
                        amplitude=Decimal(str(data.get("amplitude", 0))),
                        open=Decimal(str(data.get("open", 0))),
                        high=Decimal(str(data.get("high", 0))),
                        low=Decimal(str(data.get("low", 0))),
                        close=Decimal(str(data.get("close", 0))),
                        pe_ratio=Decimal(str(data.get("pe_ratio", 0))),
                        pb_ratio=Decimal(str(data.get("pb_ratio", 0))),
                        market_cap=data.get("market_cap"),
                        updated_at=datetime.now(),
                    ))
            except Exception as e:
                logger.error(f"Error fetching quote for {code}: {e}")

        return results

    async def get_history(
        self,
        code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "daily",
        limit: int = 100,
    ) -> HistoryResponse:
        """Get historical price data."""
        # Default to last 6 months if no dates specified
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=180)

        data = await self.fetcher.get_history(
            code=code,
            start_date=start_date,
            end_date=end_date,
            period=period,
        )

        # Get stock name
        name = await self.fetcher.get_name(code)

        ohlcv_data = []
        for item in data:
            ohlcv_data.append(OHLCV(
                date=item["date"],
                open=Decimal(str(item["open"])),
                high=Decimal(str(item["high"])),
                low=Decimal(str(item["low"])),
                close=Decimal(str(item["close"])),
                volume=item["volume"],
                amount=Decimal(str(item["amount"])),
                pct_chg=Decimal(str(item.get("pct_chg", 0))),
            ))

        return HistoryResponse(
            code=code,
            name=name,
            period=period,
            data=ohlcv_data,
            limit=limit,
        )

    async def get_indicators(
        self,
        code: str,
        period: str = "daily",
    ) -> IndicatorResponse:
        """Get technical indicators."""
        from app.ml.indicators import TechnicalIndicators

        # Get historical data
        history = await self.get_history(code=code, period=period, limit=100)
        df = self._to_dataframe(history.data)

        # Calculate indicators
        ti = TechnicalIndicators()
        indicators = ti.calculate_all(df)

        return IndicatorResponse(
            code=code,
            date=history.data[-1].date if history.data else date.today(),
            moving_averages=indicators.get("moving_averages", {}),
            bias=indicators.get("bias"),
            volume_ratio=indicators.get("volume_ratio"),
            macd=indicators.get("macd"),
            kdj=indicators.get("kdj"),
        )

    async def analyze_stock(self, request: AnalysisRequest) -> AnalysisResponse:
        """Perform deep analysis on a stock."""
        code = request.code

        # Get current quote
        quotes = await self.get_quotes([code])
        quote = quotes[0] if quotes else None

        # Get indicators
        indicators = await self.get_indicators(code)

        # Get chip distribution if requested
        chip = None
        if request.options and request.options.get("include_chip"):
            chip = await self._get_chip_distribution(code)

        # Get news if requested
        recent_news = []
        if request.options and request.options.get("include_news"):
            recent_news = await self._get_recent_news(code)

        # Build analysis
        analysis = self._build_analysis(quote, indicators)

        return AnalysisResponse(
            code=code,
            name=quote.name if quote else None,
            current_price=quote.price if quote else Decimal("0"),
            pct_chg=quote.pct_chg if quote else Decimal("0"),
            analysis=analysis,
            indicators={
                "moving_averages": indicators.moving_averages,
                "bias": str(indicators.bias) if indicators.bias else None,
                "volume_ratio": str(indicators.volume_ratio) if indicators.volume_ratio else None,
            },
            chip_distribution=chip,
            recent_news=recent_news,
            updated_at=datetime.now(),
        )

    async def generate_daily_review(self, request: DailyReviewRequest) -> DailyReviewResponse:
        """Generate daily market review."""
        from app.ml.market_analyzer import MarketAnalyzer

        analyzer = MarketAnalyzer()

        # Get market overview data
        overview = await analyzer.generate_market_overview(request.date)

        # Get hot sectors
        hot_sectors = []
        if request.include_hot_sectors:
            hot_sectors = await analyzer.get_hot_sectors(request.date)

        # Get market sentiment
        sentiment = None
        if request.include_market_sentiment:
            sentiment = await analyzer.get_market_sentiment(request.date)

        return DailyReviewResponse(
            date=request.date,
            market_overview=overview,
            hot_sectors=hot_sectors,
            market_sentiment=sentiment,
            tomorrow_outlook=None,  # AI will generate this
            generated_at=datetime.now(),
        )

    async def _get_chip_distribution(self, code: str) -> Dict[str, Any]:
        """Get chip distribution data."""
        try:
            data = await self.fetcher.get_chip_distribution(code)
            return data or {}
        except Exception as e:
            logger.error(f"Error fetching chip distribution: {e}")
            return {}

    async def _get_recent_news(self, code: str) -> List[Dict[str, Any]]:
        """Get recent news for a stock."""
        from app.ml.search_service import SearchService

        try:
            service = SearchService()
            news = await service.search_news(code, limit=5)
            return [{"title": n.title, "url": n.url, "sentiment": n.sentiment} for n in news]
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []

    def _build_analysis(
        self,
        quote: Optional[QuoteResponse],
        indicators: IndicatorResponse,
    ) -> Dict[str, Any]:
        """Build analysis from quote and indicators."""
        trend = "neutral"
        score = 50

        # Simple trend analysis based on MA
        if quote:
            ma5 = indicators.moving_averages.get("ma5")
            ma20 = indicators.moving_averages.get("ma20")
            if ma5 and ma20:
                price = float(quote.price)
                if price > float(ma5) > float(ma20):
                    trend = "上升趋势"
                    score = 70
                elif price < float(ma5) < float(ma20):
                    trend = "下降趋势"
                    score = 30

        return {
            "trend": trend,
            "tech_score": score,
            "recommendation": "持有",
            "risk_level": "中",
        }

    def _to_dataframe(self, data: List[OHLCV]):
        """Convert OHLCV list to pandas DataFrame."""
        import pandas as pd

        return pd.DataFrame([{
            "date": d.date,
            "open": float(d.open),
            "high": float(d.high),
            "low": float(d.low),
            "close": float(d.close),
            "volume": d.volume,
        } for d in data])
