from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.api.deps import get_feedback_service, get_optimization_service
from app.services.feedback_service import FeedbackService
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/feedback")


class FeedbackRecordCreateRequest(BaseModel):
    target_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    score: float = Field(ge=0, le=5)
    tags: list[str] = Field(default_factory=list)
    comment: str | None = None
    source: str = Field(default="user", pattern="^(user|chatbot|system|manual)$")


@router.post("/records", status_code=201)
def create_feedback_record(
    request: FeedbackRecordCreateRequest,
    http_request: Request,
    service: FeedbackService = Depends(get_feedback_service),
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> dict[str, Any]:
    try:
        record = service.record(
            target_type=request.target_type,
            target_id=request.target_id,
            score=request.score,
            tags=request.tags,
            comment=request.comment,
            source=request.source,
        )
        settings = http_request.app.state.settings
        optimization_trigger: dict[str, Any] = {"triggered": False, "reason": "disabled"}
        if settings.feedback_event_optimization_enabled:
            try:
                optimization_trigger = optimization_service.maybe_trigger_from_feedback_event(
                    feedback_id=record["feedback_id"],
                    min_records=settings.feedback_event_optimization_min_records,
                    cooldown_seconds=settings.feedback_event_optimization_cooldown_seconds,
                )
            except Exception as exc:  # pragma: no cover - defensive path
                optimization_trigger = {"triggered": False, "reason": "trigger_error", "error": str(exc)}
        record["optimization_trigger"] = optimization_trigger
        return record
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/records")
def list_feedback_records(
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: FeedbackService = Depends(get_feedback_service),
) -> dict[str, Any]:
    return service.list_records(
        target_type=target_type,
        target_id=target_id,
        source=source,
        limit=limit,
    )
