from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import importlib.metadata
# Polyfill for Python 3.9 compatibility with some google-auth/api-core versions
if not hasattr(importlib.metadata, 'packages_distributions'):
    importlib.metadata.packages_distributions = lambda: {}
from mock_kite import MockKiteConnect
from risk_engine import RiskEngine
from agent_layer import IntelligenceLayer
from data_pipeline import DataPipeline
from model_engine import ModelEngine
from broker_factory import get_broker_client
from news_scraper import NewsScraper
from config import config
from auth_middleware import get_current_user
import os
import uvicorn
import logging
import redis
import json

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradeverseBackend")

# Initialize Redis
redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

app = FastAPI(title="Tradeverse Agentic Platform")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
        logger.info("⚙️ Starting Background System Initialization...")
        # broker_factory handles credentials from Redis/Config
        kite = get_broker_client()
        risk_engine = RiskEngine(daily_loss_limit=config.DAILY_LOSS_LIMIT, max_position_size=config.MAX_POSITION_SIZE)
        intelligence = IntelligenceLayer(config.GEMINI_API_KEY)
        initialization_status["ready"] = True
        logger.info("✅ Systems Initialized & Ready.")
    except Exception as e:
        logger.error(f"❌ Initialization Failed: {e}")
        initialization_status["error"] = str(e)

# Caches for data pipeline and model training
pipeline_cache = {}
training_metrics = {}

def normalize_symbol(symbol: str):
    """Maps frontend symbols to yfinance symbols."""
    u_symbol = symbol.upper()
    if "BANKNIFTY" in u_symbol or "BANK" in u_symbol:
        return "^NSEBANK"
    if "NIFTY" in u_symbol and "BANK" not in u_symbol:
        return "^NSEI"
    return symbol

import asyncio
from monitoring import monitor

@app.on_event("startup")
async def startup_event():
    # Start systems initialization in background so we don't block port bind
    asyncio.create_task(initialize_systems())
    # Start watchdog
    asyncio.create_task(run_watchdog())

async def run_watchdog():
    while True:
        try:
            await asyncio.to_thread(monitor.check_watchdog)
        except Exception as e:
            logger.error(f"Watchdog Error: {e}")
        await asyncio.sleep(5)

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

@app.post("/api/monitoring/heartbeat")
async def heartbeat(user: dict = Depends(get_current_user)):
    """Receives pulse from frontend to keep Auto-Mode alive."""
    monitor.record_heartbeat(user.get('uid'))
    return {"status": "pulse_received"}

@app.get("/api/market/ltp/{symbol}")
async def get_ltp(symbol: str):
    """
    Fetches the Last Traded Price for a symbol.
    """
    try:
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
    return risk_engine.get_risk_status()

