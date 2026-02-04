"""Strategy Management API Routes."""

from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    BacktestRequest,
    BacktestResponse,
    SignalResponse,
)
from app.services.strategy_service import StrategyService

router = APIRouter()


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db),
):
    """List all strategies."""
    service = StrategyService(db)
    return await service.list_strategies(
        category=category,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    db=Depends(get_db),
):
    """Create a new strategy."""
    service = StrategyService(db)
    return await service.create_strategy(strategy)


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db=Depends(get_db),
):
    """Get strategy details."""
    service = StrategyService(db)
    return await service.get_strategy(strategy_id)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    update: StrategyUpdate,
    db=Depends(get_db),
):
    """Update strategy."""
    service = StrategyService(db)
    return await service.update_strategy(strategy_id, update)


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db=Depends(get_db),
):
    """Delete a strategy."""
    service = StrategyService(db)
    await service.delete_strategy(strategy_id)
    return {"message": "Strategy deleted"}


@router.post("/{strategy_id}/test", response_model=BacktestResponse)
async def backtest_strategy(
    strategy_id: int,
    request: BacktestRequest,
    db=Depends(get_db),
):
    """Run backtest for a strategy."""
    service = StrategyService(db)
    return await service.backtest(strategy_id, request)


@router.get("/signals", response_model=List[SignalResponse])
async def get_active_signals(
    code: Optional[str] = None,
    limit: int = 50,
    db=Depends(get_db),
):
    """Get active trading signals."""
    service = StrategyService(db)
    return await service.get_signals(code=code, limit=limit)
