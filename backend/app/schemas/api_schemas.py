from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class StockSyncItem(BaseModel):
    code: str = Field(min_length=1, max_length=10)
    name: str | None = Field(default=None, max_length=64)
    industry: str | None = Field(default=None, max_length=64)
    market: str | None = Field(default=None, max_length=16)
    is_active: bool = True


class StockSyncRequest(BaseModel):
    stocks: list[StockSyncItem] | None = None


class StockOut(BaseModel):
    code: str
    name: str
    industry: str | None = None
    market: str | None = None
    is_active: bool
    updated_at: datetime


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    sort_order: int = 0


class WatchlistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    sort_order: int | None = None


class WatchlistStockCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10)
    sort_order: int = 0


class WatchlistOut(BaseModel):
    id: int
    name: str
    sort_order: int
    stock_count: int
    created_at: datetime


class ReportListItem(BaseModel):
    id: int
    code: str
    report_type: str
    report_date: date
    generated_at: datetime
    status: str
    source: str | None = None
    model: str | None = None


class ReportDetail(BaseModel):
    markdown: str
    metadata: dict[str, Any]
