
import sys
import os
from datetime import datetime
import time

# Add current directory to path so we can import paper_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from paper_manager import paper_manager
    from data_pipeline import DataPipeline
    
    # Strictly BANKNIFTY Reference
    try:
        pipeline = DataPipeline(symbol="^NSEBANK", interval="1m")
        pipeline.fetch_data()
        price = float(pipeline.raw_data.iloc[-1]['Close'])
    except:
        price = 60800.0 # Fallback 

    print(f"Current BANKNIFTY Reference: {price}")

    # 1. Place a Bullish Breakthrough Order (BN F&O)
    paper_manager.place_trade(
        symbol="BANKNIFTY",
        side="BUY",
        quantity=15, # 1 Lot
        price=price,
        reasoning="SIMULATION: BN Bullish breakout confirmed by GEX Wall rejection at 60500.",
        mode="SIMULATION"
    )
    time.sleep(0.1)
    print("Placed Bank Nifty Bullish Simulation Order")

    # 2. Place a Bearish Scalp Position (BN F&O)
    paper_manager.place_trade(
        symbol="BANKNIFTY",
        side="SELL",
        quantity=30, # 2 Lots
        price=price + 50,
        reasoning="SIMULATION: BN Resistance detected at R1. Heavy Call writing observed in DerivMatrix.",
        mode="SIMULATION"
    )
    time.sleep(0.1)
    print("Placed Bank Nifty Bearish Simulation Order")

    # 3. Place a completed BN trade for History
    t3 = paper_manager.place_trade(
        symbol="BANKNIFTY",
        side="BUY",
        quantity=15,
        price=price - 100,
        reasoning="SIMULATION: BN Mean reversion from S1. RSI Oversold on 5m BN chart.",
        mode="SIMULATION"
    )
    time.sleep(0.1)
    if t3:
        paper_manager.close_trade(
            trade_id=t3['trade_id'],
            exit_price=price - 20, # Profit
            reasoning="SIMULATION: BN Target hit. Scaling out at Neutral Zone."
        )
    print("Placed and Closed a Bank Nifty Simulation Trade for History")

except Exception as e:
    print(f"Error: {e}")
