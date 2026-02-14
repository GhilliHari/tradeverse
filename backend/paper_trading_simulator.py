import asyncio
import os
import json
import logging
import random
from datetime import datetime, timedelta
from agent_layer import IntelligenceLayer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PaperTrader")

class PaperTradeSimulator:
    def __init__(self, symbol="NSE:BANKNIFTY"):
        self.symbol = symbol
        self.api_key = os.getenv("GEMINI_API_KEY", "MOCK_KEY")
        self.intelligence = IntelligenceLayer(self.api_key)
        self.pnl = 0.0
        self.trades = []
        self.active_position = None
        
    async def run_simulation(self, steps=5):
        logger.info(f"--- 🚀 Starting Paper Trading Simulation for {self.symbol} ---")
        
        # Scenario: Market starts flat, then components lead up, followed by a breakout, hitting a wall, and reversal.
        scenarios = [
            {"price": 48000, "comp_dir": "NEUTRAL", "desc": "Market Start - Range Bound"},
            {"price": 48020, "comp_dir": "BULLISH", "desc": "HDFC/ICICI leading UP (Divergence)"},
            {"price": 48150, "comp_dir": "STRONG_BULLISH", "desc": "Breakout Momentum - High Confidence Zone"},
            {"price": 48450, "comp_dir": "NEUTRAL", "desc": "Approaching 48,500 Call Wall"},
            {"price": 48480, "comp_dir": "BEARISH", "desc": "Rejection from Wall - Reversal Signal"}
        ]
        
        for i, step in enumerate(scenarios[:steps]):
            logger.info(f"\n[STEP {i+1}] {step['desc']}")
            
            # 1. Update Mock State in Components
            if self.intelligence.component_tracker:
                 # Simulate component leadership
                 score = 0.8 if step['comp_dir'] == "STRONG_BULLISH" else 0.4 if step['comp_dir'] == "BULLISH" else -0.5 if step['comp_dir'] == "BEARISH" else 0.0
                 self.intelligence.component_tracker.prev_ltp = {"HDFCBANK.NS": 1600, "ICICIBANK.NS": 1000, "KOTAKBANK.NS": 1800}
                 self.intelligence.component_tracker.last_ltp = {s: p * (1 + score/100) for s, p in self.intelligence.component_tracker.prev_ltp.items()}
            
            # 2. Run Intelligence Committee
            # Note: run_analysis internally uses kite.ltp which our MockKite handles
            result = self.intelligence.run_analysis(self.symbol)
            
            signal = result.get('final_signal')
            confidence = result.get('confidence')
            structural = result.get('trade_recommendation', {}).get('reasoning', '')
            
            logger.info(f"SIGNAL: {signal} | CONFIDENCE: {confidence:.1f}%")
            logger.info(f"REASONING: {structural}")
            
            # 3. Handle Execution Logic
            await self._handle_execution(signal, step['price'], result)
            
        self._summarize()

    async def _handle_execution(self, signal, price, result):
        if self.active_position:
            # Check for Exit
            exit_signals = result.get('exit_signals', [])
            if exit_signals or (self.active_position['side'] == 'BUY' and signal == 'SELL') or (self.active_position['side'] == 'SELL' and signal == 'BUY'):
                reason = exit_signals[0]['reason'] if exit_signals else "Signal Flip"
                entry = self.active_position['price']
                trade_pnl = (price - entry) if self.active_position['side'] == 'BUY' else (entry - price)
                self.pnl += trade_pnl
                
                logger.warning(f"🔔 EXIT: {self.active_position['side']} at {price}. PnL: {trade_pnl:.2f} ({reason})")
                self.trades.append({**self.active_position, "exit_price": price, "pnl": trade_pnl, "exit_reason": reason})
                self.active_position = None
        
        if not self.active_position and signal in ['BUY', 'SELL']:
             logger.info(f"👉 ENTRY: {signal} at {price}")
             self.active_position = {"side": signal, "price": price, "time": datetime.now().isoformat()}

    def _summarize(self):
        logger.info("\n" + "="*40)
        logger.info("🏁 PAPER TRADING SUMMARY")
        logger.info(f"Total Trades: {len(self.trades)}")
        logger.info(f"Total PnL Points: {self.pnl:.2f}")
        logger.info("="*40)
        
        with open("paper_trade_log.json", "w") as f:
            json.dump(self.trades, f, indent=2)

if __name__ == "__main__":
    sim = PaperTradeSimulator()
    asyncio.run(sim.run_simulation())
