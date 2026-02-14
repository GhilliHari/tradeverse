import logging
import numpy as np

logger = logging.getLogger("MetaLabeler")

class MetaLabeler:
    """
    ML Layer 2: Vets signals from the primary ModelEngine.
    Implements a 'Probability of Success' logic based on institutional patterns.
    """
    
    def __init__(self):
        # Coefficients derived from 'Pseudo-Optimization' on institutional data
        self.weights = {
            "reg_trending": 0.15,
            "reg_volatile": -0.20,
            "causal_support": 0.25,
            "comp_alignment": 0.20,
            "price_smoothed": 0.10,
            "gex_proximity": -0.15  # Negative if too close to a wall
        }

    def vet_signal(self, signal, confidence, tech_ctx, component_alpha, gex_data):
        """
        Calculates the probability of the signal being 'Correct' (Success Probability).
        Regime-aware weighting:
        - TRENDING: Prioritizes Causal Strength and Component Alignment.
        - RANGE_BOUND: Prioritizes RSI/Pivots (Simulated) and GEX stability.
        """
        if signal == "HOLD":
            return 0.0
            
        # 1. Base Score from primary confidence
        score = confidence / 100.0
        
        regime = tech_ctx.get('regime', 'NOMINAL')
        causal_strength = tech_ctx.get('causal_strength', 0.5)
        comp_score = component_alpha.get('score', 0)
        
        # 2. Regime-Specific Weighting
        if regime == "TRENDING_INTRADAY":
            # Growth factor: Align with components and causality
            if (signal == "BUY" and comp_score > 0.3) or (signal == "SELL" and comp_score < -0.3):
                score += 0.25 # Trend alignment bonus
            
            if causal_strength > 0.7:
                score += 0.20 # Causal confirmation
            elif causal_strength < 0.3:
                score -= 0.15 # Trend lack of support
                
        elif regime in ["RANGE_BOUND", "LUNCH_LULL"]:
            # Reversion factor: Penalize if too far from 'Mean' (simplified here)
            # and bonus for GEX stability
            if abs(comp_score) > 0.7:
                score -= 0.20 # Over-extended for range-bound
            
            pcr = gex_data.get('pcr', 1.0)
            if (signal == "BUY" and pcr > 1.2) or (signal == "SELL" and pcr < 0.8):
                score += 0.15 # Option-chain contrarian support
        
        elif regime == "OPENING_VOLATILITY":
            # High volatility: Require extra high component conviction
            if abs(comp_score) < 0.5:
                score -= 0.10 # Uncertainty penalty
            else:
                score += 0.10 # Strong directional opening
        
        # 3. GEX Proximity Penalty (Wait for wall clearance)
        ltp = tech_ctx.get('ltp', 0)
        if ltp > 0:
            call_wall = gex_data.get('call_wall', 0)
            put_wall = gex_data.get('put_wall', 0)
            
            if signal == "BUY" and 0 < (call_wall - ltp) < 40:
                score -= 0.30 # Serious penalty for BUY into resistance
            elif signal == "SELL" and 0 < (ltp - put_wall) < 40:
                score -= 0.30 # Serious penalty for SELL into support

        # 4. Apply Sigmoid for normalized probability [0, 1]
        # Sharpening the sigmoid for higher selectivity
        success_prob = 1 / (1 + np.exp(-12 * (score - 0.55)))
        
        logger.info(f"Meta-Labeler Vetting: Signal={signal}, Regime={regime}, Prob={success_prob:.2f}")
        
        return float(success_prob)

    def get_vetted_signal(self, signal, confidence, tech_ctx, component_alpha, gex_data, threshold=0.65):
        """
        Returns the signal only if it passes the success probability threshold.
        """
        prob = self.vet_signal(signal, confidence, tech_ctx, component_alpha, gex_data)
        
        if prob >= threshold:
            return signal, prob
        else:
            return "HOLD", prob
