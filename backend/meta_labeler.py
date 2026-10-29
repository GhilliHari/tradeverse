import logging
import numpy as np
import os
import joblib

try:
    import numpy.random._pickle as _np_pickle
    from numpy.random import PCG64 as _OrigPCG64

    class PCG64(_OrigPCG64):
        def __setstate__(self, state):
            if isinstance(state, tuple):
                state = state[0]
            super().__setstate__(state)

    _np_pickle.BitGenerators['PCG64'] = PCG64
    _np_pickle.BitGenerators[_OrigPCG64] = PCG64
    _np_pickle.BitGenerators[PCG64] = PCG64
    _orig_bg_ctor = _np_pickle.__bit_generator_ctor

    def _compat_bg_ctor(bg='MT19937'):
        if isinstance(bg, _OrigPCG64):
            return bg
        if bg in _np_pickle.BitGenerators:
            return _np_pickle.BitGenerators[bg]()
        return _orig_bg_ctor(bg)

    _np_pickle.__bit_generator_ctor = _compat_bg_ctor
    _orig_gen_ctor = _np_pickle.__generator_ctor
    _np_pickle.__generator_ctor = lambda bg='MT19937', bg_ctor=_compat_bg_ctor: _orig_gen_ctor(bg, _compat_bg_ctor)
except Exception:
    pass

logger = logging.getLogger("MetaLabeler")

class MetaLabeler:
    """
    ML Layer 2: Vets signals from the primary ModelEngine.
    Implements a trained classifier to predict the probability of success.
    Falls back to a 'Probability of Success' rule-based logic if no trained model exists.
    """
    
    def __init__(self):
        # Coefficients derived from 'Pseudo-Optimization' on institutional data
        self.weights = {
            "reg_trending": 0.15,
            "reg_volatile": -0.20,
            "causal_support": 0.25,
            "comp_alignment": 0.20,
            "price_smoothed": 0.10,
            "gex_proximity": -0.15
        }
        self.model = None
        self.load_model()

    def load_model(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "meta_model.joblib")
        if os.path.exists(path):
            try:
                self.model = joblib.load(path)
                logger.info("Loaded trained Meta-Labeler model successfully.")
            except Exception as e:
                logger.warning(f"Failed to load Meta-Labeler model: {e}")

    def train(self, X_meta, y_meta):
        """
        Trains the Meta-Labeler using features (X_meta) and binary outcomes (y_meta).
        """
        from sklearn.ensemble import RandomForestClassifier
        logger.info(f"Training ML Meta-Labeler Classifier on {len(X_meta)} trades...")
        
        # Keep depth shallow to prevent overfitting on trade occurrences
        self.model = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42, class_weight='balanced', n_jobs=-1)
        self.model.fit(X_meta, y_meta)
        
        # Save model
        base_dir = os.path.dirname(os.path.abspath(__file__))
        joblib.dump(self.model, os.path.join(base_dir, "meta_model.joblib"))
        logger.info("Meta-Labeler model saved successfully.")

    def vet_signal(self, signal, confidence, tech_ctx, component_alpha, gex_data, features_row=None):
        """
        Calculates the probability of the signal being 'Correct' (Success Probability).
        If a trained ML model is available, uses it. Otherwise falls back to rule-based heuristics.
        """
        if signal == "HOLD":
            return 0.0
            
        # If ML model is trained and features are provided, use ML prediction
        if self.model is not None and features_row is not None:
            try:
                # Expecting features_row to be pre-scaled and contain the exact features matching the trained model
                # Ensure features_row is 2D
                if len(features_row.shape) == 1:
                    features_row = features_row.reshape(1, -1)
                prob = self.model.predict_proba(features_row)[:, 1][0]
                logger.info(f"ML Meta-Labeler Vetting: Signal={signal}, Prob={prob:.2f}")
                return float(prob)
            except Exception as e:
                logger.warning(f"Error in ML Meta-Labeler prediction, falling back to rule-based: {e}")

        # Fallback to rule-based
        score = confidence / 100.0
        regime = tech_ctx.get('regime', 'NOMINAL')
        causal_strength = tech_ctx.get('causal_strength', 0.5)
        comp_score = component_alpha.get('score', 0)
        
        if regime == "TRENDING_INTRADAY":
            if (signal == "BUY" and comp_score > 0.3) or (signal == "SELL" and comp_score < -0.3):
                score += 0.25
            if causal_strength > 0.7:
                score += 0.20
            elif causal_strength < 0.3:
                score -= 0.15
        elif regime in ["RANGE_BOUND", "LUNCH_LULL"]:
            if abs(comp_score) > 0.7:
                score -= 0.20
            pcr = gex_data.get('pcr', 1.0)
            if (signal == "BUY" and pcr > 1.2) or (signal == "SELL" and pcr < 0.8):
                score += 0.15
        elif regime == "OPENING_VOLATILITY":
            if abs(comp_score) < 0.5:
                score -= 0.10
            else:
                score += 0.10
                
        # GEX Proximity Penalty
        ltp = tech_ctx.get('ltp', 0)
        if ltp > 0:
            call_wall = gex_data.get('call_wall', 0)
            put_wall = gex_data.get('put_wall', 0)
            if signal == "BUY" and 0 < (call_wall - ltp) < 40:
                score -= 0.30
            elif signal == "SELL" and 0 < (ltp - put_wall) < 40:
                score -= 0.30

        success_prob = 1 / (1 + np.exp(-12 * (score - 0.55)))
        logger.info(f"Fallback Meta-Labeler Vetting: Signal={signal}, Regime={regime}, Prob={success_prob:.2f}")
        return float(success_prob)

    def get_vetted_signal(self, signal, confidence, tech_ctx, component_alpha, gex_data, threshold=0.65, features_row=None):
        prob = self.vet_signal(signal, confidence, tech_ctx, component_alpha, gex_data, features_row=features_row)
        if prob >= threshold:
            return signal, prob
        else:
            return "HOLD", prob
