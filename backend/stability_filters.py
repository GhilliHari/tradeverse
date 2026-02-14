import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StabilityFilters:
    """
    Provides noise reduction and anomaly detection for trading data.
    Uses Kalman Filters for smoothing and Isolation Forest for outlier detection.
    """
    
    def apply_kalman_filter(self, price_series):
        """
        Smoothes price data using a Kalman Filter to reduce noise.
        """
        from pykalman import KalmanFilter
        try:
            if isinstance(price_series, pd.Series):
                prices = price_series.values
            else:
                prices = price_series
                
            kf = KalmanFilter(transition_matrices=[1],
                              observation_matrices=[1],
                              initial_state_mean=prices[0],
                              initial_state_covariance=1,
                              observation_covariance=1,
                              transition_covariance=0.01)
            
            state_means, _ = kf.filter(prices)
            return state_means.flatten()
        except Exception as e:
            logger.error(f"Error applying Kalman Filter: {e}")
            return price_series.values if isinstance(price_series, pd.Series) else price_series
    
    def detect_outliers(self, features, contamination=0.05):
        """
        Detects anomalies in feature space using Isolation Forest.
        Returns a boolean array where True indicates an outlier.
        """
        from sklearn.ensemble import IsolationForest
        try:
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            outliers = iso_forest.fit_predict(features)
            # IsolationForest returns -1 for outliers and 1 for inliers
            return outliers == -1
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return np.zeros(len(features), dtype=bool)

if __name__ == "__main__":
    print("StabilityFilters initialized. Kalman and Anomaly filters ready.")
