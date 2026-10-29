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
        
        # Relative/Stationary features only for multi-year robustness
        self.features = [
            'Is_Fractal_Low', 'CMO', 'RSI_Slope', 'Mass_Index', 'RSI_x_Vol', 'TR', 'Vol_Ratio', 
            'BB_STD', 'CCI', 'sentiment_score', 'ATR_14', 'ADX', 'Ret_1d', 'DX', 'Gap', 
            'Ret_3d', 'RSI_Vol_Adj', '+DI', 'Ret_5d', 'RSI', 'CCI_Vol_Adj', 'Ret_2d', 'PCR', 
            'Trend_Confidence', 'Inflation_Proxy', 'CMF', 'TSI', 'Coppock', 'WillR', 
            'BN_Nifty_Ratio', 'Klinger', 'Dist_SMA200', 'USDINR', 'DPO', 'MACD_Signal', 
            'MACD_Hist', 'MACD', 'RSI_Vol_Imbalance', 'Dist_EMA21', 'Bull_Power', 'ROC', 
            'Stoch_RSI', 'Bear_Power', 'Is_Fractal_High', 'Aroon_Down', 'Price_FracDiff', 
            'OI_Change', 'Aroon_Up', 'Force_Index', 'OBV', 'Fisher', 'HMA_20', 'MFI', 
            'Vol_Change', 'Streak', 'CE_Delta', 'CE_Theta', 'CE_Gamma', 'CE_Vega', 
            'PE_Delta', 'PE_Theta', 'PE_Gamma', 'PE_Vega', 'CE_Premium', 'PE_Premium',
            'Is_Liquidity_Grab', 'HWM', 'SB', 'HWD'
        ]


    def train(self, train_df, test_df, target_precision=0.80):
        if train_df is None or test_df is None or not isinstance(train_df, pd.DataFrame) or train_df.empty:
            logger.error('ModelEngine.train received None or empty DataFrame.')
            raise ValueError('Training dataset is empty or invalid. Please check historical market data connection.')
        """
        Trains a Voting Ensemble (Random Forest + HistGradientBoosting) with feature selection, class oversampling, and F1 optimization.
        """
        logger.info(f"Preparing data for Ensemble Training (Target Precision: {target_precision*100}%)...")
        
        # Filter features to those actually present in training data and having non-zero variance
        original_feature_count = len(self.features)
        self.features = [
            col for col in self.features 
            if col in train_df.columns and col in test_df.columns and train_df[col].std() > 1e-8
        ]
        logger.info(f"Active features for training: {len(self.features)} (dropped {original_feature_count - len(self.features)} constant or missing columns)")

        # 1. Feature Importance Selection using a temporary Random Forest
        X_train_full = train_df[self.features]
        y_train_full = train_df['Target_Next_Day']
        
        # Scale temporarily
        scaler_temp = StandardScaler()
        X_train_full_scaled = scaler_temp.fit_transform(X_train_full)
        if np.isnan(X_train_full_scaled).any() or np.isinf(X_train_full_scaled).any():
            X_train_full_scaled = np.nan_to_num(X_train_full_scaled, nan=0.0, posinf=0.0, neginf=0.0)

        logger.info("Performing feature importance pruning using Random Forest...")
        temp_rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight='balanced')
        temp_rf.fit(X_train_full_scaled, y_train_full)
        importances = temp_rf.feature_importances_
        
        # Sort and select top features (e.g. top 25 features to prevent overfitting)
        indices = np.argsort(importances)[::-1]
        top_k = min(25, len(self.features))
        selected_features = [self.features[i] for i in indices[:top_k]]
        logger.info(f"Selected top {top_k} features for final training: {selected_features}")
        self.features = selected_features

        # 2. Strict Chronological Train / Validation Split (Prevent Leakage)
        val_size = max(100, int(len(train_df) * 0.2))
        sub_train_df = train_df.iloc[:-val_size]
        val_df = train_df.iloc[-val_size:]
        logger.info(f"Chronological Split: Sub-Train={len(sub_train_df)} rows, Clean Val={len(val_df)} rows")

        # 3. Fit scaler on un-polluted training data
        X_sub_train = sub_train_df[self.features]
        self.scaler.fit(X_sub_train)

        # 4. Apply Class Balancing (Oversampling) strictly to the SUB-TRAIN set only
        pos_samples = sub_train_df[sub_train_df['Target_Next_Day'] == 1]
        neg_samples = sub_train_df[sub_train_df['Target_Next_Day'] == 0]
        
        if len(pos_samples) > 0 and len(neg_samples) > len(pos_samples):
             logger.info(f"Applying Class Balancing to Sub-Train: Pos={len(pos_samples)}, Neg={len(neg_samples)}")
             oversampled_pos = pos_samples.sample(len(neg_samples), replace=True, random_state=42)
             balanced_train_df = pd.concat([neg_samples, oversampled_pos]).sample(frac=1.0, random_state=42)
        else:
             balanced_train_df = sub_train_df

        X_train_scaled = self.scaler.transform(balanced_train_df[self.features])
        y_train = balanced_train_df['Target_Next_Day']
        
        X_val_scaled = self.scaler.transform(val_df[self.features])
        y_val = val_df['Target_Next_Day']

        X_test = test_df[self.features]
        y_test = test_df['Target_Next_Day']
        X_test_scaled = self.scaler.transform(X_test)
        
        for arr in [X_train_scaled, X_val_scaled, X_test_scaled]:
            if np.isnan(arr).any() or np.isinf(arr).any():
                arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

        # 5. Train Ensemble Model
        logger.info("Training Histogram Gradient Boosting Classifier (Aggressive)...")
        hgb = HistGradientBoostingClassifier(
            learning_rate=0.03,
            max_iter=500,
            max_depth=12,
            random_state=42,
            class_weight='balanced',
            l2_regularization=0.1
        )
        
        logger.info("Training Random Forest Classifier (Detail Oriented)...")
        rf = RandomForestClassifier(
            n_estimators=300, 
            max_depth=12,
            min_samples_split=5,
            random_state=42, 
            class_weight='balanced',
            n_jobs=-1
        )
        
        ensemble = VotingClassifier(
            estimators=[('hgb', hgb), ('rf', rf)],
            voting='soft'
        )
        
        logger.info("Applying Isotonic Probability Calibration to Ensemble...")
        self.model = CalibratedClassifierCV(ensemble, method='isotonic', cv=TimeSeriesSplit(n_splits=5))
        self.model.fit(X_train_scaled, y_train)

        # 6. Optimize for Precision/F1 on CLEAN (un-oversampled) Validation data
        logger.info("Optimizing threshold on clean Validation set (Natural Market Distribution)...")
        y_probs_val = self.model.predict_proba(X_val_scaled)[:, 1]
        
        precisions, recalls, thresholds = precision_recall_curve(y_val, y_probs_val)
        
        candidates = []
        for i in range(len(thresholds)):
            thresh = thresholds[i]
            if thresh < 0.50: # Enforce minimum 50% probability floor to prevent noise trading
                continue
            y_pred_val = (y_probs_val >= thresh).astype(int)
            trades = int(np.sum(y_pred_val))
            if trades < 3: # Need at least a few trades
                continue
            prec = precision_score(y_val, y_pred_val, zero_division=0)
            rec = recall_score(y_val, y_pred_val, zero_division=0)
            f1 = f1_score(y_val, y_pred_val, zero_division=0)
            candidates.append((prec, f1, rec, thresh, trades))
            
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        best_threshold = 0.55 if self.model_type == 'daily' else 0.52
        if candidates:
            best_prec, best_f1, best_rec, best_thresh, best_trades = candidates[0]
            best_threshold = float(best_thresh)
            logger.info(f"Selected clean threshold: {best_threshold:.4f} (Val Precision={best_prec:.4f}, F1={best_f1:.4f}, Recall={best_rec:.4f}, Val Trades={best_trades})")
        else:
            logger.warning(f"No threshold met criteria on clean validation. Defaulting to safe floor: {best_threshold:.4f}")
            
        self.threshold = best_threshold

        # Final Probs for reporting on Test set
        y_probs = self.model.predict_proba(X_test_scaled)[:, 1]
        logger.info(f"Test Set Probs: Min={np.min(y_probs):.4f}, Max={np.max(y_probs):.4f}, Mean={np.mean(y_probs):.4f}")

        # 6. Integrate OOD Detection (K-Means Clustering)
        logger.info("Training Regime Cluster Filter (OOD)...")
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        self.kmeans.fit(X_train_scaled)

        # 7. Train Meta-Labeler Classifier
        try:
            logger.info("Generating primary predictions on train set for Meta-Labeler training...")
            train_probs = self.model.predict_proba(X_train_scaled)[:, 1]
            train_preds = (train_probs >= self.threshold).astype(int)
            idx_trades = np.where(train_preds == 1)[0]
            
            if len(idx_trades) >= 10:
                X_meta = X_train_scaled[idx_trades]
                y_meta = y_train.iloc[idx_trades].values
                
                from meta_labeler import MetaLabeler
                ml_labeler = MetaLabeler()
                ml_labeler.train(X_meta, y_meta)
            else:
                logger.warning(f"Not enough trades generated on train set to train ML Meta-Labeler ({len(idx_trades)} < 10). Skipping Meta-Labeler training.")
        except Exception as e:
            logger.warning(f"Failed to train Meta-Labeler: {e}")
        
        # Evaluate
        y_pred = (y_probs >= self.threshold).astype(int)
        
        # Calculate Equity Curve (Cumulative Returns)
        forward_returns = test_df['Ret_1d'].shift(-1).fillna(0)
        strategy_returns = forward_returns * y_pred
        cumulative_strategy = (1 + strategy_returns).cumprod() * 100
        cumulative_benchmark = (1 + forward_returns).cumprod() * 100
        
        equity_curve_full = []
        for i, date in enumerate(test_df.index):
             equity_curve_full.append({
                  "date": date.strftime("%Y-%m-%d" if self.model_type == "daily" else "%Y-%m-%d %H:%M"),
                  "strategy": round(cumulative_strategy.iloc[i], 2),
                  "benchmark": round(cumulative_benchmark.iloc[i], 2)
             })
        
        step = max(1, len(equity_curve_full) // 200)
        equity_curve_sampled = equity_curve_full[::step]
        if len(equity_curve_sampled) > 0 and equity_curve_sampled[-1] != equity_curve_full[-1]:
              equity_curve_sampled.append(equity_curve_full[-1])
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "raw_precision": precision_score(y_test, (y_probs >= 0.5).astype(int), zero_division=0),
            "max_prob": float(np.max(y_probs)),
            "optimized_threshold": float(self.threshold),
            "trade_count": int(np.sum(y_pred)),
            "equity_curve": equity_curve_sampled,
            "final_strategy_return": round(cumulative_strategy.iloc[-1] - 100, 2) if len(cumulative_strategy) > 0 else 0,
            "final_benchmark_return": round(cumulative_benchmark.iloc[-1] - 100, 2) if len(cumulative_benchmark) > 0 else 0
        }
        
        logger.info(f"Ultra-Precision Results: Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}, Trades: {metrics['trade_count']}, MaxProb: {metrics['max_prob']:.4f}")
        
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
            self.features = config.get("features", self.features)
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
