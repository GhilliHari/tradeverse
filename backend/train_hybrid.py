import logging
import sys
from data_pipeline import DataPipeline
from model_engine import ModelEngine
from tft_engine import TFTEngine
from rl_trading_agent import RLTradingAgent
from regime_engine import IntradayRegimeEngine

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HybridTrainer')

def train_daily_strategist():
    logger.info('>>> Training Daily Strategist Model (12 Years History) <<<')
    dp = DataPipeline(interval='1d')
    if dp.run_full_pipeline():
        engine = ModelEngine(model_type='daily')
        metrics = engine.train(dp.train_data, dp.test_data)
        logger.info(f'Daily Model Metrics: {metrics}')
        logger.info('Daily Ensemble Model Trained.')
    else:
        logger.error('Daily Data Pipeline Failed!')

def train_intraday_sniper():
    logger.info('>>> Training Intraday Sniper Model (5m Microstructure) <<<')
    dp = DataPipeline(interval='5m')
    if dp.run_full_pipeline():
        engine = ModelEngine(model_type='intraday')
        metrics = engine.train(dp.train_data, dp.test_data)
        logger.info(f'Intraday Model Metrics: {metrics}')
        logger.info('Intraday Ensemble Model Trained.')
    else:
        logger.error('Intraday Data Pipeline Failed!')

def train_tft_transformer():
    logger.info('>>> Training TFT Deep Transformer (Temporal Context) <<<')
    dp = DataPipeline(interval='1d')
    if dp.run_full_pipeline():
        me = ModelEngine(model_type='daily')
        me.load_artifacts()
        tft = TFTEngine(me.features)
        tft.train(dp.train_data, epochs=10)
        tft.save_model()
        logger.info('TFT Transformer Training Complete.')
    else:
        logger.error('TFT Data Pipeline Failed!')

def train_rl_optimizer():
    logger.info('>>> Training RL Sniper (PPO Timing Optimizer) <<<')
    dp = DataPipeline(interval='5m')
    if dp.run_full_pipeline():
        me = ModelEngine(model_type='daily')
        me.load_artifacts()
        agent = RLTradingAgent(dp.train_data, me.features)
        agent.train(total_timesteps=6000)
        agent.save_model()
        logger.info('RL Sniper Training Complete.')
    else:
        logger.error('RL Data Pipeline Failed!')

def train_regime_hmm():
    logger.info('>>> Training Regime HMM Classifier <<<')
    dp = DataPipeline(interval='5m')
    if dp.run_full_pipeline():
        regime_engine = IntradayRegimeEngine()
        regime_engine.fit(dp.cleaned_data)
        regime_engine.save_model()
        logger.info('Regime HMM Model Trained & Saved.')
    else:
        logger.error('Regime Data Pipeline Failed!')

if __name__ == '__main__':
    logger.info('Starting Hybrid Model Training Sequence...')
    train_daily_strategist()
    train_intraday_sniper()
    train_tft_transformer()
    train_rl_optimizer()
    train_regime_hmm()
    logger.info('All Neural Core Brains Rebuilt and Optimized.')
