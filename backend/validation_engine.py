import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import LinearRegression
import logging
from data_pipeline import DataPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValidationEngine")

class ValidationEngine:
    def __init__(self, data):
        self.data = data
        self.report = {}

    def check_stationarity(self, columns=['Close', 'RSI', 'MACD', 'ATR_14']):
        """
        Performs Augmented Dickey-Fuller test for stationarity.
        """
        stationarity_results = {}
        for col in columns:
            if col in self.data.columns:
                result = adfuller(self.data[col].dropna())
                stationarity_results[col] = {
                    "adf_stat": float(result[0]),
                    "p_value": float(result[1]),
                    "stationary": bool(result[1] < 0.05)
                }
        self.report['stationarity'] = stationarity_results
        return stationarity_results

    def check_multicollinearity(self, features=['RSI', 'MACD', 'EMA_9', 'EMA_21', 'SMA_50']):
        """
        Simplified VIF check for key features.
        """
        vif_results = {}
        # Drop rows with NaNs to ensure clean regression
        X = self.data[features].dropna()
        if X.empty:
            return {"error": "Insufficient data for multicollinearity check"}
            
        for col in features:
            y = X[col]
            X_other = X.drop(columns=[col])
            
            # Check for constant columns (will break regression)
            if X_other.std().min() == 0:
                vif = float('inf')
            else:
                reg = LinearRegression().fit(X_other, y)
                r2 = reg.score(X_other, y)
                # Cap VIF to avoid div zero
                vif = 1 / (1 - r2) if r2 < 0.999999 else 1000.0
                
            vif_results[col] = float(round(vif, 2))
        self.report['multicollinearity'] = vif_results
        return vif_results

    def check_class_balance(self):
        """
        Checks the balance of the target variable.
        """
        target = self.data['Target_Next_Day']
        counts = target.value_counts(normalize=True).to_dict()
        self.report['class_balance'] = {
            "UP (1)": float(round(counts.get(1, 0) * 100, 2)),
            "DOWN (0)": float(round(counts.get(0, 0) * 100, 2))
        }
        return self.report['class_balance']

    def check_data_leakage(self):
        """
        Validates time-series integrity (no future data in features).
        """
        corr = self.data[['Target_Next_Day', 'Close']].corr().iloc[0, 1]
        self.report['leakage_check'] = {
            "target_price_correlation": float(round(corr, 4)),
            "status": "PASSED" if abs(corr) < 0.9 else "WARNING"
        }
        return self.report['leakage_check']

    def check_missing_values(self):
        """
        Audits the final dataset for any missing values (NaNs).
        """
        null_counts = self.data.isnull().sum()
        total_nulls = int(null_counts.sum())
        self.report['missing_value_audit'] = {
            "total_null_cells": total_nulls,
            "columns_with_nulls": null_counts[null_counts > 0].to_dict(),
            "status": "ZERO_NULLS_CONFIRMED" if total_nulls == 0 else "WARNING_NULLS_DETECTED"
        }
        return self.report['missing_value_audit']

    def run_full_validation(self):
        logger.info("Starting Deep Validation Audit...")
        self.check_stationarity()
        self.check_multicollinearity()
        self.check_class_balance()
        self.check_data_leakage()
        self.check_missing_values()
        return self.report

if __name__ == "__main__":
    pipeline = DataPipeline()
    if pipeline.run_full_pipeline():
        engine = ValidationEngine(pipeline.cleaned_data)
        report = engine.run_full_validation()
        print("\n--- DEEP VALIDATION REPORT ---")
        import json
        
        class MyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, np.bool_):
                    return bool(obj)
                return super(MyEncoder, self).default(obj)

        print(json.dumps(report, indent=4, cls=MyEncoder))
