"""Stock Analyzer - Technical Analysis Engine."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

import pandas as pd

from app.ml.indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """Stock technical analysis engine."""

    def __init__(self):
        self.indicators = TechnicalIndicators()

    async def analyze(
        self,
        code: str,
        quotes: Dict[str, Any],
        history_data: list,
    ) -> Dict[str, Any]:
        """Perform comprehensive stock analysis."""
        if not history_data:
            return self._empty_analysis(code)

        # Convert to DataFrame
        df = self._to_dataframe(history_data)

        # Calculate indicators
        ind = self.indicators.calculate_all(df)

        # Determine trend
        trend = self._determine_trend(df, ind)

        # Calculate AI score
        score = self._calculate_ai_score(df, ind)

        # Generate recommendation
        recommendation = self._generate_recommendation(trend, ind, score)

        # Risk assessment
        risk = self._assess_risk(df, ind)

        return {
            "code": code,
            "name": quotes.get("name", ""),
            "current_price": quotes.get("price", 0),
            "pct_chg": quotes.get("pct_chg", 0),
            "analysis": {
                "trend": trend,
                "tech_score": score,
                "ai_recommendation": recommendation,
                "risk_level": risk,
            },
            "indicators": {
                "ma5": str(ind["moving_averages"].get("ma5", "0")),
                "ma10": str(ind["moving_averages"].get("ma10", "0")),
                "ma20": str(ind["moving_averages"].get("ma20", "0")),
                "bias": str(ind.get("bias", "0")),
                "volume_ratio": str(ind.get("volume_ratio", "0")),
            },
            "macd": {
                "dif": str(ind["macd"]["dif"]),
                "dea": str(ind["macd"]["dea"]),
                "macd": str(ind["macd"]["macd"]),
            },
            "kdj": {
                "k": str(ind["kdj"]["k"]),
                "d": str(ind["kdj"]["d"]),
                "j": str(ind["kdj"]["j"]),
            },
            "updated_at": datetime.now().isoformat(),
        }

    def _determine_trend(
        self, df, indicators: Dict[str, Any]
    ) -> str:
        """Determine current market trend."""
        if df.empty or len(df) < 20:
            return "震荡"

        close = df["close"].iloc[-1]
        ma5 = float(indicators["moving_averages"].get("ma5", 0))
        ma20 = float(indicators["moving_averages"].get("ma20", 0))
        ma60 = float(indicators["moving_averages"].get("ma60", ma20))

        # Short-term trend
        if close > ma5 > ma20:
            short_term = "上升"
        elif close < ma5 < ma20:
            short_term = "下降"
        else:
            short_term = "震荡"

        # Medium-term trend
        if ma5 > ma20:
            medium_term = "多头"
        elif ma5 < ma20:
            medium_term = "空头"
        else:
            medium_term = "震荡"

        return f"{medium_term}{short_term}"

    def _calculate_ai_score(
        self, df, indicators: Dict[str, Any]
    ) -> int:
        """Calculate AI analysis score (0-100)."""
        if df.empty:
            return 50

        score = 50  # Base score

        # Trend contribution (+/- 20)
        ma5 = float(indicators["moving_averages"].get("ma5", 0))
        ma20 = float(indicators["moving_averages"].get("ma20", 0))
        close = df["close"].iloc[-1]

        if close > ma5 > ma20:
            score += 15
        elif close > ma5:
            score += 5
        elif close < ma5 < ma20:
            score -= 15
        elif close < ma5:
            score -= 5

        # MACD contribution (+/- 15)
        macd = indicators["macd"]
        dif = float(macd["dif"])
        dea = float(macd["dea"])

        if dif > dea > 0:
            score += 10
        elif dif > dea:
            score += 5
        elif dif < dea < 0:
            score -= 10
        elif dif < dea:
            score -= 5

        # KDJ contribution (+/- 10)
        kdj = indicators["kdj"]
        k = float(kdj["k"])
        d = float(kdj["d"])

        if 50 < k < 80 and k > d:
            score += 5
        elif k < 20 and k > d:  # Oversold bounce
            score += 3
        elif k > 80:  # Overbought
            score -= 5

        # Volume confirmation (+/- 5)
        vol_ratio = float(indicators.get("volume_ratio", 1))
        if vol_ratio > 1.5:
            score += 3
        elif vol_ratio < 0.5:
            score -= 2

        # Clamp score
        return max(0, min(100, score))

    def _generate_recommendation(
        self, trend: str, indicators: Dict[str, Any], score: int
    ) -> str:
        """Generate trading recommendation."""
        if "多" in trend and score >= 70:
            return "强烈买入"
        elif "多" in trend and score >= 60:
            return "买入"
        elif "空" in trend and score <= 30:
            return "强烈卖出"
        elif "空" in trend and score <= 40:
            return "卖出"
        elif score >= 70:
            return "逢低买入"
        elif score <= 30:
            return "逢高卖出"
        else:
            return "持有观望"

    def _assess_risk(self, df, indicators: Dict[str, Any]) -> str:
        """Assess risk level."""
        if df.empty:
            return "高"

        # Volatility (simplified)
        returns = df["close"].pct_change().dropna()
        volatility = returns.std() * 100

        if volatility > 5:
            risk = "极高"
        elif volatility > 3:
            risk = "高"
        elif volatility > 2:
            risk = "中"
        else:
            risk = "低"

        return risk

    def _to_dataframe(self, data: list) -> pd.DataFrame:
        """Convert list to DataFrame."""
        if not data:
            return pd.DataFrame()

        return pd.DataFrame(data)

    def _empty_analysis(self, code: str) -> Dict[str, Any]:
        """Return empty analysis result."""
        return {
            "code": code,
            "analysis": {
                "trend": "无法判断",
                "tech_score": 50,
                "ai_recommendation": "数据不足",
                "risk_level": "高",
            },
            "indicators": {},
            "macd": {"dif": "0", "dea": "0", "macd": "0"},
            "kdj": {"k": "50", "d": "50", "j": "50"},
        }
