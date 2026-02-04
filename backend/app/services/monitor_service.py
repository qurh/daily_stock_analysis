"""Monitor Service."""

import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.schemas.monitor import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertListResponse,
    AlertHistoryResponse,
    AlertHistoryEntry,
)
from app.models.business import Alerts, AlertHistory

logger = logging.getLogger(__name__)


class MonitorService:
    """Market monitoring service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_alerts(self, active_only: bool = True) -> AlertListResponse:
        """List all alerts."""
        query = select(Alerts)

        if active_only:
            query = query.where(Alerts.is_active == True)

        query = query.order_by(desc(Alerts.created_at))
        result = await self.db.execute(query)
        alerts = result.scalars().all()

        return AlertListResponse(
            alerts=[self._to_alert_response(a) for a in alerts],
            total=len(alerts),
        )

    async def create_alert(self, alert: AlertCreate) -> AlertResponse:
        """Create a new alert."""
        model = Alerts(
            code=alert.code,
            alert_type=alert.alert_type,
            threshold=alert.threshold,
            direction=alert.direction,
            is_active=alert.enabled,
            notify_channels=alert.notify_channels,
            notes=alert.notes,
        )

        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)

        return self._to_alert_response(model)

    async def update_alert(
        self, alert_id: int, update: AlertUpdate
    ) -> AlertResponse:
        """Update alert configuration."""
        query = select(Alerts).where(Alerts.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        if update.threshold is not None:
            alert.threshold = update.threshold
        if update.direction is not None:
            alert.direction = update.direction
        if update.enabled is not None:
            alert.is_active = update.enabled
        if update.notify_channels is not None:
            alert.notify_channels = update.notify_channels
        if update.notes is not None:
            alert.notes = update.notes

        await self.db.flush()
        await self.db.refresh(alert)

        return self._to_alert_response(alert)

    async def delete_alert(self, alert_id: int) -> None:
        """Delete an alert."""
        query = select(Alerts).where(Alerts.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()

        if alert:
            await self.db.delete(alert)
            await self.db.flush()

    async def get_history(self, limit: int = 100) -> AlertHistoryResponse:
        """Get alert trigger history."""
        query = select(AlertHistory).order_by(desc(AlertHistory.triggered_at)).limit(limit)
        result = await self.db.execute(query)
        history = result.scalars().all()

        return AlertHistoryResponse(
            history=[
                AlertHistoryEntry(
                    id=h.id,
                    alert_id=h.alert_id,
                    alert_type=h.alert_type,  # Need to join
                    code=h.code,
                    triggered_at=h.triggered_at,
                    message=h.message,
                    data_snapshot=h.data_snapshot or {},
                )
                for h in history
            ],
            total=len(history),
        )

    async def check_alerts(self):
        """Check all active alerts against current prices."""
        from app.services.market_service import MarketService

        market_service = MarketService(self.db)

        # Get all active alerts
        query = select(Alerts).where(Alerts.is_active == True)
        result = await self.db.execute(query)
        alerts = result.scalars().all()

        # Group by code
        codes = list(set(a.code for a in alerts if a.code))
        if not codes:
            return

        # Get current quotes
        quotes = await market_service.get_quotes(codes)
        quote_map = {q.code: q for q in quotes}

        # Check each alert
        for alert in alerts:
            quote = quote_map.get(alert.code)
            if not quote:
                continue

            triggered = False
            message = ""

            if alert.alert_type == "price_above":
                if quote.price >= alert.threshold:
                    triggered = True
                    message = f"{alert.code} 股价 {quote.price} 超过阈值 {alert.threshold}"
            elif alert.alert_type == "price_below":
                if quote.price <= alert.threshold:
                    triggered = True
                    message = f"{alert.code} 股价 {quote.price} 低于阈值 {alert.threshold}"
            elif alert.alert_type == "pct_chg_above":
                if abs(quote.pct_chg) >= alert.threshold:
                    triggered = True
                    message = f"{alert.code} 涨跌幅 {quote.pct_chg}% 超过阈值 {alert.threshold}%"

            if triggered:
                await self._trigger_alert(alert, quote, message)

    async def _trigger_alert(self, alert, quote, message: str):
        """Record alert trigger."""
        # Update alert
        alert.last_triggered = datetime.now()
        alert.trigger_count += 1

        # Record history
        history = AlertHistory(
            alert_id=alert.id,
            code=alert.code,
            alert_type=alert.alert_type,
            triggered_at=datetime.now(),
            message=message,
            data_snapshot={
                "price": str(quote.price),
                "pct_chg": str(quote.pct_chg),
            },
        )
        self.db.add(history)

        # TODO: Send notifications

        await self.db.flush()

    def _to_alert_response(self, alert: Alerts) -> AlertResponse:
        """Convert model to response."""
        return AlertResponse(
            id=alert.id,
            code=alert.code,
            alert_type=alert.alert_type,
            threshold=alert.threshold,
            direction=alert.direction,
            enabled=alert.is_active,
            notify_channels=alert.notify_channels or [],
            notes=alert.notes,
            last_triggered=alert.last_triggered,
            trigger_count=alert.trigger_count,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
