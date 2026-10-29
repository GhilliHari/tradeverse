import numpy as np
import logging

logger = logging.getLogger("StrategyOptimizer")

class StrategyOptimizer:
    """
    Calculates dynamic entry/exit parameters for Tradeverse.
    """
    
    @staticmethod
    def calculate_tsl(entry_price, current_price, side, atr, regime="NOMINAL", is_premium=False, profit_pct=0.0):
        """
        Calculates the Trailing Stop Loss level.
        If profit_pct > 20%, 'Alpha Lock' activates, tightening the SL.
        """
        # Padding SL in VOLATILE regimes
        multiplier = 2.0 if regime == "VOLATILE" else 1.5
        
        # --- NEW: Trailing Alpha Lock ---
        # If we have captured significant alpha (>20%), tighten the SL multiplier
        # to lock in profits and prevent a 'winner-to-loser' reversal.
        if profit_pct >= 20.0:
            multiplier = 0.8 # Tighten to sub-ATR level
            logger.info(f"⚡ Trailing Alpha Lock Activated (Profit: {profit_pct:.1f}%). Tightening SL...")
        
        # If trading premium directly, ATR is spot-based, so we must approximate Premium ATR
        # Usually, Delta * Spot ATR = Premium ATR. (We estimate Delta ~0.5 for ATM)
        risk_dist = (atr * 0.5 * multiplier) if is_premium else (atr * multiplier)
        
        if side == "BUY":
            potential_tsl = current_price - risk_dist
            return max(entry_price - risk_dist, potential_tsl)
        else: # SELL / PUT
            if is_premium:
                potential_tsl = current_price - risk_dist
                return max(entry_price - risk_dist, potential_tsl)
            else:
                potential_tsl = current_price + risk_dist
                return min(entry_price + risk_dist, potential_tsl)


    @staticmethod
    def calculate_targets(price, side, atr, pivot_levels=None, regime="NOMINAL", gex_data=None, is_premium=False, is_expiry=False):
        """
        Calculates Take Profit targets based on regime capacity and GEX walls.
        If is_premium=True, targets are calculated based on Option Premium gain percentages.
        """
        targets = []
        
        if is_premium:
            # For Premium, we target absolute percentage gains (e.g. 15%, 30%)
            # adjusted slightly by regime
            # Expiry Day: Target much higher moves (Gamma)
            base_target = 0.40 if is_expiry else 0.15 
            
            if regime == "TRENDING_INTRADAY" or (is_expiry and regime == "VOLATILE"):
                targets.append(price * (1 + base_target * 1.5)) 
                targets.append(price * (1 + base_target * 3.0)) 
            else:
                targets.append(price * (1 + base_target)) 
                targets.append(price * (1 + base_target * 2.0)) 
            
            return sorted(list(set(targets))) # Always rising if premium
            
        else:
            # Base ATR multiples adjusted by regime (Spot Logic)
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
    def calculate_convergence_score(signals, regime="NOMINAL"):
        """
        signals: Dict of factor -> score/label
        regime: Current market regime (NOMINAL, VOLATILE, TRENDING, etc.)
        Returns a tuple of (aggregate_score, component_scores)
        """
        # --- NEW: Dynamic Regime-Based Weighting (Neural Core Upgrade) ---
        # Default Weights
        weights = {
            "technical": 0.35,  # AI Model Prediction
            "tft": 0.15,       # Temporal Context
            "rl": 0.10,        # Sniper Timing
            "sentiment": 0.10, # News/Social
            "options": 0.10,   # PCR/OI
            "order_flow": 0.15, # Real-time Bid/Ask Level-2 Tape
            "macro": 0.05      # Global Cues (USDINR, Brent, DXY)
        }

        # Override weights based on regime for better predictive accuracy
        if regime == "VOLATILE" or regime == "OPENING_VOLATILITY":
            # In volatility, prioritize real-time signals and noise-resistant RL
            weights = {
                "technical": 0.20,
                "tft": 0.10,
                "rl": 0.25,      # RL is better at handling chaotic price action
                "sentiment": 0.05,
                "options": 0.10,
                "order_flow": 0.30, # Level-2 is the truth in volatility
                "macro": 0.05
            }
        elif regime == "TRENDING_INTRADAY" or regime == "POWER_HOUR_TREND":
            # In strong trends, prioritize Macro (Sentiment) and AI confidence
            weights = {
                "technical": 0.40,
                "tft": 0.20,
                "rl": 0.05,
                "sentiment": 0.20, # News drives trends
                "options": 0.05,
                "order_flow": 0.05,
                "macro": 0.10      # Macro leads long trends
            }
        elif regime == "RANGE_BOUND" or regime == "LUNCH_LULL":
            # In range-bound markets, prioritize mean-reversion (Options/Order Flow)
            weights = {
                "technical": 0.15,
                "tft": 0.10,
                "rl": 0.15,
                "sentiment": 0.05,
                "options": 0.25, # High PCR/Low PCR drives reversals
                "order_flow": 0.30
            }
        
        score = 0.0
        details = {k: 0.0 for k in weights.keys()}
        
        # Mapping logic (Refined with confidence scaling)
        # Technical
        if signals.get('tech_pred') == "UP": 
            score += weights['technical']
            details['technical'] = 1.0
        elif signals.get('tech_pred') == "DOWN": 
            score -= weights['technical']
            details['technical'] = -1.0
        
        # TFT
        if signals.get('tft_pred') == "UP": 
            score += weights['tft']
            details['tft'] = 1.0
        elif signals.get('tft_pred') == "DOWN": 
            score -= weights['tft']
            details['tft'] = -1.0
        
        # RL Sniper
        if signals.get('rl_action') == 1: 
            score += weights['rl']
            details['rl'] = 1.0
        elif signals.get('rl_action') == 2: 
            score -= weights['rl']
            details['rl'] = -1.0
        
        # Sentiment (Continuous score -1.0 to 1.0)
        sent_val = signals.get('sentiment_score', 0)
        score += (sent_val * weights['sentiment'])
        details['sentiment'] = sent_val
        
        # Options (PCR Mapping: High PCR = Put Writing = Bullish Support, Low PCR = Call Writing = Bearish Resistance)
        pcr = signals.get('pcr', 1.0)
        if pcr > 1.15: 
            pcr_str = 1.0 if pcr > 1.3 else 0.5 # Strong vs moderate bullish floor
            score += (pcr_str * weights['options'])
            details['options'] = pcr_str
        elif pcr < 0.85: 
            pcr_str = -1.0 if pcr < 0.7 else -0.5 # Strong vs moderate bearish ceiling
            score -= (abs(pcr_str) * weights['options'])
            details['options'] = pcr_str
            
        # Order Flow
        flow = signals.get('order_flow_signal', 'NEUTRAL')
        if flow == "UP":
            score += weights['order_flow']
            details['order_flow'] = 1.0
        elif flow == "DOWN":
            score -= weights['order_flow']
            details['order_flow'] = -1.0
            
        # Macro
        macro_sig = signals.get('macro_signal', 'NEUTRAL')
        if macro_sig == "BULLISH" and 'macro' in weights:
            score += weights['macro']
            details['macro'] = 1.0
        elif macro_sig == "BEARISH" and 'macro' in weights:
            score -= weights['macro']
            details['macro'] = -1.0
            
        # Technical Momentum Confirmation (VWAP & EMA Alignment)
        tech_context = signals.get('tech_context', {})
        ltp = tech_context.get('ltp', 0)
        vwap = tech_context.get('vwap', 0)
        ema_9 = tech_context.get('ema_9', 0)
        ema_21 = tech_context.get('ema_21', 0)
        
        if ltp > 0 and vwap > 0:
            if ltp > vwap and ema_9 > ema_21:
                score += 0.10 # Bullish momentum confirmation
            elif ltp < vwap and ema_9 < ema_21:
                score -= 0.10 # Bearish momentum confirmation

        # --- PILLAR ENHANCEMENTS: Astro, Pattern & Component Leadership ---
        astro_val = signals.get('astro_score', 0.0)
        if astro_val != 0:
            score += (astro_val * 0.08)
            details['astro'] = astro_val

        pattern_val = signals.get('pattern_score', 0.0)
        if pattern_val != 0:
            score += (pattern_val * 0.12)
            details['pattern'] = pattern_val

        comp_lead_val = signals.get('component_lead_score', 0.0)
        if comp_lead_val != 0:
            score += (comp_lead_val * 0.15) # Heavyweight HDFC + ICICI Bank leadership
            details['component_lead'] = comp_lead_val

        # --- ADVANCED VETO LOGIC ---
        # 1. Tech vs Flow Veto
        tech = signals.get('tech_pred')
        if tech == "UP" and flow == "DOWN":
            score -= 0.35 # Heavy penalty
            details['order_flow'] -= 0.5
        elif tech == "DOWN" and flow == "UP":
            score += 0.35
            details['order_flow'] += 0.5

        # 2. Options Extreme Veto (Contrarian Reversal)
        if pcr > 1.6 and tech == "UP":
            # Extremely overbought Put-Call ratio: Bull trap risk
            score *= 0.5 
            logger.warning("⚠️ Consensus: Bull Trap Risk Detected (Extreme High PCR)")
        elif pcr < 0.5 and tech == "DOWN":
            # Extremely oversold Put-Call ratio: Bear trap risk
            score *= 0.5
            logger.warning("⚠️ Consensus: Bear Trap Risk Detected (Extreme Low PCR)")

        # 3. Regimeconviction scaling
        if regime == "RANGE_BOUND":
            score *= 0.65 # Reduce absolute conviction by 35%
        elif regime == "LUNCH_LULL" or regime == "CLOSING_SQUEEZE":
            score *= 0.50 # Reduce absolute conviction by 50%
        
        return score, details
