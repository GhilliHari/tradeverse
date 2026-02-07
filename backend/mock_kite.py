import random
import time
from datetime import datetime

class MockKiteConnect:
    """
    Simulates the Zerodha Kite Connect API interface.
    """
    def __init__(self, api_key, access_token=None):
        self.api_key = api_key
        self.access_token = access_token
        self.orders_list = [] # Avoid clash with method name 'orders'

    def is_connected(self):
        return True

    def ltp(self, instrument_token):
        """
        Simulates fetching the Last Traded Price.
        instrument_token: e.g. "NSE:INFY"
        """
        # Indian Market Base prices (INR)
        base_prices = {
            "NSE:RELIANCE": 2950.0,
            "NSE:HDFCBANK": 1650.0,
            "NSE:TCS": 3950.0,
            "NSE:INFY": 1580.0,
            "NSE:BANKNIFTY": 52500.0,
            "NSE:NIFTY50": 24200.0
        }
        price = base_prices.get(instrument_token, 100.0)
        # Add some random volatility
        volatility = 0.001 
        simulated_price = price + (price * random.uniform(-volatility, volatility))
        return {instrument_token: {"last_price": round(simulated_price, 2)}}

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None, validity=None, tag=None):
        """
        Simulates placing an order.
        """
        order_id = f"ORDER_{int(time.time() * 1000)}"
        order = {
            "order_id": order_id,
            "variety": variety,
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "product": product,
            "order_type": order_type,
            "price": price,
            "status": "COMPLETE",
            "timestamp": datetime.now().isoformat()
        }
        self.orders_list.append(order)
        return order_id

    def orders(self):
        """
        Returns the list of simulated orders.
        """
        return self.orders_list

    def positions(self):
        """
        Simulates current open positions.
        """
        # For now, return empty or dummy positions
        return {
            "net": [],
            "day": []
        }

    def get_option_chain(self, symbol="NSE:BANKNIFTY"):
        """
        Simulates a Bank Nifty Option Chain around the current spot price.
        """
        spot = self.ltp(symbol)[symbol]["last_price"]
        # Strike prices are usually at 100 point intervals for Bank Nifty
        base_strike = round(spot / 100) * 100
        strikes = []
        
        for i in range(-5, 6):
            strike_price = base_strike + (i * 100)
            # Simple heuristic for premium calculation
            dist = abs(spot - strike_price)
            ce_premium = max(10, (spot - strike_price) + (200 - dist * 0.5) + random.uniform(-5, 5))
            pe_premium = max(10, (strike_price - spot) + (200 - dist * 0.5) + random.uniform(-5, 5))
            
            strikes.append({
                "strike": strike_price,
                "ce_premium": round(ce_premium, 2),
                "pe_premium": round(pe_premium, 2),
                "oi_ce": random.randint(10000, 100000),
                "oi_pe": random.randint(10000, 100000)
            })
        return strikes

    def profile(self):
        """
        Simulates user profile.
        """
        return {
            "user_id": "TRADEVERSE_MOCK",
            "user_name": "Pro Trader",
            "email": "trader@tradeverse.ai"
        }
    def liquidate_all_positions(self):
        """
        Simulates emergency liquidation.
        """
        self.orders_list = [] # Clear orders
        return True
