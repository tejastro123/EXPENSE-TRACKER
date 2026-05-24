import redis.asyncio as redis
from app.core.config import settings

class AsyncRedisClient:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)

    async def ping(self):
        return await self.client.ping()

    async def close(self):
        await self.client.close()

    async def get(self, key: str):
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        return await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        return await self.client.delete(key)

    async def incr(self, key: str):
        return await self.client.incr(key)

    async def expire(self, key: str, seconds: int):
        return await self.client.expire(key, seconds)

    async def rpush(self, key: str, value: str):
        return await self.client.rpush(key, value)

    async def lrange(self, key: str, start: int, end: int):
        return await self.client.lrange(key, start, end)


redis_client = AsyncRedisClient()
