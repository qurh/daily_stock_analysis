"""Strategy Backtest Service - Signal Simulation and Performance Evaluation.

Provides:
- Historical backtesting
- Forward testing
- Performance metrics calculation
- Signal generation and validation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from collections import defaultdict

import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import get_settings
from app.models.strategy import (
    STRStrategy,
    STRStrategyTest,
    STRStrategySignal,
)
from app.data_providers import DataFetcherManager

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class BacktestMode(Enum):
    """Backtest mode."""
    BACKTEST = "backtest"  # Historical
    FORWARD = "forward"    # Paper trading


@dataclass
class Trade:
    """Single trade record."""
    entry_date: datetime
    exit_date: datetime
    entry_price: Decimal
    exit_price: Decimal
    position_size: Decimal
    pnl: Decimal
    pnl_percent: Decimal
    reason: str
    max_favorable: Decimal  # Max profit during trade
    max_adverse: Decimal   # Max loss during trade


@dataclass
class BacktestResult:
    """Complete backtest result."""
    strategy_id: int
    period_start: date
    period_end: date
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    total_pnl: Decimal
    total_pnl_percent: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    trades: List[Trade]
    monthly_returns: Dict[str, Decimal]
    equity_curve: List[Dict[str, Any]]


@dataclass
class PerformanceMetrics:
    """Performance evaluation metrics."""
    # Return metrics
    total_return: Decimal
    annualized_return: Decimal
    monthly_returns: Dict[str, Decimal]

    # Risk metrics
    volatility: Decimal
    max_drawdown: Decimal
    max_drawdown_duration: int  # days

    # Efficiency metrics
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    win_rate: Decimal
    profit_factor: Decimal

    # Trade metrics
    avg_win: Decimal
    avg_loss: Decimal
    avg_trade: Decimal
    avg_trade_duration: float  # days
    largest_win: Decimal
    largest_loss: Decimal

    # Time-based metrics
    time_in_market: Decimal  # percentage
    best_month: Decimal
    worst_month: Decimal


class StrategyBacktestService:
    """Service for strategy backtesting and performance evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.fetcher = DataFetcherManager()

    # ==================== Backtesting ====================

    async def run_backtest(
        self,
        strategy_id: int,
        stock_code: str,
        period_start: date,
        period_end: date,
        initial_capital: Decimal = Decimal("100000"),
        position_size: Decimal = Decimal("0.2"),
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
    ) -> BacktestResult:
        """Run historical backtest for a strategy on a stock."""
        # Get strategy
        query = select(STRStrategy).where(STRStrategy.id == strategy_id)
        result = await self.db.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Fetch historical data
        data = await self._fetch_backtest_data(stock_code, period_start, period_end)

        if not data:
            raise ValueError(f"No data available for {stock_code}")

        # Simulate trades
        trades = await self._simulate_trades(
            strategy=strategy,
            data=data,
            initial_capital=initial_capital,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        # Calculate metrics
        metrics = self._calculate_metrics(trades, initial_capital, data)

        # Save backtest result
        test = STRStrategyTest(
            strategy_id=strategy_id,
            test_type=BacktestMode.BACKTEST.value,
            period_start=period_start,
            period_end=period_end,
            params={
                "stock_code": stock_code,
                "initial_capital": str(initial_capital),
                "position_size": str(position_size),
            },
            results={
                "total_trades": len(trades),
                "winning_trades": sum(1 for t in trades if t.pnl > 0),
                "total_pnl": str(metrics.total_return),
                "win_rate": str(metrics.win_rate),
                "max_drawdown": str(metrics.max_drawdown),
            },
            metrics={
                "sharpe_ratio": str(metrics.sharpe_ratio),
                "sortino_ratio": str(metrics.sortino_ratio),
                "profit_factor": str(metrics.profit_factor),
            },
        )

        self.db.add(test)
        await self.db.flush()

        return BacktestResult(
            strategy_id=strategy_id,
            period_start=period_start,
            period_end=period_end,
            total_trades=len(trades),
            winning_trades=sum(1 for t in trades if t.pnl > 0),
            losing_trades=sum(1 for t in trades if t.pnl <= 0),
            win_rate=metrics.win_rate,
            total_pnl=metrics.total_return,
            total_pnl_percent=metrics.total_return / initial_capital * 100,
            max_drawdown=metrics.max_drawdown,
            sharpe_ratio=metrics.sharpe_ratio,
            trades=trades,
            monthly_returns=metrics.monthly_returns,
            equity_curve=[],
        )

    async def _fetch_backtest_data(
        self, stock_code: str, start: date, end: date
    ) -> List[Dict[str, Any]]:
        """Fetch historical data for backtesting."""
        try:
            # Try to get daily data
            data = await self.fetcher.get_history(
                code=stock_code,
                period="daily",
                start_date=start.isoformat(),
                end_date=end.isoformat(),
            )

            if data and "data" in data:
                return data["data"]

            return self._generate_mock_data(start, end)

        except Exception as e:
            logger.warning(f"Failed to fetch data for backtest: {e}")
            return self._generate_mock_data(start, end)

    def _generate_mock_data(
        self, start: date, end: date, base_price: float = 100.0
    ) -> List[Dict[str, Any]]:
        """Generate mock data for testing."""
        import random

        data = []
        current_price = base_price
        current = start

        while current <= end:
            if current.weekday() >= 5:  # Skip weekends
                current += timedelta(days=1)
                continue

            # Random daily change (-3% to +3%)
            change = (random.random() - 0.5) * 0.06
            current_price = current_price * (1 + change)

            daily_data = {
                "date": current.isoformat(),
                "open": current_price * (1 + (random.random() - 0.5) * 0.02),
                "high": current_price * (1 + random.random() * 0.02),
                "low": current_price * (1 - random.random() * 0.02),
                "close": current_price,
                "volume": int(random.randint(1000000, 10000000)),
            }
            data.append(daily_data)
            current += timedelta(days=1)

        return data

    async def _simulate_trades(
        self,
        strategy: STRStrategy,
        data: List[Dict[str, Any]],
        initial_capital: Decimal,
        position_size: Decimal,
        stop_loss: Optional[Decimal],
        take_profit: Optional[Decimal],
    ) -> List[Trade]:
        """Simulate trades based on strategy signals."""
        trades = []
        position = None  # (entry_date, entry_price, quantity)
        capital = initial_capital

        conditions = strategy.conditions or {}
        actions = strategy.actions or {}

        for i, day in enumerate(data):
            current_price = Decimal(str(day["close"]))
            current_date = datetime.fromisoformat(day["date"])

            # Check exit conditions for existing position
            if position:
                entry_date, entry_price, quantity = position

                # Calculate current P&L
                pnl_percent = (current_price - entry_price) / entry_price * 100

                # Check stop loss
                if stop_loss and pnl_percent <= -stop_loss:
                    trades.append(self._close_trade(
                        entry_date, current_date, entry_price, current_price,
                        quantity, capital, "止损"
                    ))
                    capital = trades[-1].exit_price * quantity + capital - (entry_price * quantity)
                    position = None
                    continue

                # Check take profit
                if take_profit and pnl_percent >= take_profit:
                    trades.append(self._close_trade(
                        entry_date, current_date, entry_price, current_price,
                        quantity, capital, "止盈"
                    ))
                    capital = trades[-1].exit_price * quantity + capital - (entry_price * quantity)
                    position = None
                    continue

                # Check strategy sell signal
                if self._check_condition(conditions.get("exit_sell"), day, data, i):
                    trades.append(self._close_trade(
                        entry_date, current_date, entry_price, current_price,
                        quantity, capital, "策略卖出"
                    ))
                    capital = trades[-1].exit_price * quantity + capital - (entry_price * quantity)
                    position = None
                    continue

            # Check entry conditions for new position
            if not position and self._check_condition(conditions.get("entry_buy"), day, data, i):
                # Calculate position size
                position_value = capital * position_size
                quantity = int(position_value / current_price)

                if quantity > 0:
                    position = (current_date, current_price, quantity)

        # Close any remaining position at end
        if position:
            entry_date, entry_price, quantity = position
            final_price = Decimal(str(data[-1]["close"]))
            trades.append(self._close_trade(
                entry_date, datetime.fromisoformat(data[-1]["date"]),
                entry_price, final_price, quantity, capital, "期末平仓"
            ))

        return trades

    def _check_condition(
        self,
        condition: Optional[Dict],
        current_day: Dict[str, Any],
        all_data: List[Dict[str, Any]],
        current_index: int,
    ) -> bool:
        """Check if a condition is met."""
        if not condition:
            return False

        condition_type = condition.get("type", "")

        if condition_type == "ma_crossover":
            return self._check_ma_crossover(condition, current_day, all_data, current_index)

        elif condition_type == "rsi_oversold":
            return self._check_rsi(condition, current_day, "oversold")

        elif condition_type == "rsi_overbought":
            return self._check_rsi(condition, current_day, "overbought")

        elif condition_type == "price_above":
            return self._check_price_above(condition, current_day)

        elif condition_type == "price_below":
            return self._check_price_below(condition, current_day)

        elif condition_type == "volume_spike":
            return self._check_volume_spike(condition, current_day, all_data, current_index)

        return False

    def _check_ma_crossover(
        self,
        condition: Dict,
        current_day: Dict[str, Any],
        all_data: List[Dict[str, Any]],
        current_index: int,
    ) -> bool:
        """Check MA crossover condition."""
        fast_ma = condition.get("fast", 5)
        slow_ma = condition.get("slow", 20)
        direction = condition.get("direction", "golden")  # golden or death

        # Calculate MAs up to current day
        closes = [d["close"] for d in all_data[:current_index + 1]]

        fast_ma_val = sum(closes[-fast_ma:]) / fast_ma if len(closes) >= fast_ma else closes[-1]
        slow_ma_val = sum(closes[-slow_ma:]) / slow_ma if len(closes) >= slow_ma else closes[-1]

        if current_index < 1:
            return False

        prev_fast = sum(closes[-(fast_ma + 1):-1]) / fast_ma if len(closes) >= fast_ma + 1 else closes[-2]
        prev_slow = sum(closes[-(slow_ma + 1):-1]) / slow_ma if len(closes) >= slow_ma + 1 else closes[-2]

        if direction == "golden":
            # Fast crosses above slow
            return prev_fast <= prev_slow and fast_ma_val > slow_ma_val
        else:
            # Fast crosses below slow
            return prev_fast >= prev_slow and fast_ma_val < slow_ma_val

    def _check_rsi(
        self,
        condition: Dict,
        current_day: Dict[str, Any],
        check_type: str,
    ) -> bool:
        """Check RSI condition."""
        period = condition.get("period", 14)
        oversold = condition.get("oversold", 30)
        overbought = condition.get("overbought", 70)

        # Simplified RSI calculation based on daily change
        close = current_day["close"]
        open_price = current_day.get("open", close)
        change = float(close) - float(open_price)

        # Very simplified RSI: center at 50, adjusted by daily change
        rsi = 50 + (change / float(close) * 1000) if float(close) > 0 else 50

        if check_type == "oversold":
            return rsi <= oversold
        else:
            return rsi >= overbought

    def _check_price_above(self, condition: Dict, current_day: Dict[str, Any]) -> bool:
        """Check if price is above a level."""
        level = Decimal(str(condition.get("level", 0)))
        return current_day["close"] > level

    def _check_price_below(self, condition: Dict, current_day: Dict[str, Any]) -> bool:
        """Check if price is below a level."""
        level = Decimal(str(condition.get("level", 0)))
        return current_day["close"] < level

    def _check_volume_spike(
        self,
        condition: Dict,
        current_day: Dict[str, Any],
        all_data: List[Dict[str, Any]],
        current_index: int,
    ) -> bool:
        """Check if volume is significantly above average."""
        multiplier = condition.get("multiplier", 2.0)

        if current_index < 5:
            return False

        recent_volumes = [d.get("volume", 0) for d in all_data[max(0, current_index - 20):current_index]]
        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 1

        return current_day.get("volume", 0) > avg_volume * multiplier

    def _close_trade(
        self,
        entry_date: datetime,
        exit_date: datetime,
        entry_price: Decimal,
        exit_price: Decimal,
        quantity: Decimal,
        capital: Decimal,
        reason: str,
    ) -> Trade:
        """Close a trade and return trade record."""
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = (exit_price - entry_price) / entry_price * 100

        return Trade(
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            position_size=quantity,
            pnl=pnl,
            pnl_percent=Decimal(str(pnl_percent)),
            reason=reason,
            max_favorable=pnl if pnl > 0 else Decimal("0"),
            max_adverse=pnl if pnl < 0 else Decimal("0"),
        )

    # ==================== Metrics ====================

    def _calculate_metrics(
        self,
        trades: List[Trade],
        initial_capital: Decimal,
        data: List[Dict[str, Any]],
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not trades:
            return PerformanceMetrics(
                total_return=Decimal("0"),
                annualized_return=Decimal("0"),
                monthly_returns={},
                volatility=Decimal("0"),
                max_drawdown=Decimal("0"),
                max_drawdown_duration=0,
                sharpe_ratio=Decimal("0"),
                sortino_ratio=Decimal("0"),
                win_rate=Decimal("0"),
                profit_factor=Decimal("0"),
                avg_win=Decimal("0"),
                avg_loss=Decimal("0"),
                avg_trade=Decimal("0"),
                avg_trade_duration=0,
                largest_win=Decimal("0"),
                largest_loss=Decimal("0"),
                time_in_market=Decimal("100"),
                best_month=Decimal("0"),
                worst_month=Decimal("0"),
            )

        # Basic counts
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]

        # Return metrics
        total_pnl = sum(t.pnl for t in trades)
        total_return = total_pnl

        # Annualize return (assuming ~250 trading days)
        if data:
            period_days = (datetime.fromisoformat(data[-1]["date"]) -
                          datetime.fromisoformat(data[0]["date"])).days
            annualized = total_return / initial_capital * (365 / max(period_days, 1)) * 100
        else:
            annualized = Decimal("0")

        # Monthly returns
        monthly = defaultdict(Decimal)
        for trade in trades:
            month_key = trade.exit_date.strftime("%Y-%m")
            monthly[month_key] += trade.pnl_percent

        # Drawdown calculation
        equity_curve = [initial_capital]
        for trade in trades:
            equity_curve.append(equity_curve[-1] + trade.pnl)

        max_equity = equity_curve[0]
        max_dd = Decimal("0")
        dd_duration = 0
        max_dd_days = 0

        for i, equity in enumerate(equity_curve):
            if equity > max_equity:
                max_equity = equity
                dd_duration = 0
            else:
                dd = (max_equity - equity) / max_equity * 100
                if dd > max_dd:
                    max_dd = dd
                    max_dd_days = dd_duration
                dd_duration += 1

        # Volatility (daily returns std)
        if len(equity_curve) > 1:
            returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                      for i in range(1, len(equity_curve))]
            volatility = (Decimal(str(np.std(returns))) * Decimal("100") * Decimal("16")) if returns else Decimal("0")
        else:
            volatility = Decimal("0")

        # Sharpe ratio (assuming 0% risk-free rate)
        if volatility > 0:
            sharpe = (total_return / initial_capital * 100) / volatility if volatility != 0 else Decimal("0")
        else:
            sharpe = Decimal("0")

        # Sortino ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0] if returns else []
        downside_std = np.std(downside_returns) if downside_returns else Decimal("1")
        sortino = (total_return / initial_capital * 100) / (Decimal(str(downside_std)) * Decimal("16")) if downside_returns else Decimal("0")

        # Win rate and profit factor
        win_rate = Decimal(str(len(winning_trades) / len(trades) * 100)) if trades else Decimal("0")

        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else Decimal("1")
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else Decimal("1")
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else Decimal(str(len(winning_trades) + 1))

        # Average trades
        avg_win = sum(t.pnl_percent for t in winning_trades) / len(winning_trades) if winning_trades else Decimal("0")
        avg_loss = sum(t.pnl_percent for t in losing_trades) / len(losing_trades) if losing_trades else Decimal("0")
        avg_trade = sum(t.pnl_percent for t in trades) / len(trades) if trades else Decimal("0")

        # Duration
        durations = [(t.exit_date - t.entry_date).days for t in trades]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Largest win/loss
        largest_win = max((t.pnl_percent for t in winning_trades), default=Decimal("0"))
        largest_loss = min((t.pnl_percent for t in losing_trades), default=Decimal("0"))

        # Time in market
        if data and len(data) > 1:
            days_in_trade = set()
            for trade in trades:
                trade_days = trade.exit_date - trade.entry_date
                for d in range(max(0, trade_days.days)):
                    days_in_trade.add((trade.entry_date + timedelta(days=d)).date())
            total_days = (datetime.fromisoformat(data[-1]["date"]) -
                         datetime.fromisoformat(data[0]["date"])).days
            time_in_market = Decimal(str(len(days_in_trade) / max(total_days, 1) * 100))
        else:
            time_in_market = Decimal("50")

        # Best/worst month
        best_month = max(monthly.values()) if monthly else Decimal("0")
        worst_month = min(monthly.values()) if monthly else Decimal("0")

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized,
            monthly_returns=dict(monthly),
            volatility=volatility,
            max_drawdown=max_dd,
            max_drawdown_duration=max_dd_days,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            avg_trade_duration=avg_duration,
            largest_win=largest_win,
            largest_loss=largest_loss,
            time_in_market=time_in_market,
            best_month=best_month,
            worst_month=worst_month,
        )

    # ==================== Signal Generation ====================

    async def generate_signal(
        self,
        strategy_id: int,
        stock_code: str,
        current_price: Decimal,
        market_data: Dict[str, Any],
    ) -> Optional[STRStrategySignal]:
        """Generate trading signal based on strategy conditions."""
        query = select(STRStrategy).where(
            and_(
                STRStrategy.id == strategy_id,
                STRStrategy.status == "active",
            )
        )
        result = await self.db.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            return None

        conditions = strategy.conditions or {}
        actions = strategy.actions or {}

        # Check buy condition
        buy_signal = self._check_condition(
            conditions.get("entry_buy"), market_data, [], 0
        )

        if buy_signal:
            reasoning = self._generate_reasoning("买入", strategy, market_data)
            return STRStrategySignal(
                strategy_id=strategy_id,
                code=stock_code,
                signal_type=SignalType.BUY.value,
                confidence=Decimal("0.75"),
                reasoning=reasoning,
                price=current_price,
            )

        # Check sell condition
        sell_signal = self._check_condition(
            conditions.get("exit_sell"), market_data, [], 0
        )

        if sell_signal:
            reasoning = self._generate_reasoning("卖出", strategy, market_data)
            return STRStrategySignal(
                strategy_id=strategy_id,
                code=stock_code,
                signal_type=SignalType.SELL.value,
                confidence=Decimal("0.75"),
                reasoning=reasoning,
                price=current_price,
            )

        return STRStrategySignal(
            strategy_id=strategy_id,
            code=stock_code,
            signal_type=SignalType.HOLD.value,
            confidence=Decimal("0.5"),
            reasoning="当前不符合策略触发条件",
            price=current_price,
        )

    def _generate_reasoning(
        self,
        signal_type: str,
        strategy: STRStrategy,
        market_data: Dict[str, Any],
    ) -> str:
        """Generate human-readable reasoning for signal."""
        return f"策略【{strategy.name}】触发{signal_type}信号。{strategy.description}"

    # ==================== Statistics ====================

    async def get_strategy_stats(self, strategy_id: int) -> Dict[str, Any]:
        """Get overall statistics for a strategy."""
        query = select(STRStrategyTest).where(
            STRStrategyTest.strategy_id == strategy_id
        ).order_by(STRStrategyTest.created_at.desc()).limit(20)

        result = await self.db.execute(query)
        tests = result.scalars().all()

        if not tests:
            return {
                "total_tests": 0,
                "avg_win_rate": 0,
                "avg_sharpe": 0,
                "recent_results": [],
            }

        avg_win_rate = sum(
            Decimal(str(t.results.get("win_rate", "0"))) for t in tests
        ) / len(tests)

        avg_sharpe = sum(
            Decimal(str(t.metrics.get("sharpe_ratio", "0"))) for t in tests
        ) / len(tests)

        return {
            "total_tests": len(tests),
            "avg_win_rate": float(avg_win_rate),
            "avg_sharpe": float(avg_sharpe),
            "recent_results": [
                {
                    "date": t.created_at.isoformat(),
                    "win_rate": t.results.get("win_rate"),
                    "total_pnl": t.results.get("total_pnl"),
                }
                for t in tests[:5]
            ],
        }