@app.post("/api/order/place")
async def place_order(order_data: Dict = Body(...)):
    """
    Validates and places an order via the broker.
    """
    # 1. Pre-order risk validation
    validation = risk_engine.validate_order(order_data)
    if not validation["allowed"]:
        return {"status": "REJECTED", "reason": validation["reason"]}

    # 2. Place order via broker (MockKite)
    try:
        order_id = kite.place_order(
            variety="regular",
            exchange=order_data.get("exchange", "NSE"),
            tradingsymbol=order_data.get("tradingsymbol"),
            transaction_type=order_data.get("transaction_type"),
            quantity=order_data.get("quantity"),
            product=order_data.get("product", "MIS"),
            order_type=order_data.get("order_type", "MARKET"),
            price=order_data.get("price")
        )
        return {"status": "COMPLETE", "order_id": order_id, "symbol": order_data.get("tradingsymbol")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broker Error: {str(e)}")

@app.post("/api/risk/circuit-breaker")
async def toggle_circuit_breaker(active: bool = Body(...), reason: str = Body("Manual trigger")):
    """
    Toggles the trading circuit breaker.
    """
    status = risk_engine.trigger_circuit_breaker(active, reason)
    return status

@app.get("/api/intelligence/analyze/{symbol}")
async def analyze_market(symbol: str):
    """
    Runs the full agentic committee analysis for a symbol.
    """
    try:
        result = intelligence.run_analysis(symbol)
        # result is a dict from LangGraph. We can inject regime here if needed, 
        # but the aggregator already has access to technical_context which we'll update.
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence Layer Error: {str(e)}")

@app.get("/api/market/options/{symbol}")
async def get_options(symbol: str):
    return kite.get_option_chain(symbol)

@app.get("/api/orders")
async def get_orders():
    """
    Fetches the order book from the active broker.
    """
    try:
        return kite.orders()
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        return []

@app.get("/api/data/pipeline/trigger")
async def trigger_pipeline(symbol: str = "NSE:BANKNIFTY"):
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
        scraper = NewsScraper()
        # Run in executor to avoid blocking async loop since requests is sync
        # For this prototype, calling directly is acceptable but async wrapper is better.
        # fast implementation:
        news = scraper.fetch_latest_news()
        return news
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        return []

# Initializes Engines
engine_daily = ModelEngine(model_type="daily")
engine_intraday = ModelEngine(model_type="intraday")

# Load artifacts on startup (if available)
engine_daily.load_artifacts()
engine_intraday.load_artifacts()

@app.get("/api/ai/predict_hybrid")
async def predict_hybrid(symbol: str = "NSE:BANKNIFTY"):
    """
    Returns Hybrid Strategic Analysis:
    - Daily Stratgist: Broad Trend (Bullish/Bearish)
    - Intraday Sniper: Immediate Entry Signal (Buy/Wait)
    """
    norm_symbol = normalize_symbol(symbol)
    response = {
        "symbol": norm_symbol,
        "daily": {"status": "NEUTRAL", "prob": 0.0},
        "intraday": {"status": "WAIT", "prob": 0.0},
        "final_action": "WAIT",
        "regime": "NOMINAL"
    }

    # 1. Run Daily Pipeline
    try:
        dp_daily = DataPipeline(norm_symbol, interval="1d")
        if dp_daily.run_full_pipeline(): # Fetches latest data
             # Get last row
             latest_daily = dp_daily.cleaned_data.iloc[[-1]]
             pred_daily = engine_daily.predict(latest_daily)

             if pred_daily:
                 response["daily"] = {
                     "status": "BULLISH" if pred_daily["prediction"] == 1 else "BEARISH",
                     "prob": pred_daily["probability"],
                     "conviction": pred_daily["conviction"]
                 }
                 response["regime"] = pred_daily.get("regime", "NOMINAL")
                 
             # Extract Tactical Metrics (Key Levels & Greeks Proxy) - Always populate if data exists
             try:
                 response["tactical"] = {
                     "pivot": round(latest_daily["Pivot"].values[0], 2) if "Pivot" in latest_daily else 0,
                     "r1": round(latest_daily["R1"].values[0], 2) if "R1" in latest_daily else 0,
                     "s1": round(latest_daily["S1"].values[0], 2) if "S1" in latest_daily else 0,
                     "rsi": round(latest_daily["RSI"].values[0], 2) if "RSI" in latest_daily else 50,
                     "atr": round(latest_daily["ATR_14"].values[0], 2) if "ATR_14" in latest_daily else 0,
                     "trend_state": int(latest_daily["Trend_State"].values[0]) if "Trend_State" in latest_daily else 0
                 }
             except Exception as e:
                 logger.warning(f"Could not extract tactical metrics: {e}")
                 response["tactical"] = {}
    except Exception as e:
        logger.error(f"Daily Model Error: {e}")

    # 2. Run Intraday Pipeline
    try:
        dp_intra = DataPipeline(norm_symbol, interval="1m")
        if dp_intra.run_full_pipeline():
             latest_intra = dp_intra.cleaned_data.iloc[[-1]]
             pred_intra = engine_intraday.predict(latest_intra)
             if pred_intra:
                 response["intraday"] = {
                     "status": "BUY" if pred_intra["prediction"] == 1 else "WAIT",
                     "prob": pred_intra["probability"],
                     "conviction": pred_intra["conviction"], # HIGH only if OOD check passes
                     "is_good_setup": pred_intra["prediction"] == 1
                 }
                 # If intraday detects a crash/volatile regime, it can override daily regime
                 if pred_intra.get("regime") in ["CRASH", "VOLATILE"]:
                     response["regime"] = pred_intra["regime"]
    except Exception as e:
        logger.error(f"Intraday Model Error: {e}")

    # 3. Synthesis
    daily_bias = response["daily"]["status"]
    intra_signal = response["intraday"]["status"]
    
    if daily_bias == "BULLISH" and intra_signal == "BUY":
        response["final_action"] = "STRONG_BUY"
    elif intra_signal == "BUY": # Sniper takes entries even if Daily is weak? Maybe reckless.
        response["final_action"] = "SCALP_BUY (Counter-Trend)"
    elif daily_bias == "BULLISH":
        response["final_action"] = "WAIT_FOR_DIP"
    else:
        response["final_action"] = "AVOID"

    return response

@app.get("/api/ai/train")
async def train_model(symbol: str = "NSE:BANKNIFTY"):
    """
    Triggers the Hybrid AI Training process using the loaded data pipeline.
    """
    normalized_symbol = normalize_symbol(symbol)
    
    # 1. Check if pipeline data is available
    if normalized_symbol not in pipeline_cache:
        # Auto-trigger pipeline if missing
        logger.info(f"Pipeline cache miss for {normalized_symbol}. Triggering ingestion...")
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
        metrics = engine_daily.train(pipeline.train_data, pipeline.test_data)
        
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
    return {
        "daily_loaded": engine_daily.model is not None,
        "intraday_loaded": engine_intraday.model is not None
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
    if hasattr(user_broker, 'is_connected'):
        is_live_connected = user_broker.is_connected()
    else:
        # Fallback logic
        is_live_connected = bool(settings.get("ANGEL_API_KEY")) or settings.get("ENV") == "MOCK"

    return {
        "env": settings.get("ENV", "MOCK"),
        "active_broker": settings.get("ACTIVE_BROKER", "ANGEL"),
        "user_profile": profile,
        "angel_connected": is_live_connected,
        "broker_status": profile.get("status", "UNKNOWN"),
        "angel_credentials": {
            "angel_client_id": settings.get("ANGEL_CLIENT_ID", ""),
            "angel_api_key": settings.get("ANGEL_API_KEY", ""),
            "angel_totp_key": settings.get("ANGEL_TOTP_KEY", ""),
            "angel_password": settings.get("ANGEL_PASSWORD", "")
        },
        "mode": config.TRADING_MODE # App-wide mode (or could be user-specific)
    }

@app.post("/api/settings/update")
async def update_settings(payload: Dict = Body(...), user: dict = Depends(get_current_user)):
    """
    Updates runtime settings for the authenticated user.
    Saves to Redis to persist across restarts and sessions.
    """
    user_id = user.get('uid')
    user_key = f"user:{user_id}:settings"
    
    # load existing settings or default
    current_settings = redis_client.get(user_key)
    settings = json.loads(current_settings) if current_settings else {}
    
    # Update fields
    if "active_broker" in payload: settings["ACTIVE_BROKER"] = payload["active_broker"]
    if "env" in payload: settings["ENV"] = payload["env"]
    if "angel_client_id" in payload: settings["ANGEL_CLIENT_ID"] = payload["angel_client_id"]
    if "angel_password" in payload: settings["ANGEL_PASSWORD"] = payload["angel_password"]
    if "angel_api_key" in payload: settings["ANGEL_API_KEY"] = payload["angel_api_key"]
    if "angel_totp_key" in payload: settings["ANGEL_TOTP_KEY"] = payload["angel_totp_key"]
    
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
        test_client = get_broker_client(user_id)
        
        # Basic connectivity check
        if hasattr(test_client, 'ltp'):
            try:
                ping = test_client.ltp("NSE:NIFTY 50")
                if ping:
                    broker_connected = True
            except:
                pass
        
        if hasattr(test_client, 'profile'):
             # fallback check
             if test_client.profile():
                 broker_connected = True

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
async def set_execution_mode(request: Request, mode: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
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

@app.post("/api/trading/autopilot")
async def execute_autopilot(symbol: str = Body(...), quantity: int = Body(1)):
    """
    Expert-level execution: Only triggers an order if Sentiment + AI Technical signals match.
    """
    # 1. Run Intelligence Analysis
    try:
        analysis = intelligence.run_analysis(symbol)
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
    
    # 3. Risk Engine Validation
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
            "analysis": analysis
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
