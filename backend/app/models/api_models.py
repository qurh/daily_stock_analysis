from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.api_database import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Stock(Base):
    __tablename__ = "stocks"

    code = Column(String(10), primary_key=True)
    name = Column(String(64), nullable=False)
    industry = Column(String(64), nullable=True)
    market = Column(String(16), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_watchlist_user_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    name = Column(String(64), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    stocks = relationship("WatchlistStock", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"
    __table_args__ = (Index("ix_watchlist_stocks_watchlist_code", "watchlist_id", "code"),)

    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), primary_key=True)
    code = Column(String(10), ForeignKey("stocks.code"), primary_key=True)
    sort_order = Column(Integer, nullable=False, default=0)
    added_at = Column(DateTime, nullable=False, default=utcnow)

    watchlist = relationship("Watchlist", back_populates="stocks")
    stock = relationship("Stock")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    __table_args__ = (Index("ix_analysis_reports_code_generated_at", "code", "generated_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    code = Column(String(10), nullable=False, index=True)
    report_type = Column(String(32), nullable=False, default="stock")
    report_date = Column(Date, nullable=False, default=date.today)
    generated_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    markdown_path = Column(String(512), nullable=False)
    summary_json = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    model = Column(String(128), nullable=True)
    source = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="ready")
