import logging
import json
from config import config
from kite_client import get_kite_client
from angel_client import AngelClient
from mock_kite import MockKiteConnect
from user_context import get_user_context
from redis_manager import redis_client

logger = logging.getLogger("BrokerFactory")

# In-memory cache for broker clients to avoid expensive re-logins on every request
# Format: { user_id: { "client": broker_instance, "credentials_hash": str } }
BROKER_CACHE = {}

def _get_credentials_hash(settings: dict) -> str:
    """Creates a simple hash of credentials to detect changes."""
    keys = ["ANGEL_API_KEY", "ANGEL_CLIENT_ID", "ANGEL_PASSWORD", "ANGEL_TOTP_KEY"]
    cred_vals = [str(settings.get(k, "")) for k in keys]
    import hashlib
    return hashlib.md5("".join(cred_vals).encode()).hexdigest()

class MockAngelClient:
    def __init__(self, user_id):
        self.user_id = user_id
    def is_connected(self): return True
    def profile(self): return {"user_id": self.user_id, "user_name": "Mock User", "broker": "ANGEL", "status": "MOCK"}
    def ltpData(self, exchange, tradingsymbol, symboltoken): return {"status": True, "data": {"last_price": 57446.25}}
    def ltp(self, symbol): 
        def _get_mock_ltp(sym):
            u_sym = sym.upper()
            try:
                import yfinance as yf
                if "BANK" in u_sym:
                    return float(yf.Ticker("^NSEBANK").fast_info['lastPrice'])
                if "FIN" in u_sym:
                    return float(yf.Ticker("^CNXFIN").fast_info['lastPrice'])
                if "MID" in u_sym:
                    return float(yf.Ticker("^NSMIDCP").fast_info['lastPrice'])
                return float(yf.Ticker("^NSEI").fast_info['lastPrice'])
            except Exception:
                if "BANK" in u_sym: return 57446.25
                if "FIN" in u_sym: return 22500.0
                if "MID" in u_sym: return 12500.0
                return 24471.70

        if isinstance(symbol, list):
            return {s: {"last_price": _get_mock_ltp(s)} for s in symbol}
        return {symbol: {"last_price": _get_mock_ltp(symbol)}}

    def place_order(self, *args, **kwargs): return f"MOCK_ORDER_{abs(hash(str(args) + str(kwargs))) % 1000000}"
    def modify_order(self, order_id, price=None, quantity=None, **kwargs):
        logger.info(f"MockAngelClient: Modified order {order_id} to price={price}, qty={quantity}")
        return {"status": True, "order_id": order_id}
    def cancel_order(self, order_id, variety="NORMAL"):
        logger.info(f"MockAngelClient: Cancelled order {order_id}")
        return {"status": True, "order_id": order_id}
    def get_option_chain(self, symbol, expiry=None): 
        import yfinance as yf
        from greeks_engine import GreeksEngine

        res = self.ltp(symbol)
        spot = res.get(symbol, {}).get("last_price", 57514.0)

        # Get live VIX
        try:
            vix = float(yf.Ticker("^INDIAVIX").fast_info['lastPrice']) / 100.0
        except Exception:
            vix = 0.12 # 12% annual volatility

        u_symbol = symbol.upper()
        if "FIN" in u_symbol: step = 50
        elif "MID" in u_symbol: step = 25
        elif "NIFTY" in u_symbol and "BANK" not in u_symbol: step = 50
        else: step = 100

        base_strike = round(spot / step) * step
        ge = GreeksEngine(risk_free_rate=0.07)
        T = 3.0 / 365.0

        strikes = []
        for i in range(-5, 6):
            strike = base_strike + (i * step)
            ce_premium = round(ge.black_scholes_price(S=spot, K=strike, T=T, v=vix, option_type="CE"), 2)
            pe_premium = round(ge.black_scholes_price(S=spot, K=strike, T=T, v=vix, option_type="PE"), 2)

            strikes.append({
                "strike": strike,
                "ce_premium": max(0.5, ce_premium),
                "pe_premium": max(0.5, pe_premium),
                "oi_ce": 150000 if i == 2 else 20000, # Call Wall
                "oi_pe": 250000 if i == -2 else 30000 # Put Wall
            })
        return strikes

    
    def _get_token_and_exchange(self, symbol):
        """Simulates token resolution."""
        if "BANKNIFTY" in symbol.upper() or "NSEBANK" in symbol.upper():
            return "NSE", "BANKNIFTY", "99926009"
        if "NIFTY" in symbol.upper() and ("BANK" not in symbol.upper() and "FIN" not in symbol.upper() and "MID" not in symbol.upper()):
            return "NSE", "NIFTY", "99926000"
        if "FIN" in symbol.upper():
            return "NSE", "FINNIFTY", "99926037"
        if "MID" in symbol.upper() or "NSMIDCP" in symbol.upper():
            return "NSE", "MIDCPNIFTY", "99926074"
        return "NSE", symbol, "12345"

    def get_historical_data(self, exchange, token, interval, start_date, end_date):
        """Simulates historical data fetching."""
        # Avoid real network calls, return None to trigger yfinance fallback if needed
        # or return mock candles. For backtests, yfinance is better for mock.
        return None 
    
    def search_scrip(self, symbol):
        return [{"exchange": "NSE", "tradingsymbol": symbol, "token": "12345"}]



