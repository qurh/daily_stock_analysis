from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_notification_service
from app.services.notification_service import NotificationHub, NotificationMessage

router = APIRouter(prefix="/notifications")


class NotificationPreviewRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    channels: list[str] = Field(default_factory=list)


class NotificationSendRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    channels: list[str] = Field(default_factory=list)


class NotificationChannelTestRequest(BaseModel):
    channel: str = Field(min_length=1)
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None


class NotificationDeliveryRetryRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None


@router.get("/channels")
def list_channels(service: NotificationHub = Depends(get_notification_service)) -> dict[str, Any]:
    return service.list_channels()


@router.get("/deliveries")
def list_notification_deliveries(
    source_type: str | None = Query(default=None),
    source_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: NotificationHub = Depends(get_notification_service),
) -> dict[str, Any]:
    return service.list_deliveries(
        source_type=source_type,
        source_id=source_id,
        channel=channel,
        status=status,
        limit=limit,
    )


@router.post("/deliveries/{delivery_id}/retry")
def retry_notification_delivery(
    delivery_id: str,
    request: NotificationDeliveryRetryRequest | None = None,
    service: NotificationHub = Depends(get_notification_service),
) -> dict[str, Any]:
    try:
        return service.retry_delivery(
            delivery_id=delivery_id,
            title=(request.title if request is not None else None),
            content=(request.content if request is not None else None),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/preview")
def preview_notifications(
    request: NotificationPreviewRequest,
    service: NotificationHub = Depends(get_notification_service),
) -> dict[str, Any]:
    try:
        return service.preview(
            message=NotificationMessage(title=request.title, content=request.content),
            channels=request.channels or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/send")
def send_notifications(
    request: NotificationSendRequest,
    service: NotificationHub = Depends(get_notification_service),
) -> dict[str, Any]:
    try:
        return service.send(
            message=NotificationMessage(title=request.title, content=request.content),
            channels=request.channels or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/channels/test")
def test_notification_channel(
    request: NotificationChannelTestRequest,
    service: NotificationHub = Depends(get_notification_service),
) -> dict[str, Any]:
    title = (request.title or "").strip() or "Notification Channel Test"
    content = (request.content or "").strip() or "notification hub test message"
    try:
        return service.test_channel(channel=request.channel, title=title, content=content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
