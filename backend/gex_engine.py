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

logger = logging.getLogger("GEXEngine")


class GEXEngine:
    def __init__(self, risk_free_rate: float = 0.07):
        self.r = risk_free_rate
        self.last_analysis: Dict[str, Any] = {}
        # Historical snapshots per symbol: symbol -> list of {time, total_ce_oi, total_pe_oi, pcr, spot}
        self.oi_history: Dict[str, List[Dict[str, Any]]] = {}

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
        symbol: str = "DEFAULT",
        lot_size: int = 30,
        days_to_expiry: float = 4.0,
        vix: float = 13.5
    ) -> Dict[str, Any]:
        """
        Comprehensive Option Chain GEX Analysis including Delta OI, Zero Gamma, and Squeeze triggers.
        """
        if not chain_data or spot_price <= 0:
            return {}

        import time
        now_ts = time.time()
        df = pd.DataFrame(chain_data)
        T = max(1.0, days_to_expiry) / 365.0
        v = max(0.08, vix / 100.0)

        # 1. Highest OI Strikes (Walls)
        call_wall_idx = df["oi_ce"].idxmax()
        put_wall_idx = df["oi_pe"].idxmax()

        call_wall = int(df.loc[call_wall_idx, "strike"])
        put_wall = int(df.loc[put_wall_idx, "strike"])

        # 2. PCR (Put-Call Ratio) - Total & ATM Battlefield
        total_ce_oi = int(df["oi_ce"].sum())
        total_pe_oi = int(df["oi_pe"].sum())
        pcr = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else 1.0

        # ATM Strike and nearest ±1 strike
        atm_strike = int(min(df["strike"], key=lambda k: abs(k - spot_price)))
        step = 100 if "BANK" in symbol.upper() else (25 if "MID" in symbol.upper() else 50)
        atm_mask = (df["strike"] >= atm_strike - step) & (df["strike"] <= atm_strike + step)
        atm_ce_oi = int(df.loc[atm_mask, "oi_ce"].sum()) if atm_mask.any() else total_ce_oi
        atm_pe_oi = int(df.loc[atm_mask, "oi_pe"].sum()) if atm_mask.any() else total_pe_oi
        pcr_atm = round(atm_pe_oi / atm_ce_oi, 3) if atm_ce_oi > 0 else pcr

        # 2b. Real-Time Delta OI Velocity & Trap Detection
        delta_ce_oi = 0
        delta_pe_oi = 0
        oi_momentum = 0.0
        bull_trap_risk = False
        bear_trap_risk = False
        short_covering = False
        long_unwinding = False

        sym_key = symbol.upper().replace("^", "").replace("NSE:", "").replace("NFO:", "")
        history = self.oi_history.get(sym_key, [])
        if history:
            # Find snapshot from 3 to 15 minutes ago, or use previous snapshot
            target_snap = history[-1]
            for snap in reversed(history):
                age_mins = (now_ts - snap["time"]) / 60.0
                if 3.0 <= age_mins <= 20.0:
                    target_snap = snap
                    break

            prev_ce = target_snap.get("total_ce_oi", total_ce_oi)
            prev_pe = target_snap.get("total_pe_oi", total_pe_oi)
            prev_spot = target_snap.get("spot", spot_price)

            delta_ce_oi = total_ce_oi - prev_ce
            delta_pe_oi = total_pe_oi - prev_pe
            denom = max(1000, abs(delta_ce_oi) + abs(delta_pe_oi))
            oi_momentum = round((delta_pe_oi - delta_ce_oi) / denom, 3)

            # Spot direction between snapshots
            spot_change = spot_price - prev_spot

            # Bull Trap: Price attempting to rise but Call writers are aggressively piling in (+30% more than PE)
            if spot_change > 0 and delta_ce_oi > 0 and delta_ce_oi > (1.35 * max(1, delta_pe_oi)):
                bull_trap_risk = True

            # Bear Trap: Price attempting to drop but Put writers are aggressively defending (+30% more than CE)
            if spot_change < 0 and delta_pe_oi > 0 and delta_pe_oi > (1.35 * max(1, delta_ce_oi)):
                bear_trap_risk = True

            # Short Covering: Net CE open interest dropping sharply into resistance
            if delta_ce_oi < -2000 or (prev_ce > 0 and (delta_ce_oi / prev_ce) <= -0.04):
                short_covering = True

            # Long Unwinding: Net PE open interest dropping sharply into support
            if delta_pe_oi < -2000 or (prev_pe > 0 and (delta_pe_oi / prev_pe) <= -0.04):
                long_unwinding = True

        # Append current snapshot into history
        if sym_key not in self.oi_history:
            self.oi_history[sym_key] = []
        self.oi_history[sym_key].append({
            "time": now_ts,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "atm_ce_oi": atm_ce_oi,
            "atm_pe_oi": atm_pe_oi,
            "pcr": pcr,
            "spot": spot_price
        })
        if len(self.oi_history[sym_key]) > 30:
            self.oi_history[sym_key] = self.oi_history[sym_key][-30:]

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
            "pcr_atm": pcr_atm,
            "delta_ce_oi": delta_ce_oi,
            "delta_pe_oi": delta_pe_oi,
            "oi_momentum": oi_momentum,
            "bull_trap_risk": bull_trap_risk,
            "bear_trap_risk": bear_trap_risk,
            "short_covering": short_covering,
            "long_unwinding": long_unwinding,
            "squeeze_alert": squeeze_alert,
            "squeeze_urgency": squeeze_urgency,
            "squeeze_message": squeeze_message,
            "magnet_point": int(magnet_point),
            "magnet_strength": float(magnet_strength),
            "sentiment": "BULLISH" if pcr > 1.15 else "BEARISH" if pcr < 0.80 else "NEUTRAL",
            "is_live": bool(total_ce_oi > 0),
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "atm_ce_oi": atm_ce_oi,
            "atm_pe_oi": atm_pe_oi,
            "strike_gex": strike_gex_list
        }

        self.last_analysis = analysis
        return analysis

    def get_safety_gate(self, signal: str, spot_price: float) -> Dict[str, Any]:
        """
        Institutional Safety Gate checking against Call/Put walls, PCR barriers,
        Zero Gamma cascades, and Delta OI bull/bear trap setups.
        """
        if not self.last_analysis:
            return {"allow": True, "reason": "No GEX/OI data available"}

        call_wall = self.last_analysis.get("call_wall", 0)
        put_wall = self.last_analysis.get("put_wall", 0)
        pcr = float(self.last_analysis.get("pcr", 1.0))
        pcr_atm = float(self.last_analysis.get("pcr_atm", pcr))
        bull_trap = bool(self.last_analysis.get("bull_trap_risk", False))
        bear_trap = bool(self.last_analysis.get("bear_trap_risk", False))
        short_cov = bool(self.last_analysis.get("short_covering", False))
        long_unwind = bool(self.last_analysis.get("long_unwinding", False))
        d_ce = int(self.last_analysis.get("delta_ce_oi", 0))
        d_pe = int(self.last_analysis.get("delta_pe_oi", 0))

        sig_upper = (signal or "").upper()
        is_bullish = sig_upper in ("BUY", "BUY_CE")
        is_bearish = sig_upper in ("SELL", "BUY_PE")

        if is_bullish:
            # 1. Extreme low PCR = overwhelming call writing barrier
            if pcr < 0.65 or pcr_atm < 0.60:
                return {
                    "allow": False, 
                    "reason": f"Heavy Call Writing Barrier (PCR: {pcr:.2f}, ATM PCR: {pcr_atm:.2f} < 0.65). Institutions capping upside."
                }
            # 2. Bull Trap: Call writers aggressively piling on into the rally
            if bull_trap and not short_cov:
                return {
                    "allow": False, 
                    "reason": f"Bull Trap Alert: Call writers adding aggressively (+{d_ce:,} contracts) into this rally."
                }
            # 3. Call Wall proximity (unless short covering underway)
            if spot_price > (call_wall - 35) and not short_cov:
                return {
                    "allow": False, 
                    "reason": f"Approaching Heavy Call Wall @ {call_wall}. High rejection probability without short covering."
                }
            # 4. Extreme overbought bubble
            if pcr > 1.70:
                return {
                    "allow": False, 
                    "reason": f"Extreme Overbought Bubble (PCR {pcr:.2f} > 1.70). High long-unwinding risk."
                }

        elif is_bearish:
            # 1. Extreme high PCR = heavy put writing cushion
            if pcr > 1.45 or pcr_atm > 1.50:
                return {
                    "allow": False, 
                    "reason": f"Strong Put Writing Cushion (PCR: {pcr:.2f}, ATM PCR: {pcr_atm:.2f} > 1.45). Institutions defending floor."
                }
            # 2. Bear Trap: Put writers aggressively building a floor into the dip
            if bear_trap and not long_unwind:
                return {
                    "allow": False, 
                    "reason": f"Bear Trap Alert: Put writers adding aggressively (+{d_pe:,} contracts) into this drop."
                }
            # 3. Put Wall proximity (unless long unwinding waterfall underway)
            if spot_price < (put_wall + 35) and not long_unwind:
                return {
                    "allow": False, 
                    "reason": f"Approaching Heavy Put Wall @ {put_wall}. Rebound risk without long unwinding."
                }
            # 4. Extreme oversold floor
            if pcr < 0.45:
                return {
                    "allow": False, 
                    "reason": f"Extreme Oversold Reversal Zone (PCR {pcr:.2f} < 0.45). Short squeeze risk."
                }

        return {"allow": True, "reason": "Path clear (Institutional OI Confluence Validated)"}


# Global singleton instance
gex_engine = GEXEngine()
