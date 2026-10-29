import numpy as np
import scipy.stats as si
import logging

logger = logging.getLogger("GreeksEngine")

class GreeksEngine:
    """
    Mathematical engine for calculating Black-Scholes Options Pricing and Greeks.
    Used to generate realistic theoretical option premiums over historical Spot data.
    """
    
    def __init__(self, risk_free_rate=0.07):
        # Defaulting to 7% for India risk-free rate
        self.r = risk_free_rate 

    def calculate_d1_d2(self, S, K, T, v):
        """
        Calculates d1 and d2 parameters for Black-Scholes.
        S: Spot Price
        K: Strike Price
        T: Time to maturity (in years)
        v: Volatility (annualized standard deviation)
        """
        if T <= 0 or v <= 0:
            return 0.0, 0.0
            
        d1 = (np.log(S / K) + (self.r + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
        d2 = d1 - v * np.sqrt(T)
        return d1, d2

    def black_scholes_price(self, S, K, T, v, option_type="CE"):
        """
        Calculates theoretical option premium.
        """
        if T <= 0:
            return max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)
            
        d1, d2 = self.calculate_d1_d2(S, K, T, v)
        
        if option_type == "CE":
            price = (S * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-self.r * T) * si.norm.cdf(d2, 0.0, 1.0))
        else: # PE
            price = (K * np.exp(-self.r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * si.norm.cdf(-d1, 0.0, 1.0))
            
        return price

    def calculate_greeks(self, S, K, T, v, option_type="CE"):
        """
        Returns a dictionary of all 5 major Greeks.
        """
        if T <= 0 or v <= 0:
            return {"Delta": 1.0 if (option_type=="CE" and S>K) else -1.0 if (option_type=="PE" and K>S) else 0.0,
                    "Gamma": 0.0, "Theta": 0.0, "Vega": 0.0, "Rho": 0.0}
                    
        d1, d2 = self.calculate_d1_d2(S, K, T, v)
        
        # Gamma and Vega are identical for Calls and Puts
        gamma = si.norm.pdf(d1, 0.0, 1.0) / (S * v * np.sqrt(T))
        vega = S * si.norm.pdf(d1, 0.0, 1.0) * np.sqrt(T) * 0.01 # Divided by 100 for 1% change
        
        if option_type == "CE":
            delta = si.norm.cdf(d1, 0.0, 1.0)
            theta = (- (S * si.norm.pdf(d1, 0.0, 1.0) * v) / (2 * np.sqrt(T)) 
                     - self.r * K * np.exp(-self.r * T) * si.norm.cdf(d2, 0.0, 1.0)) / 365.0 # Daily decay
            rho = K * T * np.exp(-self.r * T) * si.norm.cdf(d2, 0.0, 1.0) * 0.01
        else: # PE
            delta = -si.norm.cdf(-d1, 0.0, 1.0)
            theta = (- (S * si.norm.pdf(d1, 0.0, 1.0) * v) / (2 * np.sqrt(T)) 
                     + self.r * K * np.exp(-self.r * T) * si.norm.cdf(-d2, 0.0, 1.0)) / 365.0 # Daily decay
            rho = -K * T * np.exp(-self.r * T) * si.norm.cdf(-d2, 0.0, 1.0) * 0.01
            
        return {
            "Delta": float(delta),
            "Gamma": float(gamma),
            "Theta": float(theta), # negative number usually
            "Vega": float(vega),
            "Rho": float(rho)
        }

    def implied_volatility(self, target_price, S, K, T, option_type="CE", tol=1e-4, max_iter=100):
        """
        Newton-Raphson method to estimate Implied Volatility (IV).
        """
        if T <= 0: return 0.0
        
        v = 0.3 # Initial guess: 30% annualized IV
        for i in range(max_iter):
            price = self.black_scholes_price(S, K, T, v, option_type)
            diff = price - target_price
            
            if abs(diff) < tol:
                return v
                
            vega = self.calculate_greeks(S, K, T, v, option_type)["Vega"] * 100 # restore to non-1% scalar
            
            if vega == 0.0: # Trap
                return v
                
            v = v - diff / vega # Newton step
            
            if v <= 0: # Volatility cannot be negative
                v = 1e-4
                
        return v
