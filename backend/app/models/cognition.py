"""Cognition and Decision Models."""

from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Numeric, ARRAY, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class COGInvestmentStyle(TimestampMixin):
    """Investment style configurations."""

    __tablename__ = "cog_investment_styles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    risk_tolerance: Mapped[str] = mapped_column(String(20), nullable=False)  # conservative/moderate/aggressive
    tech_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.5)
    fundamental_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.3)
    sentiment_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.2)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class COGCognitionState(TimestampMixin):
    """Current market cognition state."""

    __tablename__ = "cog_cognition_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_stage: Mapped[str] = mapped_column(String(20), nullable=False)  # consolidation/trend_up/trend_down/extreme/bottom/top
    risk_attitude: Mapped[str] = mapped_column(String(20), nullable=False)
    style_id: Mapped[int] = mapped_column(Integer, nullable=True)
    overall_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.5)
    active_signals: Mapped[List[str]] = mapped_column(ARRAY(String))
    market_sentiment: Mapped[str] = mapped_column(String(20))  # bullish/bearish/neutral
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class COGConfidenceLog(TimestampMixin):
    """Confidence scoring logs."""

    __tablename__ = "cog_confidence_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conclusion_type: Mapped[str] = mapped_column(String(50), nullable=False)
    conclusion_id: Mapped[int] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    factors: Mapped[List[str]] = mapped_column(JSON, default=list)
