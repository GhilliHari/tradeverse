import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataFetcher")

def fetch_backtest_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=15) # Buffer for 10 trading days
    
    symbols = ["^NSEBANK", "HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "^INDIAVIX"]
    interval = "5m"
    
    logger.info(f"Fetching {interval} data for {symbols} from {start_date.date()} to {end_date.date()}")
    
    # Download data
    data = yf.download(symbols, start=start_date, end=end_date, interval=interval, group_by='ticker')
    
    if data.empty:
        logger.error("No data fetched. Check symbols or internet connection.")
        return
    
    # Save to CSV for the backtester
    data.to_csv("historical_backtest_data.csv")
    logger.info("✅ Data saved to historical_backtest_data.csv")

if __name__ == "__main__":
    fetch_backtest_data()
