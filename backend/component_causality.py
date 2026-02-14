import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger("ComponentCausality")
logging.basicConfig(level=logging.INFO)

class ComponentTracker:
    """
    Tracks the top 3 heavyweights of Bank Nifty (HDFC, ICICI, Kotak) 
    to identify lead-lag relationships and convergence signals.
    Combined weightage: ~62% of the index.
    """
    
    COMPONENTS = {
        "HDFCBANK.NS": 0.29,
        "ICICIBANK.NS": 0.23,
        "KOTAKBANK.NS": 0.10
    }
    
    def __init__(self, kite=None):
        self.kite = kite
        self.last_ltp = {}
        self.prev_ltp = {}
        self.symbols = list(self.COMPONENTS.keys())
        
    def fetch_live_data(self) -> Dict[str, float]:
        """Fetches latest prices for components."""
        prices = {}
        try:
            if self.kite:
                # Use Zerodha for live tracking
                kite_symbols = [f"NSE:{s.replace('.NS', '')}" for s in self.symbols]
                ltps = self.kite.ltp(kite_symbols)
                for ks in kite_symbols:
                    s = f"{ks.replace('NSE:', '')}.NS"
                    prices[s] = ltps.get(ks, {}).get('last_price', 0)
            else:
                # Fallback to yfinance snapshot
                data = yf.download(self.symbols, period="1d", interval="1m", progress=False)
                if not data.empty:
                    # Handle MultiIndex Columns (Metric, Ticker)
                    if isinstance(data.columns, pd.MultiIndex):
                        for s in self.symbols:
                            if s in data['Close'].columns:
                                prices[s] = data['Close'][s].iloc[-1]
                    else:
                        # Single symbol fallback (though unlikely here)
                        for s in self.symbols:
                             if s in data.columns:
                                 prices[s] = data[s].iloc[-1]
                        
            self.prev_ltp = self.last_ltp.copy()
            self.last_ltp = prices
            return prices
        except Exception as e:
            import traceback
            logger.error(f"Error fetching component data: {e}\n{traceback.format_exc()}")
            return {}

    def calculate_component_score(self) -> Dict:
        """
        Calculates a weighted direction score (-1.0 to 1.0).
        Positive = Heavyweights leading UP.
        Negative = Heavyweights leading DOWN.
        """
        if not self.last_ltp or not self.prev_ltp:
            return {"score": 0.0, "status": "NEUTRAL", "convergence": 0.0}
            
        score = 0.0
        details = {}
        up_count = 0
        
        for symbol, weight in self.COMPONENTS.items():
            curr = self.last_ltp.get(symbol, 0)
            prev = self.prev_ltp.get(symbol, 0)
            
            direction = 0
            if curr > prev:
                direction = 1
                up_count += 1
            elif curr < prev:
                direction = -1
                
            score += (direction * weight)
            details[symbol] = direction
            
        # Normalize score (since sum of weights is ~0.62)
        total_weight = sum(self.COMPONENTS.values())
        normalized_score = score / total_weight
        
        status = "NEUTRAL"
        if normalized_score >= 0.5: status = "STRONG_BULLISH"
        elif normalized_score > 0: status = "BULLISH"
        elif normalized_score <= -0.5: status = "STRONG_BEARISH"
        elif normalized_score < 0: status = "BEARISH"
        
        return {
            "score": round(normalized_score, 2),
            "status": status,
            "convergence": round(up_count / len(self.symbols), 2),
            "details": details
        }

    def get_lead_signal(self, index_price: float, prev_index_price: float) -> str:
        """
        Identifies divergence: Components moving but Index is flat.
        """
        res = self.calculate_component_score()
        comp_score = res['score']
        
        index_dir = 0
        if index_price > prev_index_price: index_dir = 1
        elif index_price < prev_index_price: index_dir = -1
        
        # Divergence Detection
        if comp_score >= 0.5 and index_dir <= 0:
            return "LEAD_BUY" # Heavyweights are pulling up, index likely to follow
        if comp_score <= -0.5 and index_dir >= 0:
            return "LEAD_SELL" # Heavyweights are dropping, index likely to follow
            
        return "SYNC"

if __name__ == "__main__":
    # Test Mock
    tracker = ComponentTracker()
    print("Fetching Component Data...")
    prices = tracker.fetch_live_data()
    print(f"Prices: {prices}")
    
    # Simulate a move
    tracker.prev_ltp = {s: p * 0.99 for s, p in prices.items()}
    score = tracker.calculate_component_score()
    print(f"Component Score: {score}")
