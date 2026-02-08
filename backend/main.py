from fastapi import FastAPI, HTTPException, Body, Depends, Request
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
from notifier import notifier
from redis_manager import redis_client
import os
import uvicorn
import logging
import json
import asyncio
from monitoring import monitor

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradeverseBackend")

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
        notifier.notify_sync("🚀 *Tradeverse Online*: Systems initialized and ready for execution.")
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
