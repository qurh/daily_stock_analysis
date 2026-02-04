"""Market Data API Routes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.market import (
    QuoteRequest,
    QuoteResponse,
    HistoryRequest,
    HistoryResponse,
    IndicatorRequest,
    IndicatorResponse,
    AnalysisRequest,
    AnalysisResponse,
    DailyReviewRequest,
    DailyReviewResponse,
)
from app.services.market_service import MarketService

router = APIRouter()


@router.get("/quote", response_model=List[QuoteResponse])
async def get_quotes(
    codes: List[str],
    db=Depends(get_db),
):
    """Get real-time quotes for specified stocks."""
    service = MarketService(db)
    return await service.get_quotes(codes)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "daily",
    limit: int = 100,
    db=Depends(get_db),
):
    """Get historical price data."""
    service = MarketService(db)
    return await service.get_history(
        code=code,
        start_date=start_date,
        end_date=end_date,
        period=period,
        limit=limit,
    )


@router.get("/indicators", response_model=IndicatorResponse)
async def get_indicators(
    code: str,
    period: str = "daily",
    db=Depends(get_db),
):
    """Get technical indicators for a stock."""
    service = MarketService(db)
    return await service.get_indicators(code=code, period=period)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(
    request: AnalysisRequest,
    db=Depends(get_db),
):
    """Perform deep analysis on a stock."""
    service = MarketService(db)
    return await service.analyze_stock(request)


@router.post("/review/daily", response_model=DailyReviewResponse)
async def generate_daily_review(
    request: DailyReviewRequest,
    db=Depends(get_db),
):
    """Generate daily market review."""
    service = MarketService(db)
    return await service.generate_daily_review(request)
