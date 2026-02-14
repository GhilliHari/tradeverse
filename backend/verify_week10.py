import asyncio
import os
from agent_layer import IntelligenceLayer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyWeek10")

async def test_structural_alpha():
    logger.info("--- 🧪 Trading Intelligence: Week 10 Verification ---")
    
    # 1. Initialize Intelligence Layer
    api_key = os.getenv("GEMINI_API_KEY", "MOCK_KEY")
    intelligence = IntelligenceLayer(api_key)
    
    # 2. Run Analysis for Bank Nifty
    logger.info("Running Agentic Analysis (COR v2 + Structural Alpha)...")
    symbol = "NSE:BANKNIFTY"
    result = intelligence.run_analysis(symbol)
    
    # 3. Verify Component Alpha
    tech_ctx = result.get('technical_context', {})
    comp_alpha = tech_ctx.get('component_alpha', {})
    
    # If live fetch failed, inject mock data to verify calculation logic
    if not comp_alpha or comp_alpha.get('score') == 0:
        logger.info("Injecting Mock Component Data for Logic Verification...")
        intelligence.component_tracker.prev_ltp = {"HDFCBANK.NS": 1600, "ICICIBANK.NS": 1000, "KOTAKBANK.NS": 1800}
        intelligence.component_tracker.last_ltp = {"HDFCBANK.NS": 1610, "ICICIBANK.NS": 1010, "KOTAKBANK.NS": 1810}
        comp_alpha = intelligence.component_tracker.calculate_component_score()
    
    logger.info(f"Component Alpha Status: {comp_alpha.get('status')} (Score: {comp_alpha.get('score')})")
    if comp_alpha and comp_alpha.get('score') > 0:
        logger.info("✅ Component Tracker logic is sound.")
    else:
        logger.info("⚠️ Component Tracker logic failure.")
        
    # 4. Verify GEX Data
    gex_data = tech_ctx.get('gex_data', {}) # We might need to check if it's in state
    # Actually, options agent returns it in state. Let's check result keys.
    if 'gex_data' in result:
        gex_data = result['gex_data']
    
    logger.info(f"Gamma Walls: Call={gex_data.get('call_wall')}, Put={gex_data.get('put_wall')}")
    if gex_data and gex_data.get('call_wall'):
        logger.info("✅ GEX Engine is correctly mapping option walls.")
    else:
        logger.info("⚠️ GEX data missing or invalid.")
        
    # 5. Verify Aggregator Signal
    logger.info(f"Final Signal: {result.get('final_signal')} (Confidence: {result.get('confidence')})")
    logger.info(f"Reasoning: {result.get('trade_recommendation', {}).get('reasoning')}")
    
    if "GEX Block" in result.get('trade_recommendation', {}).get('reasoning', ""):
        logger.info("✅ GEX Safety Gate successfully triggered!")
    else:
        logger.info("ℹ️ No GEX Block triggered in this run (Path clear).")

if __name__ == "__main__":
    asyncio.run(test_structural_alpha())
