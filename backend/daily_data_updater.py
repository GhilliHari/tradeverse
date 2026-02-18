"""
Daily Data Updater Service

This module runs a background job to update historical data for all tracked symbols
daily after market close (4:00 PM IST).
"""

import asyncio
import logging
from datetime import datetime
from data_pipeline import DataPipeline

logger = logging.getLogger(__name__)

async def update_daily_data():
    """
    Updates all datasets daily after market close.
    """
    logger.info("🔄 Starting Daily Data Update Cycle...")
    
    symbols = ["^NSEBANK", "^NSEI"]
    
    try:
        for symbol in symbols:
            logger.info(f"Downloading latest data for {symbol}...")
            
            # 1. Update Daily Data (12Y)
            pipeline_daily = DataPipeline(symbol=symbol, interval="1d")
            # fetch_data() automatically handles download and caching if implemented
            # For now, we just trigger the pipeline
            if pipeline_daily.run_full_pipeline():
                metrics = pipeline_daily.get_data_quality_metrics()
                logger.info(f"✅ Updated {symbol} Daily: {metrics['total_records']} records (Freshness: {metrics['data_freshness_hours']}h)")
            else:
                logger.error(f"❌ Failed to update {symbol} Daily")
                
            # 2. Update Intraday Data (7D) - Optional, mainly for fast cache warming
            # pipeline_intra = DataPipeline(symbol=symbol, interval="1m")
            # pipeline_intra.run_full_pipeline()
            
        logger.info("✅ Daily Data Update Cycle Completed.")
        
    except Exception as e:
        logger.error(f"❌ Daily Data Update Failed: {e}")
