
import sys
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugTrace")

# Import directly from the local directory
try:
    from agent_layer import IntelligenceLayer
    from config import config
except ImportError as e:
    print(f"Import Error during startup: {e}")
    sys.exit(1)

def test_intelligence():
    print("Initializing IntelligenceLayer...")
    try:
        intel = IntelligenceLayer(config.GEMINI_API_KEY)
        print("Running analysis for ^NSEBANK...")
        # Mocking minimal state
        # Instead of just calling run_analysis, we try to run individual nodes to isolate zope.interface
        from agent_layer import AgentState
        
        state: AgentState = {
            'symbol': "^NSEBANK",
            'news_context': [],
            'technical_context': {},
            'sentiment_analysis': "",
            'sentiment_label': "NEUTRAL",
            'technical_analysis': "",
            'pcr': 1.0,
            'oi_change': 0.0,
            'ai_prediction': "UNKNOWN",
            'tft_prediction': "NEUTRAL",
            'rl_action': 0,
            'order_flow_signal': "NEUTRAL",
            'order_flow_confidence': 0.0,
            'sentiment_score': 0.0,
            'risk_approval': False,
            'final_signal': "HOLD",
            'confidence': 0.0,
            'regime': "NOMINAL",
            'trade_recommendation': {},
            'is_expiry': False,
            'model_scores': {},
            'positions': [],
            'exit_signals': [],
            'custom_df': None
        }
        
        print("Testing _technical_agent node directly...")
        try:
            tech_res = intel._technical_agent(state)
            print("Technical Agent Success:", list(tech_res.keys()))
        except Exception as e:
            print("--- Technical Agent FAIL ---")
            traceback.print_exc()
            
        print("Testing full graph run (run_analysis)...")
        # run_analysis(symbol, positions=None, custom_df=None, greedy=False)
        result = intel.run_analysis("^NSEBANK")
        print("Graph Results:", list(result.keys()))
        
    except Exception as e:
        print("--- Global Error ---")
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligence()
