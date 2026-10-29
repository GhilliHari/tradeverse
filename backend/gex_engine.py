"""
Upgraded Institutional GEX (Gamma Exposure) & Squeeze Detection Engine for Tradeverse
Features:
- Quantitative strike-level Dollar/Rupee Gamma calculations
- Zero Gamma Level (Gamma Flip Point) calculation
- Market Maker Gamma Regime: Positive Gamma (Stabilizing/Chop) vs Negative Gamma (Volatility Expansion)
- Real-time Gamma Squeeze & Liquidation Cascade detection
- High-OI Call/Put Gravity Walls and Max Pain
"""

import math
import pandas as pd
import numpy as np
import scipy.stats as si
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("GEXEngine")


class GEXEngine:
    def __init__(self, risk_free_rate: float = 0.07):
        self.r = risk_free_rate
        self.last_analysis: Dict[str, Any] = {}

    def calculate_bs_gamma(self, S: float, K: float, T: float, v: float) -> float:
        """Calculates Black-Scholes Gamma."""
        if T <= 0 or v <= 0 or S <= 0:
            return 0.0
        d1 = (np.log(S / K) + (self.r + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
        return float(si.norm.pdf(d1) / (S * v * np.sqrt(T)))

    def analyze_chain(
        self,
        chain_data: List[Dict[str, Any]],
        spot_price: float,
        lot_size: int = 30,
        days_to_expiry: float = 4.0,
        vix: float = 13.5
    ) -> Dict[str, Any]:
        """
        Comprehensive Option Chain GEX Analysis including Zero Gamma and Squeeze triggers.
        """
        if not chain_data or spot_price <= 0:
            return {}

        df = pd.DataFrame(chain_data)
        T = max(1.0, days_to_expiry) / 365.0
        v = max(0.08, vix / 100.0)

        # 1. Highest OI Strikes (Walls)
        call_wall_idx = df["oi_ce"].idxmax()
        put_wall_idx = df["oi_pe"].idxmax()

        call_wall = int(df.loc[call_wall_idx, "strike"])
        put_wall = int(df.loc[put_wall_idx, "strike"])

        # 2. PCR (Put-Call Ratio)
        total_ce_oi = int(df["oi_ce"].sum())
        total_pe_oi = int(df["oi_pe"].sum())
        pcr = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else 1.0

        # 3. Max Pain Approximation
        pain_scores = []
        for strike in df["strike"]:
            loss = 0
            for row in chain_data:
                ce_loss = max(0, row["strike"] - strike) * row.get("oi_ce", 0)
                pe_loss = max(0, strike - row["strike"]) * row.get("oi_pe", 0)
                loss += ce_loss + pe_loss
            pain_scores.append(loss)

        max_pain_idx = np.argmin(pain_scores)
        max_pain = int(df.loc[max_pain_idx, "strike"])

        # 4. Quantitative GEX Calculation per strike
        # Call GEX is positive for market makers (they are long gamma if customer buys calls)
        # Put GEX is negative for market makers (they are short gamma if customer buys puts)
        strike_gex_list = []
        total_net_gex = 0.0

        for row in chain_data:
            k = float(row["strike"])
            oi_ce = float(row.get("oi_ce", 0))
            oi_pe = float(row.get("oi_pe", 0))

            gamma = self.calculate_bs_gamma(spot_price, k, T, v)

            # In Crores INR (1 Crore = 10,000,000)
            # GEX per 1% move = OI * Spot * Gamma * LotSize * 0.01
            call_gex = (oi_ce * spot_price * gamma * lot_size * 0.01) / 1e7
            put_gex = (-oi_pe * spot_price * gamma * lot_size * 0.01) / 1e7
            net_gex_strike = call_gex + put_gex

            total_net_gex += net_gex_strike

            strike_gex_list.append({
                "strike": int(k),
                "call_gex_cr": round(call_gex, 3),
                "put_gex_cr": round(put_gex, 3),
                "net_gex_cr": round(net_gex_strike, 3),
                "gamma": round(gamma, 7)
            })

        total_net_gex_cr = round(total_net_gex, 2)

        # 5. Zero Gamma Level (Gamma Flip Point) calculation
        # Interpolate where cumulative Net GEX switches signs
        sorted_strikes = sorted(strike_gex_list, key=lambda x: x["strike"])
        zero_gamma_level = float(spot_price)

        for i in range(len(sorted_strikes) - 1):
            s1 = sorted_strikes[i]
            s2 = sorted_strikes[i + 1]
            if (s1["net_gex_cr"] <= 0 and s2["net_gex_cr"] >= 0) or (s1["net_gex_cr"] >= 0 and s2["net_gex_cr"] <= 0):
                # Linear interpolation
                denom = (s2["net_gex_cr"] - s1["net_gex_cr"])
                if abs(denom) > 1e-5:
                    zero_gamma_level = round(s1["strike"] + (0 - s1["net_gex_cr"]) * (s2["strike"] - s1["strike"]) / denom)
                else:
                    zero_gamma_level = round((s1["strike"] + s2["strike"]) / 2)
                break
        else:
            # Fallback if all positive or all negative: place near max pain or mid-wall
            zero_gamma_level = int(round((call_wall + put_wall) / 2))

        # 6. Market Maker Gamma Regime
        is_positive_gamma = spot_price >= zero_gamma_level
        gamma_regime = "POSITIVE_GAMMA_STABILIZING" if is_positive_gamma else "NEGATIVE_GAMMA_ACCELERATION"
        gamma_regime_desc = (
            "Market Makers are Long Gamma: Dips are bought and rallies are sold. Volatility is suppressed, favoring Mean Reversion & Credit Spreads."
            if is_positive_gamma else
            "Market Makers are Short Gamma: Moves are amplified by delta hedging. Volatility accelerates rapidly, favoring Directional Breakouts."
        )

        # 7. Gamma Squeeze & Cascade Trigger Detector
        dist_to_call_wall_pct = (call_wall - spot_price) / spot_price * 100.0
        dist_to_put_wall_pct = (spot_price - put_wall) / spot_price * 100.0

        squeeze_alert = "STABLE_PINNED"
        squeeze_urgency = "LOW"
        squeeze_message = f"Spot is cleanly oscillating between Call Wall ({call_wall}) and Put Wall ({put_wall})."

        if 0.0 <= dist_to_call_wall_pct <= 0.6:
            squeeze_alert = "GAMMA_WALL_CALL_SQUEEZE"
            squeeze_urgency = "HIGH"
            squeeze_message = f"🚨 CALL WALL SQUEEZE ALERT: Spot is within {dist_to_call_wall_pct:.2f}% of Call Wall ({call_wall}). A breakout above forces heavy dealer short covering!"
        elif dist_to_call_wall_pct < 0.0:
            squeeze_alert = "GAMMA_WALL_BLOWN_OUT_BULLISH"
            squeeze_urgency = "EXTREME"
            squeeze_message = f"🚀 CALL WALL BREACHED: Spot ({spot_price:,.2f}) has blown past {call_wall}. Explosive short squeeze in progress!"
        elif 0.0 <= dist_to_put_wall_pct <= 0.6:
            squeeze_alert = "PUT_WALL_CASCADE_WARNING"
            squeeze_urgency = "HIGH"
            squeeze_message = f"⚠️ PUT WALL BREAKDOWN WARNING: Spot is within {dist_to_put_wall_pct:.2f}% of Put Wall ({put_wall}). Breaching down triggers negative gamma selling cascades!"
        elif dist_to_put_wall_pct < 0.0:
            squeeze_alert = "PUT_WALL_CASCADE_ACTIVE"
            squeeze_urgency = "EXTREME"
            squeeze_message = f"🛑 PUT WALL BREACHED: Spot ({spot_price:,.2f}) below {put_wall}. Negative gamma waterfall in progress!"

        # Distance to magnets
        dist_to_pain = abs(spot_price - max_pain)
        dist_to_cw = abs(spot_price - call_wall)
        dist_to_pw = abs(spot_price - put_wall)
        magnet_point = max_pain
        magnet_strength = 0.0

        if dist_to_pain < 100:
            magnet_strength = 0.5
        if dist_to_cw < 50 or dist_to_pw < 50:
            magnet_strength = 0.8
            magnet_point = call_wall if dist_to_cw < dist_to_pw else put_wall

        analysis = {
            "call_wall": int(call_wall),
            "put_wall": int(put_wall),
            "max_pain": int(max_pain),
            "zero_gamma_level": int(zero_gamma_level),
            "net_gex_crores": total_net_gex_cr,
            "gamma_regime": gamma_regime,
            "gamma_regime_desc": gamma_regime_desc,
            "is_positive_gamma": is_positive_gamma,
            "pcr": pcr,
            "squeeze_alert": squeeze_alert,
            "squeeze_urgency": squeeze_urgency,
            "squeeze_message": squeeze_message,
            "magnet_point": int(magnet_point),
            "magnet_strength": float(magnet_strength),
            "sentiment": "BULLISH" if pcr > 1.1 else "BEARISH" if pcr < 0.7 else "NEUTRAL",
            "is_live": bool(total_ce_oi > 0),
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "strike_gex": strike_gex_list
        }

        self.last_analysis = analysis
        return analysis

    def get_safety_gate(self, signal: str, spot_price: float) -> Dict[str, Any]:
        """Safety gate checking against Call/Put walls and Zero Gamma cascades."""
        if not self.last_analysis:
            return {"allow": True, "reason": "No GEX data"}

        call_wall = self.last_analysis.get("call_wall", 0)
        put_wall = self.last_analysis.get("put_wall", 0)
        zero_gamma = self.last_analysis.get("zero_gamma_level", 0)

        if signal == "BUY" and spot_price > (call_wall - 30):
            return {"allow": False, "reason": f"APPROACHING HEAVY CALL WALL @ {call_wall}"}

        if signal == "SELL" and spot_price < (put_wall + 30):
            return {"allow": False, "reason": f"APPROACHING HEAVY PUT WALL @ {put_wall}"}

        return {"allow": True, "reason": "Path clear"}


# Global singleton instance
gex_engine = GEXEngine()
