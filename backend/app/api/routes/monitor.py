"""Monitor Service API Routes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.monitor import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertListResponse,
    AlertHistoryResponse,
)
from app.services.monitor_service import MonitorService

router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    active_only: bool = True,
    db=Depends(get_db),
):
    """List all alerts."""
    service = MonitorService(db)
    return await service.list_alerts(active_only=active_only)


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db=Depends(get_db),
):
    """Create a new alert."""
    service = MonitorService(db)
    return await service.create_alert(alert)


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    update: AlertUpdate,
    db=Depends(get_db),
):
    """Update alert configuration."""
    service = MonitorService(db)
    return await service.update_alert(alert_id, update)


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db=Depends(get_db),
):
    """Delete an alert."""
    service = MonitorService(db)
    await service.delete_alert(alert_id)
    return {"message": "Alert deleted"}


@router.get("/alerts/history", response_model=AlertHistoryResponse)
async def get_alert_history(
    limit: int = 100,
    db=Depends(get_db),
):
    """Get alert trigger history."""
    service = MonitorService(db)
    return await service.get_history(limit=limit)
