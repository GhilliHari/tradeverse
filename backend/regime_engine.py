"""
Intraday Regime Classification Engine for Bank Nifty F&O Trading

This module classifies market regimes throughout the trading day to enable
regime-adaptive trading strategies. Different regimes require different approaches.

Regime Types:
1. OPENING_VOLATILITY (9:15-9:45): High volatility, wide spreads
2. TRENDING_INTRADAY (9:45-14:30): Directional moves, trend following
3. RANGE_BOUND (10:00-14:00): Sideways, mean reversion
4. LUNCH_LULL (12:00-13:30): Low volume, avoid trading
5. POWER_HOUR (14:30-15:15): Volume spike, momentum trades
6. CLOSING_SQUEEZE (15:15-15:30): Square-off pressure, exit positions

Author: Tradeverse AI
"""

import numpy as np
import pandas as pd
from datetime import datetime, time
from hmmlearn.hmm import GaussianHMM
import logging
from typing import Dict, Tuple, Optional
import joblib
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegimeEngine")


class IntradayRegimeEngine:
    """
    Intraday Regime Classification Engine for Bank Nifty.
    
    Uses a combination of:
    - Time-based rules (market opens/closes, lunch hour)
    - Hidden Markov Models (HMM) for feature-based classification
    - Technical indicators (ADX, ATR, Volume)
    """
    
    def __init__(self, n_regimes: int = 6):
        """
        Initialize the regime engine.
        
        Args:
            n_regimes: Number of regimes to detect (default 6)
        """
        self.n_regimes = n_regimes
        self.hmm = GaussianHMM(
            n_components=n_regimes, 
            covariance_type="full", 
            n_iter=100,
            random_state=42
        )
        self.is_trained = False
        
        # Regime mapping (HMM state ID -> Regime name)
        self.regime_map = {
            0: "OPENING_VOLATILITY",
            1: "TRENDING_INTRADAY",
            2: "RANGE_BOUND",
            3: "LUNCH_LULL",
            4: "POWER_HOUR",
            5: "CLOSING_SQUEEZE"
        }
        
        # Reverse mapping
        self.regime_to_id = {v: k for k, v in self.regime_map.items()}
        
        # Normalization stats
        self.means = None
        self.stds = None
        
        # Model path
        self.model_path = os.path.join(os.path.dirname(__file__), "models", "regime_hmm.joblib")
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Regime characteristics for validation
        self.regime_characteristics = {
            "OPENING_VOLATILITY": {"atr_percentile": 0.8, "volume_percentile": 0.7},
            "TRENDING_INTRADAY": {"adx_min": 20, "volume_percentile": 0.5},
            "RANGE_BOUND": {"adx_max": 20, "bb_width_percentile": 0.3},
            "LUNCH_LULL": {"volume_percentile": 0.3, "atr_percentile": 0.4},
            "POWER_HOUR": {"volume_percentile": 0.8, "atr_percentile": 0.6},
            "CLOSING_SQUEEZE": {"volume_percentile": 0.9, "atr_percentile": 0.7}
        }
    
    def fit(self, data: pd.DataFrame):
        """
        Train the HMM on historical intraday data.
        
        Args:
            data: DataFrame with columns: ATR_14, ADX, Volume, BB_STD
        """
        required_cols = ['ATR_14', 'ADX', 'Volume', 'BB_STD']
        
        # Validate columns
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            logger.error(f"Missing columns for regime training: {missing_cols}")
            return False
        
        # Prepare features
        features = data[required_cols].copy()
        
        # Normalize features (z-score)
        features_normalized = (features - features.mean()) / features.std()
        features_normalized = features_normalized.fillna(0)
        
        # Remove any remaining NaN/Inf
        features_normalized = features_normalized.replace([np.inf, -np.inf], 0)
        
        if len(features_normalized) < 100:
            logger.warning(f"Insufficient data for HMM training ({len(features_normalized)} rows)")
            return False
        
        try:
            logger.info(f"Training HMM with {len(features_normalized)} samples...")
            self.hmm.fit(features_normalized.values)
            self.is_trained = True
            
            # Store normalization stats
            self.means = features.mean().to_dict()
            self.stds = features.std().to_dict()
            
            logger.info("✅ HMM training complete")
            return True
        except Exception as e:
            logger.error(f"HMM training failed: {e}")
            return False

    def save_model(self):
        """Saves the trained HMM and normalization stats."""
        if not self.is_trained:
            logger.warning("Attempted to save untrained model.")
            return False
            
        try:
            model_data = {
                "hmm": self.hmm,
                "means": self.means,
                "stds": self.stds,
                "n_regimes": self.n_regimes
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"✅ Regime model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save regime model: {e}")
            return False

    def load_model(self):
        """Loads the trained HMM and normalization stats."""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file not found: {self.model_path}")
            return False
            
        try:
            model_data = joblib.load(self.model_path)
            self.hmm = model_data["hmm"]
            self.means = model_data["means"]
            self.stds = model_data["stds"]
            self.n_regimes = model_data.get("n_regimes", 6)
            self.is_trained = True
            logger.info(f"✅ Regime model loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load regime model: {e}")
            return False
    
    def _get_time_based_regime(self, current_time: datetime) -> str:
        """
        Determine regime based purely on time of day.
        
        Args:
            current_time: Current datetime
            
        Returns:
            Regime name or None if no time-based override
        """
        hour = current_time.hour
        minute = current_time.minute
        
        # Opening volatility (9:15 - 9:45)
        if hour == 9 and minute < 45:
            return "OPENING_VOLATILITY"
        
        # Lunch lull (12:00 - 13:30)
        if (hour == 12) or (hour == 13 and minute < 30):
            return "LUNCH_LULL"
        
        # Power hour (14:30 - 15:15)
        if (hour == 14 and minute >= 30) or (hour == 15 and minute < 15):
            return "POWER_HOUR"
        
        # Closing squeeze (15:15 - 15:30)
        if hour == 15 and minute >= 15:
            return "CLOSING_SQUEEZE"
        
        return None  # No time-based override
    
    def classify_regime(self, current_time: datetime, features: pd.Series) -> str:
        """
        Classify the current market regime.
        
        Args:
            current_time: Current datetime
            features: Series with ATR_14, ADX, Volume, BB_STD
            
        Returns:
            Regime name (e.g., "TRENDING_INTRADAY")
        """
        # 1. Check time-based override first
        time_regime = self._get_time_based_regime(current_time)
        if time_regime:
            return time_regime
        
        # 2. Use HMM for feature-based classification
        if not self.is_trained:
            logger.warning("HMM not trained. Defaulting to RANGE_BOUND.")
            return "RANGE_BOUND"
        
        try:
            # Prepare features
            required_cols = ['ATR_14', 'ADX', 'Volume', 'BB_STD']
            feature_values = features[required_cols].values.reshape(1, -1)
            
            # Use stored normalization stats
            if self.means and self.stds:
                means_vec = np.array([self.means[c] for c in required_cols])
                stds_vec = np.array([self.stds[c] for c in required_cols])
                feature_values = (feature_values - means_vec) / (stds_vec + 1e-8)
            else:
                # Fallback to local normalization (not ideal for out-of-sample)
                feature_values = (feature_values - np.mean(feature_values)) / (np.std(feature_values) + 1e-8)
            
            # Predict regime
            regime_id = self.hmm.predict(feature_values)[0]
            regime_name = self.regime_map.get(regime_id, "RANGE_BOUND")
            
            return regime_name
            
        except Exception as e:
            logger.error(f"Regime classification failed: {e}")
            return "RANGE_BOUND"  # Safe default
    
    def get_regime_probability(self, features: pd.Series) -> Dict[str, float]:
        """
        Get probability distribution over all regimes.
        
        Args:
            features: Series with ATR_14, ADX, Volume, BB_STD
            
        Returns:
            Dict mapping regime names to probabilities
        """
        if not self.is_trained:
            return {regime: 1.0/self.n_regimes for regime in self.regime_map.values()}
        
        try:
            required_cols = ['ATR_14', 'ADX', 'Volume', 'BB_STD']
            feature_values = features[required_cols].values.reshape(1, -1)
            feature_values = (feature_values - np.mean(feature_values)) / (np.std(feature_values) + 1e-8)
            
            # Get log probabilities
            log_probs = self.hmm.score_samples(feature_values)[0]
            
            # Convert to probabilities
            probs = np.exp(log_probs)
            probs = probs / probs.sum()
            
            return {self.regime_map[i]: float(probs[i]) for i in range(self.n_regimes)}
            
        except Exception as e:
            logger.error(f"Probability calculation failed: {e}")
            return {regime: 1.0/self.n_regimes for regime in self.regime_map.values()}
    
    def get_regime_transition_matrix(self) -> np.ndarray:
        """
        Get the regime transition probability matrix.
        
        Returns:
            NxN matrix where element [i,j] is P(regime_j | regime_i)
        """
        if not self.is_trained:
            logger.warning("HMM not trained. Returning uniform transition matrix.")
            return np.ones((self.n_regimes, self.n_regimes)) / self.n_regimes
        
        return self.hmm.transmat_
    
    def get_regime_characteristics(self, regime: str) -> Dict:
        """
        Get the expected characteristics of a regime.
        
        Args:
            regime: Regime name
            
        Returns:
            Dict with expected ATR, ADX, Volume percentiles
        """
        return self.regime_characteristics.get(regime, {})
    
    def get_trading_strategy(self, regime: str) -> Dict[str, str]:
        """
        Get recommended trading strategy for a regime.
        
        Args:
            regime: Regime name
            
        Returns:
            Dict with strategy recommendations
        """
        strategies = {
            "OPENING_VOLATILITY": {
                "approach": "AVOID or SCALP",
                "entry": "Wait for volatility to settle",
                "exit": "Quick exits, tight stops",
                "position_size": "Reduce by 50%"
            },
            "TRENDING_INTRADAY": {
                "approach": "TREND FOLLOWING",
                "entry": "Breakouts, pullbacks to VWAP",
                "exit": "Trailing stops, target extensions",
                "position_size": "Full size"
            },
            "RANGE_BOUND": {
                "approach": "MEAN REVERSION",
                "entry": "Oversold/overbought, support/resistance",
                "exit": "Mean reversion to VWAP",
                "position_size": "Full size"
            },
            "LUNCH_LULL": {
                "approach": "AVOID",
                "entry": "No new positions",
                "exit": "Hold existing, tight stops",
                "position_size": "0%"
            },
            "POWER_HOUR": {
                "approach": "MOMENTUM",
                "entry": "Volume spikes, directional bias",
                "exit": "Ride momentum, wider stops",
                "position_size": "Full size"
            },
            "CLOSING_SQUEEZE": {
                "approach": "EXIT ALL",
                "entry": "No new positions",
                "exit": "Square off all positions by 3:15 PM",
                "position_size": "0%"
            }
        }
        
        return strategies.get(regime, strategies["RANGE_BOUND"])


