import logging
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline import DataPipeline
from model_engine import ModelEngine

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LiteTrainer")

def train_daily_strategist():
    logger.info(">>> Training Daily Strategist Model (12 Years History) <<<")
    dp = DataPipeline(symbol="^NSEBANK", interval="1d")
    
    if dp.run_full_pipeline():
        engine = ModelEngine(model_type="daily")
        metrics = engine.train(dp.train_data, dp.test_data)
        logger.info(f"Daily Ensemble Model Trained. Metrics: {metrics.get('precision', 0):.4f}")
    else:
        logger.error("Daily Data Pipeline Failed!")

def train_intraday_sniper():
    logger.info(">>> Training Intraday Sniper Model (7 Days History) <<<")
    dp = DataPipeline(symbol="^NSEBANK", interval="5m")
    
    if dp.run_full_pipeline():
        engine = ModelEngine(model_type="intraday")
        metrics = engine.train(dp.train_data, dp.test_data)
        logger.info(f"Intraday Model Trained. Metrics: {metrics.get('precision', 0):.4f}")
    else:
        logger.error("Intraday Data Pipeline Failed!")

if __name__ == "__main__":
    logger.info("Starting Lite Model Training Sequence (Sklearn Core)...")
    try:
        train_daily_strategist()
        train_intraday_sniper()
        logger.info("Lite Neural Core Brains Rebuilt and Optimized.")
    except Exception as e:
        logger.error(f"Training Failed: {e}")
        sys.exit(1)
