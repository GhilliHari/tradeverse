import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrderFlowEngine")

class OrderFlowEngine:
    """
    LightGBM Model to analyze Level-2 Bid/Ask Order Book data.
    Predicts short-term directional pressure: UP (1), DOWN (-1), or NEUTRAL (0).
    """
    def __init__(self, depth=5):
        self.depth = depth
        self.model_path = os.path.join(os.path.dirname(__file__), "models", "lgbm_order_flow.joblib")
        self.model = None
        self.is_trained = False
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
    def _extract_features(self, order_book):
        """
        Calculates higher-order features from a raw Level-2 snapshot.
        order_book expected format:
        {
            'bids': [{'price': float, 'qty': int}, ...],
            'asks': [{'price': float, 'qty': int}, ...]
        }
        """
        bids = pd.DataFrame(order_book.get('bids', []))
        asks = pd.DataFrame(order_book.get('asks', []))
        
        # Handle empty/malformed books
        if bids.empty or asks.empty:
            return pd.Series({
                'spread': 0, 'mid_price': 0, 'bid_volume': 0, 'ask_volume': 0,
                'imbalance_ratio': 0.5, 'vwap_bid': 0, 'vwap_ask': 0,
                'wall_bid_dist': 0, 'wall_ask_dist': 0
            })
            
        # Limit to configured depth
        bids = bids.head(self.depth)
        asks = asks.head(self.depth)
        
        best_bid = bids['price'].iloc[0]
        best_ask = asks['price'].iloc[0]
        mid_price = (best_bid + best_ask) / 2.0
        spread = best_ask - best_bid
        
        total_bid_vol = bids['qty'].sum()
        total_ask_vol = asks['qty'].sum()
        
        # Pressure Metrics
        imbalance_ratio = total_bid_vol / (total_bid_vol + total_ask_vol + 1e-8)
        
        vwap_bid = (bids['price'] * bids['qty']).sum() / (total_bid_vol + 1e-8)
        vwap_ask = (asks['price'] * asks['qty']).sum() / (total_ask_vol + 1e-8)
        
        # Wall Detection (Find the largest order in the top N levels)
        max_bid_idx = bids['qty'].idxmax()
        max_ask_idx = asks['qty'].idxmax()
        
        wall_bid_price = bids.loc[max_bid_idx, 'price']
        wall_ask_price = asks.loc[max_ask_idx, 'price']
        
        wall_bid_dist = (mid_price - wall_bid_price) / mid_price * 10000 # bps
        wall_ask_dist = (wall_ask_price - mid_price) / mid_price * 10000 # bps
        
        return pd.Series({
            'spread': spread,
            'mid_price': mid_price,
            'bid_volume': total_bid_vol,
            'ask_volume': total_ask_vol,
            'imbalance_ratio': imbalance_ratio,
            'vwap_bid': vwap_bid,
            'vwap_ask': vwap_ask,
            'wall_bid_dist': wall_bid_dist,
            'wall_ask_dist': wall_ask_dist
        })

    def train(self, historical_snapshots, labels):
        """
        historical_snapshots: List of order_book dicts
        labels: List of integers (1=UP, 0=NEUTRAL, -1=DOWN)
        """
        logger.info(f"Extracting features from {len(historical_snapshots)} Level-2 snapshots...")
        
        features_df = pd.DataFrame([self._extract_features(ob) for ob in historical_snapshots])
        
        X_train, X_test, y_train, y_test = train_test_split(features_df, labels, test_size=0.2, random_state=42)
        
        logger.info("Training LightGBM Order Flow Classifier...")
        
        self.model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            objective='multiclass',
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            eval_metric='multi_logloss',
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )
        
        preds = self.model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        logger.info(f"✅ LightGBM Training Complete. Test Accuracy: {acc:.4f}")
        
        self.is_trained = True
        self.save_model()
        
        return acc

    def analyze_flow(self, current_order_book):
        """
        Returns: String ('UP', 'DOWN', 'NEUTRAL') and Confidence (Float)
        """
        if not self.is_trained:
            if not self.load_model():
                return "NEUTRAL", 0.0
                
        features = self._extract_features(current_order_book).to_frame().T
        
        # Protect against all-zero features
        if features['mid_price'].iloc[0] == 0:
            return "NEUTRAL", 0.0
            
        probs = self.model.predict_proba(features)[0]
        pred_idx = np.argmax(probs)
        confidence = probs[pred_idx]
        
        # Mapping index back to label (Assuming classes [-1, 0, 1])
        classes = self.model.classes_
        pred_label = classes[pred_idx]
        
        if confidence < 0.60:
            return "NEUTRAL", confidence
            
        if pred_label == 1:
            return "UP", confidence
        elif pred_label == -1:
            return "DOWN", confidence
        else:
            return "NEUTRAL", confidence

    def save_model(self):
        if self.is_trained and self.model:
            joblib.dump(self.model, self.model_path)
            logger.info(f"Order Flow model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.is_trained = True
            logger.info("Order Flow model loaded.")
            return True
        logger.warning("No trained Order Flow model found.")
        return False

if __name__ == "__main__":
    # Rapid Smoke Test
    logger.info("Running Order Flow Engine Smoke Test...")
    engine = OrderFlowEngine()
    
    # Generate Synthetic Order Book Data
    np.random.seed(42)
    snapshots = []
    labels = []
    
    for _ in range(1000):
        mid = 50000 + np.random.normal(0, 50)
        is_bullish = np.random.rand() > 0.5
        
        if is_bullish:
            bid_vol_mult = 3.0
            labels.append(1)
        else:
            bid_vol_mult = 0.33
            labels.append(-1)
            
        ob = {
            'bids': [{'price': mid - i*0.5, 'qty': int(np.random.randint(100, 500) * bid_vol_mult)} for i in range(1, 6)],
            'asks': [{'price': mid + i*0.5, 'qty': int(np.random.randint(100, 500) / bid_vol_mult)} for i in range(1, 6)]
        }
        snapshots.append(ob)
        
    engine.train(snapshots, labels)
    
    test_ob = {
        'bids': [{'price': 50000 - i, 'qty': 1000} for i in range(1, 6)], # Massive buy wall
        'asks': [{'price': 50000 + i, 'qty': 100} for i in range(1, 6)]
    }
    
    signal, conf = engine.analyze_flow(test_ob)
    logger.info(f"Test Signal on Massive Buy Wall: {signal} (Confidence: {conf:.2f})")
