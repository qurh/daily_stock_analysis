"""Conclusion Lifecycle Models."""

from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Numeric, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class CONCLConclusion(TimestampMixin):
    """Analysis conclusions with lifecycle tracking."""

    __tablename__ = "concl_conclusions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conclusion_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    validity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # intraday/weekly/monthly
    validity_period: Mapped[int] = mapped_column(Integer)  # minutes
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="preliminary")  # preliminary/validated/expired/verified
    triggering_conditions: Mapped[List[str]] = mapped_column(ARRAY(String))
    related_codes: Mapped[List[str]] = mapped_column(ARRAY(String))
    related_indicators: Mapped[List[str]] = mapped_column(ARRAY(String))
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)
    validated_at: Mapped[datetime] = mapped_column(DateTime)
    expired_at: Mapped[datetime] = mapped_column(DateTime)
    verified_at: Mapped[datetime] = mapped_column(DateTime)


class CONCLValidation(TimestampMixin):
    """Conclusion validation records."""

    __tablename__ = "concl_validations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conclusion_id: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # price_trigger/time_trigger/event_trigger/indicator_trigger
    validation_result: Mapped[str] = mapped_column(String(20), nullable=False)  # validated/expired/partial
    actual_outcome: Mapped[str] = mapped_column(Text)
    deviation_analysis: Mapped[str] = mapped_column(Text)


class CONCLRevisionHistory(TimestampMixin):
    """Conclusion revision history."""

    __tablename__ = "concl_revision_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conclusion_id: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_type: Mapped[str] = mapped_column(String(20), nullable=False)  # confidence_adjust/condition_update/status_change
    old_value: Mapped[str] = mapped_column(Text)
    new_value: Mapped[str] = mapped_column(Text)
    revision_reason: Mapped[str] = mapped_column(Text)
    triggered_by: Mapped[str] = mapped_column(String(50))  # auto/user/system
