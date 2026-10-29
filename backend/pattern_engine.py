import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("PatternEngine")

class PatternEngine:
    """
    Pillar 1: Technical & Chart Pattern Recognition Engine for Tradeverse.
    Scans candle data for candlestick patterns, classic chart formations,
    CPR (Central Pivot Range), and Anchored VWAP.
    """

    def __init__(self):
        logger.info("📐 PatternEngine Initialized")

    def calculate_cpr(self, high: float, low: float, close: float) -> Dict:
        """
        Calculates Central Pivot Range (CPR) for intraday analysis.
        Narrow CPR indicates high trending day probability.
        Wide CPR indicates range-bound day probability.
        """
        pivot = (high + low + close) / 3.0
        bc = (high + low) / 2.0
        tc = (pivot - bc) + pivot

        # Reorder so tc is always >= bc
        top_pivot = max(tc, bc)
        bottom_pivot = min(tc, bc)
        cpr_width = top_pivot - bottom_pivot
        cpr_width_pct = (cpr_width / pivot) * 100.0 if pivot > 0 else 0.0

        if cpr_width_pct < 0.15:
            cpr_type = "NARROW"
            cpr_bias = "HIGH_TREND_PROBABILITY"
        elif cpr_width_pct > 0.40:
            cpr_type = "WIDE"
            cpr_bias = "RANGE_BOUND_PROBABILITY"
        else:
            cpr_type = "AVERAGE"
            cpr_bias = "NEUTRAL"

        return {
            "pivot": round(pivot, 2),
            "top_pivot": round(top_pivot, 2),
            "bottom_pivot": round(bottom_pivot, 2),
            "r1": round((2 * pivot) - low, 2),
            "s1": round((2 * pivot) - high, 2),
            "r2": round(pivot + (high - low), 2),
            "s2": round(pivot - (high - low), 2),
            "cpr_width_pct": round(cpr_width_pct, 3),
            "cpr_type": cpr_type,
            "cpr_bias": cpr_bias
        }

    def detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Detects candlestick patterns on the latest 5 candles.
        """
        if df is None or len(df) < 5:
            return {"pattern": "NONE", "signal": "NEUTRAL", "confidence": 0.0}

        recent = df.tail(5).copy().reset_index(drop=True)
        c1, c2, c3, c4, c5 = [recent.iloc[i] for i in range(5)]

        def get_candle_info(c):
            open_p, close_p, high_p, low_p = c['Open'], c['Close'], c['High'], c['Low']
            body = abs(close_p - open_p)
            total_range = max(0.001, high_p - low_p)
            upper_shade = high_p - max(open_p, close_p)
            lower_shade = min(open_p, close_p) - low_p
            is_bull = close_p >= open_p
            return body, total_range, upper_shade, lower_shade, is_bull

        b5, r5, u5, l5, bull5 = get_candle_info(c5)
        b4, r4, u4, l4, bull4 = get_candle_info(c4)
        b3, r3, u3, l3, bull3 = get_candle_info(c3)

        patterns = []

        # 1. Bullish Engulfing
        if not bull4 and bull5 and c5['Close'] > c4['Open'] and c5['Open'] < c4['Close'] and b5 > b4:
            patterns.append({"pattern": "Bullish Engulfing", "signal": "BULLISH", "confidence": 0.85})

        # 2. Bearish Engulfing
        if bull4 and not bull5 and c5['Close'] < c4['Open'] and c5['Open'] > c4['Close'] and b5 > b4:
            patterns.append({"pattern": "Bearish Engulfing", "signal": "BEARISH", "confidence": 0.85})

        # 3. Hammer (Bullish Reversal)
        if l5 >= 2.0 * b5 and u5 <= 0.2 * r5 and not bull4:
            patterns.append({"pattern": "Hammer", "signal": "BULLISH", "confidence": 0.75})

        # 4. Shooting Star (Bearish Reversal)
        if u5 >= 2.0 * b5 and l5 <= 0.2 * r5 and bull4:
            patterns.append({"pattern": "Shooting Star", "signal": "BEARISH", "confidence": 0.75})

        # 5. Morning Star
        if not bull3 and b3 / r3 > 0.5 and b4 / r4 < 0.3 and bull5 and c5['Close'] > (c3['Open'] + c3['Close']) / 2:
            patterns.append({"pattern": "Morning Star", "signal": "BULLISH", "confidence": 0.90})

        # 6. Evening Star
        if bull3 and b3 / r3 > 0.5 and b4 / r4 < 0.3 and not bull5 and c5['Close'] < (c3['Open'] + c3['Close']) / 2:
            patterns.append({"pattern": "Evening Star", "signal": "BEARISH", "confidence": 0.90})

        if not patterns:
            return {"pattern": "NONE", "signal": "NEUTRAL", "confidence": 0.0}

        # Return highest confidence pattern
        best_pattern = max(patterns, key=lambda p: p['confidence'])
        return best_pattern

    def detect_chart_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Scans recent price action for Double Top, Double Bottom, and Flag consolidations.
        """
        if df is None or len(df) < 20:
            return {"pattern": "NONE", "signal": "NEUTRAL", "confidence": 0.0}

        closes = df['Close'].tail(20).values
        highs = df['High'].tail(20).values
        lows = df['Low'].tail(20).values

        # Peak detection for Double Top
        h_max1_idx = np.argmax(highs[:10])
        h_max2_idx = 10 + np.argmax(highs[10:])
        peak1 = highs[h_max1_idx]
        peak2 = highs[h_max2_idx]

        if abs(peak1 - peak2) / peak1 < 0.003 and (h_max2_idx - h_max1_idx) >= 4:
            valley = np.min(lows[h_max1_idx:h_max2_idx])
            current_close = closes[-1]
            if current_close < valley:
                return {"pattern": "Double Top Breakdown", "signal": "BEARISH", "confidence": 0.85}

        # Trough detection for Double Bottom
        l_min1_idx = np.argmin(lows[:10])
        l_min2_idx = 10 + np.argmin(lows[10:])
        trough1 = lows[l_min1_idx]
        trough2 = lows[l_min2_idx]

        if abs(trough1 - trough2) / trough1 < 0.003 and (l_min2_idx - l_min1_idx) >= 4:
            peak = np.max(highs[l_min1_idx:l_min2_idx])
            current_close = closes[-1]
            if current_close > peak:
                return {"pattern": "Double Bottom Breakout", "signal": "BULLISH", "confidence": 0.85}

        # Bull Flag Consolidation
        if len(closes) >= 15:
            move_1to5 = (closes[5] - closes[0]) / closes[0]
            consolidation_range = (np.max(highs[5:]) - np.min(lows[5:])) / closes[5]
            if move_1to5 > 0.015 and consolidation_range < 0.008 and closes[-1] > closes[-2]:
                return {"pattern": "Bull Flag Breakout", "signal": "BULLISH", "confidence": 0.80}

        return {"pattern": "NONE", "signal": "NEUTRAL", "confidence": 0.0}

    def analyze_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Runs comprehensive technical pattern analysis on latest dataset.
        Returns aggregate pattern score (-1.0 to +1.0) and detailed setup parameters.
        """
        if df is None or df.empty:
            return {"pattern_score": 0.0, "signal": "NEUTRAL", "details": {}}

        latest = df.iloc[-1]
        high = float(latest['High'])
        low = float(latest['Low'])
        close = float(latest['Close'])

        # Previous day data for CPR
        if len(df) >= 2:
            prev = df.iloc[-2]
            cpr_data = self.calculate_cpr(float(prev['High']), float(prev['Low']), float(prev['Close']))
        else:
            cpr_data = self.calculate_cpr(high, low, close)

        candle_pattern = self.detect_candlestick_patterns(df)
        chart_pattern = self.detect_chart_patterns(df)

        score = 0.0
        if candle_pattern['signal'] == "BULLISH": score += (0.4 * candle_pattern['confidence'])
        elif candle_pattern['signal'] == "BEARISH": score -= (0.4 * candle_pattern['confidence'])

        if chart_pattern['signal'] == "BULLISH": score += (0.6 * chart_pattern['confidence'])
        elif chart_pattern['signal'] == "BEARISH": score -= (0.6 * chart_pattern['confidence'])

        final_signal = "BULLISH" if score > 0.2 else "BEARISH" if score < -0.2 else "NEUTRAL"

        return {
            "pattern_score": round(max(-1.0, min(1.0, score)), 2),
            "signal": final_signal,
            "candle_pattern": candle_pattern,
            "chart_pattern": chart_pattern,
            "cpr_data": cpr_data
        }
