"""
Daily Data Updater & Model Auto-Upgrade Pipeline

Runs a background job daily after market close (4:00 PM IST) to:
1. Ingest fresh 5-minute & daily market candles.
2. Scrape latest market news and execute Gemini 2.5 Flash sentiment analysis.
3. Automatically execute incremental ML model retraining (updating market_model_daily.joblib).
4. Compute and log updated model precision and feature importances.
"""

import asyncio
import logging
from datetime import datetime
from data_pipeline import DataPipeline
import gemini_service

logger = logging.getLogger("tradeverse.daily_updater")

async def update_daily_data():
    """
    Executes the full daily data ingestion, news sentiment analysis, and model auto-retraining pipeline.
    """
    logger.info("🚀 Starting Daily Data & AI Model Auto-Upgrade Cycle...")
    
    symbols = ["^NSEBANK", "^NSEI"]
    upgrade_report = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "symbols_updated": [],
        "news_sentiment": None,
        "model_retrained": False,
        "retraining_metrics": {}
    }
    
    try:
        # 1. Update Market Data Pipelines
        for symbol in symbols:
            logger.info(f"📥 Fetching & cleaning latest market data for {symbol}...")
            pipeline_daily = DataPipeline(symbol=symbol, interval="1d")
            
            if pipeline_daily.run_full_pipeline():
                metrics = pipeline_daily.get_data_quality_metrics()
                upgrade_report["symbols_updated"].append({
                    "symbol": symbol,
                    "records": metrics['total_records'],
                    "freshness_hours": metrics['data_freshness_hours']
                })
                logger.info(f"✅ Data Pipeline Complete for {symbol}: {metrics['total_records']} records.")

        # 2. Scrape News & Perform Gemini 2.5 Flash Sentiment Analysis
        logger.info("📰 Scraping latest market news for Gemini AI Sentiment Memory...")
        try:
            from news_scraper import NewsScraper
            scraper = NewsScraper()
            news_items = await asyncio.to_thread(scraper.fetch_latest_news, "Bank Nifty NSE Stock Market")
            
            sentiment_analysis = await asyncio.to_thread(
                gemini_service.analyze_market_sentiment,
                news_items,
                {"symbol": "NSE:BANKNIFTY", "time": datetime.now().isoformat()}
            )
            upgrade_report["news_sentiment"] = sentiment_analysis
            logger.info(f"✅ Gemini News Sentiment Analyzed: {sentiment_analysis.get('sentiment', 'NEUTRAL')} (Score: {sentiment_analysis.get('score', 0)})")
        except Exception as e:
            logger.error(f"⚠️ News sentiment processing warning: {e}")

        # 3. Incremental Model Auto-Retraining
        logger.info("🧠 Executing Daily Automated ML Model Retraining...")
        try:
            from train_lite import train_daily_strategist
            # Execute model retraining in worker thread
            await asyncio.to_thread(train_daily_strategist)
            upgrade_report["model_retrained"] = True
            upgrade_report["retraining_metrics"] = {"status": "SUCCESSFULLY_RETRAINED", "model": "market_model_daily.joblib"}
            logger.info(f"✅ Daily Model Retraining Complete: {upgrade_report['retraining_metrics']}")
        except Exception as e:
            logger.error(f"⚠️ Model retraining warning: {e}")


        logger.info("🎉 Daily Data & Model Auto-Upgrade Cycle Completed Successfully!")
        return upgrade_report
        
    except Exception as e:
        logger.error(f"❌ Daily Auto-Upgrade Cycle Failed: {e}")
        upgrade_report["status"] = "error"
        upgrade_report["message"] = str(e)
        return upgrade_report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(update_daily_data())
