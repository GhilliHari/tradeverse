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

def run_fast_summary():
    print('=' * 75)
    print('TRADEVERSE SYSTEM BACKTEST & PERFORMANCE AUDIT REPORT')
    print('=' * 75)

    dp = DataPipeline(symbol='^NSEBANK', interval='5m')
    dp.run_full_pipeline()
    
    if dp.cleaned_data is None or dp.cleaned_data.empty:
        print('Failed to fetch dataset.')
        return
        
    df = dp.cleaned_data
    engine = ModelEngine(model_type='intraday')
    
    naive_wins, naive_total = 0, 0
    regime_wins, regime_total = 0, 0
    atr_wins, atr_losses, atr_stale = 0, 0, 0

    step = 3
    for i in range(100, len(df) - 15, step):
        window = df.iloc[i : i + 1]
        future_window = df.iloc[i + 1 : i + 13]
        
        if window[engine.features].isna().any().any():
            continue
            
        res = engine.predict(window)
        prob = res['probability']
        is_ood = res['is_ood']
        regime = res.get('regime', 'NOMINAL')
        
        entry = window['Close'].values[-1]
        atr = window['ATR_14'].values[-1] if 'ATR_14' in window.columns else 120
        
        tp_fixed = entry * 1.0025
        sl_fixed = entry * 0.9985
        
        def check_outcome(fut, target, stop):
            for _, c in fut.iterrows():
                if c['High'] >= target: return 'WIN'
                if c['Low'] <= stop: return 'LOSS'
            return 'STALE'

        if prob > 0.52:
            naive_total += 1
            if check_outcome(future_window, tp_fixed, sl_fixed) == 'WIN':
                naive_wins += 1
                
        if prob > 0.58 and not is_ood and regime != 'CRASH':
            regime_total += 1
            if check_outcome(future_window, tp_fixed, sl_fixed) == 'WIN':
                regime_wins += 1

        if prob > 0.62 and not is_ood:
            tp_atr = entry + (atr * 1.8)
            sl_atr = entry - (atr * 1.2)
            out = check_outcome(future_window, tp_atr, sl_atr)
            if out == 'WIN': atr_wins += 1
            elif out == 'LOSS': atr_losses += 1
            else: atr_stale += 1

    wr_naive = (naive_wins / naive_total * 100) if naive_total > 0 else 0.0
    wr_regime = (regime_wins / regime_total * 100) if regime_total > 0 else 0.0
    atr_total = atr_wins + atr_losses + atr_stale
    wr_atr = (atr_wins / atr_total * 100) if atr_total > 0 else 0.0

    print('')
    print('Evaluation Period: Past 59 Days (' + str(len(df)) + ' 5-min candles)')
    print('Model Core: Sklearn Calibrated Ensemble (RF + HistGBDT + Regime OOD)')
    print('-' * 75)
    print('%-32s | %-8s | %-6s | %-10s | %-12s' % ('Strategy Tier', 'Trades', 'Wins', 'Win Rate', 'Status'))
    print('-' * 75)
    print('%-32s | %-8d | %-6d | %8.2f%%  | %-12s' % ('1. Naive Model (Fixed 0.52)', naive_total, naive_wins, wr_naive, 'BASELINE'))
    print('%-32s | %-8d | %-6d | %8.2f%%  | %-12s' % ('2. Regime-Aware OOD Filter', regime_total, regime_wins, wr_regime, 'FILTERED'))
    print('%-32s | %-8d | %-6d | %8.2f%%  | %-12s' % ('3. ATR Risk-Managed Execution', atr_total, atr_wins, wr_atr, 'HIGH-CONVICTION'))
    print('=' * 75)

if __name__ == '__main__':
    run_fast_summary()
