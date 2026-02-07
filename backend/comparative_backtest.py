import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline import DataPipeline
from model_engine import ModelEngine
from broker_factory import get_broker_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComparativeBacktest")

def run_backtest(df, engine, strategy_type="naive"):
    """
    Runs a backtest on the given dataframe.
    strategy_type: 'naive' (fixed threshold) or 'regime_aware' (OOD + Dynamic)
    """
    trades = []
    
    # We analyze the last 1000 candles
    for i in range(len(df) - 30):
        # Current Slice
        window = df.iloc[i : i + 20]
        future_window = df.iloc[i + 20 : i + 30] # 10 min horizon
        
        # 1. Get Predictions
        # Skip if window has NaNs in required features
        if window[engine.features].isna().any().any():
            continue
            
        result = engine.predict(window)
        prob = result['probability']
        is_ood = result['is_ood']
        
        # Strategy Logic
        signal = "HOLD"
        
        if strategy_type == "naive":
            # Naive: Just use a fixed 0.55 threshold, ignore regime
            if prob > 0.55:
                signal = "BUY"
        else:
            # Regime Aware: 0.60 threshold + OOD filter
            if prob > 0.60 and not is_ood:
                signal = "BUY"
        
        if signal == "BUY":
            entry_price = window['Close'].values[-1]
            tp = entry_price * 1.002
            sl = entry_price * 0.999
            
            # Outcome
            won = False
            for _, candle in future_window.iterrows():
                if candle['High'] >= tp:
                    won = True
                    break
                if candle['Low'] <= sl:
                    break
            
            trades.append(1 if won else 0)
            
    if not trades:
        return 0.0, 0
        
    win_rate = (sum(trades) / len(trades)) * 100
    return win_rate, len(trades)

def main():
    dp = DataPipeline()
    # Initialize Broker for data fetch
    broker = get_broker_client()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # yfinance symbol to fetch_live_data_broker
    dp.symbol = "^NSEBANK"
    dp.interval = "1m"
    dp.fetch_live_data_broker(broker, start_date.strftime("%Y-%m-%d %H:%M"), end_date.strftime("%Y-%m-%d %H:%M"))
    
    if dp.cleaned_data is None or dp.cleaned_data.empty:
        print("Failed to load data.")
        return
        
    df = dp.cleaned_data.tail(1000)
    engine = ModelEngine(model_type="intraday")
    
    print(f"\n--- Comparative Backtest: Navie vs Regime-Aware (1000 candles) ---")
    
    wr_naive, count_naive = run_backtest(df, engine, "naive")
    print(f"NAIVE STRATEGY:  Win Rate: {wr_naive:.2f}% | Total Trades: {count_naive}")
    
    wr_aware, count_aware = run_backtest(df, engine, "regime_aware")
    print(f"REGIME-AWARE:    Win Rate: {wr_aware:.2f}% | Total Trades: {count_aware}")
    
    improvement = wr_aware - wr_naive
    print(f"\nPRECISION BOOST: {improvement:+.2f}%")
    
    if improvement > 0:
        print("SUCCESS: Regime-awareness successfully filtered out low-probability trades.")
    else:
        print("NOTE: Market may be currently very stable, minimizing the impact of regime filtering.")

if __name__ == "__main__":
    main()
