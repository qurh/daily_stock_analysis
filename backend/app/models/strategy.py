"""Strategy and Review Models."""

from datetime import datetime, date
from decimal import Decimal
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Boolean, JSON, Numeric, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class STRStrategy(TimestampMixin):
    """Trading strategies."""

    __tablename__ = "str_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # trend/value/breakout/etc.
    description: Mapped[str] = mapped_column(Text)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False)
    actions: Mapped[dict] = mapped_column(JSON, nullable=False)
    risk_management: Mapped[dict] = mapped_column(JSON, default=dict)
    examples: Mapped[List[dict]] = mapped_column(JSON, default=list)
    source_doc_id: Mapped[int] = mapped_column(Integer, nullable=True)
    verification_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/active/deprecated
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)


class STRStrategyTest(TimestampMixin):
    """Strategy backtest results."""

    __tablename__ = "str_strategy_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(Integer, nullable=False)
    test_type: Mapped[str] = mapped_column(String(20))  # backtest/forward
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)


class STRStrategySignal(TimestampMixin):
    """Generated trading signals."""

    __tablename__ = "str_strategy_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # buy/sell/hold
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    reasoning: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class STRDailyReview(TimestampMixin):
    """Daily review records."""

    __tablename__ = "str_daily_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    market_overview: Mapped[str] = mapped_column(Text)
    hot_sectors: Mapped[List[dict]] = mapped_column(JSON, default=list)
    winning_trades: Mapped[List[dict]] = mapped_column(JSON, default=list)
    losing_trades: Mapped[List[dict]] = mapped_column(JSON, default=list)
    lessons_learned: Mapped[List[str]] = mapped_column(ARRAY(String))
    knowledge_gained: Mapped[List[str]] = mapped_column(ARRAY(String))
    tomorrow_focus: Mapped[List[str]] = mapped_column(ARRAY(String))
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)


class STRLearningRecord(TimestampMixin):
    """Learning and improvement records."""

    __tablename__ = "str_learning_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # review/feedback/backtest
    source_id: Mapped[int] = mapped_column(Integer, nullable=True)
    key_insights: Mapped[List[str]] = mapped_column(ARRAY(String))
    applied_to_strategy: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)
