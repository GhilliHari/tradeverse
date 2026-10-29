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
        Fetches the Last Traded Price from actual live market feed (yfinance).
        instrument_token: e.g. "NSE:BANKNIFTY", "NSE:NIFTY50", "NSE:RELIANCE", etc.
        """
        import yfinance as yf
        u_sym = str(instrument_token).upper()
        
        yf_map = {
            "NSE:BANKNIFTY": "^NSEBANK",
            "BANKNIFTY": "^NSEBANK",
            "NSE:NIFTY50": "^NSEI",
            "NSE:NIFTY": "^NSEI",
            "NIFTY": "^NSEI",
            "NSE:FINNIFTY": "^CNXFIN",
            "FINNIFTY": "^CNXFIN",
            "NSE:MIDCPNIFTY": "^NSMIDCP",
            "MIDCPNIFTY": "^NSMIDCP",
            "NSE:INDIA VIX": "^INDIAVIX",
            "NSE:RELIANCE": "RELIANCE.NS",
            "NSE:HDFCBANK": "HDFCBANK.NS",
            "NSE:TCS": "TCS.NS",
            "NSE:INFY": "INFY.NS"
        }
        
        ticker_symbol = yf_map.get(u_sym, u_sym.replace("NSE:", "") + ".NS")
        
        try:
            live_price = float(yf.Ticker(ticker_symbol).fast_info['lastPrice'])
            if live_price > 0:
                return {instrument_token: {"last_price": round(live_price, 2)}}
        except Exception:
            pass

        # Static fallback only if internet/ticker lookup fails completely
        fallback_prices = {
            "NSE:RELIANCE": 2950.0,
            "NSE:HDFCBANK": 1650.0,
            "NSE:TCS": 3950.0,
            "NSE:INFY": 1580.0,
            "NSE:BANKNIFTY": 57514.0,
            "NSE:NIFTY50": 24295.0
        }
        price = fallback_prices.get(instrument_token, 100.0)
        return {instrument_token: {"last_price": round(price, 2)}}

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
        return {
            "net": [],
            "day": []
        }

    def get_option_chain(self, symbol="NSE:BANKNIFTY"):
        """
        Generates option chain around current live spot price using Black-Scholes options pricing model and live VIX.
        """
        import yfinance as yf
        from greeks_engine import GreeksEngine

        res = self.ltp(symbol)
        spot = res.get(symbol, {}).get("last_price", 57514.0)

        # Get live VIX
        try:
            vix = float(yf.Ticker("^INDIAVIX").fast_info['lastPrice']) / 100.0
        except Exception:
            vix = 0.12 # 12% annual volatility

        # Strike step selection
        u_sym = symbol.upper()
        if "FIN" in u_sym: step = 50
        elif "MID" in u_sym: step = 25
        elif "NIFTY" in u_sym and "BANK" not in u_sym: step = 50
        else: step = 100

        base_strike = round(spot / step) * step
        ge = GreeksEngine(risk_free_rate=0.07)
        T = 3.0 / 365.0 # Assume 3 days to weekly expiry

        strikes = []
        for i in range(-5, 6):
            strike_price = base_strike + (i * step)
            ce_premium = round(ge.black_scholes_price(S=spot, K=strike_price, T=T, v=vix, option_type="CE"), 2)
            pe_premium = round(ge.black_scholes_price(S=spot, K=strike_price, T=T, v=vix, option_type="PE"), 2)

            strikes.append({
                "strike": strike_price,
                "ce_premium": max(0.5, ce_premium),
                "pe_premium": max(0.5, pe_premium),
                "oi_ce": 55000 if i == 2 else 25000,
                "oi_pe": 65000 if i == -2 else 30000
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
