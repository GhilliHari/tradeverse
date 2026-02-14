import numpy as np
import logging

logger = logging.getLogger("StrategyOptimizer")

class StrategyOptimizer:
    """
    Calculates dynamic entry/exit parameters for Tradeverse.
    """
    
    @staticmethod
    def calculate_tsl(entry_price, current_price, side, atr, regime="NOMINAL"):
        """
        Calculates the Trailing Stop Loss level with regime-aware padding.
        """
        # Padding SL in VOLATILE regimes to avoid being stopped out by noise
        multiplier = 2.0 if regime == "VOLATILE" else 1.5
        risk_dist = atr * multiplier
        
        if side == "BUY":
            potential_tsl = current_price - risk_dist
            return max(entry_price - risk_dist, potential_tsl)
        else: # SELL
            potential_tsl = current_price + risk_dist
            return min(entry_price + risk_dist, potential_tsl)

    @staticmethod
    def calculate_targets(price, side, atr, pivot_levels=None, regime="NOMINAL", gex_data=None):
        """
        Calculates Take Profit targets based on regime capacity and GEX walls.
        """
        targets = []
        
        # Base ATR multiples adjusted by regime
        if regime == "TRENDING_INTRADAY":
            targets.append(price + (atr * 3.0) if side == "BUY" else price - (atr * 3.0))
            targets.append(price + (atr * 5.0) if side == "BUY" else price - (atr * 5.0))
        else: # NOMINAL or SIDEWAYS
            targets.append(price + (atr * 1.5) if side == "BUY" else price - (atr * 1.5))
            targets.append(price + (atr * 2.5) if side == "BUY" else price - (atr * 2.5))
        
        # Incorporate Pivot Levels with regime filtering
        if pivot_levels:
            if side == "BUY":
                if pivot_levels.get('R1'): targets.append(pivot_levels['R1'])
                if regime == "TRENDING_INTRADAY" and pivot_levels.get('R2'): 
                    targets.append(pivot_levels['R2'])
            else:
                if pivot_levels.get('S1'): targets.append(pivot_levels['S1'])
                if regime == "TRENDING_INTRADAY" and pivot_levels.get('S2'): 
                    targets.append(pivot_levels['S2'])
                    
        # --- NEW: GEX-Optimized Exits (Phase 5) ---
        if gex_data:
            if side == "BUY":
                call_wall = gex_data.get('call_wall', 0)
                if call_wall > price:
                    targets.append(call_wall - 10) # Exit slightly before the wall
            else:
                put_wall = gex_data.get('put_wall', 0)
                if 0 < put_wall < price:
                    targets.append(put_wall + 10) # Exit slightly before the wall
        
        return sorted(list(set(targets)), reverse=(side == "SELL"))

    @staticmethod
    def calculate_convergence_score(signals):
        """
        signals: Dict of factor -> score/label
        Returns a tuple of (aggregate_score, component_scores)
        """
        weights = {
            "technical": 0.40,  # AI Model Prediction
            "tft": 0.20,       # Temporal Context
            "rl": 0.15,        # Sniper Timing
            "sentiment": 0.15, # News/Social
            "options": 0.10    # PCR/OI
        }
        
        score = 0.0
        details = {k: 0.0 for k in weights.keys()}
        
        # Mapping logic
        if signals.get('tech_pred') == "UP": 
            score += weights['technical']
            details['technical'] = 1.0
        elif signals.get('tech_pred') == "DOWN": 
            score -= weights['technical']
            details['technical'] = -1.0
        
        if signals.get('tft_pred') == "UP": 
            score += weights['tft']
            details['tft'] = 1.0
        elif signals.get('tft_pred') == "DOWN": 
            score -= weights['tft']
            details['tft'] = -1.0
        
        if signals.get('rl_action') == 1: 
            score += weights['rl']
            details['rl'] = 1.0
        elif signals.get('rl_action') == 2: 
            score -= weights['rl']
            details['rl'] = -1.0
        
        sent_val = signals.get('sentiment_score', 0)
        score += (sent_val * weights['sentiment'])
        details['sentiment'] = sent_val
        
        pcr = signals.get('pcr', 1.0)
        if pcr < 0.85: 
            score += weights['options']
            details['options'] = 1.0
        elif pcr > 1.15: 
            score -= weights['options']
            details['options'] = -1.0
        
        return score, details
