import logging
import sys
from data_pipeline import DataPipeline
from model_engine import ModelEngine
from tft_engine import TFTEngine
from rl_trading_agent import RLTradingAgent

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HybridTrainer")

def train_daily_strategist():
    logger.info(">>> Training Daily Strategist Model (12 Years History) <<<")
    dp = DataPipeline(interval="1d")
    
    if dp.run_full_pipeline():
        engine = ModelEngine(model_type="daily")
        engine.train(dp.train_data, dp.test_data)
        logger.info("Daily Ensemble Model Trained.")
    else:
        logger.error("Daily Data Pipeline Failed!")

def train_tft_transformer():
    logger.info(">>> Training TFT Deep Transformer (Temporal Context) <<<")
    dp = DataPipeline(interval="1d") # TFT usually performs better on daily/hourly structures
    if dp.run_full_pipeline():
        me = ModelEngine() # To get feature list
        tft = TFTEngine(me.features)
        tft.train(dp.train_data, epochs=10)
        tft.save_model()
        logger.info("TFT Transformer Training Complete.")
    else:
        logger.error("TFT Data Pipeline Failed!")

def train_rl_optimizer():
    logger.info(">>> Training RL Sniper (PPO Entry/Exit Optimizer) <<<")
    dp = DataPipeline(interval="1m") # RL needs granular steps to optimize timing
    if dp.run_full_pipeline():
        me = ModelEngine()
        agent = RLTradingAgent(dp.train_data, me.features)
        agent.train(total_timesteps=10000)
        agent.save_model()
        logger.info("RL Sniper Training Complete.")
    else:
        logger.error("RL Data Pipeline Failed!")

def train_intraday_sniper():
    logger.info(">>> Training Intraday Sniper Model (7 Days History) <<<")
    dp = DataPipeline(interval="1m")
    
    if dp.run_full_pipeline():
        engine = ModelEngine(model_type="intraday")
        metrics = engine.train(dp.train_data, dp.test_data)
        logger.info(f"Intraday Model Metrics: {metrics}")
    else:
        logger.error("Intraday Data Pipeline Failed!")

if __name__ == "__main__":
    logger.info("Starting Hybrid Model Training Sequence...")
    
    # Train all models in the stack
    train_daily_strategist()
    train_intraday_sniper()
    train_tft_transformer()
    train_rl_optimizer()
    
    logger.info("All Neural Core Brains Rebuilt and Optimized.")
