import time
import os
from agent_layer import IntelligenceLayer
import logging

# Suppress logs for cleaner benchmark output
logging.getLogger().setLevel(logging.ERROR)

def benchmark_latency(symbol="^NSEBANK", iterations=5):
    api_key = os.getenv("GEMINI_API_KEY", "MOCK_KEY")
    intel = IntelligenceLayer(api_key)
    
    print(f"--- Latency Benchmark for {symbol} ({iterations} iterations) ---")
    
    latencies = []
    for i in range(iterations):
        start_time = time.time()
        result = intel.run_analysis(symbol)
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000 # in ms
        latencies.append(latency)
        print(f"Iteration {i+1}: {latency:.2f} ms | Signal: {result['final_signal']}")
        
    avg_latency = sum(latencies) / len(latencies)
    print(f"\nAverage Latency: {avg_latency:.2f} ms")
    
    if avg_latency < 500:
        print("RESULT: SUCCESS (Under 500ms target)")
    else:
        print("RESULT: FAILED (Over 500ms target)")

if __name__ == "__main__":
    benchmark_latency()
