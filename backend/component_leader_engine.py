import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
import yfinance as yf

logger = logging.getLogger("ComponentLeaderEngine")

class ComponentLeaderEngine:
    """
    Pillar 4: Heavyweight Component Leadership & Divergence Engine for Tradeverse.
    Tracks real-time tick returns of top constituent stocks to validate index breakouts
    and prevent false breakouts caused by low-weight constituent divergence.
    """

    def __init__(self):
        # Index Heavyweight Constituent Weightings
        self.baskets = {
            "BANKNIFTY": {
                "HDFCBANK.NS": 0.291,
                "ICICIBANK.NS": 0.228,
                "SBIN.NS": 0.102,
                "AXISBANK.NS": 0.094,
                "KOTAKBANK.NS": 0.081
            },
            "FINNIFTY": {
                "HDFCBANK.NS": 0.284,
                "ICICIBANK.NS": 0.215,
                "SBIN.NS": 0.088,
                "BAJFINANCE.NS": 0.072,
                "AXISBANK.NS": 0.069
            },
            "NIFTY": {
                "RELIANCE.NS": 0.092,
                "HDFCBANK.NS": 0.086,
                "ICICIBANK.NS": 0.064,
                "INFY.NS": 0.053,
                "TCS.NS": 0.038
            }
        }
        logger.info("🏛️ ComponentLeaderEngine Initialized (BankNifty, FinNifty & Nifty Heavyweight Baskets)")

    def _resolve_basket_key(self, symbol: str) -> str:
        u_sym = symbol.upper()
        if "FIN" in u_sym:
            return "FINNIFTY"
        if "BANK" in u_sym:
            return "BANKNIFTY"
        return "NIFTY"

    def get_live_component_returns(self, symbol: str = "BANKNIFTY") -> Dict[str, Any]:
        """
        Fetches live returns for index constituent stocks and computes weighted return momentum.
        """
        basket_key = self._resolve_basket_key(symbol)
        weights = self.baskets.get(basket_key, self.baskets["BANKNIFTY"])
        component_data = {}
        weighted_return = 0.0
        total_weight = sum(weights.values())

        for ticker, weight in weights.items():
            try:
                t = yf.Ticker(ticker)
                fast_info = getattr(t, 'fast_info', None)
                if fast_info:
                    last_p = fast_info.last_price
                    prev_close = fast_info.previous_close
                    if last_p and prev_close and prev_close > 0:
                        pct_chg = ((last_p - prev_close) / prev_close) * 100.0
                        component_data[ticker] = {
                            "last_price": round(last_p, 2),
                            "change_pct": round(pct_chg, 2),
                            "weight": weight
                        }
                        weighted_return += (pct_chg * weight)
            except Exception as e:
                logger.debug(f"Component fetch fallback for {ticker}: {e}")

        weighted_return_norm = weighted_return / total_weight if total_weight > 0 else 0.0
        lead_score = round(max(-1.0, min(1.0, weighted_return_norm / 1.5)), 2)

        leading_signal = "NEUTRAL"
        if lead_score > 0.20:
            leading_signal = "BULLISH_LEAD"
        elif lead_score < -0.20:
            leading_signal = "BEARISH_LEAD"

        return {
            "basket": basket_key,
            "lead_score": lead_score,
            "leading_signal": leading_signal,
            "weighted_return_pct": round(weighted_return_norm, 2),
            "components": component_data
        }

    def validate_constituent_confluence(self, symbol: str, signal: str) -> Dict[str, Any]:
        """
        Gate 6: Institutional Heavyweight Divergence Guard.
        Validates if top constituents support the trade direction.
        """
        sig_upper = (signal or "").upper()
        if sig_upper == "HOLD":
            return {"allow": True, "reason": "Signal is HOLD"}

        try:
            comp_res = self.get_live_component_returns(symbol)
            components = comp_res.get("components", {})
            weighted_ret = float(comp_res.get("weighted_return_pct", 0.0))
            is_bullish = sig_upper in ("BUY", "BUY_CE")
            is_bearish = sig_upper in ("SELL", "BUY_PE")

            if not components:
                return {"allow": True, "reason": "Constituents feed unavailable (fallback pass)"}

            # Check Top 2 Heavyweights (e.g., HDFC and ICICI)
            top_tickers = list(components.keys())[:2]
            changes = [components[t]["change_pct"] for t in top_tickers if t in components]

            if is_bullish:
                # If top 2 constituents are both negative (< -0.25%)
                if len(changes) >= 2 and all(c < -0.25 for c in changes):
                    return {
                        "allow": False,
                        "reason": f"Heavyweight Divergence: Top leaders {top_tickers} are both negative ({changes}). Breakout lacks institutional backing."
                    }
                if weighted_ret < -0.35:
                    return {
                        "allow": False,
                        "reason": f"Sector Drag: Constituent weighted return is bearish ({weighted_ret:+.2f}%)."
                    }

            elif is_bearish:
                # If top 2 constituents are both positive (> +0.25%)
                if len(changes) >= 2 and all(c > 0.25 for c in changes):
                    return {
                        "allow": False,
                        "reason": f"Heavyweight Divergence: Top leaders {top_tickers} are both positive ({changes}). Breakdown lacks institutional backing."
                    }
                if weighted_ret > 0.35:
                    return {
                        "allow": False,
                        "reason": f"Sector Support: Constituent weighted return is bullish ({weighted_ret:+.2f}%)."
                    }

            return {
                "allow": True, 
                "reason": f"Constituent Confluence Validated ({comp_res.get('leading_signal')}, Weighted: {weighted_ret:+.2f}%)"
            }
        except Exception as e:
            logger.debug(f"Constituent validation error: {e}")
            return {"allow": True, "reason": "Constituent validation skipped on error"}


# Global singleton instance
component_leader_engine = ComponentLeaderEngine()
