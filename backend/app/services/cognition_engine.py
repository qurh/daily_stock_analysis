"""Cognition Engine - Confidence Assessment and Conflict Detection.

Provides:
- Confidence scoring for AI conclusions
- Conflict detection between conclusions
- Market stage recognition
- Risk attitude adjustment
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import get_settings
from app.models.cognition import (
    COGInvestmentStyle,
    COGCognitionState,
    COGConfidenceLog,
)
from app.models.conclusion import CONCLConclusion

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level classification."""
    VERY_LOW = "very_low"      # < 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"             # 0.7 - 0.9
    VERY_HIGH = "very_high"   # > 0.9


class MarketStage(Enum):
    """Market cycle stages."""
    BOTTOM = "bottom"          # 底部区域
    CONSOLIDATION = "consolidation"  # 震荡整理
    TREND_UP = "trend_up"     # 上涨趋势
    EXTREME = "extreme"        # 极端行情
    TREND_DOWN = "trend_down"  # 下跌趋势


class ConflictSeverity(Enum):
    """Conflict severity levels."""
    MINOR = "minor"           # 轻微差异，可忽略
    MODERATE = "moderate"     # 中度冲突，需审视
    SEVERE = "severe"         # 严重冲突，需仲裁
    CRITICAL = "critical"     # 矛盾结论，不可共存


@dataclass
class ConfidenceFactor:
    """Factor contributing to confidence score."""
    name: str
    impact: float  # -1 to 1
    weight: float  # 0 to 1
    description: str


@dataclass
class ConfidenceAssessment:
    """Complete confidence assessment result."""
    overall_score: float
    level: ConfidenceLevel
    factors: List[ConfidenceFactor]
    recommendation: str
    risk_warning: Optional[str] = None


@dataclass
class ConflictResult:
    """Conflict detection result."""
    has_conflict: bool
    severity: ConflictSeverity
    conflicting_pairs: List[Tuple[int, int]]
    analysis: str
    resolution: Optional[str] = None


@dataclass
class CognitionState:
    """Current market cognition state."""
    market_stage: MarketStage
    risk_attitude: str
    overall_confidence: float
    active_signals: List[str]
    market_sentiment: str
    confidence_trend: str  # improving/stable/declining
    last_updated: datetime


