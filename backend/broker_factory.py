import logging
import json
from config import config
from kite_client import get_kite_client
from angel_client import AngelClient
from mock_kite import MockKiteConnect
from user_context import get_user_context
from redis_manager import redis_client

logger = logging.getLogger("BrokerFactory")

class MockAngelClient:
    def __init__(self, user_id):
        self.user_id = user_id
    def is_connected(self): return True
    def profile(self): return {"user_id": self.user_id, "user_name": "Mock User", "broker": "ANGEL", "status": "MOCK"}
    def ltpData(self, exchange, tradingsymbol, symboltoken): return {"status": True, "data": {"last_price": 500.0}}
    def ltp(self, symbol): 
        if isinstance(symbol, list):
            return {s: {"last_price": 500.0} for s in symbol}
        return {symbol: {"last_price": 500.0}}
    def place_order(self, *args, **kwargs): return "MOCK_ORDER_ID"
    def get_option_chain(self, symbol, expiry=None): 
        # Simulated Bank Nifty Chain
        spot = 50000
        strikes = []
        for i in range(-5, 6):
            strike = 50000 + (i * 100)
            strikes.append({
                "strike": strike,
                "ce_premium": 100,
                "pe_premium": 100,
                "oi_ce": 50000 if strike == 50500 else 10000,
                "oi_pe": 200000 if strike == 49500 else 20000
            })
        return strikes


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
    # Default to system config if not set for user (Backwards compatibility)
    active_broker = user_settings.get("ACTIVE_BROKER", config.ACTIVE_BROKER)
    
    if active_broker == "ANGEL":
        api_key = user_settings.get("ANGEL_API_KEY", config.ANGEL_API_KEY)
        client_id = user_settings.get("ANGEL_CLIENT_ID", config.ANGEL_CLIENT_ID)
        password = user_settings.get("ANGEL_PASSWORD", config.ANGEL_PASSWORD)
        totp_key = user_settings.get("ANGEL_TOTP_KEY", config.ANGEL_TOTP_KEY)
        
        if api_key and client_id:
             return AngelClient(api_key, client_id, password, totp_key)
        else:
             logger.warning(f"Angel keys missing for {user_id}. Falling back to Mock.")
             return MockAngelClient(f"MOCK_{user_id}")

    # Default / Fallback
    return MockAngelClient(f"MOCK_{user_id}")
