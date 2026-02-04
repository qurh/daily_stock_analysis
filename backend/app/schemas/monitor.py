"""Monitor Service Schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """Alert creation schema."""

    code: Optional[str] = Field(None, description="Stock code (optional)")
    alert_type: str = Field(..., description="alert_above/below/change")
    threshold: Decimal
    direction: str = Field("above", description="above/below")
    enabled: bool = True
    notify_channels: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class AlertUpdate(BaseModel):
    """Alert update schema."""

    threshold: Optional[Decimal] = None
    direction: Optional[str] = None
    enabled: Optional[bool] = None
    notify_channels: Optional[List[str]] = None
    notes: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert response schema."""

    id: int
    code: Optional[str]
    alert_type: str
    threshold: Decimal
    direction: str
    enabled: bool
    notify_channels: List[str]
    notes: Optional[str]
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    """Alert list response."""

    alerts: List[AlertResponse]
    total: int


class AlertHistoryEntry(BaseModel):
    """Alert history entry."""

    id: int
    alert_id: int
    alert_type: str
    code: Optional[str]
    triggered_at: datetime
    message: str
    data_snapshot: Dict[str, Any]


class AlertHistoryResponse(BaseModel):
    """Alert history response."""

    history: List[AlertHistoryEntry]
    total: int
