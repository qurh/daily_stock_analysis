"""Failure Case Service - Error Pattern Recording and Analysis.

Provides:
- Failure case recording
- Pattern detection
- Improvement suggestions
- Similar case retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.config import get_settings
from app.models.failure import FCFailureCase, FCFailureReference

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error type classification."""
    DATA_DELAY = "data_delay"           # 数据延迟
    INDICATOR_FAILURE = "indicator_failure"  # 指标失效
    LOGIC_ERROR = "logic_error"         # 逻辑错误
    MARKET_STRUCTURE_CHANGE = "market_structure_change"  # 市场结构变化
    BLACK_SWAN = "black_swan"           # 黑天鹅事件
    INFORMATION_ASYMMETRY = "information_asymmetry"  # 信息不对称
    OVERFITTING = "overfitting"        # 过拟合
    FALSE_SIGNAL = "false_signal"       # 假信号


class Severity(Enum):
    """Failure severity levels."""
    LOW = "low"           # 低影响
    MEDIUM = "medium"     # 中等影响
    HIGH = "high"         # 高影响
    CRITICAL = "critical" # 严重影响


@dataclass
class FailureCaseRecord:
    """Complete failure case record."""
    id: Optional[int]
    original_conclusion_type: str
    original_conclusion_id: Optional[int]
    original_conclusion: str
    actual_outcome: str
    error_type: ErrorType
    error_analysis: str
    lessons_learned: str
    improvement_suggestions: str
    severity: Severity
    related_codes: List[str]
    related_indicators: List[str]
    occurred_at: datetime
    identified_at: datetime


@dataclass
class FailurePattern:
    """Detected failure pattern."""
    pattern_name: str
    frequency: int
    error_types: List[ErrorType]
    affected_indicators: List[str]
    average_loss: float
    mitigation: str


