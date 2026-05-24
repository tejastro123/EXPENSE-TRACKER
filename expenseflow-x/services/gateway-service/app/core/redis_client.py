import redis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)

    async def ping(self):
        return self.client.ping()

    async def close(self):
        self.client.close()

    def get(self, key: str):
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int = None):
        return self.client.set(key, value, ex=ex)

    def delete(self, key: str):
        return self.client.delete(key)

    def incr(self, key: str):
        return self.client.incr(key)

    def expire(self, key: str, seconds: int):
        return self.client.expire(key, seconds)


redis_client = RedisClient()
