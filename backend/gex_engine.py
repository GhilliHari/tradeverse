import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("GEXEngine")
logging.basicConfig(level=logging.INFO)

class GEXEngine:
    """
    Identifies institutional 'Gravity' points and Gamma Walls 
    based on Option Chain Open Interest (OI) mapping.
    """
    
    def __init__(self):
        self.last_analysis = {}
        
    def analyze_chain(self, chain_data: List[Dict], spot_price: float) -> Dict:
        """
        Processes option chain data to find Walls and Max Pain.
        """
        if not chain_data:
            return {}
            
        df = pd.DataFrame(chain_data)
        
        # 1. Highest OI Strikes (Walls)
        call_wall_idx = df['oi_ce'].idxmax()
        put_wall_idx = df['oi_pe'].idxmax()
        
        call_wall = df.loc[call_wall_idx, 'strike']
        put_wall = df.loc[put_wall_idx, 'strike']
        
        # 2. PCR (Put-Call Ratio) - Intraday Sentiment
        total_ce_oi = df['oi_ce'].sum()
        total_pe_oi = df['oi_pe'].sum()
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0
        
        # 3. Max Pain Approximation
        # (Strike where total value of options is minimized for buyers)
        pain_scores = []
        for strike in df['strike']:
            # For each strike, calculate theoretical loss for CE/PE buyers
            loss = 0
            for row in chain_data:
                # If expiry price is 'strike', buyers of CE/PE at 'row[strike]' lose money
                ce_loss = max(0, row['strike'] - strike) * row['oi_ce']
                pe_loss = max(0, strike - row['strike']) * row['oi_pe']
                loss += ce_loss + pe_loss
            pain_scores.append(loss)
            
        max_pain_idx = np.argmin(pain_scores)
        max_pain = df.loc[max_pain_idx, 'strike']
        
        # 4. Determine Gravity (Attraction Strength)
        # If spot is very close to a major wall or max pain
        dist_to_pain = abs(spot_price - max_pain)
        dist_to_call_wall = abs(spot_price - call_wall)
        dist_to_put_wall = abs(spot_price - put_wall)
        
        magnet_point = max_pain
        magnet_strength = 0.0
        
        if dist_to_pain < 100:
            magnet_strength = 0.5 # Moderate pull
        if dist_to_call_wall < 50 or dist_to_put_wall < 50:
            magnet_strength = 0.8 # Strong resistance/support
            magnet_point = call_wall if dist_to_call_wall < dist_to_put_wall else put_wall
            
        analysis = {
            "call_wall": int(call_wall),
            "put_wall": int(put_wall),
            "max_pain": int(max_pain),
            "pcr": round(pcr, 2),
            "magnet_point": int(magnet_point),
            "magnet_strength": magnet_strength,
            "sentiment": "BULLISH" if pcr > 1.1 else "BEARISH" if pcr < 0.7 else "NEUTRAL"
        }
        
        self.last_analysis = analysis
        return analysis

    def get_safety_gate(self, signal: str, spot_price: float) -> Dict:
        """
        Blocks or warns if a trade is being placed directly into a Major Wall.
        """
        if not self.last_analysis:
            return {"allow": True, "reason": "No GEX data"}
            
        call_wall = self.last_analysis['call_wall']
        put_wall = self.last_analysis['put_wall']
        
        if signal == "BUY" and spot_price > (call_wall - 30):
             return {"allow": False, "reason": f"APPROACHING HEAVY CALL WALL @ {call_wall}"}
             
        if signal == "SELL" and spot_price < (put_wall + 30):
             return {"allow": False, "reason": f"APPROACHING HEAVY PUT WALL @ {put_wall}"}
             
        return {"allow": True, "reason": "Path clear"}

if __name__ == "__main__":
    # Test Mock
    engine = GEXEngine()
    mock_chain = [
        {"strike": 48000, "oi_ce": 50000, "oi_pe": 200000},
        {"strike": 48100, "oi_ce": 30000, "oi_pe": 100000},
        {"strike": 48200, "oi_ce": 20000, "oi_pe": 50000},
        {"strike": 48300, "oi_ce": 40000, "oi_pe": 30000},
        {"strike": 48400, "oi_ce": 150000, "oi_pe": 10000},
        {"strike": 48500, "oi_ce": 300000, "oi_pe": 5000},
    ]
    res = engine.analyze_chain(mock_chain, 48250)
    print(f"GEX Analysis: {res}")
    gate = engine.get_safety_gate("BUY", 48480)
    print(f"Safety Gate (BUY @ 48480): {gate}")
