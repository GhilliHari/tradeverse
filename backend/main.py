from fastapi import FastAPI, HTTPException, Body, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import importlib.metadata
# Polyfill for Python 3.9 compatibility with some google-auth/api-core versions
if not hasattr(importlib.metadata, 'packages_distributions'):
    importlib.metadata.packages_distributions = lambda: {}

from mock_kite import MockKiteConnect
from risk_engine import RiskEngine
# Heavy modules (AgentLayer, DataPipeline, ModelEngine) are now lazy-loaded
from broker_factory import get_broker_client
# NewsScraper -> Lazy load
from config import config
from auth_middleware import get_current_user, verify_owner
from notifier import notifier
from redis_manager import redis_client
import os
import uvicorn
import logging
import json
import asyncio
from datetime import datetime, time, timedelta



# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradeverseBackend")

# Redis Client (Centralized)
# redis_client is imported from redis_manager at the top


app = FastAPI(title="Tradeverse Agentic Platform")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Use False to avoid security blocks when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Objects (Initialized lazily during startup)
kite = None
risk_engine = None
intelligence = None
initialization_status = {"ready": False, "error": None}

async def initialize_systems():
    global kite, risk_engine, intelligence, initialization_status
    try:
        # Wait for 5 seconds to allow Uvicorn to bind port and serve health checks
        # This prevents CPU starvation during startup from causing deployment timeouts
        await asyncio.sleep(5)
        
        logger.info("⚙️ Starting Background System Initialization...")
        # broker_factory handles credentials from Redis/Config
        # Offload blocking network/disk I/O to threads to prevent event loop freeze
        kite = await asyncio.to_thread(get_broker_client)
        
        risk_engine = RiskEngine(daily_loss_limit=config.DAILY_LOSS_LIMIT, max_position_size=config.MAX_POSITION_SIZE)
        
        # IntelligenceLayer init involves model loading and broker connection (heavy)
        from agent_layer import IntelligenceLayer
        intelligence = await asyncio.to_thread(IntelligenceLayer, config.GEMINI_API_KEY)
        
        initialization_status["ready"] = True
        logger.info("✅ Systems Initialized & Ready.")
        
        # Notify via sync wrapper since we are in async context but notifier might be sync
        await asyncio.to_thread(notifier.notify_sync, "🚀 *Tradeverse Online*: Systems initialized and ready for execution.")

    except Exception as e:
        logger.error(f"❌ Initialization Failed: {e}")
        initialization_status["error"] = str(e)

# Caches for data pipeline and model training
pipeline_cache = {}
training_metrics = {}

# Training Status Tracker (Global)
training_status = {
    "is_training": False,
    "progress": 0,
    "stage": "IDLE",
    "message": "No training in progress",
    "started_at": None,
    "completed_at": None,
    "metrics": {}
}

# Observatory Simulation Engine (Global)
from simulation_engine import SimulationEngine
simulation_engine = SimulationEngine(data_dir="observatory_data")
simulation_task = None  # Will hold the asyncio task

def normalize_symbol(symbol: str):
    """Maps frontend symbols to yfinance symbols."""
    u_symbol = symbol.upper()
    if "BANKNIFTY" in u_symbol or "BANK" in u_symbol:
        return "^NSEBANK"
    if "NIFTY" in u_symbol and "BANK" not in u_symbol:
        return "^NSEI"
    return symbol


from monitoring import monitor

@app.on_event("startup")
async def startup_event():
    # Start systems initialization in background so we don't block port bind
    asyncio.create_task(initialize_systems())
    # Start watchdog
    asyncio.create_task(run_watchdog())

    # Force Default to MOCK on Startup for Safety
    logger.info("🔒 Enforcing Default MOCK Mode on Startup")
    config.ENV = "MOCK"
    config.ACTIVE_BROKER = "MOCK_KITE"
    config.save()

async def run_watchdog():
    """
    Watches specialized data pipelines and system health.
    Also handles daily data updates at 4:00 PM IST.
    """
    from daily_data_updater import update_daily_data
    
    while True:
        try:
            # System Health Check
            if not config.GEMINI_API_KEY:
                logger.warning("Watchdog: Gemini API Key Not Found")
                
            # Check if it's 4:00 PM IST (16:00) for daily update
            # Simple check run once a minute
            now = datetime.now()
            if now.hour == 16 and now.minute == 0:
                logger.info("Watchdog: Triggering Daily Data Update")
                asyncio.create_task(update_daily_data())
                # Sleep for 61 seconds to avoid double triggering
                await asyncio.sleep(61)
                
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Watchdog Error: {e}")
            await asyncio.sleep(60)

@app.get("/")
async def root():
    return {
        "message": "Tradeverse API is active", 
        "initialization": initialization_status,
        "mode": config.ENV,
        "status": "NOMINAL" if initialization_status["ready"] else "INITIALIZING"
    }

@app.get("/api/health")
async def health_check():
    if not initialization_status["ready"]:
        if initialization_status["error"]:
             raise HTTPException(status_code=500, detail=f"Init Error: {initialization_status['error']}")
        return {"status": "INITIALIZING"}
    return {"status": "READY"}

    monitor.record_heartbeat(user.get('uid'))
    return {"status": "pulse_received"}

@app.post("/api/settings/whatsapp/test")
async def test_whatsapp(user: dict = Depends(get_current_user)):
    """Triggers a test transparency notification to the configured phone."""
    try:
        from notifier import notifier
        if not notifier.enabled:
            return {"status": "error", "message": "WhatsApp Notifier is NOT enabled. Please save your Phone and API Key first."}
            
        msg = "🔔 *Tradeverse Alert*: WhatsApp Integration Verified! You are now receiving system transparency alerts."
        # Notifier uses async send_message
        await notifier.send_message(msg)
        return {"status": "success", "message": "Test message dispatched. Check your WhatsApp!"}
    except Exception as e:
        logger.error(f"WhatsApp Test Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/settings/telegram/test")
async def test_telegram(user: dict = Depends(get_current_user)):
    try:
        from notifier import notifier
        if not notifier.telegram.enabled:
            return {"status": "error", "message": "Telegram Notifier is NOT enabled. Please save your Bot Token and Chat ID first."}
            
        msg = "🔔 *Tradeverse Alert*: Telegram Integration Verified! You are now receiving system transparency alerts."
        await notifier.telegram.send_message(msg)
        return {"status": "success", "message": "Test message dispatched. Check your Telegram!"}
    except Exception as e:
        logger.error(f"Telegram Test Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/ltp/{symbol}")
