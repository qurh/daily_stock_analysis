"""Strategy Management Schemas."""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class StrategyCreate(BaseModel):
    """Strategy creation schema."""

    name: str
    category: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    risk_management: Dict[str, Any] = Field(default_factory=dict)
    source_doc_id: Optional[int] = None


class StrategyUpdate(BaseModel):
    """Strategy update schema."""

    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    risk_management: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class StrategyResponse(BaseModel):
    """Strategy response schema."""

    id: int
    name: str
    category: str
    description: Optional[str]
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    risk_management: Dict[str, Any]
    source_doc_id: Optional[int]
    verification_count: int
    success_rate: Optional[Decimal]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class StrategyListResponse(BaseModel):
    """Strategy list response."""

    strategies: List[StrategyResponse]
    total: int
    limit: int
    offset: int


class BacktestRequest(BaseModel):
    """Backtest request schema."""

    code: str
    start_date: date
    end_date: date
    initial_capital: Decimal = Decimal("100000")
    params: Dict[str, Any] = Field(default_factory=dict)


class BacktestMetrics(BaseModel):
    """Backtest metrics."""

    total_return: Decimal
    annualized_return: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    trade_count: int


class BacktestResponse(BaseModel):
    """Backtest response."""

    strategy_id: int
    code: str
    period_start: date
    period_end: date
    metrics: BacktestMetrics
    trades: List[Dict[str, Any]] = Field(default_factory=list)
    chart_data: List[Dict[str, Any]] = Field(default_factory=list)


class SignalResponse(BaseModel):
    """Trading signal response."""

    id: int
    strategy_id: int
    strategy_name: str
    code: str
    signal_type: str  # buy/sell/hold
    confidence: Decimal
    reasoning: Optional[str]
    price: Decimal
    created_at: datetime
