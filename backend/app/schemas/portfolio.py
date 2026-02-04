"""Portfolio Management Schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class PortfolioPosition(BaseModel):
    """Portfolio position schema."""

    id: Optional[int] = None
    code: str
    name: Optional[str]
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    profit_loss: Decimal
    profit_pct: Decimal
    position_ratio: Decimal
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PortfolioCreate(BaseModel):
    """Create position schema."""

    code: str
    name: Optional[str] = None
    quantity: Decimal
    avg_cost: Decimal
    notes: Optional[str] = None


class PortfolioUpdate(BaseModel):
    """Update position schema."""

    quantity: Optional[Decimal] = None
    avg_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class PortfolioSummary(BaseModel):
    """Portfolio summary statistics."""

    total_value: Decimal
    total_profit: Decimal
    total_profit_pct: Decimal
    cash_balance: Decimal
    position_count: int


class PortfolioResponse(BaseModel):
    """Portfolio response schema."""

    summary: PortfolioSummary
    positions: List[PortfolioPosition]
    updated_at: datetime


class TransactionCreate(BaseModel):
    """Create transaction schema."""

    code: str
    transaction_type: str  # buy/sell
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal("0")
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    """Transaction response schema."""

    id: int
    code: str
    transaction_type: str
    quantity: Decimal
    price: Decimal
    total: Decimal
    fees: Decimal
    notes: Optional[str]
    transaction_date: datetime
    created_at: datetime
