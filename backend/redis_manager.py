
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

class ResilientRedis:
    """
    Wraps a real Redis client with automatic, permanent failover to RedisMock
    if the remote Redis host (e.g., expired Upstash instance) is unreachable.
    Non-blocking at import time so Uvicorn binds the port immediately.
    """
    def __init__(self, url: str):
        self.url = url
        self.mock = RedisMock()
        self._failed_over = False
        try:
            self._client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=1.5,
                socket_timeout=1.5,
            )
            logger.info(f"Redis Client configured for {url.split('@')[-1]}")
        except Exception as e:
            logger.warning(f"⚠️ Redis Config Failed: {e}. Falling back to RedisMock.")
            self._client = None
            self._failed_over = True

    def _call(self, method_name: str, *args, **kwargs):
        if self._failed_over or self._client is None:
            return getattr(self.mock, method_name)(*args, **kwargs)
        try:
            return getattr(self._client, method_name)(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"⚠️ Redis unreachable ({e}). Automatically failing over to in-memory RedisMock."
            )
            self._failed_over = True
            return getattr(self.mock, method_name)(*args, **kwargs)

    def get(self, key):
        return self._call("get", key)

    def set(self, key, val, ex=None):
        return self._call("set", key, val, ex=ex)

    def delete(self, key):
        return self._call("delete", key)

    def ping(self):
        return self._call("ping")

    def sadd(self, key, *values):
        return self._call("sadd", key, *values)

    def srem(self, key, *values):
        return self._call("srem", key, *values)

    def smembers(self, key):
        return self._call("smembers", key)

    def exists(self, key):
        return self._call("exists", key)


def get_redis_client():
    if not config.REDIS_URL:
        logger.warning("⚠️ No REDIS_URL found. Using RedisMock.")
        return RedisMock()
    return ResilientRedis(config.REDIS_URL)

redis_client = get_redis_client()

class SignalCache:
    """
    Wrapper for Redis caching of expensive analysis signals.
    """
    def __init__(self, client=None):
        self.client = client if client else redis_client
        self.ttl = 300 # 5 minute default cache (since we use 5m candles)

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
