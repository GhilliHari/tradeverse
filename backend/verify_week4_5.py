import pandas as pd
import numpy as np
from data_pipeline import DataPipeline
from model_engine import ModelEngine
from feature_optimizer import FeatureOptimizer
from stability_filters import StabilityFilters
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_engines():
    print("\n--- Starting Verification for Week 4 & 5 ---")
    
    # Get features from ModelEngine to align synthetic data
    model_engine = ModelEngine(model_type='intraday')
    model_engine_features = model_engine.features

    # Use ^NSEBANK for yfinance compatibility in fallback
    dp = DataPipeline(symbol="^NSEBANK", interval="5m")
    
    try:
        status = dp.run_full_pipeline()
        if not status or dp.train_data is None:
             raise ValueError("Pipeline returned no data")
    except Exception as e:
        print(f"Pipeline run failed or returned no data: {e}")
        print("Falling back to synthetic data for verification...")
        # Create dummy data for testing if real data fails
        dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='5min')
        synthetic_df = pd.DataFrame(index=dates)
        # Initialize all features with random data
        for feat in model_engine_features:
            synthetic_df[feat] = np.random.randn(500).cumsum() if 'Dist' in feat or 'ROC' in feat else np.random.uniform(0, 100, 500)
        
        # Add basic price/volume data
        synthetic_df['Close'] = np.random.randn(500).cumsum() + 50000
        synthetic_df['Volume'] = np.random.randint(100, 1000, 500)
        synthetic_df['Target_Next_Day'] = np.random.randint(0, 2, 500)
        
        dp.train_data = synthetic_df.iloc[:400]
        dp.test_data = synthetic_df.iloc[400:]
    
    if dp.train_data is not None:
        print(f"Data ready. Rows: {len(dp.train_data)}")
    else:
        print("❌ CRITICAL: Data initialization failed completely.")
        return

    # 2. Test StabilityFilters
    try:
        print("\nStep 2: Testing StabilityFilters...")
        filters = StabilityFilters()
        smoothed = filters.apply_kalman_filter(dp.train_data['Close'])
        print(f"✅ Kalman Filter applied. Smoothed std: {smoothed.std():.2f}, Raw std: {dp.train_data['Close'].std():.2f}")
        
        # Use two of the features we just created
        outliers = filters.detect_outliers(dp.train_data[['Close', 'RSI']])
        print(f"✅ Outlier detection (Isolation Forest) found {sum(outliers)} outliers in {len(outliers)} rows.")
    except Exception as e:
        print(f"❌ StabilityFilters test failed: {e}")
        import traceback
        traceback.print_exc()

    # 3. Test FeatureOptimizer
    try:
        print("\nStep 3: Testing FeatureOptimizer...")
        model_engine = ModelEngine(model_type='intraday')
        # Train is needed for SHAP to have a model to explain
        # We need a trained model. If we can't train quickly, we'll see.
        model_engine.train(dp.train_data, dp.test_data)
        
        optimizer = FeatureOptimizer()
        # Features are defined in model_engine.features
        features_to_check = [f for f in model_engine.features if f in dp.test_data.columns]
        if not features_to_check:
                features_to_check = dp.test_data.columns.tolist()
                
        scores = optimizer.get_feature_importance_scores(model_engine.model, dp.test_data[features_to_check])
        
        if scores:
            print("✅ SHAP Importance Scores:")
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for feat, score in sorted_scores[:5]:
                print(f"  - {feat}: {score:.4f}")
        else:
            print("❌ FeatureOptimizer returned no scores.")
    except Exception as e:
        print(f"❌ FeatureOptimizer test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_engines()
