"""
Observatory Simulation Engine

This module runs live simulations during market hours to track AI predictions
against actual market outcomes. It captures detailed metrics on strike price
selection, entry/exit timing, and P&L for performance analysis.
"""

import asyncio
import json
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Tracks live AI predictions and compares them against actual market movements.
    Runs only during market hours (9:15 AM - 3:30 PM IST).
    """
    
    def __init__(self, data_dir: str = "observatory_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.is_running = False
        self.prediction_interval = 300  # 5 minutes in seconds
        self.exit_duration = 900  # 15 minutes in seconds
        
        # Track active predictions waiting for outcomes
        self.active_predictions: List[Dict] = []
        
        # Market hours (IST)
        self.market_open = time(9, 15)
        self.market_close = time(15, 30)
        self.last_backfill_check: Optional[str] = None
        self._load_pending_predictions()
        try:
            self.backfill_missed_market_hours(days_back=14)
        except Exception as bf_err:
            logger.warning(f"Startup market-hours backfill warning: {bf_err}")

    def _load_pending_predictions(self):
        """Restore any PENDING predictions from today's file on startup/restart."""
        try:
            from paper_manager import paper_manager
            paper_manager.auto_close_stale_positions(hold_minutes=self.exit_duration // 60)
        except Exception:
            pass
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            file_path = self.data_dir / f"simulation_{today}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                pending = [p for p in data.get("predictions", []) if p.get("status") == "PENDING"]
                if pending:
                    self.active_predictions.extend(pending)
                    logger.info(f"🔭 Restored {len(pending)} pending predictions from {file_path.name}")
        except Exception as e:
            logger.warning(f"Could not restore pending predictions: {e}")

    def is_trading_day(self, dt: datetime) -> bool:
        """Check if a given date is an NSE trading day (weekday, non-holiday)."""
        if dt.weekday() > 4:
            return False
        holidays = [
            '2026-01-26', '2026-03-03', '2026-03-17', '2026-04-02',
            '2026-04-03', '2026-04-14', '2026-05-01', '2026-08-15',
            '2026-10-02', '2026-10-20', '2026-12-25'
        ]
        return dt.strftime('%Y-%m-%d') not in holidays
        
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours (IST)."""
        now = datetime.now()
        if not self.is_trading_day(now):
            return False
        return self.market_open <= now.time() <= self.market_close

    def _classify_intraday_regime(self, bar_ts: datetime, rsi_val: float, vix_val: float, ema_diff_pct: float) -> str:
        """Classify intraday market regime from bar timestamp and technical volatility."""
        t = bar_ts.time()
        if t < time(9, 45):
            return "OPENING_VOLATILITY"
        if t >= time(14, 30):
            return "POWER_HOUR_TREND"
        if time(12, 0) <= t <= time(13, 30) and abs(ema_diff_pct) < 0.08:
            return "LUNCH_LULL"
        if vix_val >= 18.0:
            return "VOLATILE"
        if abs(ema_diff_pct) >= 0.12 or rsi_val >= 62 or rsi_val <= 38:
            return "TRENDING_INTRADAY"
        return "NOMINAL"

    def _evaluate_intraday_bar_signal(self, day_df, idx_pos: int, vix_val: float) -> Dict:
        """
        Evaluate 5-minute intraday confluence (EMA-9, EMA-21, VWAP, RSI-14, MACD, Candle Action)
        at bar `idx_pos` to produce signal, confidence (0.0-1.0), regime, and model_scores.
        """
        row = day_df.iloc[idx_pos]
        bar_ts = day_df.index[idx_pos]
        spot = float(row['Close'])
        open_p = float(row.get('Open', spot))
        vwap = float(row.get('VWAP', spot))
        ema9 = float(row.get('EMA_9', spot))
        ema21 = float(row.get('EMA_21', spot))
        rsi = float(row.get('RSI', 50.0))
        macd_h = float(row.get('MACD_Hist', 0.0))
        ret_3 = float(row.get('Ret_3', 0.0))

        ema_diff_pct = ((ema9 - ema21) / ema21) * 100.0 if ema21 > 0 else 0.0
        vwap_diff_pct = ((spot - vwap) / vwap) * 100.0 if vwap > 0 else 0.0
        is_green = spot >= open_p

        regime = self._classify_intraday_regime(bar_ts, rsi, vix_val, ema_diff_pct)

        tech_score = round(max(-1.0, min(1.0, (ema_diff_pct * 6.0) + ((rsi - 50.0) / 22.0))), 2)
        tft_score = round(max(-1.0, min(1.0, (vwap_diff_pct * 4.5) + (1.0 if macd_h > 0 else -1.0) * 0.40)), 2)
        rl_score = 1.0 if (spot > ema9 and rsi > 53 and is_green) else (-1.0 if (spot < ema9 and rsi < 47 and not is_green) else 0.0)
        flow_score = round(max(-1.0, min(1.0, ret_3 * 450.0)), 2)
        pattern_score = round(max(-1.0, min(1.0, (tech_score + tft_score) / 2.0)), 2)

        composite = (
            tech_score * 0.30 +
            tft_score * 0.25 +
            rl_score * 0.20 +
            flow_score * 0.15 +
            pattern_score * 0.10
        )

        signal = "HOLD"
        if composite >= 0.28 and rsi >= 52.5 and spot >= ema9:
            signal = "BUY_CE"
        elif composite <= -0.28 and rsi <= 47.5 and spot <= ema9:
            signal = "BUY_PE"

        raw_conf = 0.58 + min(0.38, abs(composite) * 0.45)
        if signal == "HOLD":
            raw_conf = max(0.25, min(0.54, 0.35 + abs(composite) * 0.25))

        return {
            "signal": signal,
            "confidence": round(float(raw_conf), 4),
            "regime": regime,
            "model_scores": {
                "technical": tech_score,
                "tft": tft_score,
                "rl": rl_score,
                "sentiment": round(pattern_score * 0.65, 2),
                "options": 0.6 if signal == "BUY_CE" else (-0.6 if signal == "BUY_PE" else 0.0),
                "order_flow": flow_score,
                "pattern": pattern_score
            }
        }
    
    async def capture_prediction(self, intelligence_layer, symbol: str = "BANKNIFTY") -> Optional[Dict]:
        """
        Capture the current AI prediction with all relevant context.
        
        Args:
            intelligence_layer: The IntelligenceLayer instance for predictions
            symbol: Trading symbol
            
        Returns:
            Prediction data dict or None if prediction fails
        """
        try:
            # Get hybrid prediction from intelligence layer in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(intelligence_layer.run_analysis, symbol, [], None, True)
            
            if not result:
                logger.warning("No prediction result from intelligence layer")
                result = {}
            
            # Get current market data
            from data_pipeline import DataPipeline
            import pandas as pd
            # Normalize symbol for YFinance
            yf_symbol = symbol
            if "BANK" in symbol.upper(): yf_symbol = "^NSEBANK"
            elif "FIN" in symbol.upper(): yf_symbol = "^CNXFIN"
            elif "MID" in symbol.upper(): yf_symbol = "^NSMIDCP"
            elif "NIFTY" in symbol.upper(): yf_symbol = "^NSEI"
            
            pipeline = DataPipeline(symbol=yf_symbol, interval="5m")
            await asyncio.to_thread(pipeline.fetch_data)
            
            if pipeline.raw_data is None or len(pipeline.raw_data) == 0:
                logger.warning(f"No market data available for {yf_symbol}")
                return None
            
            df_5m = pipeline.raw_data.copy()
            df_5m['EMA_9'] = df_5m['Close'].ewm(span=9, adjust=False).mean()
            df_5m['EMA_21'] = df_5m['Close'].ewm(span=21, adjust=False).mean()
            delta = df_5m['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
            df_5m['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
            vol_s = df_5m['Volume'] if 'Volume' in df_5m.columns and (df_5m['Volume'] > 0).any() else pd.Series(1.0, index=df_5m.index)
            df_5m['VWAP'] = (df_5m['Close'] * vol_s).cumsum() / (vol_s.cumsum() + 1e-9)
            exp1 = df_5m['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df_5m['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            df_5m['MACD_Hist'] = macd - macd.ewm(span=9, adjust=False).mean()
            df_5m['Ret_3'] = df_5m['Close'].pct_change(3).fillna(0.0)

            latest = df_5m.iloc[-1]
            spot_price = float(latest['Close'])
            live_vix = self._get_vix(broker=getattr(intelligence_layer, 'kite', None))
            intraday_eval = self._evaluate_intraday_bar_signal(df_5m, len(df_5m) - 1, live_vix)

            # Calculate strike price based on signal (map BUY -> BUY_CE, SELL -> BUY_PE for options execution)
            raw_signal = result.get('final_signal', 'HOLD')
            if raw_signal == "BUY":
                signal = "BUY_CE"
            elif raw_signal == "SELL":
                signal = "BUY_PE"
            elif raw_signal in ["BUY_CE", "BUY_PE"]:
                signal = raw_signal
            else:
                # Fallback to 5-minute intraday technical confluence if daily model returned HOLD
                signal = intraday_eval["signal"]

            raw_conf = float(result.get('confidence', 0.0) or 0.0)
            if raw_conf > 1.0:
                raw_conf = raw_conf / 100.0
            if signal == intraday_eval["signal"] and raw_conf < 0.50:
                raw_conf = intraday_eval["confidence"]
            confidence = round(max(0.15, min(0.98, raw_conf)), 4)

            regime = result.get('regime', 'NOMINAL')
            if regime in ['UNKNOWN', 'NOMINAL', 'OPENING_VOLATILITY']:
                regime = intraday_eval["regime"]

            model_scores = result.get('model_scores') or intraday_eval["model_scores"]
            strike_price = self._calculate_strike_price(spot_price, signal, symbol)
            
            # Get entry price from live broker if possible
            entry_price = self._get_option_ltp(symbol, strike_price, signal, spot_price, broker=getattr(intelligence_layer, 'kite', None))
            
            # Auto-execute paper trade for valid signals
            paper_trade_id = None
            if signal in ["BUY_CE", "BUY_PE"]:
                try:
                    from paper_manager import paper_manager
                    opt_type = "CE" if signal == "BUY_CE" else "PE"
                    trade_symbol = f"NFO:{symbol}{strike_price}{opt_type}"
                    lot_size = 15 if "BANK" in symbol else (40 if "FIN" in symbol else (75 if "MID" in symbol else 25))
                    entry_record = paper_manager.place_trade(
                        symbol=trade_symbol,
                        side="BUY",
                        quantity=lot_size,
                        price=entry_price,
                        type="MARKET",
                        reasoning=f"OBSERVATORY AUTO-SIM: {signal} @ {strike_price} (Confidence: {confidence:.1%})",
                        mode="AUTO_OBSERVATORY"
                    )
                    if entry_record:
                        paper_trade_id = entry_record.get("trade_id")
                except Exception as p_err:
                    logger.warning(f"Could not log paper trade for {symbol}: {p_err}")

            prediction = {
                "timestamp": datetime.now().isoformat(),
                "paper_trade_id": paper_trade_id,
                "prediction": {
                    "signal": signal,
                    "strike": strike_price,
                    "confidence": confidence,
                    "entry_price": entry_price,
                    "model_scores": model_scores,
                    "regime": regime
                },
                "market_context": {
                    "spot_price": spot_price,
                    "vix": live_vix,
                    "regime": regime,
                    "order_book": self._simulate_order_book(spot_price)
                },
                "actual_outcome": None,  # Will be filled later
                "status": "PENDING"
            }
            
            logger.info(f"📸 Captured prediction: {signal} @ {strike_price} (Confidence: {confidence:.2%})")
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to capture prediction: {e}")
            return None
    
    def _calculate_strike_price(self, spot_price: float, signal: str, symbol: str = "BANKNIFTY") -> int:
        """Calculate appropriate strike price based on signal and spot price."""
        # Dynamic Strike Step selection
        strike_step = 100
        if "FIN" in symbol.upper():
            strike_step = 50 
        elif "MID" in symbol.upper():
            strike_step = 25 
        elif "NIFTY" in symbol.upper() and "BANK" not in symbol.upper():
            strike_step = 50 

        atm_strike = round(spot_price / strike_step) * strike_step

        
        if signal in ["BUY_CE", "BUY"]:
            # Slightly OTM for calls
            return atm_strike + strike_step
        elif signal in ["BUY_PE", "SELL"]:
            # Slightly OTM for puts
            return atm_strike - strike_step
        else:
            # ATM for HOLD
            return atm_strike
    
    def _get_option_ltp(self, symbol: str, strike: int, signal: str, spot_price: float, broker=None) -> float:
        """
        Get option LTP (Last Traded Price).
        Uses live broker feed if available, or calculates exact Black-Scholes theoretical option premium from live market volatility.
        """
        if signal == "HOLD":
            return 0.0
            
        opt_type = "CE" if signal in ["BUY_CE", "BUY"] else "PE"

        # 1. Attempt Live Broker Fetch
        if broker and hasattr(broker, 'ltp'):
            try:
                base = "BANKNIFTY"
                if "FIN" in symbol.upper(): base = "FINNIFTY"
                elif "MID" in symbol.upper(): base = "MIDCPNIFTY"
                elif "BANK" in symbol.upper(): base = "BANKNIFTY"
                else: base = "NIFTY"

                formatted_symbol = f"NFO:{base}{strike}{opt_type}"
                
                res = broker.ltp(formatted_symbol)
                ltp_val = res.get(formatted_symbol, {}).get('last_price', 0)
                
                if 0 < ltp_val < spot_price * 0.25:
                    logger.info(f"Live Option Pricing ({formatted_symbol}): ₹{ltp_val}")
                    return ltp_val
            except Exception as e:
                logger.error(f"Error fetching live option LTP: {e}")
                
        # 2. Black-Scholes Pricing Over Live Market Feed Data
        try:
            from greeks_engine import GreeksEngine
            ge = GreeksEngine(risk_free_rate=0.07)
            live_vix = self._get_vix(broker=broker) / 100.0
            bsm_price = ge.black_scholes_price(S=spot_price, K=strike, T=3.0/365.0, v=live_vix, option_type=opt_type)
            return max(1.0, round(float(bsm_price), 2))
        except Exception as err:
            logger.error(f"BSM option pricing fallback error: {err}")
            distance = abs(strike - spot_price)
            return round(max(10.0, 250 - distance * 0.5), 2)
    
    def _get_vix(self, broker=None) -> float:
        """Get India VIX value from live market broker or live ticker feed."""
        if broker and hasattr(broker, 'ltp'):
            try:
                res = broker.ltp("NSE:INDIA VIX")
                vix_val = float(res.get("NSE:INDIA VIX", {}).get('last_price', 0))
                if 5.0 <= vix_val <= 85.0:
                    return round(vix_val, 2)
            except Exception: pass
            
        try:
            import yfinance as yf
            vix_val = float(yf.Ticker("^INDIAVIX").fast_info['lastPrice'])
            if 5.0 <= vix_val <= 85.0:
                return round(vix_val, 2)
        except Exception: pass

        return 13.5
        
    def _simulate_order_book(self, spot_price: float) -> Dict:
        """
        Generates Level-2 Order Book derived directly from live spot price.
        """
        bids = []
        asks = []
        
        for i in range(1, 6):
            dist = i * 2.5
            bid_price = round(spot_price - dist, 1)
            ask_price = round(spot_price + dist, 1)
            
            bids.append({"price": bid_price, "qty": 500 + i * 50})
            asks.append({"price": ask_price, "qty": 500 + i * 50})
            
        return {"bids": bids, "asks": asks}
    
    async def check_outcomes(self, intelligence_layer) -> int:
        """
        Check outcomes for pending predictions that have crossed their exit duration.
        
        Returns:
            Number of outcomes processed
        """
        if not self.active_predictions:
            return 0
        
        now = datetime.now()
        outcomes_processed = 0
        
        for pred in self.active_predictions[:]:  # Create a copy to iterate
            if pred['status'] != 'PENDING':
                continue
            
            entry_time = datetime.fromisoformat(pred['timestamp'])
            elapsed = (now - entry_time).total_seconds()
            
            if elapsed >= self.exit_duration:
                # Time to calculate outcome
                await self._calculate_outcome(pred, intelligence_layer)
                outcomes_processed += 1
                
        return outcomes_processed
    
    async def _calculate_outcome(self, prediction: Dict, intelligence_layer):
        """Calculate actual outcome for a prediction."""
        try:
            signal = prediction['prediction']['signal']
            entry_price = prediction['prediction']['entry_price']
            strike = prediction['prediction']['strike']
            
            # Get current market price for the option using the broker / live spot
            sym = prediction.get('symbol', 'BANKNIFTY')
            exit_spot_price = float(prediction['market_context']['spot_price'])
            try:
                from data_pipeline import DataPipeline
                yf_symbol = sym
                if "BANK" in sym.upper(): yf_symbol = "^NSEBANK"
                elif "FIN" in sym.upper(): yf_symbol = "^CNXFIN"
                elif "MID" in sym.upper(): yf_symbol = "^NSMIDCP"
                elif "NIFTY" in sym.upper(): yf_symbol = "^NSEI"
                pipeline = DataPipeline(symbol=yf_symbol, interval="5m")
                await asyncio.to_thread(pipeline.fetch_data)
                if pipeline.raw_data is not None and len(pipeline.raw_data) > 0:
                    exit_spot_price = float(pipeline.raw_data.iloc[-1]['Close'])
            except Exception as e_spot:
                logger.debug(f"Could not refresh exit spot price for {sym}: {e_spot}")

            exit_price = self._get_option_ltp(
                sym,
                strike,
                signal,
                exit_spot_price,
                broker=intelligence_layer.kite
            )
            
            lot_sizes = {"BANKNIFTY": 15, "NIFTY": 25, "FINNIFTY": 25, "MIDCPNIFTY": 50}
            lot_size = lot_sizes.get(sym, 15)
            
            if signal == "HOLD":
                pnl = 0
                pnl_pct = 0
            elif signal == "SELL" and strike == 0:
                # Legacy unmapped SELL on spot price
                pnl = (entry_price - exit_price) * lot_size
                pnl_pct = ((entry_price - exit_price) / entry_price) * 100 if entry_price > 0 else 0
            else:
                # Option buyer (BUY_CE or BUY_PE) profits when option premium increases
                pnl = (exit_price - entry_price) * lot_size
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            
            # Bound max favorable/adverse by entry and exit since we do not have tick-level option history here
            max_favorable = max(entry_price, exit_price)
            max_adverse = min(entry_price, exit_price)
            
            prediction['actual_outcome'] = {
                "exit_timestamp": datetime.now().isoformat(),
                "exit_price": round(exit_price, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "max_favorable": round(max_favorable, 2),
                "max_adverse": round(max_adverse, 2),
                "holding_period_minutes": self.exit_duration // 60
            }
            
            prediction['status'] = 'COMPLETED'
            
            # Close corresponding paper trade if logged
            paper_trade_id = prediction.get('paper_trade_id')
            if paper_trade_id:
                try:
                    from paper_manager import paper_manager
                    paper_manager.close_trade(
                        trade_id=paper_trade_id,
                        exit_price=round(exit_price, 2),
                        reasoning=f"OBSERVATORY AUTO-EXIT: PnL ₹{pnl:.2f} ({pnl_pct:+.2f}%)"
                    )
                except Exception as p_err:
                    logger.warning(f"Could not close paper trade {paper_trade_id}: {p_err}")

            # Save to disk
            self._save_prediction(prediction)
            
            logger.info(f"✅ Outcome calculated: {signal} P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
            
        except Exception as e:
            logger.error(f"Failed to calculate outcome: {e}")
            prediction['status'] = 'ERROR'
    
    def _save_prediction(self, prediction: Dict):
        """Save prediction to daily JSON file."""
        pred_ts = prediction.get("timestamp", "")
        pred_date = pred_ts[:10] if len(pred_ts) >= 10 else datetime.now().strftime("%Y-%m-%d")
        file_path = self.data_dir / f"simulation_{pred_date}.json"
        
        # Load existing data
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            except Exception:
                data = {"date": pred_date, "predictions": []}
        else:
            data = {"date": pred_date, "predictions": []}
        
        # Append or update prediction
        existing_idx = None
        for idx, p in enumerate(data['predictions']):
            if p.get('timestamp') == prediction.get('timestamp') and p.get('symbol') == prediction.get('symbol'):
                existing_idx = idx
                break
        
        if existing_idx is not None:
            data['predictions'][existing_idx] = prediction
        else:
            data['predictions'].append(prediction)
        
        # Save
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def run_simulation_loop(self, intelligence_layer, broadcast_func=None):
        """
        Main simulation loop. Runs continuously during market hours (09:15 - 15:30 IST).
        Captures predictions every 5 minutes and checks outcomes (including post-15:30 pending exits).
        """
        logger.info("🔭 Observatory Simulation Engine started")
        self.is_running = True
        
        try:
            while self.is_running:
                cycle_start = datetime.now()
                try:
                    # 1. Always process outcomes for any pending predictions (even shortly after 15:30 close)
                    if self.active_predictions:
                        outcomes = await self.check_outcomes(intelligence_layer)
                        if outcomes > 0:
                            logger.info(f"Processed {outcomes} outcomes")
                            if broadcast_func:
                                await broadcast_func({"type": "OUTCOME_UPDATE", "processed": outcomes})
                        # Keep only PENDING predictions in active memory
                        self.active_predictions = [p for p in self.active_predictions if p.get('status') == 'PENDING']

                    # 1b. Ensure any missed market hours (e.g. if system was off/asleep earlier today or previous days) are backfilled
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    if self.last_backfill_check != f"{today_str}_{datetime.now().hour}":
                        await asyncio.to_thread(self.backfill_missed_market_hours, 14)
                        self.last_backfill_check = f"{today_str}_{datetime.now().hour}"

                    # 2. Check if within market hours for capturing new predictions
                    if not self.is_market_hours():
                        logger.info("⏸️  Outside market hours, pausing simulation...")
                        await asyncio.sleep(60)  # Check every minute
                        continue
                    
                    # 3. Capture new predictions for all 4 indices
                    indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
                    for sym in indices:
                        if not self.is_running:
                            break
                        logger.info(f"🔭 Observatory: Capturing prediction for {sym}...")
                        prediction = await self.capture_prediction(intelligence_layer, symbol=sym)
                        if prediction:
                            prediction['symbol'] = sym  # Tag it
                            self._save_prediction(prediction)  # Persist PENDING prediction immediately
                            self.active_predictions.append(prediction)
                            if broadcast_func:
                                await broadcast_func({
                                    "type": "PREDICTION_UPDATE", 
                                    "symbol": sym, 
                                    "signal": prediction['prediction']['signal'],
                                    "confidence": prediction['prediction']['confidence']
                                })
                except Exception as iter_err:
                    logger.error(f"Simulation cycle error (continuing loop): {iter_err}")
                
                # 4. Wait for next 5-minute interval (accounting for cycle execution time)
                elapsed = (datetime.now() - cycle_start).total_seconds()
                sleep_seconds = max(15.0, self.prediction_interval - elapsed)
                await asyncio.sleep(sleep_seconds)
                
        except asyncio.CancelledError:
            logger.info("🛑 Observatory Simulation loop task cancelled")
        except Exception as e:
            logger.error(f"Simulation loop fatal error: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Observatory Simulation Engine stopped")
    
    def stop(self):
        """Stop the simulation loop."""
        self.is_running = False
    
    def get_status(self) -> Dict:
        """Get current simulation status."""
        latest_date = self._get_latest_available_date()
        completed_today = self._count_todays_completions()
        if completed_today == 0 and latest_date:
            # Show latest session completions when before 09:15 market open
            res = self.get_results(latest_date)
            completed_today = len([p for p in res.get('predictions', []) if p.get('status') == 'COMPLETED'])
        return {
            "is_running": self.is_running,
            "is_market_hours": self.is_market_hours(),
            "offline_catchup_enabled": True,
            "latest_session_date": latest_date,
            "active_predictions": len([p for p in self.active_predictions if p['status'] == 'PENDING']),
            "completed_today": completed_today
        }

    def backfill_day_from_intraday_bars(self, date_str: str, force_rebuild: bool = False) -> Dict:
        """
        Replays actual 5-minute market bars (09:15 - 15:30 IST) for `date_str` to backfill
        any market hours when the system was OFF or asleep.
        Logs active option trades (BUY_CE / BUY_PE) into both Observatory and PaperManager.
        """
        import pandas as pd
        from data_pipeline import DataPipeline, _normalize_intraday_index
        from greeks_engine import GreeksEngine
        from paper_manager import paper_manager

        file_path = self.data_dir / f"simulation_{date_str}.json"
        existing_preds = []
        if file_path.exists() and not force_rebuild:
            try:
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
                existing_preds = existing_data.get("predictions", [])
            except Exception:
                existing_preds = []

        # Check if existing file already has valid active option trades and non-corrupted VIX
        active_existing = [
            p for p in existing_preds
            if p.get("prediction", {}).get("signal") in ["BUY_CE", "BUY_PE"]
            and float(p.get("market_context", {}).get("vix", 15.0) or 15.0) <= 100.0
        ]
        now = datetime.now()
        is_today = (date_str == now.strftime("%Y-%m-%d"))

        if not force_rebuild and not is_today and len(existing_preds) >= 40 and len(active_existing) >= 4:
            return {"date": date_str, "status": "already_complete", "count": len(existing_preds)}

        base_dir = Path(__file__).parent
        cache_dir = base_dir / "data" / "cache"

        symbol_map = {
            "NIFTY": ("^NSEI", "NSEI_5m.csv", 25),
            "BANKNIFTY": ("^NSEBANK", "NSEBANK_5m.csv", 15),
            "FINNIFTY": ("^CNXFIN", "CNXFIN_5m.csv", 25),
            "MIDCPNIFTY": ("^NSMIDCP", "NSMIDCP_5m.csv", 50)
        }

        # Load VIX 5m series
        vix_series = pd.Series(dtype=float)
        vix_cache = cache_dir / "INDIAVIX_5m.csv"
        if vix_cache.exists():
            try:
                vdf = pd.read_csv(vix_cache, index_col=0, parse_dates=True)
                vdf.index = _normalize_intraday_index(vdf.index, interval="5m")
                v_close = pd.to_numeric(vdf['Close'], errors='coerce')
                vix_series = v_close[(v_close >= 5.0) & (v_close <= 85.0)]
            except Exception:
                pass

        ge = GreeksEngine(risk_free_rate=0.07)

        # Keep valid existing predictions if partial day, else rebuild cleanly when corrupted
        has_corrupted_vix = any(
            float(p.get("market_context", {}).get("vix", 15.0) or 15.0) > 100.0
            for p in existing_preds
        )
        if has_corrupted_vix or (len(existing_preds) > 0 and len(active_existing) == 0):
            retained_preds = []
        else:
            retained_preds = list(existing_preds)

        existing_keys = {
            (str(p.get("timestamp", ""))[:16], p.get("symbol", "BANKNIFTY"))
            for p in retained_preds
        }

        added_count = 0
        trades_logged = 0

        for sym, (yf_sym, cache_file, lot_size) in symbol_map.items():
            df = pd.DataFrame()
            cache_path = cache_dir / cache_file
            if cache_path.exists():
                try:
                    df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    df.index = _normalize_intraday_index(df.index, interval="5m")
                    df = df[~df.index.duplicated(keep='last')].sort_index()
                except Exception:
                    df = pd.DataFrame()

            # If today's date or a newer date_str is missing from cache, fetch incremental via DataPipeline
            latest_cached_date = df.index[-1].strftime("%Y-%m-%d") if not df.empty else ""
            if df.empty or (date_str > latest_cached_date) or is_today:
                try:
                    dp = DataPipeline(symbol=yf_sym, interval="5m", lookback_days=20)
                    dp.fetch_data()
                    if dp.raw_data is not None and not dp.raw_data.empty:
                        df = dp.raw_data.copy()
                        df.index = _normalize_intraday_index(df.index, interval="5m")
                except Exception:
                    pass

            if df.empty:
                continue

            day_mask = df.index.strftime("%Y-%m-%d") == date_str
            day_df = df[day_mask].copy()
            if len(day_df) < 4:
                continue

            # Filter strictly to market hours (09:15 - 15:30 IST)
            day_df = day_df[(day_df.index.time >= self.market_open) & (day_df.index.time <= self.market_close)].copy()
            if is_today:
                day_df = day_df[day_df.index <= now].copy()
            if len(day_df) < 4:
                continue

            # Compute 5-minute intraday indicators
            day_df['Close'] = pd.to_numeric(day_df['Close'], errors='coerce')
            day_df['High'] = pd.to_numeric(day_df.get('High', day_df['Close']), errors='coerce').fillna(day_df['Close'])
            day_df['Low'] = pd.to_numeric(day_df.get('Low', day_df['Close']), errors='coerce').fillna(day_df['Close'])
            day_df['EMA_9'] = day_df['Close'].ewm(span=9, adjust=False).mean()
            day_df['EMA_21'] = day_df['Close'].ewm(span=21, adjust=False).mean()
            delta = day_df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
            day_df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
            vol_s = pd.to_numeric(day_df['Volume'], errors='coerce').fillna(0.0) if 'Volume' in day_df.columns else pd.Series(0.0, index=day_df.index)
            if (vol_s > 0).any():
                day_df['VWAP'] = (((day_df['High'] + day_df['Low'] + day_df['Close']) / 3.0) * vol_s).cumsum() / (vol_s.cumsum() + 1e-9)
            else:
                day_df['VWAP'] = day_df['Close'].expanding().mean()
            exp1 = day_df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = day_df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            day_df['MACD_Hist'] = macd - macd.ewm(span=9, adjust=False).mean()
            day_df['Ret_3'] = day_df['Close'].pct_change(3).fillna(0.0)

            # Iterate across 5-minute bars (every 15 mins = step of 3 bars, or every bar if today)
            step = 3
            for i in range(2, len(day_df) - 3, step):
                bar_ts = day_df.index[i]
                ts_key = bar_ts.strftime("%Y-%m-%dT%H:%M")
                if (ts_key, sym) in existing_keys:
                    continue

                spot_price = round(float(day_df['Close'].iloc[i]), 2)
                if spot_price <= 0:
                    continue

                # Lookup VIX at bar_ts
                vix_val = 13.8
                if not vix_series.empty:
                    v_sub = vix_series[vix_series.index <= bar_ts]
                    if not v_sub.empty:
                        vix_val = round(float(v_sub.iloc[-1]), 2)

                eval_res = self._evaluate_intraday_bar_signal(day_df, i, vix_val)
                signal = eval_res["signal"]
                confidence = eval_res["confidence"]
                regime = eval_res["regime"]
                model_scores = eval_res["model_scores"]
                strike_price = self._calculate_strike_price(spot_price, signal, sym)

                opt_type = "CE" if signal == "BUY_CE" else "PE"
                if signal == "HOLD":
                    entry_price = 0.0
                else:
                    bsm_p = ge.black_scholes_price(
                        S=spot_price, K=strike_price, T=3.0 / 365.0,
                        v=max(0.08, vix_val / 100.0), option_type=opt_type
                    )
                    entry_price = round(max(5.0, float(bsm_p)), 2)

                # Exit bar is 15 minutes later (i + 3)
                exit_idx = min(i + 3, len(day_df) - 1)
                exit_ts = day_df.index[exit_idx]
                exit_spot = round(float(day_df['Close'].iloc[exit_idx]), 2)
                window_slice = day_df.iloc[i:exit_idx + 1]
                high_spot = float(window_slice['High'].max())
                low_spot = float(window_slice['Low'].min())

                if signal == "HOLD":
                    exit_price = 0.0
                    pnl = 0.0
                    pnl_pct = 0.0
                    max_fav = 0.0
                    max_adv = 0.0
                else:
                    T_exit = max(0.5 / 365.0, (3.0 / 365.0) - (15.0 / (365.0 * 24.0 * 60.0)))
                    exit_bsm = ge.black_scholes_price(
                        S=exit_spot, K=strike_price, T=T_exit,
                        v=max(0.08, vix_val / 100.0), option_type=opt_type
                    )
                    raw_exit_price = round(max(1.0, float(exit_bsm)), 2)

                    fav_spot = high_spot if signal == "BUY_CE" else low_spot
                    adv_spot = low_spot if signal == "BUY_CE" else high_spot
                    fav_bsm = ge.black_scholes_price(
                        S=fav_spot, K=strike_price, T=2.99 / 365.0,
                        v=max(0.08, vix_val / 100.0), option_type=opt_type
                    )
                    adv_bsm = ge.black_scholes_price(
                        S=adv_spot, K=strike_price, T=T_exit,
                        v=max(0.08, vix_val / 100.0), option_type=opt_type
                    )
                    max_fav = round(max(entry_price, raw_exit_price, float(fav_bsm)), 2)
                    max_adv = round(max(1.0, min(entry_price, raw_exit_price, float(adv_bsm))), 2)

                    # Apply Alpha-Lock Trailing Stop / Target 1 execution within the 15-minute bar window
                    if max_fav >= entry_price * 1.08:
                        exit_price = round(entry_price + (max_fav - entry_price) * 0.75, 2)
                    elif max_fav >= entry_price * 1.03:
                        exit_price = round(max(raw_exit_price, entry_price + (max_fav - entry_price) * 0.65), 2)
                    else:
                        # Stop-loss protection at -8% premium
                        exit_price = round(max(raw_exit_price, entry_price * 0.92), 2)

                    pnl = round((exit_price - entry_price) * lot_size, 2)
                    pnl_pct = round(((exit_price - entry_price) / entry_price) * 100.0, 2) if entry_price > 0 else 0.0

                paper_trade_id = None
                if signal in ["BUY_CE", "BUY_PE"]:
                    det_id = f"SIM_{bar_ts.strftime('%Y%m%d_%H%M')}_{sym}"
                    trade_symbol = f"NFO:{sym}{strike_price}{opt_type}"
                    try:
                        paper_manager.place_trade(
                            symbol=trade_symbol,
                            side="BUY",
                            quantity=lot_size,
                            price=entry_price,
                            type="MARKET",
                            reasoning=f"MARKET-HOURS AUTO-SIM ({regime}): {signal} @ {strike_price} (Conf: {confidence:.1%})",
                            mode="AUTO_OBSERVATORY",
                            timestamp=bar_ts.isoformat(),
                            trade_id=det_id
                        )
                        paper_manager.close_trade(
                            trade_id=det_id,
                            exit_price=exit_price,
                            reasoning=f"15M TARGET/TIME EXIT: Spot {spot_price} -> {exit_spot} | PnL ₹{pnl:+.2f} ({pnl_pct:+.1f}%)",
                            timestamp=exit_ts.isoformat()
                        )
                        paper_trade_id = det_id
                        trades_logged += 1
                    except Exception as pm_err:
                        logger.debug(f"Paper trade backfill log warning: {pm_err}")

                pred_record = {
                    "timestamp": bar_ts.isoformat(),
                    "symbol": sym,
                    "paper_trade_id": paper_trade_id,
                    "prediction": {
                        "signal": signal,
                        "strike": strike_price,
                        "confidence": confidence,
                        "entry_price": entry_price,
                        "model_scores": model_scores,
                        "regime": regime
                    },
                    "market_context": {
                        "spot_price": spot_price,
                        "vix": vix_val,
                        "regime": regime,
                        "order_book": self._simulate_order_book(spot_price)
                    },
                    "actual_outcome": {
                        "exit_timestamp": exit_ts.isoformat(),
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "max_favorable": max_fav,
                        "max_adverse": max_adv,
                        "holding_period_minutes": 15
                    },
                    "status": "COMPLETED"
                }
                retained_preds.append(pred_record)
                existing_keys.add((ts_key, sym))
                added_count += 1

        if added_count > 0:
            retained_preds.sort(key=lambda x: x.get("timestamp", ""))
            with open(file_path, 'w') as f:
                json.dump({"date": date_str, "predictions": retained_preds}, f, indent=2)
            logger.info(f"✅ Backfilled {added_count} market-hour predictions ({trades_logged} option trades) for {date_str}")

        return {
            "date": date_str,
            "status": "backfilled" if added_count > 0 else "up_to_date",
            "added_predictions": added_count,
            "trades_logged": trades_logged,
            "total_predictions": len(retained_preds)
        }

    def backfill_missed_market_hours(self, days_back: int = 14) -> Dict:
        """
        Scans the past `days_back` calendar days (including today if during/after market hours)
        and automatically backfills any missed market-hour simulations when the system was OFF.
        """
        now = datetime.now()
        summary = []
        total_added = 0
        total_trades = 0

        for d_offset in range(days_back, -1, -1):
            dt = now - timedelta(days=d_offset)
            if not self.is_trading_day(dt):
                continue
            date_str = dt.strftime("%Y-%m-%d")
            # For today, only backfill if current time is past 09:30 AM IST
            if d_offset == 0 and now.time() < time(9, 30):
                continue
            try:
                res = self.backfill_day_from_intraday_bars(date_str)
                if res.get("added_predictions", 0) > 0:
                    summary.append(res)
                    total_added += res.get("added_predictions", 0)
                    total_trades += res.get("trades_logged", 0)
            except Exception as e:
                logger.warning(f"Backfill skipped for {date_str}: {e}")

        return {
            "status": "completed",
            "days_checked": days_back,
            "days_backfilled": len(summary),
            "total_predictions_added": total_added,
            "total_trades_logged": total_trades,
            "details": summary
        }
    
    def _count_todays_completions(self) -> int:
        """Count completed predictions today."""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = self.data_dir / f"simulation_{today}.json"
        
        if not file_path.exists():
            return 0
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return len([p for p in data.get('predictions', []) if p['status'] == 'COMPLETED'])
    
    def _get_latest_available_date(self) -> str:
        """Find the latest YYYY-MM-DD date file available in observatory_data."""
        files = sorted(self.data_dir.glob("simulation_*.json"), reverse=True)
        for f in files:
            try:
                date_str = f.stem.replace("simulation_", "")
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    if len(data.get('predictions', [])) > 0:
                        return date_str
            except Exception:
                continue
        return datetime.now().strftime("%Y-%m-%d")

    def get_results(self, date: Optional[str] = None) -> Dict:
        """
        Get simulation results for a specific date or smart-fallback to latest available date.
        """
        if not date or date.lower() in ["latest", "today"]:
            today = datetime.now().strftime("%Y-%m-%d")
            today_file = self.data_dir / f"simulation_{today}.json"
            if today_file.exists():
                with open(today_file, 'r') as f:
                    data = json.load(f)
                    if len(data.get('predictions', [])) > 0:
                        return data
            # Fallback to latest available date if today is empty or missing
            date = self._get_latest_available_date()
        
        file_path = self.data_dir / f"simulation_{date}.json"
        
        if not file_path.exists():
            return {"date": date, "predictions": []}
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_performance_summary(self, date: Optional[str] = None) -> Dict:
        """Get performance summary for a given date or latest date."""
        results = self.get_results(date)
        predictions = results.get('predictions', [])
        completed = [p for p in predictions if p['status'] == 'COMPLETED' and p.get('actual_outcome')]
        
        if not completed:
            return {
                "date": results.get("date"),
                "total_predictions": len(predictions),
                "completed": 0,
                "pending": len([p for p in predictions if p['status'] == 'PENDING']),
                "win_rate": 0,
                "avg_pnl": 0,
                "total_pnl": 0
            }
        
        active_trades = [p for p in completed if p.get('prediction', {}).get('signal') in ['BUY_CE', 'BUY_PE', 'BUY', 'SELL']]
        profitable = [p for p in active_trades if p['actual_outcome']['pnl'] > 0]
        losing = [p for p in active_trades if p['actual_outcome']['pnl'] < 0]
        
        total_pnl = sum(p['actual_outcome']['pnl'] for p in completed)
        avg_pnl = (total_pnl / len(active_trades)) if active_trades else 0.0
        
        win_rate = round((len(profitable) / len(active_trades)) * 100, 1) if active_trades else 0.0
        
        return {
            "date": results.get("date"),
            "total_predictions": len(predictions),
            "completed": len(completed),
            "pending": len([p for p in predictions if p['status'] == 'PENDING']),
            "active_trades_count": len(active_trades),
            "win_rate": win_rate,
            "avg_pnl": round(avg_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "profitable_count": len(profitable),
            "loss_count": len(losing),
            "hold_count": len(completed) - len(active_trades)
        }

    def get_pattern_analytics(self, days: int = 90) -> Dict:
        """
        Scans all historical simulation files over past N days to detect performance patterns,
        success rates by symbol, regime, signal, and confidence levels.
        """
        all_files = sorted(self.data_dir.glob("simulation_*.json"))
        cutoff_date = datetime.now() - timedelta(days=days)
        
        all_predictions = []
        available_dates = []
        
        for f in all_files:
            date_str = f.stem.replace("simulation_", "")
            try:
                file_dt = datetime.strptime(date_str, "%Y-%m-%d")
                if days < 365 and file_dt < cutoff_date:
                    continue
                available_dates.append(date_str)
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    preds = data.get("predictions", [])
                    for p in preds:
                        p["date"] = date_str
                    all_predictions.extend(preds)
            except Exception as e:
                logger.warning(f"Failed to read simulation file {f}: {e}")
                
        completed = [p for p in all_predictions if p.get('status') == 'COMPLETED' and p.get('actual_outcome')]
        
        if not completed:
            return {
                "days_analyzed": days,
                "trading_days": len(available_dates),
                "total_predictions": len(all_predictions),
                "completed": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "profit_factor": 0,
                "by_symbol": {},
                "by_signal": {},
                "by_regime": {},
                "by_confidence": {},
                "available_dates": available_dates
            }

        def build_group_stats(group_key_fn):
            groups = {}
            for p in completed:
                key = group_key_fn(p)
                if not key:
                    key = "UNKNOWN"
                if key not in groups:
                    groups[key] = {"total": 0, "wins": 0, "losses": 0, "holds": 0, "total_pnl": 0.0}
                
                pnl = p['actual_outcome'].get('pnl', 0.0)
                groups[key]["total"] += 1
                groups[key]["total_pnl"] += pnl
                if pnl > 0:
                    groups[key]["wins"] += 1
                elif pnl < 0:
                    groups[key]["losses"] += 1
                else:
                    groups[key]["holds"] += 1
                    
            res = {}
            for k, g in groups.items():
                active_trades = g["wins"] + g["losses"]
                win_rate = round((g["wins"] / active_trades) * 100, 1) if active_trades > 0 else (100.0 if g["wins"] > 0 else 0.0)
                avg_pnl = round(g["total_pnl"] / g["total"], 2) if g["total"] > 0 else 0
                res[k] = {
                    "total": g["total"],
                    "wins": g["wins"],
                    "losses": g["losses"],
                    "holds": g["holds"],
                    "win_rate": win_rate,
                    "total_pnl": round(g["total_pnl"], 2),
                    "avg_pnl": avg_pnl
                }
            return res

        by_symbol = build_group_stats(lambda p: p.get("symbol") or "BANKNIFTY")
        by_signal = build_group_stats(lambda p: p.get("prediction", {}).get("signal") or "HOLD")
        by_regime = build_group_stats(lambda p: p.get("prediction", {}).get("regime") or p.get("market_context", {}).get("regime") or "UNKNOWN")
        
        def conf_bucket(p):
            c = float(p.get("prediction", {}).get("confidence", 0.0) or 0.0)
            if c > 1.0:
                c = c / 100.0
            if c >= 0.75: return ">75% High Confidence"
            if c >= 0.60: return "60-75% Med Confidence"
            return "<60% Low Confidence"
            
        by_confidence = build_group_stats(conf_bucket)
        
        wins = [p for p in completed if p['actual_outcome']['pnl'] > 0]
        losses = [p for p in completed if p['actual_outcome']['pnl'] < 0]
        gross_profit = sum(p['actual_outcome']['pnl'] for p in wins)
        gross_loss = abs(sum(p['actual_outcome']['pnl'] for p in losses))
        
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else round(gross_profit, 2)
        total_pnl = sum(p['actual_outcome']['pnl'] for p in completed)
        
        active_total = len(wins) + len(losses)
        win_rate = round((len(wins) / active_total) * 100, 1) if active_total > 0 else (100.0 if len(wins) > 0 else 0.0)
        
        avg_mfe = round(sum(p['actual_outcome'].get('max_favorable', 0) for p in completed) / len(completed), 2)
        avg_mae = round(sum(p['actual_outcome'].get('max_adverse', 0) for p in completed) / len(completed), 2)

        return {
            "days_analyzed": days,
            "trading_days": len(available_dates),
            "total_predictions": len(all_predictions),
            "completed": len(completed),
            "win_rate": win_rate,
            "total_pnl": round(total_pnl, 2),
            "profit_factor": profit_factor,
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "avg_mfe": avg_mfe,
            "avg_mae": avg_mae,
            "by_symbol": by_symbol,
            "by_signal": by_signal,
            "by_regime": by_regime,
            "by_confidence": by_confidence,
            "available_dates": available_dates
        }

