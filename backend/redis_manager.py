
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
    try:
        client = redis.from_url(config.REDIS_URL, decode_responses=True)
        client.ping()
        logger.info(f"Connected to Redis at {config.REDIS_URL}")
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis Connection Failed: {e}. Falling back to RedisMock.")
        return RedisMock()

redis_client = get_redis_client()
