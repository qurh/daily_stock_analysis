"""Review Schemas."""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class DailyReviewCreate(BaseModel):
    """Daily review creation schema."""

    date: date
    market_overview: Optional[str] = None
    hot_sectors: List[Dict[str, Any]] = Field(default_factory=list)
    winning_trades: List[Dict[str, Any]] = Field(default_factory=list)
    losing_trades: List[Dict[str, Any]] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    knowledge_gained: List[str] = Field(default_factory=list)
    tomorrow_focus: List[str] = Field(default_factory=list)


class DailyReviewResponse(BaseModel):
    """Daily review response."""

    id: int
    date: date
    market_overview: Optional[str]
    hot_sectors: List[Dict[str, Any]]
    winning_trades: List[Dict[str, Any]]
    losing_trades: List[Dict[str, Any]]
    lessons_learned: List[str]
    knowledge_gained: List[str]
    tomorrow_focus: List[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime] = None


class WeeklyReviewResponse(BaseModel):
    """Weekly review response."""

    id: int
    week_start: date
    week_end: date
    market_summary: str
    sector_performance: List[Dict[str, Any]]
    key_lessons: List[str]
    strategy_updates: List[Dict[str, Any]]
    next_week_outlook: Optional[str]
    created_at: datetime


class ReviewCalendarDay(BaseModel):
    """Single calendar day data."""

    date: date
    has_review: bool
    review_id: Optional[int]


class ReviewCalendarResponse(BaseModel):
    """Review calendar response."""

    year: int
    month: int
    days: List[ReviewCalendarDay]
