import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from agent_layer import IntelligenceLayer
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_integration():
    print("\n--- Starting Verification for Week 7 (Agent Layer Integration) ---")
    
    # 1. Initialize IntelligenceLayer
    # Use a dummy key; we'll mock the Gemini model
    intel = IntelligenceLayer(gemini_api_key="MOCK_KEY")
    
    # Verify engines were loaded
    engines = [intel.causality_engine, intel.regime_engine, intel.feature_optimizer, intel.stability_filters, intel.model_engine]
    if all(engines):
        print("✅ All COR Engines initialized correctly in IntelligenceLayer.")
    else:
        print("❌ Some engines failed to initialize.")
        for name, eng in zip(["Causality", "Regime", "Optimizer", "Stability", "Model"], engines):
            if not eng: print(f"   Missing: {name}")

    # 2. Mock External Dependencies
    # Mock DataPipeline via its original module since it's lazily imported in agent_layer
    with patch('data_pipeline.DataPipeline') as MockPipeline:
        mock_pipeline_inst = MockPipeline.return_value
        mock_pipeline_inst.run_full_pipeline.return_value = True
        mock_pipeline_inst.fetch_live_data_broker.return_value = True
        
        # Create synthetic data with all required features
        features = intel.features
        dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='5min')
        synthetic_df = pd.DataFrame(index=dates)
        for feat in features:
            synthetic_df[feat] = np.random.randn(500).cumsum() if 'Dist' in feat or 'ROC' in feat else np.random.uniform(0, 100, 500)
        
        synthetic_df['Close'] = np.random.randn(500).cumsum() + 50000
        synthetic_df['Volume'] = np.random.randint(100, 1000, 500)
        synthetic_df['ATR_14'] = np.random.uniform(50, 150, 500)
        synthetic_df['High_Low'] = np.random.uniform(20, 100, 500)
        synthetic_df['Pivot'] = np.random.uniform(49000, 51000, 500)
        synthetic_df['R1'] = np.random.uniform(50000, 52000, 500)
        synthetic_df['S1'] = np.random.uniform(48000, 50000, 500)
        synthetic_df['Target_Next_Day'] = np.random.randint(0, 2, 500)
        
        mock_pipeline_inst.cleaned_data = synthetic_df
        mock_pipeline_inst.raw_data = synthetic_df # For causality
        
        # Mock Gemini Model
        intel.model.generate_content = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "SENTIMENT: POSITIVE, REASON: Market looks bullish."
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        intel.model.generate_content.return_value = mock_response
        
        # Mock Broker
        intel.kite = MagicMock()
        intel.kite.is_connected.return_value = True
        intel.kite.ltp.return_value = {"^NSEBANK": {"last_price": 50500}}
        intel.kite.get_option_chain.return_value = []

        # 3. TEST SCENARIO A: High Confidence (Should produce BUY/SELL)
        print("\nScenario A: Testing High Confidence Signal...")
        # Force a high-conviction pred in ModelEngine if possible, or just check what it returns
        # We rely on synthetic data likely producing *something*
        result = intel.run_analysis("^NSEBANK")
        
        print(f"Final Signal: {result['final_signal']}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Regime: {result['regime']}")
        
        if result['confidence'] > 0:
            print("✅ Confidence correctly propagated to Agent state.")
        
        # 4. TEST SCENARIO B: Confidence Gating (Force low confidence)
        print("\nScenario B: Testing Confidence Gating (<70%)...")
        # We can temporarily patch predict_with_confidence to return low confidence
        with patch.object(intel.model_engine, 'predict_with_confidence') as mock_pred:
            mock_pred.return_value = {
                'prediction': 1,
                'probability': 0.6,
                'confidence': 65.0, # Below 70% threshold
                'regime_provided': 'NOMINAL',
                'conviction': 'LOW',
                'is_ood': False,
                'atr': 100,
                'levels': {'Pivot': 50000, 'R1': 51000, 'S1': 49000}
            }
            
            result_gated = intel.run_analysis("^NSEBANK")
            print(f"Gated Signal: {result_gated['final_signal']} (Conf: {result_gated['confidence']:.1f}%)")
            
            if result_gated['final_signal'] == "HOLD":
                print("✅ Gating logic successfully blocked low-confidence signal.")
            else:
                print("❌ Gating logic failed to block low-confidence signal.")

    print("\n--- Integration Verification Complete ---")

if __name__ == "__main__":
    verify_integration()
