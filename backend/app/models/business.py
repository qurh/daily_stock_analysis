"""Business Data Models."""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, BigInteger, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampMixin


class StockDaily(TimestampMixin):
    """Daily stock data."""

    __tablename__ = "stock_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    high: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    low: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    close: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    volume: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    pct_chg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    ma5: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ma10: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ma20: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    volume_ratio: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    data_source: Mapped[str] = mapped_column(String(50))


class StockRealtime(TimestampMixin):
    """Real-time stock quotes."""

    __tablename__ = "stock_realtime"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    pct_chg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    volume_ratio: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    turnover_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    amplitude: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    pe_ratio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    pb_ratio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_mv: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    circ_mv: Mapped[Decimal] = mapped_column(Numeric(18, 2))


class ChipDistribution(TimestampMixin):
    """Chip distribution data."""

    __tablename__ = "chip_distribution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    profit_ratio: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    concentration_90: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    concentration_70: Mapped[Decimal] = mapped_column(Numeric(6, 2))


class Portfolio(TimestampMixin):
    """Portfolio positions."""

    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    profit_loss: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    profit_pct: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    position_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    notes: Mapped[str] = mapped_column(Text)


class PortfolioHistory(TimestampMixin):
    """Portfolio history snapshots."""

    __tablename__ = "portfolio_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    positions_snapshot: Mapped[dict] = mapped_column(JSON)


class Alerts(TimestampMixin):
    """Alert configurations."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    direction: Mapped[str] = mapped_column(String(10))  # above/below
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered: Mapped[datetime] = mapped_column(DateTime)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    notify_channels: Mapped[dict] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text)


class AlertHistory(TimestampMixin):
    """Alert trigger history."""

    __tablename__ = "alert_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(Integer, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    message: Mapped[str] = mapped_column(Text)
    data_snapshot: Mapped[dict] = mapped_column(JSON)


class Tasks(TimestampMixin):
    """Task queue for background jobs."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/success/failed
    payload: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    error: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime] = mapped_column(DateTime)
