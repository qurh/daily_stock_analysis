from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_backtest_service
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtest")


class BacktestJobCreateRequest(BaseModel):
    scope: str = Field(default="market", pattern="^(market|symbol)$")
    symbol: str | None = None
    eval_window_days: int = Field(default=10, ge=1, le=365)


@router.post("/jobs", status_code=202)
def create_backtest_job(
    request: BacktestJobCreateRequest,
    service: BacktestService = Depends(get_backtest_service),
) -> dict[str, str]:
    try:
        return service.submit_job(
            scope=request.scope,
            symbol=request.symbol,
            eval_window_days=request.eval_window_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}")
def get_backtest_job(
    job_id: str,
    service: BacktestService = Depends(get_backtest_service),
) -> dict[str, Any]:
    job = service.get_job(job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Backtest job not found: {job_id}")
    return job


@router.get("/results")
def list_backtest_results(
    job_id: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: BacktestService = Depends(get_backtest_service),
) -> dict[str, Any]:
    return service.list_results(
        job_id=job_id,
        symbol=symbol,
        outcome=outcome,
        limit=limit,
    )


@router.get("/performance")
def get_backtest_performance(
    job_id: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    service: BacktestService = Depends(get_backtest_service),
) -> dict[str, Any]:
    return service.aggregate(job_id=job_id, symbol=symbol)


@router.get("/performance/{symbol}")
def get_backtest_performance_by_symbol(
    symbol: str,
    service: BacktestService = Depends(get_backtest_service),
) -> dict[str, Any]:
    return service.aggregate(symbol=symbol)
