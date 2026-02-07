from data_pipeline import DataPipeline
from model_engine import ModelEngine
import logging

logging.basicConfig(level=logging.INFO)

print("Starting debug run...")
try:
    dp = DataPipeline("^NSEBANK")
    print("Running pipeline...")
    stats = dp.run_full_pipeline()
    if stats:
        print("Pipeline Success. Stats:", stats)
        engine = ModelEngine()
        print("Training model...")
        metrics = engine.train(dp.train_data, dp.test_data)
        print("Metrics:", metrics)
    else:
        print("Pipeline Failed.")
except Exception as e:
    print("CRITICAL EXCEPTION:", str(e))
    import traceback
    traceback.print_exc()
