import pandas as pd
import numpy as np
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_engine import RiskEngine
from model_engine import ModelEngine

def test_system_status():
    print("--- 1. TESTING SYSTEM STATUS (Risk Engine) ---")
    risk = RiskEngine(daily_loss_limit=1000.0)
    
    # Initial State
    status = risk.get_risk_status()
    print(f"Initial Status: {status['circuit_breaker_status']} (Daily Loss: {status['current_daily_loss']})")
    
    # Simulate a Loss Breach
    print("Simulating ₹1500 Loss (Limit is ₹1000)...")
    risk.update_pnl(-1500)
    status = risk.get_risk_status()
    print(f"Status after Breach: {status['circuit_breaker_status']} (Daily Loss: {status['current_daily_loss']})")
    
    # Manual Reset
    print("Manually Resetting Circuit Breaker...")
    risk.trigger_circuit_breaker(active=False)
    status = risk.get_risk_status()
    print(f"Status after Reset: {'HALTED' if risk.circuit_breaker_active else 'NOMINAL'}\n")

def test_market_regime():
    print("--- 2. TESTING MARKET REGIME (AI Engine) ---")
    engine = ModelEngine(model_type="daily")
    if not engine.load_artifacts():
        print("Error: Could not load model artifacts. Ensure training has been run once.")
        return

    # Create dummy data row with required features
    features = engine.features
    dummy_data = pd.DataFrame([np.zeros(len(features))], columns=features)
    
    # 1. Test Nominal (Zeroed features usually close to training mean if scaled well)
    print("Testing NOMINAL Regime...")
    res_nominal = engine.predict(dummy_data)
    print(f"Regime: {res_nominal['regime']} (Distance: {res_nominal['ood_distance']:.2f})")

    # 2. Test VOLATILE/CRASH (Randomly extreme values to force OOD distance)
    print("\nTesting Out-of-Distribution (OOD) Detection...")
    extreme_data = pd.DataFrame([np.random.rand(len(features)) * 1000], columns=features)
    res_extreme = engine.predict(extreme_data)
    print(f"Regime: {res_extreme['regime']} (Distance: {res_extreme['ood_distance']:.2f})")
    
    if res_extreme['regime'] in ['VOLATILE', 'CRASH']:
        print(f"SUCCESS: System correctly identified '{res_extreme['regime']}' regime via OOD cluster detection.")
    else:
        print("WARNING: System did not detect OOD. Distance threshold might need adjustment.")

if __name__ == "__main__":
    test_system_status()
    test_market_regime()