def get_broker_client(user_id: str = None):
    """
    Factory to return a broker client for a specific user.
    If no user_id is provided, it attempts to get it from context.
    """
    if not user_id:
        user_id = get_user_context()
        
    logger.info(f"Factory initializing broker for User: {user_id}")

    # Fetch User Credentials from Redis
    user_key = f"user:{user_id}:settings"
    user_settings_json = redis_client.get(user_key)
    
    user_settings = {}
    if user_settings_json:
        try:
            user_settings = json.loads(user_settings_json)
        except:
             logger.error(f"Failed to parse settings for {user_id}")

    # Determine Environment and Broker for this user
    # Default to system config ONLY IF user is OWNER. 
    # Otherwise, require specific keys or fall back to Mock.
    is_owner = user_id == config.OWNER_EMAIL or redis_client.get(f"user:{user_id}:email") == config.OWNER_EMAIL # Backup check
    
    active_broker = user_settings.get("ACTIVE_BROKER", config.ACTIVE_BROKER if is_owner else "MOCK")
    
    if active_broker == "ANGEL":
        # Only use global config defaults if the user is the owner
        api_key = user_settings.get("ANGEL_API_KEY", config.ANGEL_API_KEY if is_owner else None)
        client_id = user_settings.get("ANGEL_CLIENT_ID", config.ANGEL_CLIENT_ID if is_owner else None)
        password = user_settings.get("ANGEL_PASSWORD", config.ANGEL_PASSWORD if is_owner else None)
        totp_key = user_settings.get("ANGEL_TOTP_KEY", config.ANGEL_TOTP_KEY if is_owner else None)
        
        if api_key and client_id:
            # CHECK CACHE
            current_cred_hash = _get_credentials_hash(user_settings)
            cached_data = BROKER_CACHE.get(user_id)
            
            if cached_data and cached_data.get("credentials_hash") == current_cred_hash:
                cached_client = cached_data.get("client")
                if hasattr(cached_client, 'is_connected') and cached_client.is_connected():
                    logger.info(f"Reusing cached AngelClient for {user_id}")
                    return cached_client
            
            # CREATE NEW CLIENT
            logger.info(f"Creating NEW AngelClient for {user_id} (Cache Miss or Cred Change)")
            client = AngelClient(api_key, client_id, password, totp_key)
            BROKER_CACHE[user_id] = {
                "client": client,
                "credentials_hash": current_cred_hash
            }
            return client
        else:
             logger.warning(f"Angel keys missing for unauthorized user {user_id}. Falling back to Mock.")
             return MockAngelClient(f"MOCK_{user_id}")

    # Default / Fallback
    return MockAngelClient(f"MOCK_{user_id}")
