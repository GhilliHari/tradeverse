import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline import DataPipeline
from model_engine import ModelEngine
from causality_engine import BankNiftyCausalityEngine
from regime_engine import IntradayRegimeEngine
from stability_filters import StabilityFilters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CORBacktester")

class CORBacktester:
    def __init__(self, symbol="SBIN.NS"):
        self.symbol = symbol
        self.model_engine = ModelEngine(model_type="intraday")
        self.causality_engine = BankNiftyCausalityEngine()
        self.regime_engine = IntradayRegimeEngine()
        self.stability_filters = StabilityFilters()
        
    def run_backtest(self, df, mode="BASELINE"):
        """
        mode: 'BASELINE' or 'COR'
        """
        trades = []
        logger.info(f"Running {mode} Backtest on {len(df)} candles...")
        
        # We need a small lookback for engines to warm up
        # 100 candles for stability/causality
        for i in range(100, len(df) - 10):
            window = df.iloc[i-50:i] # Lookback for features
            current_row = df.iloc[i:i+1]
            future_window = df.iloc[i+1:i+11] # 10 candle horizon
            
            # Skip if features are missing
            if window[self.model_engine.features].isna().any().any():
                continue
            
            # 1. Pipeline Execution
            signal = "HOLD"
            confidence = 0.0
            
            if mode == "BASELINE":
                # Baseline: Just use raw model prediction
                res = self.model_engine.predict(current_row)
                if res and res['probability'] >= 0.51:
                    signal = "BUY"
                    confidence = res['probability'] * 100
                    if i < 110: logger.info(f"BASELINE Signal: Prob={res['probability']:.4f}")
            else:
                # COR: Full Pipeline
                # A. Stability Filtering
                # (Normally applied to pipeline, here we simulate current state)
                
                # B. Regime Detection
                regime = self.regime_engine.classify_regime(current_row.index[0], current_row.iloc[0])
                
                # C. Causal Strength (Futures -> Spot)
                # In backtest we use raw window for causality
                causal_res = self.causality_engine.detect_causal_relationships(window)
                causal_strength = causal_res.get('overall_causal_strength', 0.5)
                
                # D. Predict with Confidence (Week 6)
                res = self.model_engine.predict_with_confidence(
                    current_row, 
                    regime=regime, 
                    causal_strength=causal_strength
                )
                
                if res:
                    confidence = res.get('confidence', 0.0)
                    # Use probability directly to see how COR filters it
                    if res['probability'] >= 0.51 and confidence >= 50.0:
                        signal = "BUY"
                    
                    if i < 110:
                         logger.info(f"COR Signal: Prob={res['probability']:.4f}, Conf={confidence:.1f}, Regime={regime}, Causal={causal_strength:.2f}")
            
            # 2. Outcome Tracking
            if signal == "BUY":
                entry_price = current_row['Close'].values[0]
                # Target: 0.2%, Stop: 0.1% (Scalping setup)
                tp = entry_price * 1.002
                sl = entry_price * 0.999
                
                won = False
                for _, candle in future_window.iterrows():
                    if candle['High'] >= tp:
                        won = True
                        break
                    if candle['Low'] <= sl:
                        break
                
                trades.append(1 if won else 0)
        
        if not trades:
            return {"win_rate": 0.0, "trade_count": 0}
            
        win_rate = (sum(trades) / len(trades)) * 100
        return {"win_rate": win_rate, "trade_count": len(trades)}

def main():
    tester = CORBacktester(symbol="SBIN.NS")
    dp = DataPipeline(symbol="SBIN.NS", interval="5m")
    
    print("\n--- COR Backtest: Baseline vs Augmented (14 Days) ---")
    
    # Fetch Data - Use yfinance directly to avoid broker setup issues
    import yfinance as yf
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    logger.info(f"Downloading data for {dp.symbol}...")
    df_raw = yf.download(dp.symbol, start=start_date, end=end_date, interval="5m")
    
    if df_raw.empty:
        print("Failed to load historical data.")
        return
        
    dp.raw_data = df_raw
    success = dp.clean_and_prepare()
    if not success or dp.cleaned_data is None or dp.cleaned_data.empty:
        print("Failed to load historical data.")
        return
        
    df = dp.cleaned_data
    
    # Fit Regime Engine on historical window
    tester.regime_engine.fit(df.head(500))
    
    # Run Backtests
    baseline = tester.run_backtest(df, mode="BASELINE")
    cor = tester.run_backtest(df, mode="COR")
    
    print("\n" + "="*40)
    print(f"BASELINE: Win Rate: {baseline['win_rate']:.2f}% | Trades: {baseline['trade_count']}")
    print(f"COR UPGRADE: Win Rate: {cor['win_rate']:.2f}% | Trades: {cor['trade_count']}")
    
    improvement = cor['win_rate'] - baseline['win_rate']
    print(f"IMPROVEMENT: {improvement:+.2f}% PRECISION BOOST")
    
    if cor['trade_count'] < baseline['trade_count'] and cor['win_rate'] > baseline['win_rate']:
        print("SUCCESS: COR successfully filtered noise and increased precision.")
    print("="*40)

if __name__ == "__main__":
    main()
