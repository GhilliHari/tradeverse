
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "tradeverse", "backend"))

from broker_factory import get_broker_client
from agent_layer import IntelligenceLayer
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationVerify")

def verify():
    # 1. Test Broker Connectivity
    logger.info("Step 1: Testing Broker Connectivity...")
    broker = get_broker_client()
    profile = broker.profile()
    logger.info(f"Profile fetched: {profile}")
    
    if profile.get("status") == "EXCEPTION":
        logger.error("Broker connection failed with exception.")
    else:
        logger.info("Broker connectivity verified (Mock or Live).")

    # 2. Test Data Pipeline + Intelligence Layer
    logger.info("\nStep 2: Testing Intelligence Layer with Broker Data Flow...")
    # Force Mock to avoid external API calls during verification if keys aren't set
    # but the logic itself should be tested.
    
    intel = IntelligenceLayer(config.GEMINI_API_KEY)
    try:
        # Run a small slice of analysis
        result = intel.run_analysis("NSE:BANKNIFTY")
        logger.info(f"Analysis successful! Signal: {result.get('final_signal')}")
        logger.info(f"LTP used: {result.get('technical_context', {}).get('ltp')}")
    except Exception as e:
        logger.error(f"Intelligence Layer failed: {e}")

    logger.info("\nVerification Complete.")

if __name__ == "__main__":
    verify()
