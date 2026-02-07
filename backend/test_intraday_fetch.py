import yfinance as yf
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)

print("Checking 1-minute data availability...")
try:
    # Check last 5 days (YF limit for 1m is usually 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    print(f"Fetching 1m data from {start_date} to {end_date}...")
    df = yf.download("^NSEBANK", start=start_date, end=end_date, interval="1m")
    
    if not df.empty:
        print(f"SUCCESS: Fetched {len(df)} 1-minute candles.")
        print(df.head())
        print(df.tail())
    else:
        print("FAILED: No data returned from yfinance.")

except Exception as e:
    print(f"ERROR: {e}")
