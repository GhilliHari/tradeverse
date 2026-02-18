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
        
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours (IST)."""
        now = datetime.now()
        current_time = now.time()
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() > 4:  # Saturday or Sunday
            return False
            
        return self.market_open <= current_time <= self.market_close
    
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
            # Get hybrid prediction from intelligence layer
            result = intelligence_layer.predict_hybrid(symbol)
            
            if not result:
                logger.warning("No prediction result from intelligence layer")
                return None
            
            # Get current market data
            from data_pipeline import DataPipeline
            pipeline = DataPipeline(symbol=f"^NSEBANK", interval="1m")
            pipeline.fetch_data()
            
            if pipeline.raw_data is None or len(pipeline.raw_data) == 0:
                logger.warning("No market data available")
                return None
            
            latest = pipeline.raw_data.iloc[-1]
            spot_price = float(latest['Close'])
            
            # Calculate strike price based on signal
            signal = result.get('final_signal', 'HOLD')
            strike_price = self._calculate_strike_price(spot_price, signal)
            
            # Get entry price (mock LTP for now - in production, fetch from broker)
            entry_price = self._get_option_ltp(symbol, strike_price, signal, spot_price)
            
            prediction = {
                "timestamp": datetime.now().isoformat(),
                "prediction": {
                    "signal": signal,
                    "strike": strike_price,
                    "confidence": result.get('confidence', 0.0),
                    "entry_price": entry_price,
                    "model_scores": result.get('model_scores', {}),
                    "regime": result.get('regime', 'UNKNOWN')
                },
                "market_context": {
                    "spot_price": spot_price,
                    "vix": self._get_vix(),  # Mock for now
                    "regime": result.get('regime', 'UNKNOWN')
                },
                "actual_outcome": None,  # Will be filled later
                "status": "PENDING"
            }
            
            logger.info(f"📸 Captured prediction: {signal} @ {strike_price} (Confidence: {result.get('confidence', 0):.2%})")
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to capture prediction: {e}")
            return None
    
    def _calculate_strike_price(self, spot_price: float, signal: str) -> int:
        """Calculate appropriate strike price based on signal and spot price."""
        # Round to nearest 100 (BANKNIFTY strikes are in 100s)
        atm_strike = round(spot_price / 100) * 100
        
        if signal == "BUY_CE":
            # Slightly OTM for calls
            return atm_strike + 100
        elif signal == "BUY_PE":
            # Slightly OTM for puts
            return atm_strike - 100
        else:
            # ATM for HOLD
            return atm_strike
    
    def _get_option_ltp(self, symbol: str, strike: int, signal: str, spot_price: float) -> float:
        """
        Get option LTP (Last Traded Price).
        Mock implementation - in production, fetch from broker API.
        """
        # Simple mock based on moneyness
        distance = abs(strike - spot_price)
        
        if signal == "BUY_CE":
            # Call premium decreases as strike moves OTM
            base_premium = 250 if distance < 200 else 150
        elif signal == "BUY_PE":
            # Put premium decreases as strike moves OTM
            base_premium = 250 if distance < 200 else 150
        else:
            base_premium = 200
        
        # Add some randomness
        import random
        return base_premium + random.uniform(-20, 20)
    
    def _get_vix(self) -> float:
        """Get India VIX value. Mock implementation."""
        import random
        return 12.0 + random.uniform(-2, 2)
    
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
            
            # Get current market price for the option
            # In production, fetch actual LTP from broker
            exit_price = self._get_option_ltp(
                "BANKNIFTY",
                strike,
                signal,
                prediction['market_context']['spot_price']
            )
            
            # Calculate P&L (assuming 15 lot size for BANKNIFTY)
            lot_size = 15
            
            if signal == "HOLD":
                pnl = 0
                pnl_pct = 0
            else:
                pnl = (exit_price - entry_price) * lot_size
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            
            # Simulate max favorable and adverse moves
            import random
            max_favorable = exit_price + random.uniform(10, 30)
            max_adverse = exit_price - random.uniform(10, 30)
            
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
            
            # Save to disk
            self._save_prediction(prediction)
            
            logger.info(f"✅ Outcome calculated: {signal} P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
            
        except Exception as e:
            logger.error(f"Failed to calculate outcome: {e}")
            prediction['status'] = 'ERROR'
    
    def _save_prediction(self, prediction: Dict):
        """Save prediction to daily JSON file."""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = self.data_dir / f"simulation_{today}.json"
        
        # Load existing data
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = {"date": today, "predictions": []}
        
        # Append or update prediction
        existing_idx = None
        for idx, p in enumerate(data['predictions']):
            if p['timestamp'] == prediction['timestamp']:
                existing_idx = idx
                break
        
        if existing_idx is not None:
            data['predictions'][existing_idx] = prediction
        else:
            data['predictions'].append(prediction)
        
        # Save
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def run_simulation_loop(self, intelligence_layer):
        """
        Main simulation loop. Runs during market hours.
        Captures predictions every N minutes and checks outcomes.
        """
        logger.info("🔭 Observatory Simulation Engine started")
        self.is_running = True
        
        try:
            while self.is_running:
                if not self.is_market_hours():
                    logger.info("⏸️  Outside market hours, pausing simulation...")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Check outcomes for pending predictions
                outcomes = await self.check_outcomes(intelligence_layer)
                if outcomes > 0:
                    logger.info(f"Processed {outcomes} outcomes")
                
                # Capture new prediction
                prediction = await self.capture_prediction(intelligence_layer)
                if prediction:
                    self.active_predictions.append(prediction)
                
                # Wait for next prediction interval
                await asyncio.sleep(self.prediction_interval)
                
        except Exception as e:
            logger.error(f"Simulation loop error: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Observatory Simulation Engine stopped")
    
    def stop(self):
        """Stop the simulation loop."""
        self.is_running = False
    
    def get_status(self) -> Dict:
        """Get current simulation status."""
        return {
            "is_running": self.is_running,
            "is_market_hours": self.is_market_hours(),
            "active_predictions": len([p for p in self.active_predictions if p['status'] == 'PENDING']),
            "completed_today": self._count_todays_completions()
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
    
    def get_results(self, date: Optional[str] = None) -> Dict:
        """
        Get simulation results for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            Simulation data dict
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        file_path = self.data_dir / f"simulation_{date}.json"
        
        if not file_path.exists():
            return {"date": date, "predictions": []}
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_performance_summary(self, date: Optional[str] = None) -> Dict:
        """Get performance summary for a given date."""
        results = self.get_results(date)
        predictions = results.get('predictions', [])
        completed = [p for p in predictions if p['status'] == 'COMPLETED' and p.get('actual_outcome')]
        
        if not completed:
            return {
                "total_predictions": len(predictions),
                "completed": 0,
                "pending": len([p for p in predictions if p['status'] == 'PENDING']),
                "win_rate": 0,
                "avg_pnl": 0,
                "total_pnl": 0
            }
        
        profitable = [p for p in completed if p['actual_outcome']['pnl'] > 0]
        
        total_pnl = sum(p['actual_outcome']['pnl'] for p in completed)
        avg_pnl = total_pnl / len(completed)
        
        return {
            "total_predictions": len(predictions),
            "completed": len(completed),
            "pending": len([p for p in predictions if p['status'] == 'PENDING']),
            "win_rate": (len(profitable) / len(completed)) * 100 if completed else 0,
            "avg_pnl": round(avg_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "profitable_count": len(profitable),
            "loss_count": len(completed) - len(profitable)
        }
