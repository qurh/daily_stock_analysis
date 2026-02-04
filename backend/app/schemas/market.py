"""Market Data Schemas."""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    """Quote request schema."""

    codes: List[str] = Field(..., description="Stock codes to query")


class QuoteResponse(BaseModel):
    """Quote response schema."""

    code: str
    name: Optional[str]
    price: Decimal
    pct_chg: Decimal
    volume: Optional[int]
    turnover_rate: Optional[Decimal]
    amplitude: Optional[Decimal]
    open: Optional[Decimal]
    high: Optional[Decimal]
    low: Optional[Decimal]
    close: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    market_cap: Optional[Decimal]
    updated_at: datetime


class HistoryRequest(BaseModel):
    """Historical data request."""

    code: str = Field(..., description="Stock code")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period: str = Field(default="daily", description="daily/weekly/monthly")
    limit: int = Field(default=100, description="Max records")


class OHLCV(BaseModel):
    """OHLCV data point."""

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal
    pct_chg: Decimal


class HistoryResponse(BaseModel):
    """Historical data response."""

    code: str
    name: Optional[str]
    period: str
    data: List[OHLCV]
    limit: int


class IndicatorRequest(BaseModel):
    """Indicator request schema."""

    code: str
    period: str = "daily"


class IndicatorResponse(BaseModel):
    """Technical indicators response."""

    code: str
    date: date
    moving_averages: Dict[str, Decimal] = Field(
        default_factory=dict, description="MA5, MA10, MA20, etc."
    )
    bias: Optional[Decimal] = None
    volume_ratio: Optional[Decimal] = None
    macd: Optional[Dict[str, Decimal]] = None
    kdj: Optional[Dict[str, Decimal]] = None


class AnalysisRequest(BaseModel):
    """Stock analysis request schema."""

    code: str
    options: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Analysis options",
    )


class AnalysisResponse(BaseModel):
    """Stock analysis response."""

    code: str
    name: Optional[str]
    current_price: Decimal
    pct_chg: Decimal
    analysis: Dict[str, Any]
    indicators: Dict[str, Any]
    chip_distribution: Optional[Dict[str, Any]] = None
    recent_news: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime


class DailyReviewRequest(BaseModel):
    """Daily review generation request."""

    date: date
    include_hot_sectors: bool = True
    include_market_sentiment: bool = True


class DailyReviewResponse(BaseModel):
    """Daily review response."""

    date: date
    market_overview: str
    hot_sectors: List[Dict[str, Any]] = Field(default_factory=list)
    market_sentiment: Optional[str] = None
    tomorrow_outlook: Optional[str] = None
    generated_at: datetime