async def get_ltp(symbol: str):
    """
    Fetches the Last Traded Price for a symbol.
    """
    try:
        if not kite:
            return {"symbol": symbol, "last_price": 0, "status": "initializing"}
        price_data = kite.ltp(symbol)
        if symbol not in price_data:
            raise HTTPException(status_code=404, detail="Symbol not found")
        return {"symbol": symbol, "last_price": price_data[symbol]["last_price"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/risk/status")
async def get_risk_status():
    """
    Returns the current risk engine status.
    """
    if not risk_engine:
        return {"ready": False, "status": "Initializing Risk Engine..."}
    return risk_engine.get_risk_status()

@app.post("/api/order/place")
async def place_order(order_data: Dict = Body(...), user: dict = Depends(get_current_user)):
    """
    Validates and places an order via the broker for the current user.
    """
    user_id = user.get("uid")
    # 1. Pre-order risk validation
    validation = risk_engine.validate_order(order_data)
    if not validation["allowed"]:
        return {"status": "REJECTED", "reason": validation["reason"]}

    # 2. Get user-specific broker client
    try:
        broker = get_broker_client(user_id)
        
        order_id = broker.place_order(
            variety="NORMAL", # Standard variety for Angel
            exchange=order_data.get("exchange", "NSE"),
            tradingsymbol=order_data.get("tradingsymbol"),
            transaction_type=order_data.get("transaction_type"),
            quantity=order_data.get("quantity"),
            product=order_data.get("product", "MIS"),
            order_type=order_data.get("order_type", "MARKET"),
            price=order_data.get("price")
        )
        msg = (f"🎯 *Order Placed ({user_id})*\n"
               f"Symbol: `{order_data.get('tradingsymbol')}`\n"
               f"Side: *{order_data.get('transaction_type')}*\n"
               f"Qty: `{order_data.get('quantity')}`\n"
               f"Type: `{order_data.get('order_type', 'MARKET')}`\n"
               f"ID: `{order_id}`")
        notifier.notify_sync(msg)
        return {"status": "COMPLETE", "order_id": order_id, "symbol": order_data.get("tradingsymbol")}
    except Exception as e:
        error_msg = f"❌ *Order Failed ({user_id})*\nSymbol: `{order_data.get('tradingsymbol')}`\nError: `{str(e)}`"
        notifier.notify_sync(error_msg)
        raise HTTPException(status_code=500, detail=f"Broker Error: {str(e)}")

@app.post("/api/risk/circuit-breaker")
async def toggle_circuit_breaker(active: bool = Body(...), reason: str = Body("Manual trigger")):
    """
    Toggles the trading circuit breaker.
    """
    status = risk_engine.trigger_circuit_breaker(active, reason)
    return status

@app.post("/api/intelligence/analyze/{symbol}")
async def analyze_market(symbol: str, positions: List[Dict] = Body(default=[])):
    """
    Runs the full agentic committee analysis, including exit monitoring for positions.
    """
    try:
        # Inject positions into the analysis state
        result = intelligence.run_analysis(symbol, positions=positions)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence Layer Error: {str(e)}")

@app.get("/api/market/options/{symbol}")
async def get_options(symbol: str):
    if not kite or not initialization_status["ready"]:
        return {"status": "error", "detail": "System initialization in progress..."}
    try:
        return kite.get_option_chain(symbol)
    except Exception as e:
        logger.error(f"Failed to fetch options for {symbol}: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/orders")
async def get_orders():
    """
    Fetches the order book from the active broker.
    """
    if not kite or not initialization_status["ready"]:
        return []
    try:
        return kite.orders()
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        return []

@app.get("/api/data/pipeline/trigger")
async def trigger_pipeline(symbol: str = "NSE:BANKNIFTY"):
    from data_pipeline import DataPipeline
    norm_symbol = normalize_symbol(symbol)
    pipeline = DataPipeline(norm_symbol)
    stats = pipeline.run_full_pipeline()
    if stats:
        pipeline_cache[norm_symbol] = pipeline
        return {"status": "success", "data": stats}
    return {"status": "failed", "message": "Pipeline execution failed"}

@app.get("/api/market/search")
async def search_market(query: str, exchange: str = "NSE"):
    if not kite:
        return []
    try:
        if hasattr(kite, 'search_scrip'):
            return kite.search_scrip(query, exchange)
        return []
        return []
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

@app.get("/api/news")
async def get_market_news():
    """
    Fetches live financial news using NewsScraper.
    """
    try:
        from news_scraper import NewsScraper
        scraper = NewsScraper()
        # Run in executor to avoid blocking async loop since requests is sync
        # For this prototype, calling directly is acceptable but async wrapper is better.
        # fast implementation:
        news = scraper.fetch_latest_news()
        return news
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        return []

# Global Engines (Lazy Initialized)
engine_daily = None
engine_intraday = None

def get_engine(type="daily"):
    global engine_daily, engine_intraday
    from model_engine import ModelEngine
    if type == "daily":
        if not engine_daily:
            engine_daily = ModelEngine(model_type="daily")
            engine_daily.load_artifacts()
        return engine_daily
    else:
        if not engine_intraday:
            engine_intraday = ModelEngine(model_type="intraday")
            engine_intraday.load_artifacts()
        return engine_intraday

@app.get("/api/ai/predict_hybrid")
async def predict_hybrid(symbol: str = "NSE:BANKNIFTY"):
    """
    Returns Hybrid Strategic Analysis using the Agentic Intelligence Layer (COR Augmented).
    """
    if not intelligence or not initialization_status["ready"]:
        return {"status": "error", "message": "Intelligence Layer not initialized"}
    
    norm_symbol = normalize_symbol(symbol)
    try:
        # Run full Agentic analysis (Weeks 6-8 integration)
        # We offload to thread because LangGraph/Gemini calls are blocking
        result = await asyncio.to_thread(intelligence.run_analysis, norm_symbol)
        
        tech_ctx = result.get('technical_context', {})
        
        # Format response for frontend consumption (Mapping COR state to UI-friendly structure)
        response = {
            "symbol": norm_symbol,
            "daily": {
                "status": result.get("sentiment_label", "NEUTRAL"),
                "prob": result.get("sentiment_score", 0.5)
            },
            "intraday": {
                "status": result.get("final_signal", "WAIT"),
                "prob": result.get("confidence", 0.0) / 100,
                "conviction": tech_ctx.get('conviction', 'LOW')
            },
            "regime": result.get("regime", "NOMINAL"),
            "confidence": result.get("confidence", 0.0),
            "causal_strength": tech_ctx.get('causal_strength', 0.5),
            "tactical": {
                "pivot": tech_ctx.get('levels', {}).get('Pivot', 0),
                "r1": tech_ctx.get('levels', {}).get('R1', 0),
                "s1": tech_ctx.get('levels', {}).get('S1', 0),
                "rsi": tech_ctx.get('rsi', 50),
                "atr": tech_ctx.get('atr', 0)
            },
            "final_action": result.get("final_signal", "HOLD"),
            "reasoning": result.get("trade_recommendation", {}).get("reasoning", ""),
            "structural": {
                "component_score": tech_ctx.get('component_alpha', {}).get('score', 0),
                "component_status": tech_ctx.get('component_alpha', {}).get('status', 'NEUTRAL'),
                "gex": result.get('gex_data', {})
            },
            "model_scores": result.get("model_scores", {})
        }
        return response
    except Exception as e:
        logger.error(f"Predict Hybrid Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/brain")
async def get_brain_status(symbol: str = "NSE:BANKNIFTY"):
    """
    Returns real-time component scores (the 'Brain' status) for a symbol.
    """
    if not intelligence or not initialization_status["ready"]:
        return {"status": "error", "message": "Intelligence Layer not initialized"}
    
    norm_symbol = normalize_symbol(symbol)
    try:
        # Offload to thread for parallel safety and blocking I/O
        result = await asyncio.to_thread(intelligence.run_analysis, norm_symbol)
        
        return {
            "symbol": norm_symbol,
            "confidence": result.get("confidence", 0.0),
            "model_scores": result.get("model_scores", {}),
            "regime": result.get("regime", "NOMINAL"),
            "final_signal": result.get("final_signal", "HOLD")
        }
    except Exception as e:
        logger.error(f"Brain Status Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def train_swarm_background():
    """
    Background task to retrain the entire AI Swarm.
    Runs in a threadpool (sync def) to avoid blocking the async event loop.
    """
    global training_status
    from datetime import datetime
    
    try:
        training_status.update({
            "is_training": True,
            "progress": 5,
            "stage": "DATA_INGESTION",
            "message": "Fetching historical data...",
            "started_at": datetime.now().isoformat()
        })
        
        # Import heavy modules with Lite Mode Fallback
        try:
            from data_pipeline import DataPipeline
            from model_engine import ModelEngine
        except ImportError:
            logger.warning("Lite Mode: ML Engines (sklearn) not available.")
            training_status.update({
                "is_training": False,
                "progress": 100,
                "stage": "COMPLETE",
                "message": "Lite Mode Active. Training Skipped (ML deps missing).",
                "completed_at": datetime.now().isoformat(),
                "metrics": {"daily": {"accuracy": 0.0}, "intraday": {"accuracy": 0.0}}
            })
            return

        # Optional Deep Learning Modules
        TFTEngine = None
        RLTradingAgent = None
        IntradayRegimeEngine = None
        
        try:
            from tft_engine import TFTEngine
        except ImportError: logger.warning("Lite Mode: TFTEngine skipped")
        
        try:
            from rl_trading_agent import RLTradingAgent
        except ImportError: logger.warning("Lite Mode: RLTradingAgent skipped")
        
        try:
            from regime_engine import IntradayRegimeEngine
        except ImportError: logger.warning("Lite Mode: RegimeEngine skipped")

        
        # Stage 1: Daily Strategist
        training_status.update({"progress": 15, "stage": "DAILY_STRATEGIST", "message": "Training Daily Ensemble..."})
        logger.info("[TRAIN_SWARM] Stage 1: Daily Strategist")
        dp_daily = DataPipeline(symbol="^NSEBANK", interval="1d")
        dp_daily.run_full_pipeline()
        daily_engine = ModelEngine(model_type="daily")
        daily_metrics = daily_engine.train(dp_daily.train_data, dp_daily.test_data)
        
        # Stage 2: Intraday Sniper
        training_status.update({"progress": 35, "stage": "INTRADAY_SNIPER", "message": "Training Intraday Model..."})
        logger.info("[TRAIN_SWARM] Stage 2: Intraday Sniper")
        dp_intraday = DataPipeline(symbol="^NSEBANK", interval="1m")
        dp_intraday.run_full_pipeline()
        intraday_engine = ModelEngine(model_type="intraday")
        intraday_metrics = intraday_engine.train(dp_intraday.train_data, dp_intraday.test_data)
        
        # Stage 3: TFT Transformer
        if TFTEngine:
            training_status.update({"progress": 55, "stage": "TFT_TRANSFORMER", "message": "Training Deep Transformer..."})
            logger.info("[TRAIN_SWARM] Stage 3: TFT Transformer")
            tft = TFTEngine(daily_engine.features)
            tft.train(dp_daily.train_data, epochs=10)
            tft.save_model()
        else:
            logger.info("[TRAIN_SWARM] Skipping Stage 3 (Lite Mode)")
        
        # Stage 4: RL Sniper
        if RLTradingAgent:
            training_status.update({"progress": 75, "stage": "RL_OPTIMIZER", "message": "Training RL Sniper..."})
            logger.info("[TRAIN_SWARM] Stage 4: RL Sniper")
            rl_agent = RLTradingAgent(dp_intraday.train_data, daily_engine.features)
            rl_agent.train(total_timesteps=5000) # Reduced for robustness
            rl_agent.save_model()
        else:
            logger.info("[TRAIN_SWARM] Skipping Stage 4 (Lite Mode)")
        
        # Stage 5: Regime HMM
        if IntradayRegimeEngine:
            training_status.update({"progress": 90, "stage": "REGIME_ENGINE", "message": "Training Regime Classifier..."})
            logger.info("[TRAIN_SWARM] Stage 5: Regime HMM")
            regime_engine = IntradayRegimeEngine()
            regime_engine.fit(dp_intraday.cleaned_data)
            regime_engine.save_model()
        else:
            logger.info("[TRAIN_SWARM] Skipping Stage 5 (Lite Mode)")
        
        # Complete
        training_status.update({
            "is_training": False,
            "progress": 100,
            "stage": "COMPLETE",
            "message": "All available models retrained successfully!",
            "completed_at": datetime.now().isoformat(),
            "metrics": {
                "daily": daily_metrics,
                "intraday": intraday_metrics
            }
        })
        logger.info("[TRAIN_SWARM] ✅ Full Swarm Rebuild Complete")
        
    except Exception as e:
        logger.error(f"[TRAIN_SWARM] ❌ Training Failed: {e}")
        training_status.update({
            "is_training": False,
            "stage": "ERROR",
            "message": f"Training failed: {str(e)}",
            "completed_at": datetime.now().isoformat()
        })

@app.post("/api/ai/train")
async def trigger_training(background_tasks: BackgroundTasks, user: dict = Depends(verify_owner)):
    """
    Triggers a full AI Swarm retrain in the background (Owner-only).
    """
    if training_status["is_training"]:
        raise HTTPException(status_code=409, detail="Training already in progress")
    
    background_tasks.add_task(train_swarm_background)
    return {
        "status": "started",
        "message": "AI Swarm retraining started in background"
    }

@app.get("/api/ai/train/status")
async def get_training_status(user: dict = Depends(get_current_user)):
    """
    Returns the current training status.
    """
    return training_status

# ============= OBSERVATORY ENDPOINTS =============

@app.post("/api/observatory/start")
async def start_observatory(user: dict = Depends(verify_owner)):
    """
    Start the live simulation engine (Owner-only).
    """
    global simulation_task, intelligence
    
    if simulation_engine.is_running:
        raise HTTPException(status_code=409, detail="Simulation already running")
    
    if intelligence is None:
        raise HTTPException(status_code=503, detail="Intelligence layer not initialized")
    
    # Start simulation in background
    simulation_task = asyncio.create_task(simulation_engine.run_simulation_loop(intelligence))
    
    return {
        "status": "started",
        "message": "Observatory simulation started"
    }

@app.post("/api/observatory/stop")
async def stop_observatory(user: dict = Depends(verify_owner)):
    """
    Stop the live simulation engine (Owner-only).
    """
    if not simulation_engine.is_running:
        raise HTTPException(status_code=409, detail="Simulation not running")
    
    simulation_engine.stop()
    
    return {
        "status": "stopped",
        "message": "Observatory simulation stopped"
    }

@app.get("/api/observatory/status")
async def get_observatory_status(user: dict = Depends(get_current_user)):
    """
    Get current observatory simulation status.
    """
    return simulation_engine.get_status()

@app.get("/api/observatory/results")
async def get_observatory_results(date: Optional[str] = None, user: dict = Depends(get_current_user)):
    """
    Get simulation results for a specific date (defaults to today).
    """
    return simulation_engine.get_results(date)

@app.get("/api/observatory/summary")
async def get_observatory_summary(date: Optional[str] = None, user: dict = Depends(get_current_user)):
    """
    Get performance summary for a specific date (defaults to today).
    """
    return simulation_engine.get_performance_summary(date)


# ============= DATA MANAGEMENT ENDPOINTS =============

@app.post("/api/data/refresh")
async def refresh_data(user: dict = Depends(verify_owner)):
    """
    Manually triggers the daily data update cycle (Owner-only).
    """
    from daily_data_updater import update_daily_data
    
    # Run in background to avoid timeout
    asyncio.create_task(update_daily_data())
    
    return {
        "status": "started",
        "message": "Data refresh cycle started in background"
    }

# ============= BACKTEST ENDPOINT =============

@app.post("/api/ai/backtest")
async def run_backtest_endpoint(request: dict):
    """
    Comprehensive Backtest Endpoint.
    Supports: daily_12y, intraday_7d, intraday_1m, intraday_1y
    """
    symbol = request.get("symbol", "^NSEBANK")
    model_type = request.get("model_type", "daily_12y")
    normalized_symbol = normalize_symbol(symbol)
    
    logger.info(f"Running Backtest: {model_type} for {normalized_symbol}")
    
    try:
        from data_pipeline import DataPipeline
        from model_engine import ModelEngine
        
        # 1. Configuration based on model_type
        interval = "1d"
        lookback_days = 3650 # 10 years
        
        if model_type == "intraday_7d":
            interval = "1m"
            lookback_days = 7
        elif model_type == "intraday_1m":
            interval = "5m"
            lookback_days = 30
        elif model_type == "intraday_1y":
            interval = "15m" 
            lookback_days = 365
            
        # 2. Fetch Data
        pipeline = DataPipeline(symbol=normalized_symbol, interval=interval, lookback_days=lookback_days)
        pipeline.run_full_pipeline()
        
        if pipeline.train_data is None or pipeline.test_data is None:
             # Fallback if split failed (e.g. not enough data)
             if pipeline.cleaned_data is not None and len(pipeline.cleaned_data) > 100:
                  pipeline.split_data()
             else:
                  raise HTTPException(status_code=400, detail="Insufficient data for backtest")

        # 3. Validation Metrics (mock training for speed if needed, or real training)
        # Using ModelEngine to train/test
        engine_type = "intraday" if "intraday" in model_type else "daily"
        engine = ModelEngine(model_type=engine_type)
        
        # Use a smaller subset for speed if it's a huge dataset in "interactive" backtest
        # But user wants "real actual data", so we use full
        metrics = engine.train(pipeline.train_data, pipeline.test_data)
        
        # 4. Enhance Metrics with Data Quality
        quality = pipeline.get_data_quality_metrics()
        
        # Merge metrics
        response_metrics = {**metrics, **quality}
        
        # Add Split Info
        response_metrics.update({
             "train_start": pipeline.train_data.index[0].strftime("%Y-%m-%d"),
             "train_end": pipeline.train_data.index[-1].strftime("%Y-%m-%d"),
             "test_start": pipeline.test_data.index[0].strftime("%Y-%m-%d"),
             "test_end": pipeline.test_data.index[-1].strftime("%Y-%m-%d"),
             "train_records": len(pipeline.train_data),
             "test_records": len(pipeline.test_data)
        })
        
        return {
            "status": "success",
            "metrics": response_metrics
        }
        
    except Exception as e:
        logger.error(f"Backtest Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/train_legacy")
async def train_model(symbol: str = "NSE:BANKNIFTY"):
    """
    DEPRECATED: Legacy sync training endpoint (kept for backwards compatibility).
    Triggers the Hybrid AI Training process using the loaded data pipeline.
    """
    normalized_symbol = normalize_symbol(symbol)
    
    # 1. Check if pipeline data is available
    if normalized_symbol not in pipeline_cache:
        # Auto-trigger pipeline if missing
        logger.info(f"Pipeline cache miss for {normalized_symbol}. Triggering ingestion...")
        from data_pipeline import DataPipeline
        pipeline = DataPipeline(symbol=normalized_symbol, interval="1d")
        stats = pipeline.run_full_pipeline()
        if not stats:
            raise HTTPException(status_code=500, detail="Data Pipeline Failed during auto-trigger")
        pipeline_cache[normalized_symbol] = pipeline
    
    pipeline = pipeline_cache[normalized_symbol]
    
    # 2. Train Daily Model (Strategist)
    if pipeline.train_data is None or pipeline.test_data is None:
         raise HTTPException(status_code=400, detail="Pipeline data not split. Run pipeline first.")
         
    try:
        logger.info(f"Starting Model Training for {normalized_symbol}...")
        metrics = get_engine("daily").train(pipeline.train_data, pipeline.test_data)
        
        # 3. Cache Intraday Model (Sniper) - Placeholder/Mock for now as Intraday needs 1m data
        # In a full flow, we'd have a separate pipeline for 1m data here.
        
        return {
            "status": "success", 
            "message": "AI Training Complete",
            "metrics": metrics,
            "mode": "HYBRID_ENSEMBLE"
        }
    except Exception as e:
        logger.error(f"Training Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training Failed: {str(e)}")

@app.get("/api/market/mmi")
async def get_market_mood_index():
    """
    Calculate Market Mood Index (MMI) based on multiple indicators.
    MMI ranges from 0 (Extreme Fear) to 100 (Extreme Greed).
    
    Factors:
    - VIX/India VIX (inverse relationship)
    - Put-Call Ratio (inverse)
    - Market Breadth (Advances/Declines)
    - Price momentum
    - Volume trends
    """
    try:
        # Get current market data
        symbol = "BANKNIFTY"
        
        # Fetch latest data point
        try:
            # Assuming 'pipeline' is an accessible instance or can be created
            # For this example, let's create a new DataPipeline instance
            # In a real app, you might have a global pipeline or pass it around
            from data_pipeline import DataPipeline
            local_pipeline = DataPipeline(symbol=normalize_symbol(symbol))
            df = local_pipeline.fetch_data(symbol, timeframe="1d", lookback_days=5)
            if df is None or len(df) == 0:
                raise ValueError("No data available")
        except Exception as e:
            logger.warning(f"Could not fetch live data for MMI: {e}")
            # Return neutral value if data unavailable
            return {
                "mmi": 50.0,
                "label": "NEUTRAL",
                "components": {
                    "vix_score": 50,
                    "pcr_score": 50,
                    "momentum_score": 50,
                    "volume_score": 50
                },
                "status": "offline",
                "message": "Using default values - market data unavailable"
            }
        
        # Calculate component scores (0-100 scale)
        
        # 1. VIX Score (inverse: high VIX = fear = low score)
        # Assume VIX range: 10 (low fear) to 30 (high fear)
        # For now, use ATR as proxy for volatility
        latest_atr = df['ATR_14'].iloc[-1] if 'ATR_14' in df.columns else 500
        vix_proxy = (latest_atr / df['close'].iloc[-1]) * 100  # ATR as % of price
        vix_score = max(0, min(100, 100 - (vix_proxy * 5)))  # Inverse and scale
        
        # 2. PCR Score (Put-Call Ratio)
        # Ideal PCR around 0.7-1.0 (neutral to slightly bullish)
        # For now, use RSI as sentiment proxy
        latest_rsi = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns else 50
        pcr_score = latest_rsi  # RSI already 0-100
        
        # 3. Momentum Score
        # Use MACD and price change
        latest_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2] if len(df) > 1 else latest_close
        price_change_pct = ((latest_close - prev_close) / prev_close) * 100
        
        # Scale price change to 0-100 (assume ±3% is extreme)
        momentum_score = max(0, min(100, 50 + (price_change_pct * 16.67)))
        
        # 4. Volume Score
        # Compare current volume to average
        if 'volume' in df.columns:
            latest_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(5).mean().iloc[-1]
            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
            volume_score = max(0, min(100, 50 + ((volume_ratio - 1) * 50)))
        else:
            volume_score = 50
        
        # Weighted MMI calculation
        mmi = (
            vix_score * 0.30 +      # VIX/Volatility: 30%
            pcr_score * 0.25 +      # Sentiment: 25%
            momentum_score * 0.30 + # Price momentum: 30%
            volume_score * 0.15     # Volume: 15%
        )
        
        # Determine label
        if mmi < 20:
            label = "EXTREME FEAR"
        elif mmi < 40:
            label = "FEAR"
        elif mmi < 60:
            label = "NEUTRAL"
        elif mmi < 80:
            label = "GREED"
        else:
            label = "EXTREME GREED"
        
        return {
            "mmi": round(mmi, 2),
            "label": label,
            "components": {
                "vix_score": round(vix_score, 2),
                "pcr_score": round(pcr_score, 2),
                "momentum_score": round(momentum_score, 2),
                "volume_score": round(volume_score, 2)
            },
            "status": "live",
            "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
        }
        
    except Exception as e:
        logger.error(f"MMI calculation failed: {e}")
        # Return neutral on error
        return {
            "mmi": 50.0,
            "label": "NEUTRAL",
            "components": {
                "vix_score": 50,
                "pcr_score": 50,
                "momentum_score": 50,
                "volume_score": 50
            },
            "status": "error",
            "message": str(e)
        }

@app.get("/api/ai/status")
async def get_ai_status():
    global engine_daily, engine_intraday
    return {
        "daily_loaded": engine_daily is not None and engine_daily.model is not None,
        "intraday_loaded": engine_intraday is not None and engine_intraday.model is not None
    }

@app.get("/api/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    """Returns current connectivity settings for the authenticated user."""
    user_id = user.get('uid')
    user_key = f"user:{user_id}:settings"
    
    current_settings = redis_client.get(user_key)
    settings = json.loads(current_settings) if current_settings else {}
    
    # Get user-specific broker instance
    user_broker = get_broker_client(user_id)
    profile = user_broker.profile()
    
    # Real-time check
    is_live_connected = False
    
    # Check if it's a real AngelClient and is connected
    from broker_factory import MockAngelClient
    if not isinstance(user_broker, MockAngelClient) and hasattr(user_broker, 'is_connected'):
        is_live_connected = user_broker.is_connected()
    else:
        is_live_connected = False

    # IP Protection: Mask credentials if not owner
    is_owner = user.get("email") == config.OWNER_EMAIL
    
    masked_creds = {
        "angel_client_id": settings.get("ANGEL_CLIENT_ID", config.ANGEL_CLIENT_ID) if is_owner else "RESTRICTED",
        "angel_api_key": settings.get("ANGEL_API_KEY", config.ANGEL_API_KEY) if is_owner else "RESTRICTED",
        "angel_totp_key": settings.get("ANGEL_TOTP_KEY", config.ANGEL_TOTP_KEY) if is_owner else "RESTRICTED",
        "angel_password": settings.get("ANGEL_PASSWORD", config.ANGEL_PASSWORD) if is_owner else "RESTRICTED"
    }

    return {
        "env": settings.get("ENV", "MOCK"),
        "active_broker": settings.get("ACTIVE_BROKER", "ANGEL"),
        "user_profile": profile,
        "angel_connected": is_live_connected,
        "is_owner": is_owner,
        "broker_status": profile.get("status", "UNKNOWN"),
        "angel_credentials": masked_creds,
        "whatsapp_credentials": {
            "whatsapp_phone": settings.get("WHATSAPP_PHONE", config.WHATSAPP_PHONE) if is_owner else "RESTRICTED",
            "whatsapp_api_key": settings.get("WHATSAPP_API_KEY", config.WHATSAPP_API_KEY) if is_owner else "RESTRICTED"
        },
        "telegram_credentials": {
            "telegram_bot_token": settings.get("TELEGRAM_BOT_TOKEN", config.TELEGRAM_BOT_TOKEN) if is_owner else "RESTRICTED",
            "telegram_chat_id": settings.get("TELEGRAM_CHAT_ID", config.TELEGRAM_CHAT_ID) if is_owner else "RESTRICTED"
        },
        "mode": config.TRADING_MODE
    }

@app.post("/api/settings/update")
async def update_settings(payload: Dict = Body(...), user: dict = Depends(verify_owner)):
    """
    Updates runtime settings for the authenticated user.
    Saves to Redis to persist across restarts and sessions.
    """
    user_id = user.get('uid')
    user_key = f"user:{user_id}:settings"
    
    # load existing settings or default
    current_settings = redis_client.get(user_key)
    settings = json.loads(current_settings) if current_settings else {}
    
    # Validating BEFORE Saving
    if "env" in payload and payload["env"] == "LIVE":
        logger.info(f"User {user_id} attempting switch to LIVE. Verifying Credentials...")
        
        # Get effective credentials (payload or existing)
        api_key = payload.get("angel_api_key") or settings.get("ANGEL_API_KEY")
        client_id = payload.get("angel_client_id") or settings.get("ANGEL_CLIENT_ID")
        password = payload.get("angel_password") or settings.get("ANGEL_PASSWORD")
        totp = payload.get("angel_totp_key") or settings.get("ANGEL_TOTP_KEY")
        
        if not (api_key and client_id and password and totp):
             raise HTTPException(status_code=400, detail="Missing Angel One Credentials for LIVE mode.")
             
        try:
             # Test Connection Explicitly
             from angel_client import AngelClient
             # Run blocking AngelClient init in a thread
             test_client = await asyncio.to_thread(AngelClient, api_key, client_id, password, totp)
             
             if not test_client.is_connected():
                  raise Exception("Broker Login Failed")
             logger.info("Credentials Verified. Allowing switch to LIVE.")
        except Exception as e:
             logger.error(f"LIVE Switch Blocked: {e}")
             raise HTTPException(status_code=400, detail=f"LIVE Mode Denied: Invalid Credentials. {str(e)}")

    # Update fields only after validation pass
    if "active_broker" in payload: settings["ACTIVE_BROKER"] = payload["active_broker"]
    
    # SAVE Angel Credentials if provided
    if "angel_api_key" in payload: 
        settings["ANGEL_API_KEY"] = payload["angel_api_key"]
        config.ANGEL_API_KEY = payload["angel_api_key"]
    if "angel_client_id" in payload: 
        settings["ANGEL_CLIENT_ID"] = payload["angel_client_id"]
        config.ANGEL_CLIENT_ID = payload["angel_client_id"]
    if "angel_password" in payload: 
        settings["ANGEL_PASSWORD"] = payload["angel_password"]
        config.ANGEL_PASSWORD = payload["angel_password"]
    if "angel_totp_key" in payload: 
        settings["ANGEL_TOTP_KEY"] = payload["angel_totp_key"]
        config.ANGEL_TOTP_KEY = payload["angel_totp_key"]

    if "whatsapp_phone" in payload:
        settings["WHATSAPP_PHONE"] = payload["whatsapp_phone"]
        config.WHATSAPP_PHONE = payload["whatsapp_phone"]
        
    if "whatsapp_api_key" in payload:
        settings["WHATSAPP_API_KEY"] = payload["whatsapp_api_key"]
        config.WHATSAPP_API_KEY = payload["whatsapp_api_key"]

    if "telegram_bot_token" in payload:
        settings["TELEGRAM_BOT_TOKEN"] = payload["telegram_bot_token"]
        config.TELEGRAM_BOT_TOKEN = payload["telegram_bot_token"]
        
    if "telegram_chat_id" in payload:
        settings["TELEGRAM_CHAT_ID"] = payload["telegram_chat_id"]
        config.TELEGRAM_CHAT_ID = payload["telegram_chat_id"]

    if "env" in payload: 
        settings["ENV"] = payload["env"]
        # Also update global config for persistence
        if payload["env"] in ["MOCK", "LIVE"]:
            config.ENV = payload["env"]
            
        if payload["env"] == "MOCK":
            settings["ACTIVE_BROKER"] = "NONE" # Deactivate real broker
            config.ACTIVE_BROKER = "MOCK_KITE"
        elif payload["env"] == "LIVE":
            settings["ACTIVE_BROKER"] = "ANGEL" # Auto-activate Angel One
            config.ACTIVE_BROKER = "ANGEL"
            
    # Persist to disk (so it survives backend restart even if Redis is Mock)
    config.save()
            
    # Save back to Redis
    redis_client.set(user_key, json.dumps(settings))
    logger.info(f"Updated settings for User: {user_id}")

    # Re-initialize broker for this user context
    # In a real app, we'd store the client instance in a connection pool mapped to user_id
    # For now, we just verify connectivity
    
    broker_connected = False
    error_msg = None
    
    try:
        # verifying connection with new settings
        # We need to temporarily force the factory to check these new settings
        # accessible via the redis key we just wrote
        # Run blocking factory in a thread
        test_client = await asyncio.to_thread(get_broker_client, user_id)
        
        # Strict Connectivity Check
        # We rely on is_connected() which verifies the session token
        if hasattr(test_client, 'is_connected') and test_client.is_connected():
             broker_connected = True
             # Update global client if connection is successful
             global kite
             kite = test_client
             logger.info(f"Global Broker Client updated for {user_id}")
        else:
             # Double check profile status just in case
             if hasattr(test_client, 'profile'):
                 p = test_client.profile()
                 if p.get('status') == 'LIVE':
                     broker_connected = True
                 else:
                     error_msg = getattr(test_client, 'login_error', "Broker Login Failed")
             else:
                 error_msg = "Broker Client Invalid"

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Broker Init Check Failed for {user_id}: {e}")

    return {
        "status": "success",
        "env": settings.get("ENV", "MOCK"),
        "active_broker": settings.get("ACTIVE_BROKER", "ANGEL"),
        "broker_connected": broker_connected,
        "error": error_msg
    }

@app.post("/api/settings/mode")
async def set_execution_mode(request: Request, mode: str = Body(..., embed=True), user: dict = Depends(verify_owner)):
    """
    Sets the execution mode (MANUAL or AUTO). Protected with IP validation.
    """
    # Optional IP validation
    from ip_middleware import ip_validator, get_client_ip
    client_ip = get_client_ip(request)
    if not ip_validator.check_trusted_ip(user.get('uid'), client_ip):
        logger.warning(f"🚫 Mode change blocked from untrusted IP: {client_ip}")
        raise HTTPException(status_code=403, detail=f"Access denied from IP {client_ip}")
    if mode in ["MANUAL", "AUTO"]:
        config.TRADING_MODE = mode
        
        # Redis-based persistence for Multi-Tenancy
        user_id = user.get('uid')
        user_key = f"user:{user_id}:settings"
        
        # Load existing settings to update just the mode
        try:
            current = redis_client.get(user_key)
            settings = json.loads(current) if current else {}
        except:
            settings = {}
            
        settings["TRADING_MODE"] = mode
        redis_client.set(user_key, json.dumps(settings))
        
        # Manage Watchdog Registration
        if mode == "AUTO":
            redis_client.sadd("set:active_auto_users", user_id)
            # Seed initial heartbeat so it doesn't immediately expire
            monitor.record_heartbeat(user_id)
        else:
            redis_client.srem("set:active_auto_users", user_id)
        
        # Legacy config save (can remove later)
        config.save()
        
        logger.info(f"User {user_id} switched Execution Mode to: {mode}")
        return {"status": "success", "mode": mode}
    return {"status": "error", "message": "Invalid mode"}

@app.post("/api/settings/disconnect")
async def disconnect_broker(broker: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    """
    Disconnects the specified broker. Protected.
    """
    if broker == "ANGEL":
        config.ANGEL_CLIENT_ID = ""
        config.ANGEL_API_KEY = ""
        config.ANGEL_TOTP_KEY = ""
        config.ANGEL_PASSWORD = ""
        
        # If Angel was active, revert to Mock
        if config.ACTIVE_BROKER == "ANGEL":
            config.ACTIVE_BROKER = "MOCK_KITE"
            
        config.save()
        
        # Re-init broker
        global kite
        kite = get_broker_client()
        
        logger.warning(f"User {user.get('uid')} disconnected Angel One.")
        return {"status": "success", "message": "Angel One Disconnected", "active_broker": config.ACTIVE_BROKER}
    
    return {"status": "ignored", "message": "Unknown broker"}

@app.get("/api/settings/trusted-ips")
async def get_trusted_ips(user: dict = Depends(get_current_user)):
    """Get list of trusted IPs for the authenticated user."""
    from ip_middleware import ip_validator
    user_id = user.get('uid')
    trusted_ips = ip_validator.get_trusted_ips(user_id)
    return {"status": "success", "trusted_ips": trusted_ips}

@app.post("/api/settings/trusted-ips/add")
async def add_trusted_ip(ip_address: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    """Add an IP address to the trusted list."""
    from ip_middleware import ip_validator
    user_id = user.get('uid')
    
    if ip_validator.add_trusted_ip(user_id, ip_address):
        return {"status": "success", "message": f"Added {ip_address} to trusted IPs"}
    else:
        raise HTTPException(status_code=400, detail="Invalid IP address format")

@app.post("/api/settings/trusted-ips/remove")
async def remove_trusted_ip(ip_address: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    """Remove an IP address from the trusted list."""
    from ip_middleware import ip_validator
    user_id = user.get('uid')
    ip_validator.remove_trusted_ip(user_id, ip_address)
    return {"status": "success", "message": f"Removed {ip_address} from trusted IPs"}

@app.post("/api/broker/emergency")
async def trigger_emergency(request: Request, user: dict = Depends(get_current_user)):
    """
    MANUAL KILL SWITCH Endpoint. Protected with IP validation.
    """
    # Optional IP validation - only if user has configured trusted IPs
    from ip_middleware import ip_validator, get_client_ip
    client_ip = get_client_ip(request)
    if not ip_validator.check_trusted_ip(user.get('uid'), client_ip):
        logger.warning(f"🚫 Emergency stop blocked from untrusted IP: {client_ip}")
        raise HTTPException(status_code=403, detail=f"Access denied from IP {client_ip}")
    logger.critical(f"🚨 EMERGENCY KILL SWITCH TRIGGERED BY {user.get('uid')} 🚨")
    global kite
    if hasattr(kite, 'liquidate_all_positions'):
        success = kite.liquidate_all_positions()
        if success:
            # Revert to Manual Mode automatically
            config.TRADING_MODE = "MANUAL"
            config.save()
            return {"status": "success", "message": "EMERGENCY LIQUIDATION COMPLETE", "mode": "MANUAL"}
        else:
            raise HTTPException(status_code=500, detail="Liquidation Failed")
    
    # Fallback if method doesn't exist but it's mock
    if config.ENV == "MOCK":
        config.TRADING_MODE = "MANUAL"
        config.save()
        return {"status": "success", "message": "MOCK EMERGENCY: Positions simulated cleared.", "mode": "MANUAL"}
        
    raise HTTPException(status_code=400, detail="Emergency Protocol not supported for current broker")

@app.post("/api/auth/logout")
async def logout_user():
    """
    Logs out the user. Currently stateless, but good for future session clearing.
    """
    return {"status": "success", "message": "Logged out"}

@app.post("/api/paper/trade")
async def place_paper_trade(trade: Dict = Body(...), user: dict = Depends(get_current_user)):
    """
    Logs a manual or simulated paper trade.
    """
    from paper_manager import paper_manager
    user_id = user.get('uid')
    
    # Optional: Check risk limits for paper trades too? (Maybe later)
    
    entry = paper_manager.place_trade(
        symbol=trade.get("symbol"),
        side=trade.get("side"),
        quantity=trade.get("quantity"),
        price=trade.get("price"),
        type=trade.get("type", "MARKET"),
        reasoning=trade.get("reasoning", ""),
        mode=trade.get("mode", "MANUAL")
    )
    
    if entry:
        return {"status": "success", "trade": entry}
    raise HTTPException(status_code=500, detail="Failed to log paper trade")

@app.post("/api/paper/close")
async def close_paper_trade(close_data: Dict = Body(...), user: dict = Depends(get_current_user)):
    """
    Closes an existing paper trade.
    """
    from paper_manager import paper_manager
    
    entry = paper_manager.close_trade(
        trade_id=close_data.get("trade_id"),
        exit_price=close_data.get("exit_price"),
        reasoning=close_data.get("reasoning", "")
    )
    
    if entry:
        return {"status": "success", "trade": entry}
    raise HTTPException(status_code=404, detail="Trade ID not found or failed to close")

@app.get("/api/paper/history")
async def get_paper_history(user: dict = Depends(get_current_user)):
    """
    Returns full paper trading history (Observatory Data).
    """
    from paper_manager import paper_manager
    return paper_manager.get_history()

@app.get("/api/paper/positions")
async def get_paper_positions(user: dict = Depends(get_current_user)):
    """
    Returns currently open paper positions.
    """
    from paper_manager import paper_manager
    return paper_manager.get_open_positions()

@app.post("/api/trading/autopilot")
async def execute_autopilot(
    symbol: str = Body(...), 
    quantity: int = Body(1),
    mode: str = Body("LIVE", embed=True),
    greedy: bool = Body(False, embed=True)
):
    """
    Expert-level execution: Only triggers an order if Sentiment + AI Technical signals match.
    Supports 'LIVE' (Broker) and 'PAPER' (Simulation) modes.
    """
    # 1. Run Intelligence Analysis
    try:
        analysis = await asyncio.to_thread(intelligence.run_analysis, symbol, greedy=greedy)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence Layer Failure: {str(e)}")
    
    signal = analysis.get("final_signal", "HOLD")
    if signal == "HOLD":
        return {
            "status": "HOLD",
            "reason": "Signal filter rejected trade (Mixed Sentiment/Technical analysis).",
            "analysis": analysis
        }
    
    # 2. Map Signal to Transaction Type
    tx_type = "BUY" if signal == "BUY" else "SELL"
    
    # 3. Execution based on Mode
    if mode == "PAPER":
        try:
            from paper_manager import paper_manager
            # Fetch current price for paper execution
            ltp = 0
            try:
                ltp = kite.ltp(symbol).get(symbol, {}).get('last_price', 0)
            except:
                pass # Fallback or use mock price
                
            entry = paper_manager.place_trade(
                symbol=symbol,
                side=tx_type,
                quantity=quantity,
                price=ltp,
                type="MARKET",
                reasoning=f"AUTO-PILOT: {analysis.get('trade_recommendation', {}).get('reasoning', 'AI Signal')}",
                mode="AUTO"
            )
            return {
                "status": "EXECUTED",
                "trade": entry,
                "signal": signal,
                "analysis": analysis,
                "mode": "PAPER"
            }
        except Exception as e:
            return {"status": "ERROR", "reason": str(e), "analysis": analysis}

    # LIVE / MOCK BROKER EXECUTION
    
    # 3b. Risk Engine Validation (Only for Broker trades)
    order_data = {
        "tradingsymbol": symbol,
        "transaction_type": tx_type,
        "quantity": quantity,
        "exchange": "NSE"
    }
    
    risk_val = risk_engine.validate_order(order_data)
    if not risk_val["allowed"]:
        return {
            "status": "RISK_REJECTED",
            "reason": risk_val["reason"],
            "analysis": analysis
        }
    
    # 4. Final Execution
    try:
        order_id = kite.place_order(
            variety="regular",
            exchange="NSE",
            tradingsymbol=symbol,
            transaction_type=tx_type,
            quantity=quantity,
            product="MIS",
            order_type="MARKET"
        )
        return {
            "status": "EXECUTED",
            "order_id": order_id,
            "signal": signal,
            "analysis": analysis,
            "mode": "BROKER"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broker Execution Error: {str(e)}")

@app.get("/api/ai/usage")
async def get_ai_usage():
    """
    Returns the current AI token usage statistics.
    """
    try:
        # Access the token manager from the intelligence layer
        return intelligence.token_manager.get_usage()
    except Exception as e:
        logger.error(f"Error fetching usage stats: {e}")
        return {"error": "Could not fetch usage statistics"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
