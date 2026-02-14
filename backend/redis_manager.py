
import logging
import redis
import json
from config import config

logger = logging.getLogger("RedisManager")

class RedisMock:
    def __init__(self):
        self.data = {}
        logger.info("Initializing Redis Mock (In-Memory)")

    def get(self, key):
        return self.data.get(key)

    def set(self, key, val, ex=None):
        self.data[key] = val
        return True

    def delete(self, key):
        self.data.pop(key, None)

    def ping(self):
        return True

    def sadd(self, key, *values):
        if key not in self.data:
            self.data[key] = set()
        for v in values:
            self.data[key].add(str(v))
        return len(values)

    def srem(self, key, *values):
        if key in self.data and isinstance(self.data[key], set):
            for v in values:
                self.data[key].discard(str(v))
            return len(values)
        return 0

    def smembers(self, key):
        if key in self.data and isinstance(self.data[key], set):
            return list(self.data[key])
        return []

    def exists(self, key):
        return key in self.data

def get_redis_client():
    if not config.REDIS_URL:
         logger.warning("⚠️ No REDIS_URL found. Using RedisMock.")
         return RedisMock()
         
    try:
        # redis-py is lazy, so simply creating the client is non-blocking.
        # We skip the blocking ping() here to ensure fast startup.
        # Connection errors will be handled by the application logic (or global error handler).
        client = redis.from_url(config.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        logger.info(f"Redis Client configured for {config.REDIS_URL.split('@')[-1]}") # Log safe URL
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis Config Failed: {e}. Falling back to RedisMock.")
        return RedisMock()

redis_client = get_redis_client()

class SignalCache:
    """
    Wrapper for Redis caching of expensive analysis signals.
    """
    def __init__(self, client=None):
        self.client = client if client else redis_client
        self.ttl = 60 # 1 minute default cache (since we use 1m candles)

    def cache_signal(self, symbol: str, signal_data: dict, ttl=None):
        """
        Caches the full signal dictionary.
        """
        if not self.client: return False
        try:
            key = f"signal:{symbol}"
            self.client.set(key, json.dumps(signal_data), ex=ttl if ttl else self.ttl)
            return True
        except Exception as e:
            logger.warning(f"Failed to cache signal: {e}")
            return False

    def get_signal(self, symbol: str):
        """
        Retrieves cached signal if available.
        """
        if not self.client: return None
        try:
            key = f"signal:{symbol}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached signal: {e}")
        return None
