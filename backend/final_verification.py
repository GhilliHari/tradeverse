
import logging
import time
import os
import sys

# Setup basic logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("final_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FinalTest")

from agent_layer import IntelligenceLayer
from risk_engine import RiskEngine
from kill_switch import KillSwitch
from config import config

def run_test():
    logger.info("🚀 STARTING FINAL SYSTEM VERIFICATION")
    
    # 1. Initialize Components
    api_key = config.GEMINI_API_KEY
    if not api_key or api_key == "MOCK_KEY":
        logger.error("🛑 CRITICAL: Gemini API Key missing or invalid.")
        return

    try:
        intel = IntelligenceLayer(api_key)
        risk = RiskEngine()
        ks = KillSwitch()
        logger.info("✅ Intelligence Layer & Risk Engine Initialized")
    except Exception as e:
        logger.error(f"❌ Initialization Failed: {e}")
        return

    symbol = "^NSEBANK"
    
    # ---------------------------------------------------------
    # Cycle 1: Normal Operation
    # ---------------------------------------------------------
    logger.info("\n--- [CYCLE 1] NORMAL OPERATION TEST ---")
    
    # Ensure Kill Switch is OFF
    if ks.is_active():
        ks.deactivate()
        
    try:
        logger.info(f"Running Analysis for {symbol}...")
        result = intel.run_analysis(symbol)
        
        # Validation Checks
        sent_label = result.get('sentiment_label', 'UNKNOWN')
        comp_alpha = result.get('technical_context', {}).get('component_alpha', {})
        signal = result.get('final_signal')
        
        logger.info(f"📊 Signal: {signal} | Confidence: {result.get('confidence', 0):.1f}%")
        logger.info(f"🧠 Sentiment: {sent_label} (Score: {result.get('sentiment_score', 0)})")
        logger.info(f"🏗️ Component Alpha: {comp_alpha.get('status', 'N/A')} (Score: {comp_alpha.get('score', 0)})")
        
        if sent_label == "NEUTRAL" and "Model unavailable" in result.get('sentiment_analysis', ''):
             logger.warning("⚠️ Sentiment Model Failed/Defaulted.")
        else:
             logger.info("✅ Sentiment Analysis Succesful.")

        if comp_alpha.get('status', 'NEUTRAL') != 'NEUTRAL' or comp_alpha.get('score', 0) != 0:
             logger.info("✅ Component Alpha Active.")
        else:
             logger.warning("⚠️ Component Alpha Neutral/Inactive (Check Mock Data?)")

        # Simulate Risk Check for Order
        order = {"price": 100, "quantity": 15}
        risk_res = risk.validate_order(order)
        if risk_res['allowed']:
            logger.info("✅ Risk Check Passed for Test Order.")
        else:
            logger.error(f"❌ Risk Check Failed: {risk_res['reason']}")

    except Exception as e:
        logger.error(f"❌ Cycle 1 Failed: {e}", exc_info=True)

    # ---------------------------------------------------------
    # Cycle 2: Kill Switch Activation
    # ---------------------------------------------------------
    logger.info("\n--- [CYCLE 2] KILL SWITCH TEST ---")
    
    ks.activate("Final Verification Test")
    time.sleep(1) # Let FS sync
    
    if ks.is_active():
        logger.info("✅ Kill Switch Activated Successfully.")
    else:
        logger.error("❌ Kill Switch Failed to Activate.")
        
    # Test Risk Engine Response
    risk_res = risk.validate_order({"price": 100, "quantity": 15})
    if not risk_res['allowed'] and "KILL SWITCH" in risk_res['reason']:
        logger.info(f"✅ Risk Engine BLOCKED Trade: {risk_res['reason']}")
    else:
        logger.error(f"❌ Risk Engine Failed to Block: {risk_res}")

    # ---------------------------------------------------------
    # Cycle 3: System Recovery
    # ---------------------------------------------------------
    logger.info("\n--- [CYCLE 3] RECOVERY TEST ---")
    
    ks.deactivate()
    time.sleep(1)
    
    if not ks.is_active():
        logger.info("✅ Kill Switch Deactivated Successfully.")
    else:
        logger.error("❌ Kill Switch Stuck Active.")
        
    # Re-test Risk Engine
    risk_res = risk.validate_order({"price": 100, "quantity": 15})
    if risk_res['allowed']:
         logger.info("✅ System Recovered. Trading Allowed.")
    else:
         logger.error(f"❌ System Failed to Recover: {risk_res}")

    logger.info("\n🏁 FINAL VERIFICATION COMPLETE.")

if __name__ == "__main__":
    run_test()
