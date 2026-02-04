"""Review API Routes."""

from fastapi import APIRouter, Depends
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.review import (
    DailyReviewCreate,
    DailyReviewResponse,
    WeeklyReviewResponse,
    ReviewCalendarResponse,
)
from app.services.review_service import ReviewService

router = APIRouter()


@router.get("/daily", response_model=List[DailyReviewResponse])
async def get_daily_reviews(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 30,
    db=Depends(get_db),
):
    """Get daily review reports."""
    service = ReviewService(db)
    return await service.get_daily_reviews(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.post("/daily", response_model=DailyReviewResponse)
async def generate_daily_review(
    review: DailyReviewCreate,
    db=Depends(get_db),
):
    """Generate or save daily review."""
    service = ReviewService(db)
    return await service.generate_daily_review(review)


@router.get("/daily/{review_date}", response_model=DailyReviewResponse)
async def get_daily_review(
    review_date: date,
    db=Depends(get_db),
):
    """Get specific daily review."""
    service = ReviewService(db)
    return await service.get_daily_review(review_date)


@router.get("/weekly", response_model=List[WeeklyReviewResponse])
async def get_weekly_reviews(
    limit: int = 12,
    db=Depends(get_db),
):
    """Get weekly review reports."""
    service = ReviewService(db)
    return await service.get_weekly_reviews(limit=limit)


@router.get("/calendar", response_model=ReviewCalendarResponse)
async def get_review_calendar(
    year: int,
    month: int,
    db=Depends(get_db),
):
    """Get review calendar for a month."""
    service = ReviewService(db)
    return await service.get_calendar(year, month)
