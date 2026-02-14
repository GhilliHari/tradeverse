import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureOptimizer:
    """
    Optimizes feature selection using SHAP (SHapley Additive exPlanations).
    Helps identify which causal and technical factors drive model predictions.
    """
    def __init__(self):
        self.explainer = None
    
    def calculate_shap_values(self, model, X):
        """
        Calculates SHAP values for a given model.
        Handles CalibratedClassifierCV by explaining the underlying ensemble.
        """
        try:
            import shap
            # Extract base estimator if it's a CalibratedClassifierCV
            from sklearn.calibration import CalibratedClassifierCV
            if isinstance(model, CalibratedClassifierCV):
                if hasattr(model, 'calibrated_classifiers_') and len(model.calibrated_classifiers_) > 0:
                    clf = model.calibrated_classifiers_[0]
                    # Robust check for attribute name (estimator vs base_estimator)
                    if hasattr(clf, 'estimator'):
                        model_to_explain = clf.estimator
                    elif hasattr(clf, 'base_estimator'):
                        model_to_explain = clf.base_estimator
                    else:
                        # Fallback to the top-level estimator
                        model_to_explain = model.estimator if hasattr(model, 'estimator') else model.base_estimator
                else:
                    model_to_explain = model.estimator if hasattr(model, 'estimator') else model.base_estimator
            else:
                model_to_explain = model

            if self.explainer is None:
                try:
                    self.explainer = shap.TreeExplainer(model_to_explain)
                except Exception:
                    # Fallback for non-tree models or complex ensembles like VotingClassifier
                    logger.info("Falling back to shap.Explainer for model.")
                    # For classifiers, SHAP often needs the probability function
                    if hasattr(model_to_explain, 'predict_proba'):
                        # Wrap it or pass it directly. shap.Explainer(model.predict_proba, X) is common for binary/multi-class
                        self.explainer = shap.Explainer(model_to_explain.predict_proba, X)
                    else:
                        self.explainer = shap.Explainer(model_to_explain, X)
            
            # For Explainer(predict_proba), shap_values might need different handling
            if hasattr(self.explainer, 'shap_values'):
                shap_values = self.explainer.shap_values(X)
            else:
                # New Explainer API returns a SHAP values object
                shap_output = self.explainer(X)
                if hasattr(shap_output, 'values'):
                    shap_values = shap_output.values
                else:
                    shap_values = shap_output
            return shap_values
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return None
    
    def get_feature_importance_scores(self, model, X):
        """
        Returns a dictionary mapping feature names to their mean absolute SHAP value (importance).
        """
        shap_values = self.calculate_shap_values(model, X)
        if shap_values is None:
            return {}
        
        # Mean absolute SHAP value per feature
        # If shap_values is an Explanation object, it might have .values
        if hasattr(shap_values, 'values'):
            vals = shap_values.values
        else:
            vals = shap_values

        # vals can be (samples, features) or (samples, features, classes)
        # or a list of (samples, features) for each class
        if isinstance(vals, list):
            # Take mean across all classes if it's a list
            importance = np.mean([np.abs(v).mean(axis=0) for v in vals], axis=0)
        elif len(vals.shape) == 3:
            # (samples, features, classes) -> mean across samples and classes
            importance = np.abs(vals).mean(axis=(0, 2))
        else:
            # (samples, features)
            importance = np.abs(vals).mean(axis=0)
            
        return dict(zip(X.columns, importance))

if __name__ == "__main__":
    # Internal test/demo
    print("FeatureOptimizer initialized. Ready for SHAP analysis.")
