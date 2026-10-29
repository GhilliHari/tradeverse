
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import logging
logging.basicConfig(level=logging.INFO)

from backend.agent_layer import IntelligenceLayer
from backend.config import config

def test_intelligence():
    print("Initializing IntelligenceLayer...")
    try:
        intel = IntelligenceLayer(config.GEMINI_API_KEY)
        print("Running analysis for ^NSEBANK...")
        # Mocking minimal state
        result = intel.run_analysis("^NSEBANK")
        print("Result Keys:", result.keys())
        print("Final Signal:", result.get('final_signal'))
        print("Confidence:", result.get('confidence'))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligence()
