"""Portfolio Service."""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.schemas.portfolio import (
    PortfolioPosition,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioSummary,
    PortfolioResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.models.business import Portfolio as PortfolioModel

logger = logging.getLogger(__name__)


class PortfolioService:
    """Portfolio management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_portfolio(self) -> PortfolioResponse:
        """Get current portfolio status with latest prices."""
        from app.services.market_service import MarketService

        market_service = MarketService(self.db)

        # Get all positions
        query = select(PortfolioModel).where(PortfolioModel.is_deleted == False)
        result = await self.db.execute(query)
        positions = result.scalars().all()

        # Get unique codes and fetch quotes
        codes = [p.code for p in positions]
        quotes = {}
        if codes:
            quote_list = await market_service.get_quotes(codes)
            quotes = {q.code: q for q in quote_list}

        # Calculate position details
        position_list = []
        total_value = Decimal("0")
        total_profit = Decimal("0")

        for pos in positions:
            quote = quotes.get(pos.code)
            current_price = quote.price if quote else pos.current_price
            pct_chg = quote.pct_chg if quote else Decimal("0")

            profit_loss = (current_price - pos.avg_cost) * pos.quantity
            profit_pct = (current_price / pos.avg_cost - 1) * 100 if pos.avg_cost > 0 else Decimal("0")

            position_list.append(PortfolioPosition(
                id=pos.id,
                code=pos.code,
                name=pos.name,
                quantity=pos.quantity,
                avg_cost=pos.avg_cost,
                current_price=current_price,
                profit_loss=profit_loss,
                profit_pct=profit_pct,
                position_ratio=Decimal("0"),  # Calculate after total
                notes=pos.notes,
                created_at=pos.created_at,
                updated_at=pos.updated_at,
            ))

            total_value += current_price * pos.quantity
            total_profit += profit_loss

        # Calculate position ratios
        for pos in position_list:
            if total_value > 0:
                pos.position_ratio = (pos.current_price * pos.quantity / total_value) * 100

        # Get cash balance (from config or separate table)
        cash_balance = Decimal("100000")  # Default, should come from settings

        summary = PortfolioSummary(
            total_value=total_value,
            total_profit=total_profit,
            total_profit_pct=(total_profit / (total_value - total_profit) * 100) if (total_value - total_profit) > 0 else Decimal("0"),
            cash_balance=cash_balance,
            position_count=len(positions),
        )

        return PortfolioResponse(
            summary=summary,
            positions=position_list,
            updated_at=datetime.now(),
        )

    async def add_position(self, position: PortfolioCreate) -> PortfolioPosition:
        """Add a new position."""
        from app.services.market_service import MarketService

        market_service = MarketService(self.db)

        # Get current price
        quotes = await market_service.get_quotes([position.code])
        current_price = quotes[0].price if quotes else position.avg_cost

        # Calculate profit/loss
        profit_loss = (current_price - position.avg_cost) * position.quantity
        profit_pct = (current_price / position.avg_cost - 1) * 100 if position.avg_cost > 0 else Decimal("0")

        pos = PortfolioModel(
            code=position.code,
            name=position.name,
            quantity=position.quantity,
            avg_cost=position.avg_cost,
            current_price=current_price,
            profit_loss=profit_loss,
            profit_pct=profit_pct,
            position_ratio=Decimal("0"),
            notes=position.notes,
        )

        self.db.add(pos)
        await self.db.flush()
        await self.db.refresh(pos)

        return PortfolioPosition(
            id=pos.id,
            code=pos.code,
            name=pos.name,
            quantity=pos.quantity,
            avg_cost=pos.avg_cost,
            current_price=current_price,
            profit_loss=profit_loss,
            profit_pct=profit_pct,
            position_ratio=Decimal("0"),
            notes=pos.notes,
            created_at=pos.created_at,
            updated_at=pos.updated_at,
        )

    async def update_position(
        self, position_id: int, update: PortfolioUpdate
    ) -> PortfolioPosition:
        """Update position details."""
        query = select(PortfolioModel).where(PortfolioModel.id == position_id)
        result = await self.db.execute(query)
        pos = result.scalar_one_or_none()

        if not pos:
            raise ValueError(f"Position {position_id} not found")

        if update.quantity is not None:
            pos.quantity = update.quantity
        if update.avg_cost is not None:
            pos.avg_cost = update.avg_cost
        if update.notes is not None:
            pos.notes = update.notes

        await self.db.flush()
        await self.db.refresh(pos)

        return PortfolioPosition(
            id=pos.id,
            code=pos.code,
            name=pos.name,
            quantity=pos.quantity,
            avg_cost=pos.avg_cost,
            current_price=pos.current_price,
            profit_loss=pos.profit_loss,
            profit_pct=pos.profit_pct,
            position_ratio=pos.position_ratio,
            notes=pos.notes,
            created_at=pos.created_at,
            updated_at=pos.updated_at,
        )

    async def delete_position(self, position_id: int) -> None:
        """Delete position (soft delete)."""
        query = select(PortfolioModel).where(PortfolioModel.id == position_id)
        result = await self.db.execute(query)
        pos = result.scalar_one_or_none()

        if pos:
            pos.is_deleted = True
            await self.db.flush()

    async def get_transactions(self, limit: int = 50) -> List[TransactionResponse]:
        """Get transaction history."""
        # TODO: Implement with transaction table
        return []

    async def add_transaction(
        self, transaction: TransactionCreate
    ) -> TransactionResponse:
        """Record a new transaction."""
        # TODO: Implement with transaction table
        return TransactionResponse(
            id=0,
            code=transaction.code,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            total=transaction.quantity * transaction.price,
            fees=transaction.fees,
            notes=transaction.notes,
            transaction_date=transaction.transaction_date or datetime.now(),
            created_at=datetime.now(),
        )