# Standalone test function
if __name__ == "__main__":
    logger.info("Testing IntradayRegimeEngine...")
    
    # Create sample intraday data
    np.random.seed(42)
    n = 1000
    
    dates = pd.date_range('2024-01-15 09:15', periods=n, freq='5min')
    
    # Simulate different regimes throughout the day
    data = pd.DataFrame({
        'ATR_14': np.random.uniform(50, 200, n),
        'ADX': np.random.uniform(10, 40, n),
        'Volume': np.random.randint(1000, 50000, n),
        'BB_STD': np.random.uniform(20, 100, n)
    }, index=dates)
    
    # Train regime engine
    engine = IntradayRegimeEngine()
    success = engine.fit(data)
    
    if success:
        print("\n" + "="*60)
        print("REGIME ENGINE TEST RESULTS")
        print("="*60)
        
        # Test at different times
        test_times = [
            datetime(2024, 1, 15, 9, 30),   # Opening
            datetime(2024, 1, 15, 10, 30),  # Mid-morning
            datetime(2024, 1, 15, 12, 30),  # Lunch
            datetime(2024, 1, 15, 14, 45),  # Power hour
            datetime(2024, 1, 15, 15, 20),  # Closing
        ]
        
        for test_time in test_times:
            regime = engine.classify_regime(test_time, data.iloc[-1])
            strategy = engine.get_trading_strategy(regime)
            
            print(f"\nTime: {test_time.strftime('%H:%M')}")
            print(f"Regime: {regime}")
            print(f"Strategy: {strategy['approach']}")
            print(f"Position Size: {strategy['position_size']}")
        
        print("\n" + "="*60)
        print("Transition Matrix (first 3x3):")
        print(engine.get_regime_transition_matrix()[:3, :3])
        print("="*60)
    else:
        print("❌ Training failed")
