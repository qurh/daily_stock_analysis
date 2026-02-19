from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_strategy_service
from app.services.strategy_service import StrategyService

router = APIRouter(prefix="/strategy")


class CognitionDistillRequest(BaseModel):
    session_id: str = Field(min_length=1)
    start_index: int | None = Field(default=None, ge=1)
    end_index: int | None = Field(default=None, ge=1)
    title: str | None = None


class CognitionReviewRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject|edit)$")
    reviewer: str = Field(min_length=1)
    editor_notes: str | None = None
    edited_markdown: str | None = None


class StrategyExtractRequest(BaseModel):
    strategy_type: str = Field(pattern="^(analysis|trading)$")
    source_scope: str = "indexed_memos"
    prompt_ref: str | None = None


class StrategyPublishRequest(BaseModel):
    backtest_job_id: str | None = None
    proposal_id: str | None = None


class StrategyRollbackRequest(BaseModel):
    reason: str | None = None


class StrategyBindRequest(BaseModel):
    flow_id: str = Field(min_length=1)
    prompt_refs: list[str] = Field(default_factory=list)
    prompt_lock_mode: str | None = Field(default=None, pattern="^(strict|lenient)$")
    effective_scope: dict[str, Any] = Field(default_factory=dict)


@router.post("/cognition/distill", status_code=201)
def distill_cognition(
    request: CognitionDistillRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    try:
        return service.distill_cognition(
            session_id=request.session_id,
            start_index=request.start_index,
            end_index=request.end_index,
            title=request.title,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/cognition/{memo_id}/review")
def review_cognition(
    memo_id: str,
    request: CognitionReviewRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    try:
        return service.review_cognition(
            memo_id=memo_id,
            action=request.action,
            reviewer=request.reviewer,
            editor_notes=request.editor_notes,
            edited_markdown=request.edited_markdown,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/extract", status_code=201)
def extract_strategy(
    request: StrategyExtractRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    try:
        return service.extract_strategy(
            strategy_type=request.strategy_type,
            source_scope=request.source_scope,
            prompt_ref=request.prompt_ref,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/versions")
def list_strategy_versions(
    strategy_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    return service.list_versions(
        strategy_type=strategy_type,
        status=status,
        limit=limit,
    )


@router.post("/{strategy_id}/publish")
def publish_strategy(
    strategy_id: str,
    request: StrategyPublishRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    try:
        return service.publish_strategy(
            strategy_id=strategy_id,
            backtest_job_id=request.backtest_job_id,
            proposal_id=request.proposal_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{strategy_id}/bind", status_code=201)
def bind_strategy(
    strategy_id: str,
    request: StrategyBindRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    try:
        return service.bind_strategy(
            strategy_id=strategy_id,
            flow_id=request.flow_id,
            prompt_refs=request.prompt_refs,
            prompt_lock_mode=request.prompt_lock_mode,
            effective_scope=request.effective_scope,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/bindings")
def list_strategy_bindings(
    flow_id: str | None = Query(default=None),
    strategy_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    return service.list_bindings(
        flow_id=flow_id,
        strategy_id=strategy_id,
        status=status,
        limit=limit,
    )


@router.post("/{strategy_id}/rollback")
def rollback_strategy(
    strategy_id: str,
    request: StrategyRollbackRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> dict[str, Any]:
    try:
        return service.rollback_strategy(
            strategy_id=strategy_id,
            reason=request.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
