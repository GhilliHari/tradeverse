import logging
import json
from config import config
from kite_client import get_kite_client
from angel_client import AngelClient
from mock_kite import MockKiteConnect
from user_context import get_user_context
import redis

# Redis Connection (Reuse global or create new)
redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

logger = logging.getLogger("BrokerFactory")

# ... (MockAngelClient remains same)

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
