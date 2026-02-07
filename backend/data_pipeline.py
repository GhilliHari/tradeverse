import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataPipeline")

class DataPipeline:
    def __init__(self, symbol="^NSEBANK", interval="1d"):
        self.symbol = symbol
        self.interval = interval
        self.raw_data = None
        self.macro_raw = None
        self.cleaned_data = None
        self.train_data = None
        self.test_data = None

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
        - 1d: 12 years history
        - 1m: 7 days history (YFinance limit)
        """
        end_date = datetime.now()
        
        if self.interval == "1d":
            start_date = end_date - timedelta(days=12*365)
        else:
            # Intraday - Increase buffer to 30 days if using Broker
            start_date = end_date - timedelta(days=30) 
        
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
                # Reset start_date to 7 days for yfinance if intraday to avoid errors
                start_date = end_date - timedelta(days=7)
                logger.warning(f"Falling back to yfinance (7-day limit) for intraday data.")

            df = yf.download(self.symbol, start=start_date, end=end_date, interval=self.interval)
            
            # Flatten columns if multi-index (prevents multi-symbol download issues)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Fetch Macro Data (Daily resolution, will be ffilled/interpolated for intraday)
            # Only strictly needed for Daily models, but good for context in Intraday too
            macro_start = start_date - timedelta(days=5) # Buffer for ffill
            macro_data = yf.download(["USDINR=X", "^NSEI"], start=macro_start, end=end_date, interval="1d")['Close']
            
            if df.empty:
                raise ValueError("Downloaded data is empty.")
            
            self.raw_data = df
            self.macro_raw = macro_data
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
        
        # Normalize Timezone (Remove TZ awareness to enable merging)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        if self.macro_raw is not None and not self.macro_raw.empty:
            if self.macro_raw.index.tz is not None:
                self.macro_raw.index = self.macro_raw.index.tz_localize(None)

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
        if hasattr(self, 'macro_raw'):
            df['USDINR'] = self.macro_raw['USDINR=X'].reindex(df.index, method='ffill')
            df['Nifty50'] = self.macro_raw['^NSEI'].reindex(df.index, method='ffill')
            df['BN_Nifty_Ratio'] = df['Close'] / df['Nifty50']
        
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
        df['PCR'] = 1.0 - (df['RSI'] - 50) / 100 + np.random.normal(0, 0.05, len(df))
        df['PCR'] = df['PCR'].clip(0.6, 1.6) # Standard BankNifty PCR range
        
        # OI Change as a proxy for institutional positioning
        # High volume on green days usually correlates with OI buildup (Long Build)
        df['OI_Change'] = (df['Volume'].pct_change() * np.sign(df['Close'].diff())).fillna(0)
        
        # --- Sentiment Quantization (Historical Simulation) ---
        # Historical sentiment isn't available via yfinance, so we initialize 
        # it with a slight correlation to price action + noise for training.
        df['sentiment_score'] = (df['Ret_1d'] * 10).clip(-1, 1) + np.random.normal(0, 0.2, len(df))
        df['sentiment_score'] = df['sentiment_score'].clip(-1, 1)

        # --- Fractional Differentiation (Stationary Memory) ---
        # We apply frac diff to the Close price with d=0.4 (optimal for price preservation)
        # This provides a "cleaner" trend feature than raw returns.
        df['Price_FracDiff'] = self.get_frac_diff(df['Close'], d=0.4)

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

        if self.interval == "1d":
            # Daily: 2-day horizon, 1x vol target
            df['Target_Next_Day'] = get_triple_barrier_labels(df, pt_sl=[1.5, 1.5], t1=2)
            # Re-map -1 to 0 for binary classifier if needed, but model might support multi-class
            # For now, let's keep it 1 for UP (profit hit) and 0 for others
            df['Target_Next_Day'] = (df['Target_Next_Day'] == 1).astype(int)
        else:
            # Intraday (Sniper): 15-min horizon, tighter targets
            df['Target_Next_Day'] = get_triple_barrier_labels(df, pt_sl=[1.0, 1.0], t1=15)
            df['Target_Next_Day'] = (df['Target_Next_Day'] == 1).astype(int)
        
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
        macro_cols = ['USDINR', 'Nifty50', 'BN_Nifty_Ratio', 'Inflation_Proxy', 'RBI_Rate_Proxy']
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

    def split_data(self):
        """
        Splits data into train and test sets.
        """
        if self.cleaned_data is None:
            return False
            
        logger.info(f"Performing Train/Test split ({self.interval})...")
        
        # Determine split point
        # For Daily: Last 2 years for test
        # For Intraday: Last 2 days for test (since we have ~7 days total)
        if self.interval == "1d":
            split_date = self.cleaned_data.index[-1] - timedelta(days=2*365)
        else:
            split_date = self.cleaned_data.index[-1] - timedelta(days=2)
        
        self.train_data = self.cleaned_data[self.cleaned_data.index < split_date]
        self.test_data = self.cleaned_data[self.cleaned_data.index >= split_date]
        
        # --- Aggressive Noise Filtering for Training ---
        if self.interval == "1d":
            # Only filter noise on Daily timeframe. Intraday IS the noise :)
            # Actually, we might want to filter flat periods in Intraday too.
            # But let's stick to Daily for now.
            train_returns = self.train_data['Close'].pct_change().abs()
            self.train_data = self.train_data[train_returns > 0.003]
        
        logger.info(f"Split complete. Train: {len(self.train_data)} rows, Test: {len(self.test_data)} rows.")
        
        quality = self.calculate_quality_metrics()
        
        return {
            "train_size": len(self.train_data),
            "test_size": len(self.test_data),
            "train_start": self.train_data.index[0].strftime('%Y-%m-%d'),
            "train_end": self.train_data.index[-1].strftime('%Y-%m-%d'),
            "test_start": self.test_data.index[0].strftime('%Y-%m-%d'),
            "test_end": self.test_data.index[-1].strftime('%Y-%m-%d'),
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
    
    def run_full_pipeline(self):
        """
        One-stop shop for ingestion.
        """
        if self.fetch_data():
            if self.clean_and_prepare():
                return self.split_data()
        return None

if __name__ == "__main__":
    pipeline = DataPipeline()
    stats = pipeline.run_full_pipeline()
    if stats:
        print("Pipeline Status: SUCCESS")
        print(stats)
    else:
        print("Pipeline Status: FAILED")
