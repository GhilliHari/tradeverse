import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from data_pipeline import DataPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FeatureSelection")

def run_feature_selection(symbol="^NSEBANK", interval="1d"):
    logger.info(f"Starting Feature Selection for {symbol} ({interval})...")
    
    dp = DataPipeline(symbol, interval)
    stats = dp.run_full_pipeline()
    
    if not stats:
        logger.error("Data ingestion failed.")
        return
    
    df = dp.train_data
    features = [c for c in df.columns if c not in ['Target_Next_Day', 'Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    X = df[features]
    y = df['Target_Next_Day']
    
    logger.info(f"Training Random Forest on {len(features)} features...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    importances = rf.feature_importances_
    feature_importance_df = pd.DataFrame({'feature': features, 'importance': importances})
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
    
    logger.info("Top 20 Features:")
    print(feature_importance_df.head(20))
    
    # Save optimized features (importance > 0.005)
    optimized_features = feature_importance_df[feature_importance_df['importance'] > 0.005]['feature'].tolist()
    logger.info(f"Optimized Feature Count: {len(optimized_features)}")
    
    return optimized_features

if __name__ == "__main__":
    optimized = run_feature_selection()
    if optimized:
        print("OPTIMIZED_FEATURES =", optimized)
