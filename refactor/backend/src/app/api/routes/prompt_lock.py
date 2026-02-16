from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.api.deps import get_prompt_lock_audit_service
from app.services.prompt_lock_audit_service import PromptLockAuditService

router = APIRouter(prefix="/prompt-lock")


@router.get("/events")
def list_prompt_lock_events(
    flow_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    last_hours: int | None = Query(default=None, ge=1, le=24 * 30),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> dict[str, Any]:
    try:
        return service.list_events(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/failures/summary")
def summarize_prompt_lock_failures(
    flow_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    last_hours: int | None = Query(default=None, ge=1, le=24 * 30),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> dict[str, Any]:
    try:
        return service.summarize_failures(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/failures/grouped")
def group_prompt_lock_failures(
    flow_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    last_hours: int | None = Query(default=None, ge=1, le=24 * 30),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    group_by: list[str] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> dict[str, Any]:
    try:
        return service.group_failures(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            group_by=group_by,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/failures/trends")
def get_prompt_lock_failure_trends(
    flow_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    last_hours: int | None = Query(default=None, ge=1, le=24 * 30),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    granularity: str = Query(default="hour"),
    split_by: str | None = Query(default=None),
    reason_top_n: int | None = Query(default=None, ge=1, le=100),
    limit: int = Query(default=200, ge=1, le=2000),
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> dict[str, Any]:
    try:
        return service.failure_trends(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            granularity=granularity,
            split_by=split_by,
            reason_top_n=reason_top_n,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/overview")
def get_prompt_lock_overview(
    flow_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    last_hours: int | None = Query(default=None, ge=1, le=24 * 30),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    include: list[str] | None = Query(default=None),
    summary_limit: int = Query(default=20, ge=1, le=200),
    group_by: list[str] | None = Query(default=None),
    grouped_limit: int = Query(default=100, ge=1, le=500),
    granularity: str = Query(default="hour"),
    split_by: str | None = Query(default=None),
    reason_top_n: int | None = Query(default=None, ge=1, le=100),
    trend_limit: int = Query(default=200, ge=1, le=2000),
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> dict[str, Any]:
    try:
        return service.build_overview(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            include=include,
            summary_limit=summary_limit,
            group_by=group_by,
            grouped_limit=grouped_limit,
            granularity=granularity,
            split_by=split_by,
            reason_top_n=reason_top_n,
            trend_limit=trend_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/overview/metrics")
def get_prompt_lock_overview_metrics(
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> dict[str, Any]:
    return service.get_overview_metrics()


@router.get("/overview/metrics/prometheus")
def get_prompt_lock_overview_metrics_prometheus(
    service: PromptLockAuditService = Depends(get_prompt_lock_audit_service),
) -> PlainTextResponse:
    return PlainTextResponse(
        content=service.get_overview_metrics_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
