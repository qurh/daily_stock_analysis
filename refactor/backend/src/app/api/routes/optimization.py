from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_optimization_service
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/optimization")


class OptimizationTriggerRequest(BaseModel):
    trigger_source: str = Field(pattern="^(event|manual|chatbot)$")
    reason: str | None = None
    backtest_job_id: str | None = None


class OptimizationProposalTarget(str, Enum):
    prompt_chat_reply = "prompt.chat.reply"
    workflow_stock_analysis = "workflow.stock.analysis"
    strategy_analysis_lifecycle = "strategy.analysis.lifecycle"


class OptimizationProposalCreateRequest(BaseModel):
    source: str = Field(pattern="^(event|manual|chatbot)$")
    target: OptimizationProposalTarget
    summary: str | None = None
    diff: dict[str, Any] = Field(default_factory=dict)


class ProposalApproveRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    note: str | None = None


class ProposalRejectRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    reason: str | None = None


@router.post("/jobs/trigger", status_code=202)
def trigger_optimization_job(
    request: OptimizationTriggerRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> dict[str, Any]:
    try:
        return service.trigger_job(
            trigger_source=request.trigger_source,
            reason=request.reason,
            backtest_job_id=request.backtest_job_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/proposals", status_code=201)
def create_optimization_proposal(
    request: OptimizationProposalCreateRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> dict[str, Any]:
    try:
        return service.create_proposal(
            source=request.source,
            target=request.target.value,
            summary=request.summary,
            diff=request.diff,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/approve")
def approve_optimization_proposal(
    proposal_id: str,
    request: ProposalApproveRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> dict[str, Any]:
    try:
        return service.approve_proposal(
            proposal_id=proposal_id,
            reviewer=request.reviewer,
            note=request.note,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/reject")
def reject_optimization_proposal(
    proposal_id: str,
    request: ProposalRejectRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> dict[str, Any]:
    try:
        return service.reject_proposal(
            proposal_id=proposal_id,
            reviewer=request.reviewer,
            reason=request.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
