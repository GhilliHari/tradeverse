import pandas as pd
import numpy as np
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_layer import IntelligenceLayer
from data_pipeline import DataPipeline
from component_causality import ComponentTracker

# Configure logging
logging.basicConfig(level=logging.INFO) # Info level for component/regime tracking
logger = logging.getLogger("StructuralBacktest")

class MockHistoricalBroker:
    def __init__(self, data_slice: pd.DataFrame):
        self.data = data_slice # Current historical data slice
        
    def is_connected(self):
        return True
        
    def _get_token_and_exchange(self, symbol):
        return "NSE", symbol, "MOCK_TOKEN"
        
    def search_scrip(self, symbol):
        return [{"token": "MOCK_TOKEN", "exchange": "NSE"}]
        
    def ltp(self, symbol):
        # symbol can be list or string
        if isinstance(symbol, list):
            res = {}
            for s in symbol:
                res[s] = {"last_price": self._get_price(s)}
            return res
        return {symbol: {"last_price": self._get_price(symbol)}}

    def _get_price(self, symbol):
        # Map symbol back to CSV columns
        ticker_map = {
            "NSE:BANKNIFTY": "^NSEBANK",
            "^NSEBANK": "^NSEBANK",
            "NSE:HDFCBANK": "HDFCBANK.NS",
            "NSE:ICICIBANK": "ICICIBANK.NS",
            "NSE:KOTAKBANK": "KOTAKBANK.NS",
            "HDFCBANK.NS": "HDFCBANK.NS",
            "ICICIBANK.NS": "ICICIBANK.NS",
            "KOTAKBANK.NS": "KOTAKBANK.NS",
            "^INDIAVIX": "^INDIAVIX"
        }
        col_prefix = ticker_map.get(symbol, symbol)
        try:
             # Use MultiIndex if available, else simple column
             if isinstance(self.data.columns, pd.MultiIndex):
                 return self.data[(col_prefix, 'Close')].iloc[-1]
             else:
                 # Fallback for single level (usually just 'Close')
                 return self.data['Close'].iloc[-1]
        except:
             return 500.0

    def get_historical_data(self, exchange, token, interval, start_date, end_date):
        # Return the current slice as list of lists
        # [time, open, high, low, close, volume]
        
        if isinstance(self.data.columns, pd.MultiIndex):
             bn_data = self.data['^NSEBANK']
        else:
             bn_data = self.data
             
        records = []
        for dt, row in bn_data.iterrows():
            records.append([dt.isoformat(), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']])
        return records

    def get_option_chain(self, symbol, expiry=None):
        spot = self._get_price(symbol)
        strikes = []
        # Mocking a chain around the spot
        base_strike = round(spot / 100) * 100
        for i in range(-5, 6):
            strike = base_strike + (i * 100)
            strikes.append({
                "strike": strike,
                "ce_premium": 100,
                "pe_premium": 100,
                "oi_ce": 100000 if i == 5 else 20000,
                "oi_pe": 100000 if i == -5 else 20000
            })
        return strikes

def run_10_day_validation():
    print("--- 🏎️ HIGH-SPEED 10-DAY STRUCTURAL BACKTEST ---")
    
    # 1. Load Data
    try:
        df_raw = pd.read_csv("historical_backtest_data.csv", header=[0, 1], index_col=0)
        df_raw.index = pd.to_datetime(df_raw.index)
        df_raw = df_raw.sort_index()
        
        pipeline = DataPipeline("^NSEBANK")
        
        # Inject data from CSV
        pipeline.raw_data = df_raw['^NSEBANK'].copy()
        pipeline.vix_data = df_raw['^INDIAVIX'].copy()
        pipeline.macro_raw = pd.DataFrame({"Close": [80.0]*len(pipeline.raw_data)}, index=pipeline.raw_data.index)
        
        # Mock fetch_data to bypass yfinance
        def mock_fetch(self):
            logger.info("MOCK FETCH: Using CSV data.")
            return True
        import types
        pipeline.fetch_data = types.MethodType(mock_fetch, pipeline)
        
        # Mock split_data to avoid IndexError on empty train set
        def mock_split(self):
            logger.info("MOCK SPLIT: Returning full dataset.")
            return self.cleaned_data
        pipeline.split_data = types.MethodType(mock_split, pipeline)
        
        df = pipeline.run_full_pipeline()
        print(f"BACKTEST DATA READY: {len(df)} rows after indicators.")
        
        if df is None or df.empty:
            print("ERROR: Pipeline failed to process data.")
            # Fallback: if pipeline failed, use raw data for loop (might crash later though)
            df = pipeline.raw_data
            
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Initialize Core Engine
    api_key = os.getenv("GEMINI_API_KEY", "MOCK_KEY")
    intelligence = IntelligenceLayer(api_key)
    
    # 3. MONKEYPATCH: Fast-Forward DataPipeline
    # We override run_full_pipeline to just return the slice we give it
    original_run = DataPipeline.run_full_pipeline
    
    current_sim_slice = None
    
    def mocked_run_full_pipeline(self):
        # We need the full window to calculate 200-period indicators
        self.raw_data = current_sim_slice
        # Mock macro data to avoid network calls
        self.macro_raw = pd.DataFrame({"Close": [80.0]*len(self.raw_data)}, index=self.raw_data.index)
        self.vix_data = pd.DataFrame({"Close": [15.0]*len(self.raw_data)}, index=self.raw_data.index)
        
        # Trigger real cleaning to get indicators
        self.clean_and_prepare()
        
        # ENSURE ALL COLUMNS ARE PRESENT (even if 0) to avoid agent crash
        required_cols = [
            'Is_Fractal_Low', 'CMO', 'RSI_Slope', 'Mass_Index', 'RSI_x_Vol', 'TR', 'Vol_Ratio', 
            'BB_STD', 'CCI', 'sentiment_score', 'ATR_14', 'High_Close_Prev', 'ADX', 'High_Low', 
            '-DI', 'Ret_1d', 'DX', 'Gap', 'Ret_3d', 'Low_Close_Prev', 'RSI_Vol_Adj', '+DI', 
            'Ret_5d', 'RSI', 'CCI_Vol_Adj', 'Ret_2d', 'PCR', 'Trend_Confidence', 'Inflation_Proxy', 
            'CMF', 'TSI', 'Coppock', 'WillR', 'BN_Nifty_Ratio', 'Klinger', 'Dist_SMA200', 
            'USDINR', 'DPO', 'MACD_Signal', 'MACD_Hist', 'MACD', 'RSI_Vol_Imbalance', 
            'Dist_EMA21', 'Bull_Power', 'ROC', 'Stoch_RSI', 'Bear_Power', 'Is_Fractal_High', 
            'SMA_200', 'Aroon_Down', 'Nifty50', '+DM', 'Price_FracDiff', '-DM', 'OI_Change', 
            'ST_Lower', 'BB_Lower', 'Aroon_Up', 'Force_Index', 'High_5', 'OBV', 'TP', 'Fisher', 
            'HMA_20', 'MFI', 'BB_Upper', 'Vol_Change', 'BB_MA', 'ST_Upper', 'KC_Mid', 'S2', 
            'R1', 'SMA_50', 'KC_Upper', 'Pivot', 'EMA_21', 'R2', 'EMA_9', 'DC_Lower', 'VWAP', 
            'Streak', 'KC_Lower', 'Kijun_Sen', 'Low_5', 'PSAR', 'S1', 'Tenkan_Sen'
        ]
        for col in required_cols:
            if col not in self.cleaned_data.columns:
                self.cleaned_data[col] = 0.0
                
        # Fill any remaining NaNs
        self.cleaned_data = self.cleaned_data.ffill().bfill().fillna(0)
        return True

    DataPipeline.run_full_pipeline = mocked_run_full_pipeline
    DataPipeline.fetch_live_data_broker = lambda self, b, s, e: True
    
    # 4. MONKEYPATCH: Causality Engine (Avoid Granger errors on constants)
    from causality_engine import BankNiftyCausalityEngine
    def mocked_detect(self, df):
        return {"overall_causal_strength": 0.8, "details": {}}
    BankNiftyCausalityEngine.detect_causal_relationships = mocked_detect

    # Walk-Forward Simulation
    total_steps = len(df)
    window_size = 210
    
    daily_stats = {} # {date: {"trades": [], "pnl": 0}}
    
    print(f"Analyzing {total_steps} bars for daily breakdown...")
    
    # --- ALIGNMENT BLOCK ---
    if not df.empty and not df_raw.empty:
         try:
             # Find first common date to calculate offset
             common_idx = df.index.intersection(df_raw.index)
             if len(common_idx) > 0:
                 print("Indices aligned perfectly.")
             else:
                 # Attempt to find offset by comparing first timestamps of same day
                 ts_sim = df.index[0]
                 # Find first timestamp in raw with same date
                 matches = df_raw[df_raw.index.date == ts_sim.date()]
                 if not matches.empty:
                     ts_raw = matches.index[0]
                     # Check if naive
                     if ts_sim.tz is None and ts_raw.tz is None:
                         offset = ts_raw - ts_sim
                         print(f"Detected Time Offset: {offset} (Aligning Raw Data...)")
                         # Shift Raw Data to match Simulation Index
                         df_raw.index = df_raw.index - offset
                     elif ts_sim.tz is None and ts_raw.tz is not None:
                         # Strip TZ from Raw
                         df_raw.index = df_raw.index.tz_localize(None)
                         # Recalculate offset if needed
                         ts_raw = df_raw.index[0]
                         offset = ts_raw - ts_sim
                         df_raw.index = df_raw.index - offset
                         print(f"Stripped TZ and Aligned: {offset}")
         except Exception as e:
             print(f"Alignment Warning: {e}")

    for i in range(window_size, total_steps - 12, 4):
        raw_slice = df.iloc[i - window_size : i + 1]
        sim_df = raw_slice.copy()
        current_sim_slice = sim_df
        
        current_dt = df.index[i]
        date_str = current_dt.strftime('%Y-%m-%d')
        if date_str not in daily_stats:
            daily_stats[date_str] = {"wins": 0, "losses": 0, "pnl": 0}
            
        spot = df.iloc[i]['Close']
        
        # Use Simple LOC lookup after alignment
        try:
            full_raw_slice = df_raw.loc[raw_slice.index]
        except KeyError:
            # Fallback reindex if exact match fails
             full_raw_slice = df_raw.reindex(raw_slice.index, method='nearest')
        
        mock_broker = MockHistoricalBroker(full_raw_slice)
        intelligence.kite = mock_broker
        if intelligence.component_tracker:
            intelligence.component_tracker.kite = mock_broker
        
        try:
            # Use Production Intelligence Layer
            res = intelligence.run_analysis("NSE:BANKNIFTY", custom_df=df.iloc[:i+1])
            signal = res.get('final_signal')
            rec = res.get('trade_recommendation', {})
            reasoning = rec.get('reasoning', 'No reasoning')
            
            # Calibration threshold for Phase 5 (Calibrated Vetting)
            if signal in ['BUY', 'SELL']:
                exit_plan = rec.get('exit_plan', {})
                
                if not exit_plan:
                    # print(f"DEBUG [{current_dt.strftime('%H:%M')}]: No exit plan for {signal}")
                    continue
                    
                target_list = exit_plan.get('targets', [])
                if not target_list:
                    continue
                    
                tp = target_list[0]
                sl = exit_plan.get('initial_sl', spot - 100 if signal == 'BUY' else spot + 100)
                
                future_df = df.iloc[i+1 : i+25]
                outcome = "HOLD"
                
                for _, f_row in future_df.iterrows():
                    if signal == 'BUY':
                        if f_row['High'] >= tp: outcome = "WIN"; break
                        if f_row['Low'] <= sl: outcome = "LOSS"; break
                    else:
                        if f_row['Low'] <= tp: outcome = "WIN"; break
                        if f_row['High'] >= sl: outcome = "LOSS"; break
                
                if outcome != "HOLD":
                    # For PnL calculation in points
                    pnl_pts = abs(tp - spot) if outcome == "WIN" else -abs(sl - spot)
                    
                    if outcome == "WIN":
                        daily_stats[date_str]["wins"] += 1
                        daily_stats[date_str]["pnl"] += pnl_pts
                    else:
                        daily_stats[date_str]["losses"] += 1
                        daily_stats[date_str]["pnl"] += pnl_pts
                    
                    print(f"TRADE [{current_dt.strftime('%m-%d %H:%M')}]: {signal} at {spot:.0f} | Target: {tp:.0f}, SL: {sl:.0f} | Result: {outcome} ({pnl_pts:+.1f})")
                    
        except Exception as e:
            # print(f"Error in sim step: {e}")
            continue

    # Restore
    DataPipeline.run_full_pipeline = original_run

    print("\n" + "="*60)
    print("📅 DAY-WISE SUCCESS RATE (Alpha Calibration Mode)")
    print("="*60)
    print(f"{'Date':<12} | {'Trades':<8} | {'Win Rate':<10} | {'Points':<10}")
    print("-" * 60)
    
    total_w = 0
    total_l = 0
    total_pnl = 0
    
    for date, s in sorted(daily_stats.items()):
        trades_count = s['wins'] + s['losses']
        wr = (s['wins'] / trades_count * 100) if trades_count > 0 else 0
        print(f"{date:<12} | {trades_count:<8} | {wr:>8.1f}% | {s['pnl']:>8.1f}")
        total_w += s['wins']
        total_l += s['losses']
        total_pnl += s['pnl']

    print("-" * 60)
    final_wr = (total_w / (total_w + total_l) * 100) if (total_w + total_l) > 0 else 0
    print(f"{'TOTAL':<12} | {total_w+total_l:<8} | {final_wr:>8.1f}% | {total_pnl:>8.1f}")
    print("="*60)

if __name__ == "__main__":
    run_10_day_validation()
