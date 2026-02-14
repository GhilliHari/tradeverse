import pandas as pd
import numpy as np
import logging
import os
from regime_engine import IntradayRegimeEngine
from data_pipeline import DataPipeline

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainRegime")

def train_regime_model():
    """
    Trains the Regime HMM using historical backtest data.
    """
    csv_path = "historical_backtest_data.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Data file not found: {csv_path}")
        return

    logger.info(f"Loading historical data from {csv_path}...")
    # Load with multi-index if necessary, or simplify
    raw_df = pd.read_csv(csv_path, index_col=0, header=[0, 1], parse_dates=True)
    
    # Extract Bank Nifty data
    if "^NSEBANK" in raw_df.columns.levels[0]:
        df = raw_df["^NSEBANK"].copy()
    else:
        # Fallback for single level
        df = raw_df.copy()
    
    logger.info(f"Loaded {len(df)} bars. Processing indicators...")
    
    # Use DataPipeline to calculate indicators
    pipeline = DataPipeline("^NSEBANK", interval="5m")
    pipeline.raw_data = df
    pipeline.clean_and_prepare()
    
    processed_data = pipeline.cleaned_data
    if processed_data.empty:
        logger.error("Indicator processing failed.")
        return
        
    logger.info(f"Processed data shape: {processed_data.shape}")
    
    # Initialize and Train Engine
    engine = IntradayRegimeEngine()
    success = engine.fit(processed_data)
    
    if success:
        engine.save_model()
        logger.info("✅ Regime HMM trained and saved successfully.")
        
        # Verify classification on some samples
        for i in range(10, 100, 20):
            sample_time = processed_data.index[i]
            sample_features = processed_data.iloc[i]
            regime = engine.classify_regime(sample_time, sample_features)
            logger.info(f"Sample {sample_time.strftime('%H:%M')}: Detected Regime = {regime}")
    else:
        logger.error("❌ Regime HMM training failed.")

if __name__ == "__main__":
    train_regime_model()
