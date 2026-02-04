"""Portfolio Management API Routes."""

from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.portfolio import (
    PortfolioPosition,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(
    db=Depends(get_db),
):
    """Get current portfolio status."""
    service = PortfolioService(db)
    return await service.get_portfolio()


@router.post("/", response_model=PortfolioPosition)
async def add_position(
    position: PortfolioCreate,
    db=Depends(get_db),
):
    """Add a new position to portfolio."""
    service = PortfolioService(db)
    return await service.add_position(position)


@router.put("/{position_id}", response_model=PortfolioPosition)
async def update_position(
    position_id: int,
    update: PortfolioUpdate,
    db=Depends(get_db),
):
    """Update position details."""
    service = PortfolioService(db)
    return await service.update_position(position_id, update)


@router.delete("/{position_id}")
async def delete_position(
    position_id: int,
    db=Depends(get_db),
):
    """Remove a position from portfolio."""
    service = PortfolioService(db)
    await service.delete_position(position_id)
    return {"message": "Position deleted"}


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    db=Depends(get_db),
):
    """Get transaction history."""
    service = PortfolioService(db)
    return await service.get_transactions(limit=limit)


@router.post("/transactions", response_model=TransactionResponse)
async def add_transaction(
    transaction: TransactionCreate,
    db=Depends(get_db),
):
    """Record a new transaction."""
    service = PortfolioService(db)
    return await service.add_transaction(transaction)
