"""Technical Indicators Calculator."""

from typing import Dict, Any
from decimal import Decimal
import pandas as pd
import numpy as np


class TechnicalIndicators:
    """Technical indicators calculator."""

    def __init__(self):
        pass

    def calculate_all(self, df) -> Dict[str, Any]:
        """Calculate all technical indicators."""
        return {
            "moving_averages": self.calculate_ma(df),
            "bias": self.calculate_bias(df),
            "volume_ratio": self.calculate_volume_ratio(df),
            "macd": self.calculate_macd(df),
            "kdj": self.calculate_kdj(df),
        }

    def calculate_ma(
        self, df, periods: list = None
    ) -> Dict[str, Decimal]:
        """Calculate moving averages."""
        if periods is None:
            periods = [5, 10, 20, 60]

        result = {}
        for period in periods:
            ma_key = f"ma{period}"
            result[ma_key] = self._safe_ma(df["close"], period)

        return result

    def calculate_bias(self, df) -> Decimal:
        """Calculate bias (乖离率)."""
        ma5 = self._safe_ma(df["close"], 5)
        close = df["close"].iloc[-1] if len(df) > 0 else 0

        if ma5 and ma5 > 0:
            return Decimal(str((close - float(ma5)) / float(ma5) * 100))
        return Decimal("0")

    def calculate_volume_ratio(self, df) -> Decimal:
        """Calculate volume ratio."""
        if len(df) < 5:
            return Decimal("0")

        recent_volume = df["volume"].iloc[-1]
        avg_volume = df["volume"].tail(5).mean()

        if avg_volume > 0:
            return Decimal(str(recent_volume / avg_volume))
        return Decimal("1")

    def calculate_macd(
        self, df
    ) -> Dict[str, Decimal]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(df) < 26:
            return {"dif": Decimal("0"), "dea": Decimal("0"), "macd": Decimal("0")}

        close = df["close"]

        # EMA12 and EMA26
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        # DIF (MACD Line)
        dif = ema12 - ema26

        # DEA (Signal Line)
        dea = dif.ewm(span=9, adjust=False).mean()

        # MACD Histogram
        macd = (dif - dea) * 2

        return {
            "dif": Decimal(str(dif.iloc[-1])),
            "dea": Decimal(str(dea.iloc[-1])),
            "macd": Decimal(str(macd.iloc[-1])),
        }

    def calculate_kdj(
        self, df
    ) -> Dict[str, Decimal]:
        """Calculate KDJ indicator."""
        if len(df) < 9:
            return {"k": Decimal("50"), "d": Decimal("50"), "j": Decimal("50")}

        low_min = df["low"].rolling(window=9).min()
        high_max = df["high"].rolling(window=9).max()

        # RSV (Raw Stochastic Value)
        rsv = (df["close"] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)

        # K, D, J
        k = rsv.rolling(window=3).mean()
        d = k.rolling(window=3).mean()
        j = 3 * k - 2 * d

        return {
            "k": Decimal(str(k.iloc[-1])) if not pd.isna(k.iloc[-1]) else Decimal("50"),
            "d": Decimal(str(d.iloc[-1])) if not pd.isna(d.iloc[-1]) else Decimal("50"),
            "j": Decimal(str(j.iloc[-1])) if not pd.isna(j.iloc[-1]) else Decimal("50"),
        }

    def _safe_ma(self, series, period: int) -> Decimal:
        """Safely calculate moving average."""
        if len(series) < period:
            if len(series) == 0:
                return Decimal("0")
            return Decimal(str(series.mean()))

        return Decimal(str(series.tail(period).mean()))
