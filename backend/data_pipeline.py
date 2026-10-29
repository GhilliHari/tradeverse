import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
import threading
from greeks_engine import GreeksEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataPipeline")

# Thread-safe locks for CSV cache files to prevent race conditions during concurrent API requests
_cache_locks = {}
_cache_locks_lock = threading.Lock()
_yf_download_lock = threading.Lock()

_SYMBOL_PRICE_BOUNDS = {
    "NSEBANK": (8000.0, 65000.0),
    "NSEI": (4000.0, 32000.0),
    "CNXFIN": (10000.0, 35000.0),
    "NSMIDCP": (50000.0, 85000.0),
    "INDIAVIX": (5.0, 85.0),
    "BANKBEES.NS": (100.0, 1000.0),
    "NIFTYBEES.NS": (50.0, 500.0),
    "HDFCBANK.NS": (100.0, 2500.0),
    "ICICIBANK.NS": (100.0, 2000.0),
    "SBIN.NS": (100.0, 1500.0),
    "KOTAKBANK.NS": (150.0, 2500.0),
    "AXISBANK.NS": (150.0, 2000.0),
    "USDINRX": (40.0, 105.0),
    "BZF": (15.0, 150.0),
    "DXY.NYB": (70.0, 125.0),
}

def _normalize_intraday_index(index: pd.Index, interval: str = "1d") -> pd.DatetimeIndex:
    """Ensure intraday timestamps are converted from UTC to IST (09:15 - 15:30) and tz-naive."""
    idx = pd.to_datetime(index)
    if idx.tz is not None:
        if interval != "1d":
            idx = idx.tz_convert("Asia/Kolkata")
        idx = idx.tz_localize(None)
    if interval != "1d" and len(idx) > 0:
        # Handle previously cached UTC-naive rows (03:45 - 09:55 UTC -> 09:15 - 15:25 IST)
        utc_mask = idx.hour < 9
        if utc_mask.any():
            idx = pd.DatetimeIndex(np.where(utc_mask, idx + pd.Timedelta(hours=5, minutes=30), idx))
    return idx

def _sanitize_symbol_df(safe_sym: str, df: pd.DataFrame, interval: str = "1d") -> pd.DataFrame:
    if df is None or df.empty or "Close" not in df.columns:
        return df
    close_num = pd.to_numeric(df["Close"], errors="coerce")
    mask = close_num.notna() & (close_num > 0)
    bounds = _SYMBOL_PRICE_BOUNDS.get(safe_sym)
    if bounds:
        lo, hi = bounds
        if interval != "1d" and safe_sym == "NSEBANK":
            lo = 35000.0
        mask = mask & (close_num >= lo) & (close_num <= hi)
    df_clean = df[mask].copy()
    if len(df_clean) > 20 and interval != "1d":
        c_sub = pd.to_numeric(df_clean["Close"], errors="coerce")
        med = c_sub.median()
        if med > 0:
            df_clean = df_clean[(c_sub >= med * 0.45) & (c_sub <= med * 1.80)].copy()
    return df_clean

def get_cache_lock(cache_path):
    with _cache_locks_lock:
        if cache_path not in _cache_locks:
            _cache_locks[cache_path] = threading.Lock()
        return _cache_locks[cache_path]

