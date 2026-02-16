from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_feedback_service
from app.services.feedback_service import FeedbackService

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
    service: FeedbackService = Depends(get_feedback_service),
) -> dict[str, Any]:
    try:
        return service.record(
            target_type=request.target_type,
            target_id=request.target_id,
            score=request.score,
            tags=request.tags,
            comment=request.comment,
            source=request.source,
        )
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
