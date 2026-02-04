"""Strategy Service."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    BacktestRequest,
    BacktestResponse,
    SignalResponse,
)
from app.models.strategy import (
    STRStrategy,
    STRStrategyTest,
    STRStrategySignal,
)

logger = logging.getLogger(__name__)


class StrategyService:
    """Strategy management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_strategies(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> StrategyListResponse:
        """List all strategies."""
        query = select(STRStrategy)

        if category:
            query = query.where(STRStrategy.category == category)
        if status:
            query = query.where(STRStrategy.status == status)

        # Get total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        query = query.offset(offset).limit(limit).order_by(desc(STRStrategy.created_at))
        result = await self.db.execute(query)
        strategies = result.scalars().all()

        return StrategyListResponse(
            strategies=[self._to_strategy_response(s) for s in strategies],
            total=total or 0,
            limit=limit,
            offset=offset,
        )

    async def get_strategy(self, strategy_id: int) -> StrategyResponse:
        """Get strategy by ID."""
        query = select(STRStrategy).where(STRStrategy.id == strategy_id)
        result = await self.db.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        return self._to_strategy_response(strategy)

    async def create_strategy(self, strategy: StrategyCreate) -> StrategyResponse:
        """Create a new strategy."""
        model = STRStrategy(
            name=strategy.name,
            category=strategy.category,
            description=strategy.description,
            conditions=strategy.conditions,
            actions=strategy.actions,
            risk_management=strategy.risk_management,
            source_doc_id=strategy.source_doc_id,
        )

        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)

        return self._to_strategy_response(model)

    async def update_strategy(
        self, strategy_id: int, update: StrategyUpdate
    ) -> StrategyResponse:
        """Update strategy."""
        query = select(STRStrategy).where(STRStrategy.id == strategy_id)
        result = await self.db.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        if update.name is not None:
            strategy.name = update.name
        if update.category is not None:
            strategy.category = update.category
        if update.description is not None:
            strategy.description = update.description
        if update.conditions is not None:
            strategy.conditions = update.conditions
        if update.actions is not None:
            strategy.actions = update.actions
        if update.risk_management is not None:
            strategy.risk_management = update.risk_management
        if update.status is not None:
            strategy.status = update.status

        await self.db.flush()
        await self.db.refresh(strategy)

        return self._to_strategy_response(strategy)

    async def delete_strategy(self, strategy_id: int) -> None:
        """Delete strategy."""
        query = select(STRStrategy).where(STRStrategy.id == strategy_id)
        result = await self.db.execute(query)
        strategy = result.scalar_one_or_none()

        if strategy:
            await self.db.delete(strategy)
            await self.db.flush()

    async def backtest(
        self, strategy_id: int, request: BacktestRequest
    ) -> BacktestResponse:
        """Run backtest for a strategy."""
        # Get strategy
        strategy = await self.get_strategy(strategy_id)

        # TODO: Implement actual backtesting logic
        # This is a placeholder

        return BacktestResponse(
            strategy_id=strategy_id,
            code=request.code,
            period_start=request.start_date,
            period_end=request.end_date,
            metrics={
                "total_return": Decimal("0"),
                "annualized_return": Decimal("0"),
                "max_drawdown": Decimal("0"),
                "win_rate": Decimal("0"),
                "profit_factor": Decimal("0"),
                "trade_count": 0,
            },
            trades=[],
            chart_data=[],
        )

    async def get_signals(
        self, code: Optional[str] = None, limit: int = 50
    ) -> List[SignalResponse]:
        """Get active trading signals."""
        query = select(STRStrategySignal)

        if code:
            query = query.where(STRStrategySignal.code == code)

        query = query.order_by(desc(STRStrategySignal.created_at)).limit(limit)
        result = await self.db.execute(query)
        signals = result.scalars().all()

        # Get strategy names
        strategy_ids = [s.strategy_id for s in signals]
        strategy_map = {}
        if strategy_ids:
            strat_query = select(STRStrategy).where(STRStrategy.id.in_(strategy_ids))
            strat_result = await self.db.execute(strat_query)
            for s in strat_result.scalars():
                strategy_map[s.id] = s.name

        return [
            SignalResponse(
                id=s.id,
                strategy_id=s.strategy_id,
                strategy_name=strategy_map.get(s.strategy_id, "Unknown"),
                code=s.code,
                signal_type=s.signal_type,
                confidence=s.confidence,
                reasoning=s.reasoning,
                price=s.price,
                created_at=s.created_at,
            )
            for s in signals
        ]

    def _to_strategy_response(self, strategy: STRStrategy) -> StrategyResponse:
        """Convert model to response."""
        return StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            category=strategy.category,
            description=strategy.description,
            conditions=strategy.conditions or {},
            actions=strategy.actions or {},
            risk_management=strategy.risk_management or {},
            source_doc_id=strategy.source_doc_id,
            verification_count=strategy.verification_count,
            success_rate=strategy.success_rate,
            status=strategy.status,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
        )