class DataPipeline:
    def __init__(self, symbol="^NSEBANK", interval="1d", lookback_days=None):
        self.symbol = symbol
        self.interval = interval
        # Auto-configure lookback based on interval
        if lookback_days is None:
            self.lookback_days = 90 if interval in ["1m", "5m", "15m", "30m", "1h"] else 15*365
        else:
            self.lookback_days = lookback_days
        self.raw_data = None
        self.futures_data = None  # NEW: For futures data
        self.vix_data = None  # NEW: For VIX data
        self.heavyweights_data = None  # NEW: For constituent stock data
        self.macro_raw = None
        self.cleaned_data = None
        self.train_data = None
        self.test_data = None

    def _fetch_cached_yf(self, symbol, start_date, end_date, interval):
        """
        Helper to fetch yfinance data using a local CSV cache.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "data", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        if isinstance(symbol, list):
            safe_sym = "_".join([s.replace("^", "").replace("=", "").replace("-", "") for s in symbol])
            sym_str = str(symbol)
        else:
            safe_sym = symbol.replace("^", "").replace("=", "").replace("-", "")
            sym_str = symbol
            
        cache_path = os.path.join(cache_dir, f"{safe_sym}_{interval}.csv")
        
        with get_cache_lock(cache_path):
            cached_df = None
            if os.path.exists(cache_path):
                try:
                    cached_df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    cached_df = _sanitize_symbol_df(safe_sym, cached_df, interval=interval)
                    if not cached_df.empty:
                        cached_df.index = _normalize_intraday_index(cached_df.index, interval=interval)
                        cached_df = cached_df[~cached_df.index.duplicated(keep='last')].sort_index()
                        last_time = cached_df.index[-1]
                        
                        overlap_time = last_time - timedelta(days=1)
                        if overlap_time < start_date:
                            pass
                        else:
                            start_date = overlap_time
                            logger.info(f"Using cache for {sym_str}. Fetching incremental from {start_date.date()}")
                except Exception as e:
                    logger.warning(f"Error reading cache for {sym_str}: {e}")
                    
            logger.info(f"Downloading {sym_str} ({interval}) from {start_date.date()} to {end_date.date()}...")
            try:
                with _yf_download_lock:
                    df = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
            except Exception as dl_err:
                logger.warning(f"Download error for {sym_str}: {dl_err}")
                df = pd.DataFrame()
            
            # Flatten columns if multi-index (prevents multi-symbol download issues)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = _sanitize_symbol_df(safe_sym, df, interval=interval)
                
            if df.empty:
                if cached_df is not None:
                    logger.warning(f"No new data returned for {sym_str}. Returning cached data.")
                    return cached_df
                else:
                    return df
                    
            df.index = _normalize_intraday_index(df.index, interval=interval)
            
            if cached_df is not None and not cached_df.empty:
                combined = pd.concat([cached_df, df])
                combined = combined[~combined.index.duplicated(keep='last')]
                combined.sort_index(inplace=True)
                df = combined
                
            try:
                df.to_csv(cache_path)
                logger.info(f"Updated cache for {sym_str} at {cache_path}")
            except Exception as e:
                logger.warning(f"Failed to write cache for {sym_str}: {e}")
                
            return df


    def get_data_quality_metrics(self) -> dict:
        """
        Calculate data quality metrics for the loaded dataset.
        """
        if self.cleaned_data is None or len(self.cleaned_data) == 0:
            return {
                "total_records": 0,
                "missing_values_pct": 0.0,
                "data_coverage_pct": 0.0,
                "last_updated": datetime.now().isoformat(),
                "data_freshness_hours": 0.0
            }
            
        total_cells = len(self.cleaned_data) * len(self.cleaned_data.columns)
        missing_cells = self.cleaned_data.isnull().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
        
        last_timestamp = self.cleaned_data.index[-1]
        if isinstance(last_timestamp, str):
            # Handle case where index might be string (shouldn't happen with pandas datetime index but safety first)
            last_timestamp = datetime.fromisoformat(last_timestamp)
            
        # Ensure timezone awareness compatibility
        now = datetime.now()
        if last_timestamp.tzinfo is not None:
             last_timestamp = last_timestamp.replace(tzinfo=None) # Compare naive-to-naive for simplicity
             
        freshness_hours = (now - last_timestamp).total_seconds() / 3600
        
        return {
            "total_records": len(self.cleaned_data),
            "missing_values_pct": round(missing_pct, 4),
            "data_coverage_pct": round(100 - missing_pct, 2),
            "last_updated": last_timestamp.isoformat(),
            "data_freshness_hours": round(freshness_hours, 1)
        }

    def get_frac_diff(self, series, d, thres=0.01):
        """
        Calculates Fractional Differentiation for a series to make it stationary 
        while preserving memory of historical price trends.
        """
        # 1. Generate weights
        w = [1.0]
        for k in range(1, 100):
            w_k = -w[-1] * ((d - k + 1) / k)
            if abs(w_k) < thres: break
            w.append(w_k)
        w = np.array(w[::-1]).reshape(-1, 1)
        
        # 2. Apply weights to series
        res = series.rolling(len(w)).apply(lambda x: np.dot(x, w), raw=True)
        return res

    def fetch_data(self):
        """
        Fetches data based on interval.
        - 1d: 15 years history (12y Train + 3y Test)
        - 1m: 7 days history (YFinance limit)
        """
        end_date = datetime.now()
        
        if self.interval == "1d":
            days = self.lookback_days if self.lookback_days else 15*365
            start_date = end_date - timedelta(days=days)
        else:
            # Intraday
            days = self.lookback_days if self.lookback_days else 30
            start_date = end_date - timedelta(days=days) 
        
        logger.info(f"Fetching {self.symbol} data ({self.interval}) from {start_date.date()} to {end_date.date()}...")
        
        try:
            # 1. Attempt Broker Fetch if available
            # Check if we have an active broker connection passed in or available globally
            from broker_factory import get_broker_client
            broker = get_broker_client()
            
            if broker and hasattr(broker, 'is_connected') and broker.is_connected() and self.interval != "1d":
                logger.info(f"Broker detected. Attempting to fetch {self.interval} data via Broker API...")
                if self.fetch_live_data_broker(broker, start_date, end_date):
                    # Successfully fetched via Broker
                    return True
            
            # 2. Fallback to yfinance (or default for Daily)
            if self.interval != "1d":
                # yfinance limits: 1m (7 days), 5m+ (59-60 days)
                max_days = 7 if self.interval == "1m" else 59
                
                requested_days = (end_date - start_date).days
                if requested_days > max_days:
                    start_date = end_date - timedelta(days=max_days)
                    logger.warning(f"Capping {self.interval} intraday request to {max_days} days (yfinance limit).")
                else:
                    logger.info(f"YFinance fallback: fetching {requested_days} days of {self.interval} data.")

            # Ensure symbol is yfinance compatible (Bank Nifty specifically)
            yf_symbol = self.symbol
            if "BANKNIFTY" in yf_symbol.upper() and not yf_symbol.startswith("^"):
                yf_symbol = "^NSEBANK"
            elif "NIFTY" in yf_symbol.upper() and "BANK" not in yf_symbol.upper() and not yf_symbol.startswith("^"):
                yf_symbol = "^NSEI"

            logger.info(f"Downloading from yfinance: {yf_symbol}...")
            # Use cached fetcher
            df = self._fetch_cached_yf(yf_symbol, start_date, end_date, self.interval)
            
            if df.empty:
                raise ValueError(f"Downloaded data for {yf_symbol} is empty.")
            
            # --- Volume Proxying for Index Symbols ---
            if yf_symbol in ["^NSEBANK", "^NSEI"]:
                proxy_symbol = "BANKBEES.NS" if yf_symbol == "^NSEBANK" else "NIFTYBEES.NS"
                logger.info(f"Fetching Volume Proxy ETF: {proxy_symbol} for index volume...")
                proxy_df = self._fetch_cached_yf(proxy_symbol, start_date, end_date, self.interval)
                if not proxy_df.empty and 'Volume' in proxy_df.columns:
                    # Align index and copy volume
                    df['Volume'] = proxy_df['Volume'].reindex(df.index, method='ffill').fillna(0.0)
                    logger.info(f"Successfully applied volume proxy using {proxy_symbol}.")
            
            # --- Heavyweight constituents fetching for Bank Nifty ---
            if yf_symbol == "^NSEBANK":
                self.heavyweights_data = {}
                heavyweight_symbols = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"]
                for hw_sym in heavyweight_symbols:
                    logger.info(f"Fetching constituent stock: {hw_sym}")
                    hw_df = self._fetch_cached_yf(hw_sym, start_date, end_date, self.interval)
                    if not hw_df.empty:
                        self.heavyweights_data[hw_sym] = hw_df
                        logger.info(f"Fetched {len(hw_df)} records for constituent {hw_sym}.")

            # Fetch Macro Data individually to avoid MultiIndex column issues
            macro_start = start_date - timedelta(days=10) # Increased buffer for ffill
            macro_symbols = ["USDINR=X", "^NSEI", "BZ=F", "DX-Y.NYB"]
            macro_data_dict = {}
            for sym in macro_symbols:
                logger.info(f"Fetching macro symbol: {sym}")
                sym_df = self._fetch_cached_yf(sym, macro_start, end_date, "1d")
                if not sym_df.empty:
                    if 'Close' in sym_df.columns:
                        macro_data_dict[sym] = sym_df['Close']
                    else:
                        macro_data_dict[sym] = sym_df.iloc[:, 0]
            macro_data = pd.DataFrame(macro_data_dict)
            
            self.raw_data = df
            self.macro_raw = macro_data
            
            # Fetch India VIX data (for volatility causality)
            try:
                logger.info(f"Fetching India VIX data...")
                vix_df = self._fetch_cached_yf("^INDIAVIX", start_date, end_date, self.interval)
                if not vix_df.empty:
                    self.vix_data = vix_df
                    logger.info(f"Successfully fetched {len(vix_df)} VIX records.")
                else:
                    logger.warning("VIX data is empty, skipping.")
            except Exception as e:
                logger.warning(f"Could not fetch VIX data: {e}")
            
            logger.info(f"Successfully fetched {len(df)} records ({self.interval}) and macro data.")
            return True
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return False

    def clean_and_prepare(self):
        """
        Cleans data: null handling, outlier removal, and column naming.
        """
        if self.raw_data is None:
            return False
        
        logger.info(f"Starting data cleaning pipeline ({self.interval})...")
        df = self.raw_data.copy()
        
        # --- NEW: Flatten MultiIndex Columns (yfinance v0.2.40+ quirk) ---
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        for attr in ['macro_raw', 'vix_data', 'futures_data']:
            obj = getattr(self, attr, None)
            if obj is not None and isinstance(obj.columns, pd.MultiIndex):
                obj.columns = obj.columns.get_level_values(0)
        
        # Normalize Timezone (Remove TZ awareness to enable merging)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        if self.macro_raw is not None and not self.macro_raw.empty:
            # Check for multi-index macro data (rare but possible with yfinance)
            if isinstance(self.macro_raw.columns, pd.MultiIndex):
                self.macro_raw.columns = self.macro_raw.columns.get_level_values(0)
            if self.macro_raw.index.tz is not None:
                self.macro_raw.index = self.macro_raw.index.tz_localize(None)

        if self.vix_data is not None and not self.vix_data.empty:
            if isinstance(self.vix_data.columns, pd.MultiIndex):
                self.vix_data.columns = self.vix_data.columns.get_level_values(0)
            if self.vix_data.index.tz is not None:
                self.vix_data.index = self.vix_data.index.tz_localize(None)
            
            # Pre-merge VIX into df
            vix_close = self.vix_data['Close']
            if isinstance(vix_close, pd.DataFrame):
                vix_close = vix_close.iloc[:, 0]
            df['VIX'] = vix_close.reindex(df.index, method='ffill')
        else:
            df['VIX'] = 15.0 # Fallback
            
        # Volatility features
        df['VIX_Change'] = df['VIX'].diff().fillna(0.0)
        df['VIX_Percentile'] = df['VIX'].rolling(window=60).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else 0.5
        ).fillna(0.5)

        # --- Heavyweight Constituent Features ---
        if getattr(self, 'heavyweights_data', None):
            hw_returns = {}
            hw_emas = {}
            weights = {
                "HDFCBANK.NS": 0.29,
                "ICICIBANK.NS": 0.23,
                "AXISBANK.NS": 0.11,
                "SBIN.NS": 0.10,
                "KOTAKBANK.NS": 0.10
            }
            
            for hw_sym, hw_df in self.heavyweights_data.items():
                if not hw_df.empty:
                    if hw_df.index.tz is not None:
                        hw_df.index = hw_df.index.tz_localize(None)
                    hw_close = hw_df['Close'].reindex(df.index, method='ffill')
                    hw_ret = hw_close.pct_change().fillna(0.0)
                    hw_returns[hw_sym] = hw_ret
                    hw_ema = hw_close.ewm(span=20, adjust=False).mean()
                    hw_emas[hw_sym] = (hw_close > hw_ema).astype(int)
            
            if hw_returns:
                weighted_ret = pd.Series(0.0, index=df.index)
                total_weight = 0.0
                for sym, ret in hw_returns.items():
                    w = weights.get(sym, 0.0)
                    weighted_ret += ret * w
                    total_weight += w
                if total_weight > 0:
                    weighted_ret = weighted_ret / total_weight
                df['HWM'] = weighted_ret
                
                breadth = pd.Series(0.0, index=df.index)
                for sym, ema_state in hw_emas.items():
                    breadth += ema_state
                df['SB'] = (breadth / len(hw_emas)) * 100.0
                
                ret_df = pd.DataFrame(hw_returns)
                df['HWD'] = ret_df.std(axis=1).fillna(0.0)
            else:
                df['HWM'] = 0.0
                df['SB'] = 50.0
                df['HWD'] = 0.0
        else:
            df['HWM'] = 0.0
            df['SB'] = 50.0
            df['HWD'] = 0.0
        
        if self.futures_data is not None and not self.futures_data.empty:
            if self.futures_data.index.tz is not None:
                self.futures_data.index = self.futures_data.index.tz_localize(None)

        # 1. Handle missing values (Forward fill followed by backward fill)
        df = df.ffill().bfill()
        # 2. Comprehensive Feature Engineering
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        # Bollinger Bands
        df['BB_MA'] = df['Close'].rolling(window=20).mean()
        df['BB_STD'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_MA'] + (df['BB_STD'] * 2)
        df['BB_Lower'] = df['BB_MA'] - (df['BB_STD'] * 2)

        # EMA & SMA
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Volatility & ATR
        df['High_Low'] = df['High'] - df['Low']
        df['High_Close_Prev'] = abs(df['High'] - df['Close'].shift(1))
        df['Low_Close_Prev'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['High_Low', 'High_Close_Prev', 'Low_Close_Prev']].max(axis=1)
        df['ATR_14'] = df['TR'].rolling(window=14).mean()

        # ADX (Average Directional Index) - simplified logic
        df['+DM'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']), 
                             np.maximum(df['High'] - df['High'].shift(1), 0), 0)
        df['-DM'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)), 
                             np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)
        df['+DI'] = 100 * (df['+DM'].rolling(14).mean() / df['TR'].rolling(14).mean())
        df['-DI'] = 100 * (df['-DM'].rolling(14).mean() / df['TR'].rolling(14).mean())
        df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
        df['ADX'] = df['DX'].rolling(14).mean()

        # Williams %R
        df['WillR'] = -100 * ((df['High'].rolling(14).max() - df['Close']) / 
                             (df['High'].rolling(14).max() - df['Low'].rolling(14).min()))

        # SuperTrend Inspired Logic (Trend State)
        df['ST_Upper'] = (df['High'] + df['Low']) / 2 + (3 * df['ATR_14'])
        df['ST_Lower'] = (df['High'] + df['Low']) / 2 - (3 * df['ATR_14'])
        df['Trend_State'] = np.where(df['Close'] > df['EMA_21'], 1, -1)

        # Money Flow Index (MFI) - Volume weighted RSI
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        positive_flow = np.where(typical_price > typical_price.shift(1), money_flow, 0)
        negative_flow = np.where(typical_price < typical_price.shift(1), money_flow, 0)
        mfr = pd.Series(positive_flow).rolling(14).sum() / pd.Series(negative_flow).rolling(14).sum()
        df['MFI'] = 100 - (100 / (1 + mfr.values))

        # Stochastic RSI
        min_rsi = df['RSI'].rolling(window=14).min()
        max_rsi = df['RSI'].rolling(window=14).max()
        df['Stoch_RSI'] = (df['RSI'] - min_rsi) / (max_rsi - min_rsi)

        # VWAP (Approximation for daily data: (Cumulative Price * Volume) / Cumulative Volume)
        df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()

        # Pivot Points (Standard Daily)
        df['Pivot'] = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
        df['R1'] = (2 * df['Pivot']) - df['Low'].shift(1)
        df['S1'] = (2 * df['Pivot']) - df['High'].shift(1)
        df['R2'] = df['Pivot'] + (df['High'].shift(1) - df['Low'].shift(1))
        df['S2'] = df['Pivot'] - (df['High'].shift(1) - df['Low'].shift(1))

        # Ichimoku Cloud Components
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        nine_period_high = df['High'].rolling(window=9).max()
        nine_period_low = df['Low'].rolling(window=9).min()
        df['Tenkan_Sen'] = (nine_period_high + nine_period_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        twentysix_period_high = df['High'].rolling(window=26).max()
        twentysix_period_low = df['Low'].rolling(window=26).min()
        df['Kijun_Sen'] = (twentysix_period_high + twentysix_period_low) / 2

        # Parabolic SAR (Simplified logic)
        df['PSAR'] = df['Close'].shift(1) # Base starting point
        
        # Chaikin Money Flow (CMF)
        mf_multiplier = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
        mf_volume = mf_multiplier * df['Volume']
        df['CMF'] = mf_volume.rolling(20).sum() / df['Volume'].rolling(20).sum()

        # Rate of Change (ROC)
        df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12)) * 100

        # Force Index (FI)
        df['Force_Index'] = (df['Close'] - df['Close'].shift(1)) * df['Volume']

        # Aroon Indicator (Trend Maturity)
        df['Aroon_Up'] = df['High'].rolling(25).apply(lambda x: float(np.argmax(x)) / 25 * 100, raw=True)
        df['Aroon_Down'] = df['Low'].rolling(25).apply(lambda x: float(np.argmin(x)) / 25 * 100, raw=True)

        # CCI (Commodity Channel Index) - Cyclical turns
        df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['CCI'] = (df['TP'] - df['TP'].rolling(20).mean()) / (0.015 * df['TP'].rolling(20).std())

        # Fisher Transform (Statistical reversal timing)
        med = (df['High'] + df['Low']) / 2
        nd = (med - med.rolling(9).min()) / (med.rolling(9).max() - med.rolling(9).min())
        nd = 0.66 * (nd - 0.5)
        nd = nd.rolling(1).sum() # Smooth
        df['Fisher'] = 0.5 * np.log((1 + nd) / (1 - nd))

        # Elder Ray (Bull and Bear Power)
        df['Bull_Power'] = df['High'] - df['EMA_21']
        df['Bear_Power'] = df['Low'] - df['EMA_21']

        # Keltner Channels (Volatility trend)
        df['KC_Mid'] = df['EMA_21']
        df['KC_Upper'] = df['KC_Mid'] + (2 * df['ATR_14'])
        df['KC_Lower'] = df['KC_Mid'] - (2 * df['ATR_14'])

        # Donchian Channels (Breakout levels)
        df['DC_Upper'] = df['High'].rolling(20).max()
        df['DC_Lower'] = df['Low'].rolling(20).min()

        # On-Balance Volume (OBV)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

        # Chande Momentum Oscillator (CMO)
        cmo_delta = df['Close'].diff()
        cmo_up = cmo_delta.where(cmo_delta > 0, 0).rolling(9).sum()
        cmo_down = (-cmo_delta.where(cmo_delta < 0, 0)).rolling(9).sum()
        df['CMO'] = 100 * (cmo_up - cmo_down) / (cmo_up + cmo_down)

        # True Strength Index (TSI)
        pc = df['Close'].diff()
        spc = pc.ewm(span=25, adjust=False).mean().ewm(span=13, adjust=False).mean()
        apc = abs(pc).ewm(span=25, adjust=False).mean().ewm(span=13, adjust=False).mean()
        df['TSI'] = 100 * (spc / apc)

        # Mass Index (Reversal detection via range expansion)
        range_ema = (df['High'] - df['Low']).ewm(span=9, adjust=False).mean()
        range_ema_ema = range_ema.ewm(span=9, adjust=False).mean()
        df['Mass_Index'] = (range_ema / range_ema_ema).rolling(25).sum()

        # Hull Moving Average (Zero-lag)
        def hma(s, p):
            wma_1 = s.rolling(p // 2).apply(lambda x: np.dot(x, np.arange(1, p // 2 + 1)) / np.arange(1, p // 2 + 1).sum(), raw=True)
            wma_2 = s.rolling(p).apply(lambda x: np.dot(x, np.arange(1, p + 1)) / np.arange(1, p + 1).sum(), raw=True)
            diff = 2 * wma_1 - wma_2
            return diff.rolling(int(np.sqrt(p))).apply(lambda x: np.dot(x, np.arange(1, int(np.sqrt(p)) + 1)) / np.arange(1, int(np.sqrt(p)) + 1).sum(), raw=True)
        
        df['HMA_20'] = hma(df['Close'], 20)

        # Coppock Curve (Long-term bottom fishing/momentum)
        roc_14 = ((df['Close'] - df['Close'].shift(14)) / df['Close'].shift(14)) * 100
        roc_11 = ((df['Close'] - df['Close'].shift(11)) / df['Close'].shift(11)) * 100
        df['Coppock'] = (roc_14 + roc_11).ewm(span=10, adjust=False).mean()

        # Detrended Price Oscillator (DPO) - Cycle identification
        df['DPO'] = df['Close'].shift(11) - df['Close'].rolling(21).mean()

        # Klinger Oscillator (Volume-based trend confirmation)
        sv = df['Volume'] * (2 * ((df['High'] + df['Low'] + df['Close']) / 3 > (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3) - 1)
        df['Klinger'] = sv.ewm(span=34, adjust=False).mean() - sv.ewm(span=55, adjust=False).mean()

        # --- Macro & BN Correlation ---
        # Integrate USD/INR and Nifty 50
        if self.macro_raw is not None and not self.macro_raw.empty:
            if 'USDINR=X' in self.macro_raw.columns:
                df['USDINR'] = self.macro_raw['USDINR=X'].reindex(df.index, method='ffill')
            else: df['USDINR'] = 83.0
            
            if '^NSEI' in self.macro_raw.columns:
                df['Nifty50'] = self.macro_raw['^NSEI'].reindex(df.index, method='ffill')
            else: df['Nifty50'] = df['Close'] # Fallback to BN itself if Nifty missing
            
            if 'BZ=F' in self.macro_raw.columns:
                df['Brent'] = self.macro_raw['BZ=F'].reindex(df.index, method='ffill')
            else: df['Brent'] = 80.0
            
            if 'DX-Y.NYB' in self.macro_raw.columns:
                df['DXY'] = self.macro_raw['DX-Y.NYB'].reindex(df.index, method='ffill')
            else: df['DXY'] = 100.0
            
            df['BN_Nifty_Ratio'] = df['Close'] / df['Nifty50']
        else:
            # Fallback values if macro data is missing
            df['USDINR'] = 83.0
            df['Nifty50'] = df['Close']
            df['Brent'] = 80.0
            df['DXY'] = 100.0
            df['BN_Nifty_Ratio'] = 1.0
        
        # Inflation & Interest Rate Proxy (Step function for mock sensitivity)
        # In a real system, we'd fetch CPI/Repo Rate. Here we use a drift-based mock for BN response.
        df['Inflation_Proxy'] = 6.0 + (np.sin(np.arange(len(df)) / 60) * 0.5) # 5.5% to 6.5% oscillation
        df['RBI_Rate_Proxy'] = 6.5 # Mock Repo Rate

        # --- Elliott Wave Inspired Structural Logic ---
        # Simplified Wave detection: Higher Highs/Lows sequence
        df['High_5'] = df['High'].rolling(window=5, center=True).max()
        df['Low_5'] = df['Low'].rolling(window=5, center=True).min()
        df['Is_Fractal_High'] = (df['High'] == df['High_5']).astype(int)
        df['Is_Fractal_Low'] = (df['Low'] == df['Low_5']).astype(int)
        
        # Wave Sequence (1-5 Impulse Attempt)
        # This is a heuristic: 1 = recovery, 2 = pullback, 3 = impulse, etc.
        df['Impulse_Wave'] = 0
        df.loc[(df['Close'] > df['EMA_21']) & (df['RSI'] > 50), 'Impulse_Wave'] = 3 # Strong active impulse
        df.loc[(df['Close'] < df['EMA_21']) & (df['RSI'] < 40), 'Impulse_Wave'] = -3 # Downwards impulse

        # --- Stop-Loss Hunting / Liquidity Grab Detector ---
        body = abs(df['Open'] - df['Close'])
        upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
        lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
        avg_vol_20 = df['Volume'].rolling(20).mean().replace(0, 1)
        
        # Bullish Liquidity Grab: Sweeps recent low, high volume, leaves long lower wick
        is_bullish_grab = (lower_wick > 2 * body) & \
                          (df['Low'] < df['Low'].rolling(10).min().shift(1)) & \
                          (df['Volume'] > 1.2 * avg_vol_20)
                          
        # Bearish Liquidity Grab: Sweeps recent high, high volume, leaves long upper wick
        is_bearish_grab = (upper_wick > 2 * body) & \
                          (df['High'] > df['High'].rolling(10).max().shift(1)) & \
                          (df['Volume'] > 1.2 * avg_vol_20)
                          
        df['Is_Liquidity_Grab'] = 0
        df.loc[is_bullish_grab, 'Is_Liquidity_Grab'] = 1
        df.loc[is_bearish_grab, 'Is_Liquidity_Grab'] = -1

        # Lagged Returns (Momentum)
        df['Ret_1d'] = df['Close'].pct_change()
        df['Ret_2d'] = df['Close'].pct_change(2)
        df['Ret_3d'] = df['Close'].pct_change(3)
        df['Ret_5d'] = df['Close'].pct_change(5)
        
        # Volume Change
        df['Vol_Change'] = df['Volume'].pct_change()
        
        # --- Advanced Signal Features (High Impact) ---
        
        # 1. Distance from Key Moving Average (Mean Reversion / Trend Strength)
        df['Dist_EMA21'] = (df['Close'] - df['EMA_21']) / df['EMA_21']
        df['Dist_SMA200'] = (df['Close'] - df['SMA_200']) / df['SMA_200']
        
        # 2. Volatility Regime (Current Vol vs Hist Vol)
        # > 1.0 means expanding volatility (Breakout potential)
        # < 1.0 means contracting volatility (Squeeze potential)
        df['Vol_Ratio'] = df['ATR_14'] / df['ATR_14'].rolling(window=50).mean()
        
        # 3. RSI Slope (3-day change)
        df['RSI_Slope'] = df['RSI'].diff(3)
        
        # 4. Interaction Terms
        df['RSI_x_Vol'] = df['RSI'] * df['Vol_Ratio']
        
        # --- Phase 3 Extensions ---
        # 4b. Advanced Interaction Features
        df['RSI_Vol_Imbalance'] = df['RSI'] * (df['Vol_Change'].clip(-2, 2))
        df['Trend_Confidence'] = df['Trend_State'] * df['ADX']
        
        # 5. Gap Analysis (Open vs Prev Close - Indicator of overnight sentiment)
        df['Gap'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
        
        # 5b. Volatility Scaling (Normalizing oscillators by ATR regimes)
        df['RSI_Vol_Adj'] = df['RSI'] / (df['Vol_Ratio'] + 0.1)
        df['CCI_Vol_Adj'] = df['CCI'] / (df['Vol_Ratio'] + 0.1)
        
        # 6. Candle Streak (Consecutive Green/Red days)
        # Positive for green streak, Negative for red streak
        df['Is_Green'] = (df['Close'] > df['Open']).astype(int)
        df['Streak'] = df['Is_Green'].groupby((df['Is_Green'] != df['Is_Green'].shift()).cumsum()).cumsum()
        # Correcting streak logic to differentiate direction
        df['Streak'] = np.where(df['Is_Green'] == 0, -df['Streak'], df['Streak'])
        
        # --- Options Data Integration (PCR & OI) ---
        # Since yfinance lacks historical options, we simulate realistic PCR/OI 
        # dynamics based on price action for the training phase, which can be 
        # swapped for real broker data during live inference.
        
        # PCR usually increases as price drops (hedging) and decreases as price rises.
        # It's a mean-reverting oscillator.
        # Use a fixed random state seed to ensure full reproducibility and remove training noise variance
        rng_synth = np.random.RandomState(42)
        noise_pcr = rng_synth.normal(0, 0.05, len(df))
        df['PCR'] = 1.0 - (df['RSI'] - 50) / 100 + noise_pcr
        df['PCR'] = df['PCR'].clip(0.6, 1.6) # Standard BankNifty PCR range
        
        # OI Change as a proxy for institutional positioning
        # High volume on green days usually correlates with OI buildup (Long Build)
        df['OI_Change'] = (df['Volume'].pct_change() * np.sign(df['Close'].diff())).fillna(0)
        
        # --- Sentiment Quantization (Historical Simulation) ---
        # Historical sentiment isn't available via yfinance, so we initialize 
        # it with a slight correlation to price action + noise for training.
        noise_sent = rng_synth.normal(0, 0.2, len(df))
        df['sentiment_score'] = (df['Ret_1d'] * 10).clip(-1, 1) + noise_sent
        df['sentiment_score'] = df['sentiment_score'].clip(-1, 1)
        
        # --- NEW: Direct Options Greeks Modeling ---
        # Calculate theoretical ATM Option Greeks for every row
        logger.info("Computing Black-Scholes Greeks (ATM)...")
        ge = GreeksEngine()
        
        # Approximate 1-day to expiry for intraday, 7-days for daily
        T = 1.0/365.0 if self.interval != "1d" else 7.0/365.0 
        
        # Vectorized-ish approach or apply for Greeks
        def get_greeks_for_row(row):
            spot = row['Close']
            # ATM Strike is Spot rounded to nearest 100
            strike = round(spot / 100) * 100 
            
            # Use real VIX if available, else fallback to 15% (0.15)
            # Yfinance VIX is often in actual percentage (e.g. 15.5) so divide by 100
            vol = (row['VIX'] / 100.0) if 'VIX' in row and row['VIX'] > 0 else 0.15
            
            # Calculate for Call
            ce_price = ge.black_scholes_price(spot, strike, T, vol, "CE")
            ce_greeks = ge.calculate_greeks(spot, strike, T, vol, "CE")
            
            # Calculate for Put
            pe_price = ge.black_scholes_price(spot, strike, T, vol, "PE")
            pe_greeks = ge.calculate_greeks(spot, strike, T, vol, "PE")
            
            return pd.Series({
                'CE_Premium': ce_price,
                'CE_Delta': ce_greeks['Delta'],
                'CE_Theta': ce_greeks['Theta'],
                'CE_Gamma': ce_greeks['Gamma'],
                'CE_Vega': ce_greeks['Vega'],
                'PE_Premium': pe_price,
                'PE_Delta': pe_greeks['Delta'],
                'PE_Theta': pe_greeks['Theta'],
                'PE_Gamma': pe_greeks['Gamma'],
                'PE_Vega': pe_greeks['Vega'],
                'ATM_Strike': strike
            })
            
        greeks_df = df.apply(get_greeks_for_row, axis=1)
        df = pd.concat([df, greeks_df], axis=1)

        # --- Fractional Differentiation (Stationary Memory) ---
        # We apply frac diff to the Close price with d=0.4 (optimal for price preservation)
        # This provides a "cleaner" trend feature than raw returns.
        df['Price_FracDiff'] = self.get_frac_diff(df['Close'], d=0.4)

        # --- INTRADAY-SPECIFIC FEATURES (for 5m, 15m, 30m, 1h intervals) ---
        if self.interval in ["1m", "5m", "15m", "30m", "1h"]:
            logger.info("Adding intraday-specific features...")
            
            # 1. VWAP (Volume Weighted Average Price)
            # Add epsilon to volume sum to avoid div by zero
            vol_sum = df['Volume'].cumsum()
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / vol_sum.replace(0, 1)
            # If VWAP is 0 (all volume 0), fallback to Close
            df['VWAP'] = np.where(df['VWAP'] == 0, df['Close'], df['VWAP'])
            
            df['Price_vs_VWAP'] = (df['Close'] - df['VWAP']) / df['VWAP'].replace(0, 1) * 100  # Percentage deviation
            df['VWAP_Slope'] = df['VWAP'].diff().fillna(0)
            
            # 2. Time-based features
            df['Hour_of_Day'] = df.index.hour
            df['Minutes_Since_Open'] = (df.index.hour - 9) * 60 + df.index.minute - 15  # Market opens at 9:15
            df['Minutes_to_Close'] = (15 - df.index.hour) * 60 + (30 - df.index.minute)  # Market closes at 15:30
            
            # 3. Volume Profile
            avg_vol = df['Volume'].rolling(window=12).mean().replace(0, 1)
            df['Volume_vs_Avg_5m'] = df['Volume'] / avg_vol  # vs. 1-hour avg
            df['Volume_Spike'] = (df['Volume'] > df['Volume'].rolling(window=12).mean() * 2).astype(int)
            df['Cumulative_Volume'] = df['Volume'].cumsum()
            
            # 4. Futures-Spot relationship (if futures data available)
            if self.futures_data is not None and not self.futures_data.empty:
                # Align futures data with spot data
                futures_close = self.futures_data['Close'].reindex(df.index, method='ffill')
                df['Futures_Close'] = futures_close
                df['Futures_Premium'] = (futures_close - df['Close']) / df['Close'] * 100  # Percentage premium
                df['Basis_Change'] = df['Futures_Premium'].diff()
            else:
                df['Futures_Close'] = df['Close']  # Fallback
                df['Futures_Premium'] = 0
                df['Basis_Change'] = 0
            
            # VIX is pre-merged at the start of clean_and_prepare
            
            logger.info(f"Added {sum([1 for c in df.columns if c in ['VWAP', 'Futures_Premium', 'VIX']])} intraday features.")

        # --- Triple Barrier Labeling Strategy ---
        # Instead of simple next-candle direction, we use barriers for volatility-adjusted targets.
        def get_triple_barrier_labels(df, pt_sl=[1.0, 1.0], t1=5):
            """
            pt_sl: Multiplier for profit taking and stop loss barriers.
            t1: Vertical barrier (max candles to wait).
            """
            # Calculate daily volatility (rolling std of returns)
            daily_vol = df['Close'].pct_change().rolling(window=20).std().fillna(0)
            
            labels = pd.Series(index=df.index, data=0)
            
            for i in range(len(df) - t1):
                price_start = df['Close'].iloc[i]
                vol = daily_vol.iloc[i]
                
                if vol == 0: continue
                
                # Barriers
                ub = price_start * (1 + pt_sl[0] * vol)
                lb = price_start * (1 - pt_sl[1] * vol)
                
                # Check which barrier is hit first
                found = False
                for j in range(1, t1 + 1):
                    current_price = df['Close'].iloc[i + j]
                    if current_price >= ub:
                        labels.iloc[i] = 1 # Profit Hit
                        found = True
                        break
                    elif current_price <= lb:
                        labels.iloc[i] = -1 # Loss Hit
                        found = True
                        break
                
                if not found:
                    # Vertical barrier hit
                    labels.iloc[i] = 0 # No significant move within time limit
            
            return labels

        # --- NEW: Options Premium Labeling (Phase 7) ---
        # Instead of predicting Spot movement, we predict if the ATM Option Premium
        # hits a specific Profit Target before a Stop Loss within the vertical barrier.
        def get_options_triple_barrier(df, side="CE", target_pct=0.10, sl_pct=0.08, time_limit=6):
            """
            Checks if the target_pct premium gain is hit before sl_pct premium loss.
            time_limit: number of 5m candles to wait (e.g. 6 = 30 mins)
            """
            labels = pd.Series(index=df.index, data=0)
            col = f"{side}_Premium"
            
            for i in range(len(df) - time_limit):
                entry_premium = df[col].iloc[i]
                if entry_premium <= 1.0: continue # Skip if premium is basically 0/expired
                
                # Barriers based on Option Premium percentages
                tp = entry_premium * (1 + target_pct)
                sl = entry_premium * (1 - sl_pct)
                
                found = False
                for j in range(1, time_limit + 1):
                    current_prem = df[col].iloc[i + j]
                    
                    if current_prem >= tp:
                        labels.iloc[i] = 1 # Profit Hit
                        found = True
                        break
                    elif current_prem <= sl:
                        labels.iloc[i] = -1 # Loss Hit
                        found = True
                        break
                        
            return labels

        if self.interval == "1d":
            # For Daily models, we still predict multi-day Spot direction for broader context
            df['Target_Next_Day'] = get_triple_barrier_labels(df, pt_sl=[1.5, 1.5], t1=2)
            df['Target_Next_Day'] = (df['Target_Next_Day'] == 1).astype(int)
        else:
            # For Intraday models, the target is specifically if a CE Option will yield +10% within 30 mins (6 candles)
            # In a true system you'd predict CE and PE separately. Here we simplify to:
            # 1 = CE hit target
            # 2 = PE hit target (simulating downward spot)
            # 0 = Choppy/Theta Decay
            
            ce_labels = get_options_triple_barrier(df, side="CE", target_pct=0.15, sl_pct=0.10, time_limit=6)
            pe_labels = get_options_triple_barrier(df, side="PE", target_pct=0.15, sl_pct=0.10, time_limit=6)
            
            # Combine logic. Priority to CE if both somehow hit (rare on 5m scale)
            df['Target_Next_Day'] = 0
            df.loc[ce_labels == 1, 'Target_Next_Day'] = 1 # BUY CE
            df.loc[pe_labels == 1, 'Target_Next_Day'] = 2 # BUY PE (effectively SELL SPOT)
            
            # Reduce multi-class to binary for the existing pipeline's compatibility
            # Let's say 1 = Strong Directional Trade (either CE or PE), 0 = Theta Trap
            # Or we can maintain Binary: 1 = UP, 0 = DOWN and filter in Agent Layer.
            # To maintain current model shape with minimum disruption, we map:
            # 1 = Upward Target Hit (CE)
            # 0 = Downward Target Hit (PE) or Choppy
            # The model will learn to predict 1 only when CE is highly profitable.
            df['Target_Next_Day'] = (ce_labels == 1).astype(int)
        
        # Log distribution for debugging "0 win rate"
        counts = df['Target_Next_Day'].value_counts()
        logger.info(f"Target Distribution ({self.interval}): {counts.to_dict()}")

        
        # 3. Clean up
        # Replace Inf with Nan
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # FIX: Handle Zero-Volume case (Common in Indices like ^NSEBANK)
        # If Volume is 0, features like MFI, VWAP, CMF become NaN. We fill them with 0.
        vol_dependent = ['MFI', 'VWAP', 'CMF', 'Vol_Change', 'Klinger', 'OBV', 'Force_Index', 'RSI_Vol_Imbalance', 'RSI_Vol_Adj', 'CCI_Vol_Adj']
        for col in vol_dependent:
            if col in df.columns:
                # Fill ALL NaNs in volume-dependent features with 0 to prevent dropna() from nuking rows
                df[col] = df[col].fillna(0.0)
        
        # Ensure macro columns are also filled
        macro_cols = ['USDINR', 'Nifty50', 'Brent', 'DXY', 'BN_Nifty_Ratio', 'Inflation_Proxy', 'RBI_Rate_Proxy']
        for col in macro_cols:
            if col in df.columns:
                df[col] = df[col].ffill().bfill().fillna(0.0)
        
        # DEBUG: Check for columns with excessive NaNs
        nan_counts = df.isna().sum()
        with_nans = nan_counts[nan_counts > 0]
        if not with_nans.empty:
            logger.info(f"Columns with NaNs before drop: \n{with_nans}")
            
        # Final pass to ensure maximum record retention
        df = df.ffill().bfill()
        
        logger.info(f"Shape before dropna: {df.shape}")
        self.cleaned_data = df.dropna()
        logger.info(f"Shape after dropna: {self.cleaned_data.shape}")
        
        if self.cleaned_data.empty:
            logger.error("Cleaning resulted in an EMPTY dataframe! Check indicator lookback vs data length.")
            # Emergency: return most recent row even if it has NaNs (filled to 0)
            self.cleaned_data = df.tail(1).fillna(0.0)
            logger.warning("Emergency fallback: Using most recent raw row with 0-filled NaNs.")

        logger.info(f"Cleaned data with advanced features has {len(self.cleaned_data)} records.")
        return True

    def calculate_quality_metrics(self):
        """
        Calculates data quality scores: Completeness, Logical Integrity, and Continuity.
        """
        if self.raw_data is None or self.cleaned_data is None:
            return {"quality_percentage": 0}

        # 1. Completeness: Retention after dropna (rolling windows eat some rows)
        raw_rows = len(self.raw_data)
        clean_rows = len(self.cleaned_data)
        completeness = (clean_rows / raw_rows) * 100 if raw_rows > 0 else 0

        # 2. Logical Integrity: OHLC consistency
        # High must be >= Low, Open, Close. Low must be <= High, Open, Close.
        logical_valid = (
            (self.raw_data['High'] >= self.raw_data['Low']) &
            (self.raw_data['High'] >= self.raw_data['Close']) &
            (self.raw_data['Low'] <= self.raw_data['Close'])
        ).sum()
        logical_integrity = (logical_valid / raw_rows) * 100 if raw_rows > 0 else 0

        # 3. Continuity: Expected vs Actual Trading Days
        # Approx 12 years * 252 trading days = 3024. 
        # But we use the actual date range to be precise.
        days_diff = (self.raw_data.index[-1] - self.raw_data.index[0]).days
        expected_trading_days = (days_diff / 365) * 250 # ~250 trading days per year
        continuity = min((raw_rows / expected_trading_days) * 100, 100) if expected_trading_days > 0 else 0

        # Aggregate Quality Score
        quality_percentage = (completeness * 0.4 + logical_integrity * 0.4 + continuity * 0.2)
        
        return {
            "quality_percentage": round(quality_percentage, 2),
            "completeness": round(completeness, 2),
            "logical_integrity": round(logical_integrity, 2),
            "continuity_score": round(continuity, 2)
        }

    def split_data(self, test_days=None):
        """
        Splits data into train and test sets.
        test_days: Number of days to use for testing (last N days).
        """
        if self.cleaned_data is None:
            return False
            
        logger.info(f"Performing Train/Test split ({self.interval})...")
        
        # Determine split point
        if self.interval == "1d":
            days = test_days if test_days else 3*365
            split_date = self.cleaned_data.index[-1] - timedelta(days=days)
        else:
            # Intraday
            days = test_days if test_days else 2
            split_date = self.cleaned_data.index[-1] - timedelta(days=days)
        
        self.train_data = self.cleaned_data[self.cleaned_data.index < split_date]
        self.test_data = self.cleaned_data[self.cleaned_data.index >= split_date]
        
        # Safety check: if train_data is too small, reduce test_days
        if len(self.train_data) < 100 and len(self.cleaned_data) >= 10:
             logger.warning("Train set too small. Adjusting split to 50/50.")
             split_idx = len(self.cleaned_data) // 2
             self.train_data = self.cleaned_data.iloc[:split_idx]
             self.test_data = self.cleaned_data.iloc[split_idx:]

        logger.info(f"Split complete. Train: {len(self.train_data)} rows, Test: {len(self.test_data)} rows.")

        
        quality = self.calculate_quality_metrics()
        
        return {
            "train_size": len(self.train_data),
            "test_size": len(self.test_data),
            "train_start": self.train_data.index[0].strftime('%Y-%m-%d') if len(self.train_data) > 0 else None,
            "train_end": self.train_data.index[-1].strftime('%Y-%m-%d') if len(self.train_data) > 0 else None,
            "test_start": self.test_data.index[0].strftime('%Y-%m-%d') if len(self.test_data) > 0 else None,
            "test_end": self.test_data.index[-1].strftime('%Y-%m-%d') if len(self.test_data) > 0 else None,
            "quality": quality
        }

    def fetch_live_data_broker(self, broker_client, start_date, end_date):
        """
        Fetches the most recent candles using the broker client's historical methods.
        """
        logger.info(f"Fetching live data for {self.symbol} via Broker...")
        
        try:
            # 1. Map yfinance symbol to Broker token
            # In Tradeverse, we usually use NSE:BANKNIFTY or similar
            broker_symbol = "NSE:BANKNIFTY" if "NSEBANK" in self.symbol.upper() else self.symbol
            exchange, tradingsymbol, token = broker_client._get_token_and_exchange(broker_symbol)
            
            if not token:
                # Try simple search
                search_res = broker_client.search_scrip(broker_symbol.split(":")[-1])
                if search_res:
                    token = search_res[0]['token']
                    exchange = search_res[0]['exchange']
            
            if not token:
                logger.error(f"Could not resolve token for {self.symbol}")
                return False

            # 2. Map Interval
            interval_map = {
                "1m": "ONE_MINUTE",
                "5m": "FIVE_MINUTE",
                "15m": "FIFTEEN_MINUTE",
                "1h": "ONE_HOUR",
                "1d": "ONE_DAY"
            }
            broker_interval = interval_map.get(self.interval, "ONE_MINUTE")

            # 3. Fetch
            candles = broker_client.get_historical_data(exchange, token, broker_interval, start_date, end_date)
            
            if not candles:
                logger.error("No candles returned from Broker.")
                return False

            # 4. Process into DataFrame
            # Angel candle format: [time, open, high, low, close, volume]
            df = pd.DataFrame(candles, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            df.set_index('Datetime', inplace=True)
            
            # Cast to float
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = df[col].astype(float)

            self.raw_data = df
            logger.info(f"Successfully fetched {len(df)} records via Broker API.")
            
            # Also fetch macro if not present
            if self.macro_raw is None:
                self.macro_raw = yf.download(["USDINR=X", "^NSEI"], start=start_date, end=end_date, interval="1d")['Close']
            
            # CRITICAL: Clean and Prepare data before returning True
            return self.clean_and_prepare()

        except Exception as e:
            logger.error(f"Broker Fetch Failed: {e}")
            return False
    

    def generate_fallback_dataframe(self):
        """
        Generates a realistic fallback DataFrame for historical training if remote APIs are unavailable.
        """
        logger.warning(f'Generating synthetic fallback historical dataset for {self.symbol}...')
        num_rows = 500 if self.interval != "1d" else 1000
        end_dt = datetime.now()
        freq = "5min" if self.interval != "1d" else "D"
        dates = pd.date_range(end=end_dt, periods=num_rows, freq=freq)
        
        base_p = 57500.0 if "BANK" in self.symbol.upper() else 24200.0
        returns = np.random.normal(0.0001, 0.005, size=num_rows)
        price_series = base_p * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'Open': price_series * (1 + np.random.uniform(-0.001, 0.001, num_rows)),
            'High': price_series * (1 + np.abs(np.random.normal(0.002, 0.001, num_rows))),
            'Low': price_series * (1 - np.abs(np.random.normal(0.002, 0.001, num_rows))),
            'Close': price_series,
            'Volume': np.random.randint(1000, 50000, size=num_rows)
        }, index=dates)
        
        self.raw_data = df
        return True

    def run_full_pipeline(self, test_days=None):
        """
        One-stop shop for ingestion.
        """
        success = False
        try:
            success = self.fetch_data()
        except Exception as e:
            logger.error(f'fetch_data exception: {e}')
            
        if not success or self.raw_data is None or self.raw_data.empty:
            logger.warning(f'Data fetch failed or returned empty for {self.symbol}. Using fallback dataset...')
            self.generate_fallback_dataframe()

        if self.clean_and_prepare():
            return self.split_data(test_days=test_days)
        return None



if __name__ == "__main__":
    pipeline = DataPipeline()
    stats = pipeline.run_full_pipeline()
    if stats:
        print("Pipeline Status: SUCCESS")
        print(stats)
    else:
        print("Pipeline Status: FAILED")
