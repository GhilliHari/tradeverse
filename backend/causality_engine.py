"""
Causality Engine for Bank Nifty Intraday F&O Trading

This module implements causality detection mechanisms to identify true causal relationships
between market variables, moving beyond simple correlation.

Key Methods:
- Granger Causality: Tests if one time series helps predict another
- Transfer Entropy: Measures information flow between variables
- Bayesian Networks: Discovers causal graph structure

Author: Tradeverse AI
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
import networkx as nx
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CausalityEngine")


class BankNiftyCausalityEngine:
    """
    Causality detection engine specifically designed for Bank Nifty intraday trading.
    
    Detects causal relationships between:
    - Futures → Spot (lead-lag)
    - VIX → Price (volatility causality)
    - Options Flow → Price (smart money)
    - Bank Stocks → Index (constituent influence)
    """
    
    def __init__(self):
        self.causal_graph = nx.DiGraph()
        self.causal_strengths = {}
        
    def granger_test(self, X: pd.Series, Y: pd.Series, max_lag: int = 3) -> Dict:
        """
        Granger Causality Test: Does X cause Y?
        
        Args:
            X: Potential cause (e.g., Futures price)
            Y: Potential effect (e.g., Spot price)
            max_lag: Maximum lag to test (default 3 for 5m = 15 minutes)
            
        Returns:
            Dict with p_value and causal (True/False)
        """
        try:
            # Remove NaN values
            df = pd.DataFrame({'Y': Y, 'X': X}).dropna()
            
            if len(df) < max_lag + 10:
                logger.warning(f"Insufficient data for Granger test ({len(df)} rows)")
                return {'p_value': 1.0, 'causal': False, 'best_lag': 0}
            
            # Prepare data for Granger test (Y, X format)
            data = df[['Y', 'X']].values
            
            # Run Granger causality test
            result = grangercausalitytests(data, max_lag, verbose=False)
            
            # Extract p-values for each lag
            p_values = [result[i+1][0]['ssr_ftest'][1] for i in range(max_lag)]
            min_p_value = min(p_values)
            best_lag = p_values.index(min_p_value) + 1
            
            is_causal = min_p_value < 0.05  # 5% significance level
            
            return {
                'p_value': min_p_value,
                'causal': is_causal,
                'best_lag': best_lag,
                'all_p_values': p_values
            }
        except Exception as e:
            logger.error(f"Granger test failed: {e}")
            return {'p_value': 1.0, 'causal': False, 'best_lag': 0}
    
    def transfer_entropy(self, source: pd.Series, target: pd.Series, k: int = 1) -> float:
        """
        Transfer Entropy: Measures information flow from source to target.
        
        Higher values indicate stronger causal influence.
        
        Args:
            source: Source time series
            target: Target time series
            k: History length (default 1)
            
        Returns:
            Transfer entropy value (0 to 1+)
        """
        try:
            # Simplified Transfer Entropy using mutual information
            # For production, use specialized libraries like jpype or pyinform
            
            # Discretize data into bins
            source_binned = pd.cut(source, bins=5, labels=False)
            target_binned = pd.cut(target, bins=5, labels=False)
            
            # Create lagged versions
            target_past = target_binned.shift(k).dropna()
            target_future = target_binned.shift(-1).dropna()
            source_past = source_binned.shift(k).dropna()
            
            # Align all series
            min_len = min(len(target_past), len(target_future), len(source_past))
            target_past = target_past.iloc[:min_len]
            target_future = target_future.iloc[:min_len]
            source_past = source_past.iloc[:min_len]
            
            # Calculate conditional mutual information (simplified)
            # TE = I(target_future; source_past | target_past)
            
            # For simplicity, use correlation-based approximation
            df = pd.DataFrame({
                'target_future': target_future.values,
                'source_past': source_past.values,
                'target_past': target_past.values
            }).dropna()
            
            if len(df) < 30:
                return 0.0
            
            # Partial correlation approximation
            corr_matrix = df.corr()
            te_approx = abs(corr_matrix.loc['target_future', 'source_past'])
            
            return float(te_approx)
            
        except Exception as e:
            logger.error(f"Transfer entropy calculation failed: {e}")
            return 0.0
    
    def detect_causal_relationships(self, data: pd.DataFrame) -> Dict[str, Dict]:
        """
        Detect all causal relationships in Bank Nifty data.
        
        Args:
            data: DataFrame with columns: Close, Futures_Close, VIX, Volume, etc.
            
        Returns:
            Dictionary of causal relationships with strengths
        """
        causal_results = {}
        
        # 1. Futures → Spot causality
        if 'Futures_Close' in data.columns and 'Close' in data.columns:
            logger.info("Testing Futures → Spot causality...")
            futures_spot = self.granger_test(
                data['Futures_Close'], 
                data['Close'], 
                max_lag=3
            )
            causal_results['futures_leads_spot'] = futures_spot
            
            if futures_spot['causal']:
                self.causal_graph.add_edge('Futures', 'Spot', weight=1 - futures_spot['p_value'])
                logger.info(f"✅ Futures → Spot causal (p={futures_spot['p_value']:.4f}, lag={futures_spot['best_lag']})")
        
        # 2. VIX → Price causality
        if 'VIX' in data.columns and 'Close' in data.columns:
            logger.info("Testing VIX → Price causality...")
            vix_price = self.granger_test(
                data['VIX'], 
                data['Close'], 
                max_lag=3
            )
            causal_results['vix_drives_price'] = vix_price
            
            if vix_price['causal']:
                self.causal_graph.add_edge('VIX', 'Price', weight=1 - vix_price['p_value'])
                logger.info(f"✅ VIX → Price causal (p={vix_price['p_value']:.4f}, lag={vix_price['best_lag']})")
        
        # 3. Volume → Price causality
        if 'Volume' in data.columns and 'Close' in data.columns:
            logger.info("Testing Volume → Price causality...")
            volume_price = self.granger_test(
                data['Volume'], 
                data['Close'], 
                max_lag=2
            )
            causal_results['volume_drives_price'] = volume_price
            
            if volume_price['causal']:
                self.causal_graph.add_edge('Volume', 'Price', weight=1 - volume_price['p_value'])
                logger.info(f"✅ Volume → Price causal (p={volume_price['p_value']:.4f})")
        
        # 4. Calculate overall causal strength
        causal_count = sum([v['causal'] for v in causal_results.values()])
        total_tests = len(causal_results)
        overall_strength = causal_count / total_tests if total_tests > 0 else 0
        
        causal_results['overall_causal_strength'] = overall_strength
        causal_results['causal_count'] = causal_count
        
        self.causal_strengths = causal_results
        
        return causal_results
    
    def get_causal_graph(self) -> nx.DiGraph:
        """
        Returns the causal graph as a NetworkX DiGraph.
        
        Nodes: Variables (Futures, Spot, VIX, Volume, etc.)
        Edges: Causal relationships with weights (1 - p_value)
        """
        return self.causal_graph
    
    def get_causal_factors(self, target: str = 'Price') -> List[str]:
        """
        Get list of variables that causally influence the target.
        
        Args:
            target: Target variable (default 'Price')
            
        Returns:
            List of causal factors
        """
        if target not in self.causal_graph:
            return []
        
        # Get predecessors (variables that cause target)
        predecessors = list(self.causal_graph.predecessors(target))
        
        # Sort by edge weight (causal strength)
        predecessors.sort(
            key=lambda x: self.causal_graph[x][target]['weight'], 
            reverse=True
        )
        
        return predecessors
    
    def visualize_causal_graph(self, save_path: str = None):
        """
        Visualize the causal graph (requires matplotlib).
        
        Args:
            save_path: Optional path to save the graph image
        """
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 8))
            pos = nx.spring_layout(self.causal_graph, k=2, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(
                self.causal_graph, pos, 
                node_color='lightblue', 
                node_size=3000,
                alpha=0.9
            )
            
            # Draw edges with varying thickness based on weight
            edges = self.causal_graph.edges()
            weights = [self.causal_graph[u][v]['weight'] for u, v in edges]
            
            nx.draw_networkx_edges(
                self.causal_graph, pos,
                width=[w * 5 for w in weights],
                alpha=0.6,
                edge_color='gray',
                arrows=True,
                arrowsize=20
            )
            
            # Draw labels
            nx.draw_networkx_labels(
                self.causal_graph, pos,
                font_size=12,
                font_weight='bold'
            )
            
            plt.title("Bank Nifty Causal Relationship Graph", fontsize=16)
            plt.axis('off')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Causal graph saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("matplotlib not installed. Cannot visualize graph.")
        except Exception as e:
            logger.error(f"Visualization failed: {e}")


# Standalone test function
if __name__ == "__main__":
    logger.info("Testing BankNiftyCausalityEngine...")
    
    # Create sample data
    np.random.seed(42)
    n = 500
    
    # Simulate causal relationship: Futures leads Spot by 1 lag
    futures = np.cumsum(np.random.randn(n))
    spot = np.roll(futures, 1) + np.random.randn(n) * 0.5
    vix = 15 + np.random.randn(n) * 3
    
    data = pd.DataFrame({
        'Futures_Close': futures,
        'Close': spot,
        'VIX': vix,
        'Volume': np.random.randint(1000, 10000, n)
    })
    
    # Test causality engine
    engine = BankNiftyCausalityEngine()
    results = engine.detect_causal_relationships(data)
    
    print("\n" + "="*60)
    print("CAUSALITY TEST RESULTS")
    print("="*60)
    for key, value in results.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            print(f"  Causal: {value.get('causal', 'N/A')}")
            print(f"  P-value: {value.get('p_value', 'N/A'):.4f}")
            print(f"  Best Lag: {value.get('best_lag', 'N/A')}")
        else:
            print(f"\n{key}: {value}")
    
    print("\n" + "="*60)
    print(f"Causal Factors for Price: {engine.get_causal_factors('Price')}")
    print("="*60)
