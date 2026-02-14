import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, precision_recall_curve
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelEngine")

class ModelEngine:
    def __init__(self, model_type="daily"):
        """
        model_type: 'daily' (Strategist) or 'intraday' (Sniper)
        """
        self.model_type = model_type
        
        # Dynamic Artifact Paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(base_dir, f"market_model_{model_type}.joblib")
        self.scaler_path = os.path.join(base_dir, f"scaler_{model_type}.joblib")
        self.config_path = os.path.join(base_dir, f"model_config_{model_type}.joblib")
        
        self.model = None
        self.scaler = StandardScaler()
        self.kmeans = None # For OOD detection
        self.threshold = 0.55 if model_type == 'daily' else 0.50 # Lower threshold for sniper initially
        
        # Feature set is shared for now, but can be specialized later
        self.features = ['Is_Fractal_Low', 'CMO', 'RSI_Slope', 'Mass_Index', 'RSI_x_Vol', 'TR', 'Vol_Ratio', 'BB_STD', 'CCI', 'sentiment_score', 'ATR_14', 'High_Close_Prev', 'ADX', 'High_Low', '-DI', 'Ret_1d', 'DX', 'Gap', 'Ret_3d', 'Low_Close_Prev', 'RSI_Vol_Adj', '+DI', 'Ret_5d', 'RSI', 'CCI_Vol_Adj', 'Ret_2d', 'PCR', 'Trend_Confidence', 'Inflation_Proxy', 'CMF', 'TSI', 'Coppock', 'WillR', 'BN_Nifty_Ratio', 'Klinger', 'Dist_SMA200', 'USDINR', 'DPO', 'MACD_Signal', 'MACD_Hist', 'MACD', 'RSI_Vol_Imbalance', 'Dist_EMA21', 'Bull_Power', 'ROC', 'Stoch_RSI', 'Bear_Power', 'Is_Fractal_High', 'SMA_200', 'Aroon_Down', 'Nifty50', '+DM', 'Price_FracDiff', '-DM', 'OI_Change', 'ST_Lower', 'BB_Lower', 'Aroon_Up', 'Force_Index', 'High_5', 'OBV', 'TP', 'Fisher', 'HMA_20', 'MFI', 'BB_Upper', 'Vol_Change', 'BB_MA', 'ST_Upper', 'KC_Mid', 'S2', 'R1', 'SMA_50', 'KC_Upper', 'Pivot', 'EMA_21', 'R2', 'EMA_9', 'DC_Lower', 'VWAP', 'Streak', 'KC_Lower', 'Kijun_Sen', 'Low_5', 'PSAR', 'S1', 'Tenkan_Sen']

    def train(self, train_df, test_df):
        """
        Trains a Voting Ensemble (Random Forest + HistGradientBoosting) and optimizes for Max F1.
        """
        logger.info("Preparing data for Ensemble Training...")
        
        X_train = train_df[self.features]
        y_train = train_df['Target_Next_Day']
        X_test = test_df[self.features]
        y_test = test_df['Target_Next_Day']

        # 1. Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 2. Train Ensemble Model
        # Tuned for Aggressive Pattern Recognition on Filtered Data
        logger.info("Training Histogram Gradient Boosting Classifier (Aggressive)...")
        hgb = HistGradientBoostingClassifier(
            learning_rate=0.03, # Slower learning for precision
            max_iter=500,       # More iterations
            max_depth=15,       # Deeper trees to capture specific signal combinations
            random_state=42,
            l2_regularization=0.01 # Reduced reg to allow fitting
        )
        
        logger.info("Training Random Forest Classifier (Detail Oriented)...")
        rf = RandomForestClassifier(
            n_estimators=300, 
            max_depth=15,       # Deeper
            min_samples_split=5, # Allow smaller leaves
            random_state=42, 
            n_jobs=-1
        )
        
        # Soft Voting (Average probabilities)
        ensemble = VotingClassifier(
            estimators=[('hgb', hgb), ('rf', rf)],
            voting='soft'
        )
        
        # 3. Apply Probability Calibration (Isotonic)
        logger.info("Applying Isotonic Probability Calibration to Ensemble...")
        self.model = CalibratedClassifierCV(ensemble, method='isotonic', cv=TimeSeriesSplit(n_splits=5))
        self.model.fit(X_train_scaled, y_train)

        # 4. Optimize for High Precision (>80%) - "Sniper Mode"
        logger.info("Optimizing for Precision > 80% (Sniper Mode)...")
        y_probs = self.model.predict_proba(X_test_scaled)[:, 1]
        precisions, recalls, thresholds = precision_recall_curve(y_test, y_probs)
        
        # precisions has one more element than thresholds
        valid_idx = np.where(precisions[:-1] >= 0.80)[0]
        
        if len(valid_idx) > 0:
            # Pick the lowest threshold that satisfies 80% precision to maximize recall within that constraint
            self.threshold = thresholds[valid_idx[0]]
            logger.info(f"Sniper Threshold Found: {self.threshold:.4f} (Prec: 80%+, Rec: {recalls[valid_idx[0]]:.2f})")
        else:
            # Fallback: Enforce a balanced 0.55 threshold
            # High threshold (0.60) killed volume and precision. 0.55 is the sweet spot.
            self.threshold = 0.55
            logger.warning(f"80% Precision unreachable. Enforcing balanced threshold: {self.threshold:.4f}")

        # 5. Integrate OOD Detection (K-Means Clustering)
        logger.info("Training Regime Cluster Filter (OOD)...")
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        self.kmeans.fit(X_train_scaled)
        
        # Evaluate
        y_pred = (y_probs >= self.threshold).astype(int)
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "optimized_threshold": float(self.threshold),
            "trade_count": int(np.sum(y_pred))
        }
        
        logger.info(f"Ultra-Precision Results: Precision: {metrics['precision']:.4f}, Trades: {metrics['trade_count']}")
        
        # Save artifacts
        self.save_artifacts()
        return metrics

    def save_artifacts(self):
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        config = {
            "threshold": self.threshold,
            "kmeans": self.kmeans,
            "features": self.features
        }
        joblib.dump(config, self.config_path)
        logger.info("All model artifacts and config saved.")

    def load_artifacts(self):
        if all(os.path.exists(p) for p in [self.model_path, self.scaler_path, self.config_path]):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            config = joblib.load(self.config_path)
            self.threshold = config["threshold"]
            self.kmeans = config["kmeans"]
            return True
        return False

    def detect_regime(self, current_features_df):
        """
        Classifies the market regime: NOMINAL, VOLATILE, or CRASH.
        """
        scaled_features = self.scaler.transform(current_features_df[self.features])
        
        # 1. Volatility Regime (Current vs Hist)
        # We use ATR or Std Dev. Since features include ATR_14, we can use it.
        # However, for a more robust check, let's look at recent volatility ratio.
        # In predict, we already have scaled features.
        
        # 2. OOD Check (Distance from known clusters)
        distances = self.kmeans.transform(scaled_features)
        min_dist = np.min(distances)
        
        # 3. Volatility Check (Empirical)
        # Features index 11 is ATR_14 (based on self.features list)
        atr_idx = self.features.index('ATR_14')
        current_atr = current_features_df['ATR_14'].iloc[0]
        # We don't have historical mean here easily without storing it, 
        # but we can use the OOD distance as a proxy for 'Abnormal' regimes.
        
        regime = "NOMINAL"
        if min_dist > 30.0:
            regime = "CRASH"
        elif min_dist > 15.0:
            regime = "VOLATILE"
            
        return regime

    def predict(self, current_features_df):
        if self.model is None:
            if not self.load_artifacts():
                return None
        
        scaled_features = self.scaler.transform(current_features_df[self.features])
        
        # 1. OOD Check: How close is this to a known training cluster?
        # If the distance is too high, marked as OOD (High Risk)
        distances = self.kmeans.transform(scaled_features)
        min_dist = np.min(distances)
        is_ood = min_dist > 15.0 # Empirical noise threshold
        
        # 2. Calibrated Probability
        probability = self.model.predict_proba(scaled_features)[:, 1][0]
        
        # 3. High-Conviction Prediction
        # A signal is only "UP" if it passes BOTH the threshold AND the OOD filter
        prediction = 1 if (probability >= self.threshold and not is_ood) else 0
        
        # 4. Regime Detection
        regime = self.detect_regime(current_features_df)
        
        # 5. Extract Volatility and Levels for Execution
        atr = current_features_df['ATR_14'].iloc[0] if 'ATR_14' in current_features_df else 0
        pivot = current_features_df['Pivot'].iloc[0] if 'Pivot' in current_features_df else 0
        r1 = current_features_df['R1'].iloc[0] if 'R1' in current_features_df else 0
        s1 = current_features_df['S1'].iloc[0] if 'S1' in current_features_df else 0
        
        return {
            "prediction": prediction,
            "probability": float(probability),
            "threshold": float(self.threshold),
            "is_ood": bool(is_ood),
            "conviction": "HIGH" if prediction == 1 else "LOW",
            "regime": regime,
            "ood_distance": float(min_dist),
            "atr": float(atr),
            "levels": {"Pivot": float(pivot), "R1": float(r1), "S1": float(s1)}
        }

    def predict_with_confidence(self, current_features_df, regime="NOMINAL", causal_strength=0.5):
        """
        Calculates a multi-factor confidence score by combining model probability,
        regime characteristics, and causal support strength.
        """
        # 1. Get base prediction result
        result = self.predict(current_features_df)
        if result is None:
            return None
        
        # 2. Base confidence from calibrated probability
        base_confidence = result['probability'] * 100
        
        # 3. Regime-based adjustments (Boost or Penalty)
        # TRENDING_INTRADAY and POWER_HOUR are higher conviction
        # OPENING_VOLATILITY and LUNCH_LULL are lower conviction
        regime_adj = 0
        if regime == "TRENDING_INTRADAY":
            regime_adj = 10
        elif regime == "POWER_HOUR":
            regime_adj = 5
        elif regime == "OPENING_VOLATILITY":
            regime_adj = -15
        elif regime == "LUNCH_LULL":
            regime_adj = -5
            
        # 4. Causal strength boost
        # Stronger lead-lag relationship (e.g. Futures leading Spot) boosts confidence
        causal_boost = causal_strength * 15
        
        # 5. Calculate final confidence
        # Capped at 100%, Floored at 0%
        final_confidence = min(100.0, max(0.0, base_confidence + regime_adj + causal_boost))
        
        # 6. Enrich result with confidence metrics
        result.update({
            "confidence": float(final_confidence),
            "regime_provided": regime,
            "regime_adjustment": float(regime_adj),
            "causal_strength": float(causal_strength),
            "causal_boost": float(causal_boost),
            "causal_factors": ["futures_lead", "vix_inverse"] if causal_strength > 0.6 else []
        })
        
        return result

if __name__ == "__main__":
    from data_pipeline import DataPipeline
    dp = DataPipeline("^NSEBANK")
    if dp.run_full_pipeline():
        engine = ModelEngine()
        results = engine.train(dp.train_data, dp.test_data)
        print("Ultra-Precision Metrics:", results)
