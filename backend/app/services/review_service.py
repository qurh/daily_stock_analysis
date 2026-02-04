"""Review Service."""

import logging
import calendar as cal
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func

from app.schemas.review import (
    DailyReviewCreate,
    DailyReviewResponse,
    WeeklyReviewResponse,
    ReviewCalendarResponse,
    ReviewCalendarDay,
)
from app.models.strategy import STRDailyReview

logger = logging.getLogger(__name__)


class ReviewService:
    """Review service for daily/weekly analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_reviews(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
    ) -> List[DailyReviewResponse]:
        """Get daily review reports."""
        query = select(STRDailyReview)

        if start_date:
            query = query.where(STRDailyReview.date >= start_date)
        if end_date:
            query = query.where(STRDailyReview.date <= end_date)

        query = query.order_by(desc(STRDailyReview.date)).limit(limit)
        result = await self.db.execute(query)
        reviews = result.scalars().all()

        return [self._to_review_response(r) for r in reviews]

    async def get_daily_review(self, review_date: date) -> DailyReviewResponse:
        """Get specific daily review."""
        query = select(STRDailyReview).where(STRDailyReview.date == review_date)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError(f"Review for {review_date} not found")

        return self._to_review_response(review)

    async def generate_daily_review(
        self, review: DailyReviewCreate
    ) -> DailyReviewResponse:
        """Generate or save daily review."""
        # Check if exists
        existing_query = select(STRDailyReview).where(
            STRDailyReview.date == review.date
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.market_overview = review.market_overview
            existing.hot_sectors = review.hot_sectors
            existing.winning_trades = review.winning_trades
            existing.losing_trades = review.losing_trades
            existing.lessons_earned = review.lessons_learned
            existing.knowledge_gained = review.knowledge_gained
            existing.tomorrow_focus = review.tomorrow_focus

            await self.db.flush()
            await self.db.refresh(existing)

            return self._to_review_response(existing)

        # Create new
        model = STRDailyReview(
            date=review.date,
            market_overview=review.market_overview,
            hot_sectors=review.hot_sectors,
            winning_trades=review.winning_trades,
            losing_trades=review.losing_trades,
            lessons_learned=review.lessons_learned,
            knowledge_gained=review.knowledge_gained,
            tomorrow_focus=review.tomorrow_focus,
        )

        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)

        return self._to_review_response(model)

    async def get_weekly_reviews(
        self, limit: int = 12
    ) -> List[WeeklyReviewResponse]:
        """Get weekly review reports."""
        # TODO: Implement weekly aggregation
        return []

    async def get_calendar(
        self, year: int, month: int
    ) -> ReviewCalendarResponse:
        """Get review calendar for a month."""
        # Get all reviews in the month
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])

        query = select(STRDailyReview).where(
            and_(
                STRDailyReview.date >= start_date,
                STRDailyReview.date <= end_date,
            )
        )
        result = await self.db.execute(query)
        reviews = result.scalars().all()

        review_dates = {r.date for r in reviews}
        review_map = {r.date: r.id for r in reviews}

        # Build calendar days
        days = []
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            current_date = date(year, month, day)
            days.append(ReviewCalendarDay(
                date=current_date,
                has_review=current_date in review_dates,
                review_id=review_map.get(current_date),
            ))

        return ReviewCalendarResponse(
            year=year,
            month=month,
            days=days,
        )

    def _to_review_response(self, review: STRDailyReview) -> DailyReviewResponse:
        """Convert model to response."""
        return DailyReviewResponse(
            id=review.id,
            date=review.date,
            market_overview=review.market_overview,
            hot_sectors=review.hot_sectors or [],
            winning_trades=review.winning_trades or [],
            losing_trades=review.losing_trades or [],
            lessons_learned=review.lessons_learned or [],
            knowledge_gained=review.knowledge_gained or [],
            tomorrow_focus=review.tomorrow_focus or [],
            created_by=review.created_by,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