class CognitionEngine:
    """Cognition engine for confidence assessment and conflict detection."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self._style_cache: Dict[int, COGInvestmentStyle] = {}

    # ==================== Confidence Assessment ====================

    async def assess_confidence(
        self,
        conclusion_type: str,
        conclusion_content: str,
        context: Dict[str, Any],
    ) -> ConfidenceAssessment:
        """Assess confidence for a conclusion."""
        factors = []

        # 1. Data freshness factor
        data_freshness = self._assess_data_freshness(context)
        factors.append(ConfidenceFactor(
            name="数据时效性",
            impact=data_freshness,
            weight=0.15,
            description="数据更新时间距离现在的时长",
        ))

        # 2. Indicator consistency factor
        indicator_consistency = self._assess_indicator_consistency(context)
        factors.append(ConfidenceFactor(
            name="指标一致性",
            impact=indicator_consistency,
            weight=0.2,
            description="多个技术指标是否指向同一方向",
        ))

        # 3. Historical accuracy factor
        historical_accuracy = await self._get_historical_accuracy(conclusion_type)
        factors.append(ConfidenceFactor(
            name="历史准确率",
            impact=historical_accuracy,
            weight=0.25,
            description="该类型结论的历史预测准确率",
        ))

        # 4. Market condition factor
        market_confidence = self._assess_market_conditions(context)
        factors.append(ConfidenceFactor(
            name="市场环境适配度",
            impact=market_confidence,
            weight=0.2,
            description="结论与当前市场环境的匹配程度",
        ))

        # 5. Source reliability factor
        source_reliability = self._assess_source_reliability(context)
        factors.append(ConfidenceFactor(
            name="信息源可靠性",
            impact=source_reliability,
            weight=0.2,
            description="支撑结论的信息来源可信度",
        ))

        # Calculate weighted score
        overall_score = sum(
            f.impact * f.weight for f in factors
        ) / sum(f.weight for f in factors) if factors else 0.5

        # Clamp to 0-1
        overall_score = max(0.0, min(1.0, overall_score))

        # Determine level
        level = self._score_to_level(overall_score)

        # Generate recommendation
        recommendation = self._generate_recommendation(level, overall_score)

        # Check for risk warnings
        risk_warning = None
        if overall_score < 0.4:
            risk_warning = "当前结论置信度较低，建议谨慎参考"
        elif level == ConfidenceLevel.VERY_LOW:
            risk_warning = "结论置信度过低，不建议作为决策依据"

        # Log confidence assessment
        await self._log_confidence(conclusion_type, overall_score, factors)

        return ConfidenceAssessment(
            overall_score=overall_score,
            level=level,
            factors=factors,
            recommendation=recommendation,
            risk_warning=risk_warning,
        )

    def _assess_data_freshness(self, context: Dict[str, Any]) -> float:
        """Assess data freshness impact on confidence."""
        data_source = context.get("data_source", "")

        # Real-time data is best
        if "realtime" in data_source.lower():
            return 1.0
        elif "daily" in data_source.lower():
            return 0.8
        elif "history" in data_source.lower():
            return 0.4
        return 0.5

    def _assess_indicator_consistency(self, context: Dict[str, Any]) -> float:
        """Assess consistency of technical indicators."""
        indicators = context.get("indicators", {})

        if not indicators:
            return 0.3  # Unknown is low confidence

        bullish = 0
        bearish = 0
        neutral = 0

        # Check common indicators
        ma_status = indicators.get("ma_status", "neutral")
        if ma_status == "bullish":
            bullish += 1
        elif ma_status == "bearish":
            bearish += 1
        else:
            neutral += 1

        macd_signal = indicators.get("macd_signal", 0)
        if macd_signal > 0:
            bullish += 1
        elif macd_signal < 0:
            bearish += 1

        rsi_value = indicators.get("rsi", 50)
        if rsi_value > 70:
            bullish += 0.5
            bearish += 0.5  # Overbought, potentially bearish
        elif rsi_value < 30:
            bearish += 0.5
            bullish += 0.5  # Oversold, potentially bullish
        else:
            neutral += 1

        # Calculate consistency
        total = bullish + bearish + neutral
        if total == 0:
            return 0.5

        dominant = max(bullish, bearish, neutral)
        return dominant / total

    async def _get_historical_accuracy(self, conclusion_type: str) -> float:
        """Get historical accuracy for conclusion type."""
        try:
            query = select(
                func.avg(COGConfidenceLog.confidence_score)
            ).where(
                COGConfidenceLog.conclusion_type == conclusion_type
            )
            result = await self.db.execute(query)
            avg_score = result.scalar()

            if avg_score:
                return float(avg_score)

            # Default based on type
            if "buy" in conclusion_type.lower() or "sell" in conclusion_type.lower():
                return 0.6  # Trading signals
            elif "trend" in conclusion_type.lower():
                return 0.55  # Trend predictions
            else:
                return 0.5  # General analysis

        except Exception as e:
            logger.debug(f"Error getting historical accuracy: {e}")
            return 0.5

    def _assess_market_conditions(self, context: Dict[str, Any]) -> float:
        """Assess how well conclusion matches market conditions."""
        market_stage = context.get("market_stage", "")

        # VLOOKUP-style adaptation matrix
        adaptation_matrix = {
            "bullish": {
                "trend_up": 0.9,
                "consolidation": 0.7,
                "bottom": 0.8,
                "trend_down": 0.3,
                "extreme": 0.2,
            },
            "bearish": {
                "trend_down": 0.9,
                "consolidation": 0.7,
                "top": 0.8,
                "trend_up": 0.3,
                "extreme": 0.2,
            },
            "neutral": {
                "consolidation": 0.85,
                "bottom": 0.7,
                "top": 0.7,
                "trend_up": 0.5,
                "trend_down": 0.5,
            },
        }

        sentiment = context.get("sentiment", "neutral")
        sentiment = sentiment.lower() if sentiment else "neutral"

        return adaptation_matrix.get(sentiment, {}).get(market_stage, 0.5)

    def _assess_source_reliability(self, context: Dict[str, Any]) -> float:
        """Assess reliability of information source."""
        source = context.get("source", "").lower()

        reliability = {
            "official": 1.0,
            "research": 0.9,
            "analyst": 0.8,
            "news": 0.6,
            "forum": 0.3,
            "social": 0.2,
        }

        for keyword, score in reliability.items():
            if keyword in source:
                return score

        return 0.5  # Default unknown

    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Convert numerical score to confidence level."""
        if score < 0.3:
            return ConfidenceLevel.VERY_LOW
        elif score < 0.5:
            return ConfidenceLevel.LOW
        elif score < 0.7:
            return ConfidenceLevel.MEDIUM
        elif score < 0.9:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

    def _generate_recommendation(self, level: ConfidenceLevel, score: float) -> str:
        """Generate recommendation based on confidence level."""
        recommendations = {
            ConfidenceLevel.VERY_LOW: "不建议采纳，需更多信息验证",
            ConfidenceLevel.LOW: "谨慎参考，建议结合其他分析",
            ConfidenceLevel.MEDIUM: "可以参考，保持适度关注",
            ConfidenceLevel.HIGH: "可靠性较高，可作为重要参考",
            ConfidenceLevel.VERY_HIGH: "高度可靠，可作为主要决策依据",
        }
        return recommendations.get(level, "无法评估")

    async def _log_confidence(
        self,
        conclusion_type: str,
        score: float,
        factors: List[ConfidenceFactor],
    ) -> None:
        """Log confidence assessment."""
        try:
            log = COGConfidenceLog(
                conclusion_type=conclusion_type,
                confidence_score=Decimal(str(score)),
                factors=[f.name for f in factors],
            )
            self.db.add(log)
            await self.db.flush()
        except Exception as e:
            logger.debug(f"Failed to log confidence: {e}")

    # ==================== Conflict Detection ====================

    async def detect_conflicts(
        self,
        conclusions: List[CONCLConclusion],
    ) -> ConflictResult:
        """Detect conflicts between conclusions."""
        if len(conclusions) < 2:
            return ConflictResult(
                has_conflict=False,
                severity=ConflictSeverity.MINOR,
                conflicting_pairs=[],
                analysis="结论数量不足，无需冲突检测",
            )

        conflicts = []
        analyzed_pairs = set()

        for i, c1 in enumerate(conclusions):
            for j, c2 in enumerate(conclusions[i + 1:], i + 1):
                pair_key = tuple(sorted([c1.id, c2.id]))
                if pair_key in analyzed_pairs:
                    continue
                analyzed_pairs.add(pair_key)

                conflict = self._check_pair_conflict(c1, c2)
                if conflict:
                    conflicts.append((c1.id, c2.id, conflict))

        if not conflicts:
            return ConflictResult(
                has_conflict=False,
                severity=ConflictSeverity.MINOR,
                conflicting_pairs=[],
                analysis="未检测到明显冲突",
            )

        # Determine overall severity
        max_severity = max(c[2] for c in conflicts)

        # Generate analysis
        analysis_parts = [f"发现 {len(conflicts)} 对冲突结论："]
        for c1_id, c2_id, severity in conflicts:
            c1 = next((c for c in conclusions if c.id == c1_id), None)
            c2 = next((c for c in conclusions if c.id == c2_id), None)
            if c1 and c2:
                analysis_parts.append(
                    f"- 结论{c1_id} ({c1.conclusion_type}) 与 结论{c2_id} ({c2.conclusion_type}): {severity.value}"
                )

        analysis = "\n".join(analysis_parts)

        # Try to generate resolution
        resolution = await self._attempt_resolution(conflicts, conclusions)

        return ConflictResult(
            has_conflict=True,
            severity=max_severity,
            conflicting_pairs=[(c[0], c[1]) for c in conflicts],
            analysis=analysis,
            resolution=resolution,
        )

    def _check_pair_conflict(
        self, c1: CONCLConclusion, c2: CONCLConclusion
    ) -> Optional[ConflictSeverity]:
        """Check if two conclusions conflict."""
        # Same conclusion - no conflict
        if c1.id == c2.id:
            return None

        # Check direction conflicts
        direction1 = self._get_direction(c1)
        direction2 = self._get_direction(c2)

        if direction1 and direction2 and direction1 != direction2:
            # Opposing directions - check severity
            return ConflictSeverity.CRITICAL

        # Check time frame conflicts
        timeframe1 = self._get_timeframe(c1)
        timeframe2 = self._get_timeframe(c2)

        if timeframe1 and timeframe2 and timeframe1 != timeframe2:
            # Different timeframes might conflict
            if direction1 == direction2:
                return ConflictSeverity.MODERATE

        # Check indicator conflicts
        indicators1 = set(c1.metadata.get("indicators", []) if c1.metadata else [])
        indicators2 = set(c2.metadata.get("indicators", []) if c2.metadata else [])

        common = indicators1 & indicators2
        if common and direction1 and direction2:
            # Same indicator, opposite direction
            return ConflictSeverity.SEVERE

        return None

    def _get_direction(self, conclusion: CONCLConclusion) -> Optional[str]:
        """Extract direction from conclusion."""
        content = conclusion.content.lower()

        bullish_keywords = ["买入", "做多", "上涨", "看好", "增持", "bullish", "buy", "long"]
        bearish_keywords = ["卖出", "做空", "下跌", "看跌", "减持", "bearish", "sell", "short"]

        for kw in bullish_keywords:
            if kw in content:
                return "bullish"
        for kw in bearish_keywords:
            if kw in content:
                return "bearish"

        return None

    def _get_timeframe(self, conclusion: CONCLConclusion) -> Optional[str]:
        """Extract timeframe from conclusion."""
        metadata = conclusion.metadata or {}
        content = conclusion.content.lower()

        if "short" in metadata.get("tags", []) or "短线" in content:
            return "short"
        elif "medium" in metadata.get("tags", []) or "中线" in content:
            return "medium"
        elif "long" in metadata.get("tags", []) or "长线" in content:
            return "long"

        return None

    async def _attempt_resolution(
        self,
        conflicts: List[Tuple],
        conclusions: List[CONCLConclusion],
    ) -> Optional[str]:
        """Attempt to resolve conflicts."""
        if not conflicts:
            return None

        resolutions = []

        for c1_id, c2_id, severity in conflicts:
            c1 = next((c for c in conclusions if c.id == c1_id), None)
            c2 = next((c for c in conclusions if c.id == c2_id), None)

            if not c1 or not c2:
                continue

            # Try confidence-based resolution
            conf1 = c1.metadata.get("confidence", 0.5) if c1.metadata else 0.5
            conf2 = c2.metadata.get("confidence", 0.5) if c2.metadata else 0.5

            if conf1 > conf2 + 0.1:
                resolutions.append(
                    f"结论{c1_id}置信度({conf1:.0%})高于结论{c2_id}({conf2:.0%})，建议优先参考"
                )
            elif conf2 > conf1 + 0.1:
                resolutions.append(
                    f"结论{c2_id}置信度({conf2:.0%})高于结论{c1_id}({conf1:.0%})，建议优先参考"
                )

        return "\n".join(resolutions) if resolutions else "建议人工审核冲突结论"

    # ==================== Market Stage Recognition ====================

    async def recognize_market_stage(
        self,
        sh_change: float,
        sz_change: float,
        volume_ratio: float,
        market_breadth: float,
    ) -> MarketStage:
        """Recognize current market stage."""
        # Logic based on multiple factors
        avg_change = (sh_change + sz_change) / 2

        if avg_change > 3:
            if volume_ratio > 1.5:
                return MarketStage.EXTREME  # Possible top
            return MarketStage.TREND_UP

        elif avg_change > 1:
            return MarketStage.TREND_UP

        elif avg_change > -1:
            return MarketStage.CONSOLIDATION

        elif avg_change > -3:
            if market_breadth < -30:
                return MarketStage.TREND_DOWN
            return MarketStage.BOTTOM

        else:
            if volume_ratio > 1.5:
                return MarketStage.EXTREME  # Possible bottom
            return MarketStage.TREND_DOWN

    # ==================== Cognition State Management ====================

    async def get_current_state(self) -> CognitionState:
        """Get current market cognition state."""
        try:
            query = select(COGCognitionState).order_by(
                COGCognitionState.updated_at.desc()
            ).limit(1)
            result = await self.db.execute(query)
            state = result.scalar_one_or_none()

            if state:
                return CognitionState(
                    market_stage=MarketStage(state.market_stage),
                    risk_attitude=state.risk_attitude,
                    overall_confidence=float(state.overall_confidence),
                    active_signals=state.active_signals or [],
                    market_sentiment=state.market_sentiment,
                    confidence_trend="stable",
                    last_updated=state.updated_at,
                )

            # Default state
            return CognitionState(
                market_stage=MarketStage.CONSOLIDATION,
                risk_attitude="moderate",
                overall_confidence=0.5,
                active_signals=[],
                market_sentiment="neutral",
                confidence_trend="stable",
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error getting cognition state: {e}")
            return CognitionState(
                market_stage=MarketStage.CONSOLIDATION,
                risk_attitude="moderate",
                overall_confidence=0.5,
                active_signals=[],
                market_sentiment="neutral",
                confidence_trend="stable",
                last_updated=datetime.utcnow(),
            )

    async def update_state(
        self,
        market_stage: MarketStage,
        risk_attitude: str,
        confidence: float,
        signals: List[str],
        sentiment: str,
    ) -> None:
        """Update current market cognition state."""
        try:
            # Get or create state
            query = select(COGCognitionState).order_by(
                COGCognitionState.updated_at.desc()
            ).limit(1)
            result = await self.db.execute(query)
            state = result.scalar_one_or_none()

            if state:
                state.market_stage = market_stage.value
                state.risk_attitude = risk_attitude
                state.overall_confidence = Decimal(str(confidence))
                state.active_signals = signals
                state.market_sentiment = sentiment
                state.updated_at = datetime.utcnow()
            else:
                state = COGCognitionState(
                    market_stage=market_stage.value,
                    risk_attitude=risk_attitude,
                    overall_confidence=Decimal(str(confidence)),
                    active_signals=signals,
                    market_sentiment=sentiment,
                )
                self.db.add(state)

            await self.db.flush()

        except Exception as e:
            logger.error(f"Error updating cognition state: {e}")

    # ==================== Investment Style ====================

    async def get_investment_style(self, style_id: Optional[int] = None) -> COGInvestmentStyle:
        """Get investment style configuration."""
        try:
            if style_id:
                query = select(COGInvestmentStyle).where(
                    COGInvestmentStyle.id == style_id
                )
            else:
                query = select(COGInvestmentStyle).where(
                    COGInvestmentStyle.is_default == True
                )

            result = await self.db.execute(query)
            style = result.scalar_one_or_none()

            if style:
                return style

            # Return moderate default
            return COGInvestmentStyle(
                name="moderate",
                description="稳健型投资风格",
                risk_tolerance="moderate",
                tech_weight=0.5,
                fundamental_weight=0.3,
                sentiment_weight=0.2,
                is_default=True,
            )

        except Exception as e:
            logger.error(f"Error getting investment style: {e}")
            return None