class FailureCaseService:
    """Service for managing failure cases and learning from mistakes."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    # ==================== Case Recording ====================

    async def record_failure(
        self,
        conclusion_type: str,
        conclusion_id: Optional[int],
        original_conclusion: str,
        actual_outcome: str,
        error_type: ErrorType,
        error_analysis: str,
        related_codes: Optional[List[str]] = None,
        related_indicators: Optional[List[str]] = None,
        severity: Severity = Severity.MEDIUM,
    ) -> FailureCaseRecord:
        """Record a new failure case."""
        occurred_at = datetime.utcnow()

        # Generate lessons learned and suggestions
        lessons = await self._generate_lessons(error_type, error_analysis)
        suggestions = await self._generate_improvements(error_type, related_indicators)

        failure_case = FCFailureCase(
            original_conclusion_type=conclusion_type,
            original_conclusion_id=conclusion_id,
            original_conclusion=original_conclusion,
            actual_outcome=actual_outcome,
            error_type=error_type.value,
            error_analysis=error_analysis,
            lessons_learned=lessons,
            improvement_suggestions=suggestions,
            severity=severity.value,
            related_codes=related_codes or [],
            related_indicators=related_indicators or [],
            occurred_at=occurred_at,
            identified_at=occurred_at,
        )

        self.db.add(failure_case)
        await self.db.flush()
        await self.db.refresh(failure_case)

        logger.info(f"Recorded failure case {failure_case.id}: {error_type.value}")

        return FailureCaseRecord(
            id=failure_case.id,
            original_conclusion_type=conclusion_type,
            original_conclusion_id=conclusion_id,
            original_conclusion=original_conclusion,
            actual_outcome=actual_outcome,
            error_type=error_type,
            error_analysis=error_analysis,
            lessons_learned=lessons,
            improvement_suggestions=suggestions,
            severity=severity,
            related_codes=related_codes or [],
            related_indicators=related_indicators or [],
            occurred_at=occurred_at,
            identified_at=occurred_at,
        )

    async def update_failure(
        self,
        case_id: int,
        lessons: Optional[str] = None,
        suggestions: Optional[str] = None,
        severity: Optional[Severity] = None,
    ) -> Optional[FailureCaseRecord]:
        """Update an existing failure case."""
        query = select(FCFailureCase).where(FCFailureCase.id == case_id)
        result = await self.db.execute(query)
        case = result.scalar_one_or_none()

        if not case:
            return None

        if lessons:
            case.lessons_learned = lessons
        if suggestions:
            case.improvement_suggestions = suggestions
        if severity:
            case.severity = severity.value

        await self.db.flush()
        await self.db.refresh(case)

        return FailureCaseRecord(
            id=case.id,
            original_conclusion_type=case.original_conclusion_type,
            original_conclusion_id=case.original_conclusion_id,
            original_conclusion=case.original_conclusion,
            actual_outcome=case.actual_outcome,
            error_type=ErrorType(case.error_type),
            error_analysis=case.error_analysis,
            lessons_learned=case.lessons_learned,
            improvement_suggestions=case.improvement_suggestions,
            severity=Severity(case.severity),
            related_codes=case.related_codes or [],
            related_indicators=case.related_indicators or [],
            occurred_at=case.occurred_at,
            identified_at=case.identified_at,
        )

    # ==================== Case Retrieval ====================

    async def get_similar_cases(
        self,
        error_type: Optional[ErrorType] = None,
        related_indicator: Optional[str] = None,
        limit: int = 5,
    ) -> List[FailureCaseRecord]:
        """Get similar failure cases for reference."""
        query = select(FCFailureCase)

        conditions = []
        if error_type:
            conditions.append(FCFailureCase.error_type == error_type.value)
        if related_indicator:
            conditions.append(
                FCFailureCase.related_indicators.contains([related_indicator])
            )

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(FCFailureCase.occurred_at.desc()).limit(limit)
        result = await self.db.execute(query)
        cases = result.scalars().all()

        return [
            FailureCaseRecord(
                id=c.id,
                original_conclusion_type=c.original_conclusion_type,
                original_conclusion_id=c.original_conclusion_id,
                original_conclusion=c.original_conclusion,
                actual_outcome=c.actual_outcome,
                error_type=ErrorType(c.error_type),
                error_analysis=c.error_analysis,
                lessons_learned=c.lessons_learned,
                improvement_suggestions=c.improvement_suggestions,
                severity=Severity(c.severity),
                related_codes=c.related_codes or [],
                related_indicators=c.related_indicators or [],
                occurred_at=c.occurred_at,
                identified_at=c.identified_at,
            )
            for c in cases
        ]

    async def get_cases_by_period(
        self,
        days: int = 30,
        limit: int = 50,
    ) -> List[FailureCaseRecord]:
        """Get failure cases from recent period."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(FCFailureCase).where(
            FCFailureCase.occurred_at >= cutoff
        ).order_by(FCFailureCase.occurred_at.desc()).limit(limit)

        result = await self.db.execute(query)
        cases = result.scalars().all()

        return [
            FailureCaseRecord(
                id=c.id,
                original_conclusion_type=c.original_conclusion_type,
                original_conclusion_id=c.original_conclusion_id,
                original_conclusion=c.original_conclusion,
                actual_outcome=c.actual_outcome,
                error_type=ErrorType(c.error_type),
                error_analysis=c.error_analysis,
                lessons_learned=c.lessons_learned,
                improvement_suggestions=c.improvement_suggestions,
                severity=Severity(c.severity),
                related_codes=c.related_codes or [],
                related_indicators=c.related_indicators or [],
                occurred_at=c.occurred_at,
                identified_at=c.identified_at,
            )
            for c in cases
        ]

    # ==================== Pattern Analysis ====================

    async def analyze_patterns(self) -> List[FailurePattern]:
        """Analyze failure patterns from recorded cases."""
        cases = await self.get_cases_by_period(days=90)

        if not cases:
            return []

        # Group by error type
        type_groups: Dict[ErrorType, List[FailureCaseRecord]] = {}
        for case in cases:
            if case.error_type not in type_groups:
                type_groups[case.error_type] = []
            type_groups[case.error_type].append(case)

        patterns = []

        for error_type, type_cases in type_groups.items():
            # Get affected indicators
            all_indicators = set()
            for case in type_cases:
                all_indicators.update(case.related_indicators)

            pattern = FailurePattern(
                pattern_name=self._get_pattern_name(error_type),
                frequency=len(type_cases),
                error_types=[error_type],
                affected_indicators=list(all_indicators)[:5],
                average_loss=self._estimate_average_loss(type_cases),
                mitigation=await self._get_mitigation(error_type),
            )
            patterns.append(pattern)

        # Sort by frequency
        patterns.sort(key=lambda x: x.frequency, reverse=True)

        return patterns

    async def detect_risk_indicators(
        self, stock_code: str
    ) -> Dict[str, Any]:
        """Detect potential risk indicators for a stock based on history."""
        # Get recent failures related to this stock
        query = select(FCFailureCase).where(
            and_(
                FCFailureCase.related_codes.contains([stock_code]),
                FCFailureCase.occurred_at >= datetime.utcnow() - timedelta(days=180),
            )
        ).order_by(FCFailureCase.occurred_at.desc())

        result = await self.db.execute(query)
        cases = result.scalars().all()

        if not cases:
            return {
                "risk_level": "low",
                "warning": "暂无相关失败记录",
                "recommendations": [],
            }

        # Calculate risk level
        error_types = set(c.error_type.value for c in cases)
        recent_high_severity = sum(
            1 for c in cases if c.severity == Severity.HIGH or c.severity == Severity.CRITICAL
        )

        risk_score = min(1.0, len(cases) * 0.2 + recent_high_severity * 0.3)

        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate warnings
        warnings = []
        for error_type in error_types:
            warning = self._get_warning(error_type)
            if warning:
                warnings.append(warning)

        # Generate recommendations
        recommendations = []
        for case in cases[:3]:
            if case.improvement_suggestions:
                recommendations.append(case.improvement_suggestions)

        return {
            "risk_level": risk_level,
            "failure_count": len(cases),
            "error_types": list(error_types),
            "warnings": warnings[:3],
            "recommendations": list(set(recommendations))[:3],
            "last_failure": cases[0].occurred_at.isoformat() if cases else None,
        }

    # ==================== Statistics ====================

    async def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get failure statistics."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(FCFailureCase).where(
            FCFailureCase.occurred_at >= cutoff
        )
        result = await self.db.execute(query)
        cases = result.scalars().all()

        # Count by error type
        type_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}

        for case in cases:
            type_counts[case.error_type] = type_counts.get(case.error_type, 0) + 1
            severity_counts[case.severity] = severity_counts.get(case.severity, 0) + 1

        return {
            "total_failures": len(cases),
            "by_error_type": type_counts,
            "by_severity": severity_counts,
            "critical_count": sum(
                1 for c in cases if c.severity == Severity.CRITICAL.value
            ),
            "improvement_rate": await self._calculate_improvement_rate(days),
        }

    async def _calculate_improvement_rate(self, days: int) -> float:
        """Calculate improvement rate over period."""
        # Compare recent failures to historical average
        recent = await self.get_cases_by_period(days=days)
        historical = await self.get_cases_by_period(days=days * 3)

        if not historical:
            return 0.5  # No historical data

        recent_rate = len(recent) / days
        historical_rate = len(historical) / (days * 3)

        if historical_rate == 0:
            return 0.5

        improvement = (historical_rate - recent_rate) / historical_rate
        return max(0.0, min(1.0, improvement))

    # ==================== Helper Methods ====================

    async def _generate_lessons(
        self, error_type: ErrorType, error_analysis: str
    ) -> str:
        """Generate lessons learned from failure."""
        lessons_map = {
            ErrorType.DATA_DELAY: "延迟的数据可能导致错误的信号，建议增加数据验证环节",
            ErrorType.INDICATOR_FAILURE: "单一指标可能失效，应使用多指标交叉验证",
            ErrorType.LOGIC_ERROR: "逻辑错误需要通过单元测试和代码审查来预防",
            ErrorType.MARKET_STRUCTURE_CHANGE: "市场结构变化时，传统策略可能失效",
            ErrorType.BLACK_SWAN: "黑天鹅事件难以预测，需设置止损保护",
            ErrorType.INFORMATION_ASYMMETRY: "注意信息来源的可靠性，交叉验证重要信息",
            ErrorType.OVERFITTING: "避免过度拟合历史数据，保持策略的普适性",
            ErrorType.FALSE_SIGNAL: "假信号是交易中的常见问题，需要更好的过滤机制",
        }

        return lessons_map.get(error_type, error_analysis[:200])

    async def _generate_improvements(
        self,
        error_type: ErrorType,
        related_indicators: Optional[List[str]],
    ) -> str:
        """Generate improvement suggestions."""
        suggestions = {
            ErrorType.DATA_DELAY: "考虑增加数据源冗余，实现多源交叉验证",
            ErrorType.INDICATOR_FAILURE: "引入自适应指标选择机制，根据市场环境动态调整",
            ErrorType.LOGIC_ERROR: "加强代码审查，增加边界条件测试",
            ErrorType.MARKET_STRUCTURE_CHANGE: "增加市场状态识别模块，动态调整策略参数",
            ErrorType.BLACK_SWAN: "设置严格的止损规则，降低单次损失上限",
            ErrorType.INFORMATION_ASYMMETRY: "建立信息可信度评估体系，优先使用权威来源",
            ErrorType.OVERFITTING: "简化模型复杂度，增加正则化约束",
            ErrorType.FALSE_SIGNAL: "增加信号确认机制，提高入场门槛",
        }

        base = suggestions.get(error_type, "需要进一步分析根本原因")

        if related_indicators:
            base += f" 特别关注指标: {', '.join(related_indicators[:3])}"

        return base

    def _get_pattern_name(self, error_type: ErrorType) -> str:
        """Get human-readable pattern name."""
        names = {
            ErrorType.DATA_DELAY: "数据延迟问题",
            ErrorType.INDICATOR_FAILURE: "指标失效模式",
            ErrorType.LOGIC_ERROR: "逻辑错误模式",
            ErrorType.MARKET_STRUCTURE_CHANGE: "市场结构变化",
            ErrorType.BLACK_SWAN: "黑天鹅事件",
            ErrorType.INFORMATION_ASYMMETRY: "信息不对称",
            ErrorType.OVERFITTING: "过拟合问题",
            ErrorType.FALSE_SIGNAL: "假信号模式",
        }
        return names.get(error_type, "未知模式")

    def _estimate_average_loss(self, cases: List[FailureCaseRecord]) -> float:
        """Estimate average loss from failure cases."""
        # This would typically calculate actual losses
        # For now, use severity-based estimation
        severity_weights = {
            Severity.LOW: 1,
            Severity.MEDIUM: 3,
            Severity.HIGH: 5,
            Severity.CRITICAL: 10,
        }

        total = sum(
            severity_weights.get(c.severity, 3)
            for c in cases
        )

        return total / len(cases) if cases else 0

    def _get_warning(self, error_type: ErrorType) -> Optional[str]:
        """Get warning message for error type."""
        warnings = {
            ErrorType.DATA_DELAY: "近期存在数据延迟问题，请核实数据时效性",
            ErrorType.INDICATOR_FAILURE: "部分技术指标可能已失效，建议交叉验证",
            ErrorType.MARKET_STRUCTURE_CHANGE: "市场结构可能发生变化，注意策略适应性",
            ErrorType.BLACK_SWAN: "关注可能的异常事件风险",
        }

        return warnings.get(error_type)

    async def _get_mitigation(self, error_type: ErrorType) -> str:
        """Get mitigation strategy for error type."""
        mitigations = {
            ErrorType.DATA_DELAY: "实施多数据源交叉验证，设置数据新鲜度检查",
            ErrorType.INDICATOR_FAILURE: "使用指标组合而非单一指标，增加自适应机制",
            ErrorType.LOGIC_ERROR: "加强测试覆盖，实施代码审查流程",
            ErrorType.MARKET_STRUCTURE_CHANGE: "建立市场状态检测，动态调整策略",
            ErrorType.BLACK_SWAN: "严格风控，设置最大回撤限制",
        }

        return mitigations.get(error_type, "需要个案分析")
