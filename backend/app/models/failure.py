"""Failure Case Models."""

from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class FCFailureCase(TimestampMixin):
    """Failure case records for learning."""

    __tablename__ = "fc_failure_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_conclusion_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_conclusion_id: Mapped[int] = mapped_column(Integer, nullable=True)
    original_conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    actual_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)  # data_delay/indicator_failure/logic_error/market_structure_change
    error_analysis: Mapped[str] = mapped_column(Text)
    lessons_learned: Mapped[str] = mapped_column(Text)
    improvement_suggestions: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high/critical
    related_codes: Mapped[List[str]] = mapped_column(ARRAY(String))
    related_indicators: Mapped[List[str]] = mapped_column(ARRAY(String))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    identified_at: Mapped[datetime] = mapped_column(DateTime)


class FCFailureReference(TimestampMixin):
    """References to failure cases."""

    __tablename__ = "fc_failure_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    failure_case_id: Mapped[int] = mapped_column(Integer, nullable=False)
    referenced_by_type: Mapped[str] = mapped_column(String(50), nullable=False)
    referenced_by_id: Mapped[int] = mapped_column(Integer, nullable=True)
    reference_context: Mapped[str] = mapped_column(Text)
