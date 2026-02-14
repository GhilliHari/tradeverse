import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("FastTrader")

def run_fast_simulation():
    logger.info("--- 🏎️ HIGH-SPEED PAPER TRADING SIMULATION (6-PILLAR HYBRID) ---")
    
    scenarios = [
        {
            "step": 1,
            "context": "Market Open (9:30 AM)",
            "data": {"ltp": 48000, "regime": "NOMINAL", "confidence": 45, "comp_alpha": 0.0, "gex": "None"},
            "result": "HOLD",
            "reasoning": "Confidence 45% below threshold. Causal lead neutral."
        },
        {
            "step": 2,
            "context": "Accumulation (10:15 AM)",
            "data": {"ltp": 48020, "regime": "NOMINAL", "confidence": 62, "comp_alpha": 0.45, "gex": "None"},
            "result": "HOLD",
            "reasoning": "Component Alpha (HDFC/ICICI) turning BULLISH (+0.45). Waiting for trend confirmation."
        },
        {
            "step": 3,
            "context": "Breakout Trigger (10:45 AM)",
            "data": {"ltp": 48100, "regime": "BULLISH", "confidence": 88, "comp_alpha": 0.92, "gex": "Call Wall @ 48,500"},
            "result": "BUY",
            "reasoning": "STRONG BULLISH Convergence. Components leading (+0.92). Clear path to 48,500 Call Wall."
        },
        {
            "step": 4,
            "context": "Exitance Zone (1:30 PM)",
            "data": {"ltp": 48460, "regime": "VOLATILE", "confidence": 75, "comp_alpha": 0.10, "gex": "Call Wall @ 48,500"},
            "result": "EXIT / SELL",
            "reasoning": "Approaching Gamma Wall (48,500). GEX Block active for new longs. Scaling out."
        },
        {
            "step": 5,
            "context": "Mean Reversion (2:45 PM)",
            "data": {"ltp": 48420, "regime": "RANGE_BOUND", "confidence": 82, "comp_alpha": -0.65, "gex": "Max Pain @ 48,300"},
            "result": "SELL (SHORT)",
            "reasoning": "Rejection from Call Wall. Components leading DOWN (-0.65). Targeting Max Pain @ 48,300."
        }
    ]

    total_pnl = 0
    entry_price = 0
    active_side = None

    for s in scenarios:
        logger.info(f"\n[Scenario {s['step']}] {s['context']}")
        logger.info(f" > State: BN @ {s['data']['ltp']} | Regime: {s['data']['regime']} | Confidence: {s['data']['confidence']}%")
        logger.info(f" > Structural: Comp Alpha: {s['data']['comp_alpha']} | GEX: {s['data']['gex']}")
        logger.info(f" > AGENT DECISION: {s['result']}")
        logger.info(f" > LOGIC: {s['reasoning']}")

        if s['result'] == "BUY" and not active_side:
            entry_price = s['data']['ltp']
            active_side = "BUY"
            logger.info(f" ✅ EXECUTED BUY @ {entry_price}")
        elif (s['result'] == "EXIT / SELL" or s['result'] == "SELL") and active_side == "BUY":
            pnl = s['data']['ltp'] - entry_price
            total_pnl += pnl
            logger.info(f" 🔔 EXECUTED EXIT @ {s['data']['ltp']}. PnL: {pnl} pts")
            active_side = None
            if s['result'] == "SELL":
                entry_price = s['data']['ltp']
                active_side = "SELL"
                logger.info(f" ✅ EXECUTED SHORT @ {entry_price}")
        elif s['result'] == "SELL" and not active_side:
             entry_price = s['data']['ltp']
             active_side = "SELL"
             logger.info(f" ✅ EXECUTED SHORT @ {entry_price}")

    logger.info("\n" + "="*50)
    logger.info(f"💰 FINAL SIMULATION PnL: {total_pnl} Points")
    logger.info("="*50)

if __name__ == "__main__":
    run_fast_simulation()
