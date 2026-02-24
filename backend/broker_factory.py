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
