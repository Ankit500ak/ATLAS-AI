import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """
    Multi-layer caching service with fallback.
    L1: In-memory (per-process, fast)
    L2: Redis (shared, persistent) - optional
    L3: Database (persistent, slow)
    """

    def __init__(self, max_memory_entries: int = 5000):
        self._memory_cache = {}
        self._max_memory_entries = max_memory_entries
        self._redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection if available."""
        try:
            import redis.asyncio as aioredis
            from app.config import settings
            if settings.redis_url:
                self._redis_client = aioredis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then Redis)."""
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry["expires_at"] > datetime.now():
                return entry["value"]
            else:
                del self._memory_cache[key]

        if self._redis_client:
            try:
                value = await self._redis_client.get(key)
                if value:
                    parsed = json.loads(value)
                    self._memory_cache[key] = {
                        "value": parsed,
                        "expires_at": datetime.now() + timedelta(minutes=5),
                    }
                    return parsed
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int = 900):
        """Set value in cache (both memory and Redis)."""
        if len(self._memory_cache) >= self._max_memory_entries:
            self._evict_expired()
            if len(self._memory_cache) >= self._max_memory_entries:
                self._evict_oldest(self._max_memory_entries // 4)

        self._memory_cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
        }

        if self._redis_client:
            try:
                await self._redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str),
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")

    async def delete(self, key: str):
        """Delete value from cache."""
        self._memory_cache.pop(key, None)

        if self._redis_client:
            try:
                await self._redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

    def _evict_expired(self):
        """Remove all expired entries from memory cache."""
        now = datetime.now()
        expired = [k for k, v in self._memory_cache.items() if v["expires_at"] <= now]
        for k in expired:
            del self._memory_cache[k]

    def _evict_oldest(self, count: int):
        """Remove the oldest entries from memory cache."""
        if not self._memory_cache:
            return
        sorted_keys = sorted(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k]["expires_at"],
        )
        for k in sorted_keys[:count]:
            del self._memory_cache[k]

    async def clear(self):
        """Clear all cache."""
        self._memory_cache.clear()
        if self._redis_client:
            try:
                keys = await self._redis_client.keys("*")
                if keys:
                    await self._redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        redis_connected = False
        if self._redis_client:
            try:
                redis_connected = self._redis_client.connection_pool is not None
            except Exception:
                redis_connected = False
        return {
            "memory_entries": len(self._memory_cache),
            "redis_connected": redis_connected,
        }


cache_service = CacheService()
