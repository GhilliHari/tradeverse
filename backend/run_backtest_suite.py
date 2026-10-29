import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline import DataPipeline
from model_engine import ModelEngine

logging.basicConfig(level=logging.ERROR)

def run_suite():
    print('=' * 70)
    print('🚀 TRADEVERSE INTEGRATED BACKTEST & STRATEGY SUITE 🚀')
    print('=' * 70)

    # Load 5m intraday data
    dp = DataPipeline(symbol='^NSEBANK', interval='5m')
    dp.run_full_pipeline()
    
    if dp.cleaned_data is None or dp.cleaned_data.empty:
        print('❌ Failed to fetch backtest dataset.')
        return
        
    df = dp.cleaned_data
    print(f'📊 Dataset Loaded: {len(df)} candles (5-min interval, ~59 Trading Days)')
    
    engine = ModelEngine(model_type='intraday')
    
    # 1. Comparative Strategy Backtest (Naive vs Regime-Aware)
    print('
--- 1. COMPARATIVE BACKTEST: Naive vs Regime-Aware ---')
    
    trades_naive = []
    trades_regime = []
    
    # Stride every 15 candles to evaluate signals across the timeline
    for i in range(100, len(df) - 20, 5):
        window = df.iloc[i : i + 1]
        future_window = df.iloc[i + 1 : i + 13] # 1 hour horizon
        
        if window[engine.features].isna().any().any():
            continue
            
        res = engine.predict(window)
        prob = res['probability']
        is_ood = res['is_ood']
        regime = res.get('regime', 'NOMINAL')
        
        entry_price = window['Close'].values[-1]
        tp = entry_price * 1.002
        sl = entry_price * 0.999
        
        # Helper outcome tracker
        def evaluate_trade(fut):
            for _, candle in fut.iterrows():
                if candle['High'] >= tp: return 1
                if candle['Low'] <= sl: return 0
            return 0

        # Naive: prob > 0.55
        if prob > 0.55:
            trades_naive.append(evaluate_trade(future_window))
            
        # Regime-Aware: prob > 0.60 and not OOD
        if prob > 0.60 and not is_ood and regime != 'CRASH':
            trades_regime.append(evaluate_trade(future_window))

    wr_naive = (sum(trades_naive)/len(trades_naive)*100) if trades_naive else 0.0
    wr_regime = (sum(trades_regime)/len(trades_regime)*100) if trades_regime else 0.0

    print(f'• Naive Strategy (Fixed Threshold 0.55):  Win Rate = {wr_naive:.2f}% | Total Trades = {len(trades_naive)}')
    print(f'• Regime-Aware Strategy (OOD Filter 0.60): Win Rate = {wr_regime:.2f}% | Total Trades = {len(trades_regime)}')
    print(f'  --> Precision Boost: {wr_regime - wr_naive:+.2f}%')

    # 2. Realistic Risk-Adjusted Execution Simulation
    print('
--- 2. REALISTIC ATR RISK-ADJUSTED EXECUTION ---')
    
    atr_trades = []
    wins, losses, stale = 0, 0, 0
    
    for i in range(100, len(df) - 20, 5):
        window = df.iloc[i:i+1]
        res = engine.predict(window)
        prob = res['probability']
        is_ood = res['is_ood']
        
        if prob > 0.62 and not is_ood:
            entry = window['Close'].values[0]
            atr = window['ATR_14'].values[0] if 'ATR_14' in window.columns else 120
            
            tp = entry + (atr * 1.8)
            sl = entry - (atr * 1.2)
            
            result = 'STALE'
            for j in range(1, 13):
                if i + j >= len(df): break
                fut_candle = df.iloc[i+j]
                if fut_candle['High'] >= tp:
                    result = 'WIN'
                    break
                elif fut_candle['Low'] <= sl:
                    result = 'LOSS'
                    break
            
            if result == 'WIN': wins += 1
            elif result == 'LOSS': losses += 1
            else: stale += 1
            atr_trades.append(result)

    total_high_conv = len(atr_trades)
    real_wr = (wins / total_high_conv * 100) if total_high_conv > 0 else 0.0

    print(f'• Total High-Conviction Signals: {total_high_conv}')
    print(f'• Successful Trades (Hit 1.8x ATR Target): {wins}')
    print(f'• Stopped Trades (Hit 1.2x ATR SL):     {losses}')
    print(f'• Expired/Stale Trades (1-hr Timeout):    {stale}')
    print(f'• REALISTIC WIN RATE: {real_wr:.2f}%')

    # Summary Report Table
    print('
' + '=' * 70)
    print('📈 FINAL STRATEGY COMPARISON SUMMARY')
    print('=' * 70)
    print(f"{'Strategy Mode':<30} | {'Total Trades':<12} | {'Win Rate (%)':<12} | {'Status':<10}")
    print('-' * 70)
    print(f"{'Naive Model (Fixed 0.55)':<30} | {len(trades_naive):<12} | {wr_naive:>10.2f}% | BASELINE")
    print(f"{'Regime-Aware Ensemble':<30} | {len(trades_regime):<12} | {wr_regime:>10.2f}% | ENHANCED")
    print(f"{'ATR Risk-Managed Execution':<30} | {total_high_conv:<12} | {real_wr:>10.2f}% | OPTIMIZED")
    print('=' * 70)

if __name__ == '__main__':
    run_suite()
