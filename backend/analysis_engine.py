import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import logging
from data_pipeline import DataPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalysisEngine")

class AnalysisEngine:
    def __init__(self, data, features):
        self.data = data
        self.features = features
        self.pca = None
        self.pca_data = None
        self.scaler = StandardScaler()

    def perform_pca(self, n_components=0.95):
        """
        Performs Principal Component Analysis to explain a certain percentage of variance.
        """
        logger.info(f"Performing PCA on {len(self.features)} features...")
        
        # 1. Scale data
        X = self.data[self.features].dropna()
        X_scaled = self.scaler.fit_transform(X)
        
        # 2. PCA
        self.pca = PCA(n_components=n_components)
        self.pca_data = self.pca.fit_transform(X_scaled)
        
        explained_variance = np.sum(self.pca.explained_variance_ratio_)
        logger.info(f"PCA complete. Components: {self.pca.n_components_}, Total Variance Explained: {explained_variance:.4f}")
        
        return {
            "n_components": int(self.pca.n_components_),
            "explained_variance_ratio": self.pca.explained_variance_ratio_.tolist(),
            "total_explained_variance": float(explained_variance)
        }

    def get_eigen_loadings(self, n_top_components=3):
        """
        Identifies which original features contribute most to the primary Eigen-Factors.
        """
        if self.pca is None:
            return None
            
        loadings = pd.DataFrame(
            self.pca.components_[:n_top_components].T,
            columns=[f'PC{i+1}' for i in range(n_top_components)],
            index=self.features
        )
        
        top_features = {}
        for pc in loadings.columns:
            top_features[pc] = loadings[pc].abs().sort_values(ascending=False).head(5).to_dict()
            
        return top_features

    def construct_eigen_portfolio(self):
        """
        In a portfolio context, PC1 is often the 'Market Factor'.
        We examine the loadings of PC1 as a proxy for an Eigen-Portfolio.
        """
        if self.pca is None:
            return None
            
        pc1_loadings = self.pca.components_[0]
        # Normalize loadings to act as weights
        weights = pc1_loadings / np.sum(np.abs(pc1_loadings))
        
        portfolio_loadings = pd.Series(weights, index=self.features).sort_values(ascending=False)
        
        return {
            "top_positive_drivers": portfolio_loadings.head(5).to_dict(),
            "top_negative_drags": portfolio_loadings.tail(5).to_dict()
        }

if __name__ == "__main__":
    from model_engine import ModelEngine
    pipeline = DataPipeline()
    if pipeline.run_full_pipeline():
        engine = ModelEngine() # To get standard feature list
        analysis = AnalysisEngine(pipeline.cleaned_data, engine.features)
        
        pca_results = analysis.perform_pca(n_components=0.90) # Explain 90% variance
        print("\n--- PCA SUMMARY ---")
        print(f"Compressed {len(engine.features)} indicators into {pca_results['n_components']} Principal Components.")
        print(f"Total variance preserved: {pca_results['total_explained_variance']*100:.2f}%")
        
        loadings = analysis.get_eigen_loadings()
        print("\n--- EIGEN-FACTOR LOADINGS (PC1 Drivers) ---")
        import json
        print(json.dumps(loadings["PC1"], indent=4))
        
        portfolio = analysis.construct_eigen_portfolio()
        print("\n--- EIGEN-PORTFOLIO WEIGHTS (Market Proxy) ---")
        print(json.dumps(portfolio["top_positive_drivers"], indent=4))
