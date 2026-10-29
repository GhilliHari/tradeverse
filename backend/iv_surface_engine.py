"""
Implied Volatility Surface & Strike Smile Engine for Tradeverse
Calculates:
- Strike-by-strike Implied Volatility (IV) for CE and PE using numerical root finding (Newton-Raphson & Bisection)
- Volatility Smile and Skew curve points
- Volatility Skew metric: 25-Delta Put IV vs 25-Delta Call IV (institutional tail risk hedging pressure)
- ATM Volatility baseline & IV Rank / Percentile estimation
- Regime-based Strategy Directive (High IV -> Writing/Credit vs Low IV -> Buying/Debit)
"""

import math
import numpy as np
try:
    import scipy.stats as si
except ImportError:
    class _NormFallback:
        @staticmethod
        def cdf(x, loc=0.0, scale=1.0):
            z = (float(x) - loc) / scale
            return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

        @staticmethod
        def pdf(x, loc=0.0, scale=1.0):
            z = (float(x) - loc) / scale
            return (1.0 / (scale * math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * z * z)

    class _SciPyStatsFallback:
        norm = _NormFallback()

    si = _SciPyStatsFallback()
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("IVSurfaceEngine")


class IVSurfaceEngine:
    def __init__(self, risk_free_rate: float = 0.07):
        self.r = risk_free_rate

    def black_scholes_price(self, S: float, K: float, T: float, v: float, option_type: str = "CE") -> float:
        """Standard Black-Scholes formula."""
        if T <= 0 or v <= 0:
            return max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)
        
        d1 = (np.log(S / K) + (self.r + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
        d2 = d1 - v * np.sqrt(T)

        if option_type == "CE":
            return float(S * si.norm.cdf(d1) - K * np.exp(-self.r * T) * si.norm.cdf(d2))
        else:
            return float(K * np.exp(-self.r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1))

    def calculate_vega(self, S: float, K: float, T: float, v: float) -> float:
        """Calculates Black-Scholes Vega."""
        if T <= 0 or v <= 0:
            return 0.0
        d1 = (np.log(S / K) + (self.r + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
        return float(S * si.norm.pdf(d1) * np.sqrt(T))

    def solve_iv(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        option_type: str = "CE",
        tol: float = 1e-4,
        max_iter: int = 40
    ) -> float:
        """
        Solves Implied Volatility (IV) given market price using hybrid Newton-Raphson with bisection fallback.
        Returns IV as a decimal (e.g. 0.165 = 16.5%).
        """
        if T <= 0 or market_price <= 0:
            return 0.14  # Default baseline

        # Intrinsic value bounds
        intrinsic = max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)
        if market_price < intrinsic:
            return 0.08  # Minimum bound

        # 1. Newton-Raphson
        v = 0.20  # Initial guess (20%)
        for _ in range(max_iter):
            price = self.black_scholes_price(S, K, T, v, option_type)
            diff = price - market_price

            if abs(diff) < tol:
                return float(np.clip(v, 0.05, 2.50))

            vega = self.calculate_vega(S, K, T, v)
            if abs(vega) < 1e-6:
                break  # Flat derivative, fallback to bisection

            v_new = v - diff / vega
            if v_new <= 0.02 or v_new > 3.0:
                break  # Out of reasonable bounds, switch to bisection
            v = v_new

        # 2. Bisection Fallback
        low, high = 0.02, 2.50
        for _ in range(30):
            mid = (low + high) / 2.0
            price = self.black_scholes_price(S, K, T, mid, option_type)
            diff = price - market_price

            if abs(diff) < tol:
                return float(mid)

            if diff > 0:
                high = mid
            else:
                low = mid

        return float(np.clip((low + high) / 2.0, 0.05, 2.50))

    def compute_iv_surface(
        self,
        chain_data: List[Dict[str, Any]],
        spot_price: float,
        days_to_expiry: float = 4.0,
        india_vix: float = 13.5
    ) -> Dict[str, Any]:
        """
        Processes an option chain to produce full Volatility Surface analytics.
        """
        if not chain_data or spot_price <= 0:
            return {}

        T = max(1.0, days_to_expiry) / 365.0
        surface_points = []
        ce_ivs = []
        pe_ivs = []

        atm_strike = min(chain_data, key=lambda x: abs(x["strike"] - spot_price))["strike"]
        atm_ce_iv = None
        atm_pe_iv = None

        for item in chain_data:
            k = float(item["strike"])
            ce_prem = float(item.get("ce_premium", 0.0))
            pe_prem = float(item.get("pe_premium", 0.0))

            # Solve IV
            ce_iv = self.solve_iv(ce_prem, spot_price, k, T, "CE")
            pe_iv = self.solve_iv(pe_prem, spot_price, k, T, "PE")

            ce_iv_pct = round(ce_iv * 100.0, 2)
            pe_iv_pct = round(pe_iv * 100.0, 2)
            skew = round(pe_iv_pct - ce_iv_pct, 2)

            ce_ivs.append(ce_iv_pct)
            pe_ivs.append(pe_iv_pct)

            if k == atm_strike:
                atm_ce_iv = ce_iv_pct
                atm_pe_iv = pe_iv_pct

            surface_points.append({
                "strike": int(k),
                "ce_premium": ce_prem,
                "pe_premium": pe_prem,
                "ce_iv": ce_iv_pct,
                "pe_iv": pe_iv_pct,
                "vol_skew": skew,
                "oi_ce": int(item.get("oi_ce", 0)),
                "oi_pe": int(item.get("oi_pe", 0))
            })

        # ATM Baseline IV
        atm_iv = round((atm_ce_iv + atm_pe_iv) / 2.0, 2) if (atm_ce_iv and atm_pe_iv) else round(india_vix, 2)

        # 25-Delta Skew Proxy (OTM Put IV vs OTM Call IV: 2 strikes OTM)
        otm_puts = [p for p in surface_points if p["strike"] < atm_strike]
        otm_calls = [p for p in surface_points if p["strike"] > atm_strike]

        otm_put_iv = otm_puts[-2]["pe_iv"] if len(otm_puts) >= 2 else atm_iv
        otm_call_iv = otm_calls[1]["ce_iv"] if len(otm_calls) >= 2 else atm_iv
        skew_metric = round(otm_put_iv - otm_call_iv, 2)

        # Skew interpretation
        if skew_metric > 3.0:
            skew_sentiment = "BEARISH_HEDGING"
            skew_interpretation = "Elevated Put Skew: Institutions are paying heavy premium for downside tail-risk puts."
        elif skew_metric < -1.5:
            skew_sentiment = "SPECULATIVE_CALL_FRENZY"
            skew_interpretation = "Inverted Skew: Aggressive retail / momentum call buying bidding up OTM call IV."
        else:
            skew_sentiment = "BALANCED"
            skew_interpretation = "Normal Volatility Smile: Balanced institutional pricing across calls and puts."

        # IV Rank estimation (based on India VIX historical distribution: 10 to 28 range)
        iv_rank = round(max(0.0, min(100.0, (atm_iv - 10.0) / (28.0 - 10.0) * 100.0)), 1)

        # Strategy Directive based on IV Regime
        if iv_rank >= 65.0:
            strategy_directive = "HIGH_IV_CREDIT_WRITING"
            directive_detail = "Implied volatility is rich. Favor selling premium: Bull Put Spreads, Bear Call Spreads, or Iron Condors."
        elif iv_rank <= 35.0:
            strategy_directive = "LOW_IV_DEBIT_BUYING"
            directive_detail = "Implied volatility is cheap. Favor buying options: Bull Call Debit Spreads or Directional Breakout Snipers."
        else:
            strategy_directive = "BALANCED_SPREADS"
            directive_detail = "Moderate volatility. Favor delta-aligned vertical spreads with defined risk."

        return {
            "spot_price": round(spot_price, 2),
            "atm_strike": int(atm_strike),
            "atm_iv": atm_iv,
            "india_vix": round(india_vix, 2),
            "iv_rank": iv_rank,
            "volatility_skew": skew_metric,
            "skew_sentiment": skew_sentiment,
            "skew_interpretation": skew_interpretation,
            "strategy_directive": strategy_directive,
            "directive_detail": directive_detail,
            "surface_points": surface_points
        }


# Global singleton instance
iv_surface_engine = IVSurfaceEngine()
