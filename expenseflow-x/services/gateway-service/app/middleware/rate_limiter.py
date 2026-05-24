import time
from app.core.redis_client import RedisClient

class RateLimiter:
    def __init__(self, redis_client: RedisClient, calls_per_minute: int = 60):
        self.redis = redis_client
        self.calls_per_minute = calls_per_minute

    async def is_rate_limited(self, ip_address: str) -> bool:
        current_minute = int(time.time() / 60)
        key = f"rate_limit:{ip_address}:{current_minute}"
        
        # Increment key
        current_calls = self.redis.incr(key)
        
        # Set expiration to 60s if new key
        if current_calls == 1:
            self.redis.expire(key, 60)
            
        return current_calls > self.calls_per_minute
