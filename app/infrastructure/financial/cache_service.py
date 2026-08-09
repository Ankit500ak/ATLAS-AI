from app.domain.services import CacheService
from typing import Any, Optional, Dict
import logging
import asyncio
import redis.asyncio as redis
from datetime import datetime

logger = logging.getLogger(__name__)


class CacheServiceImpl(CacheService):
    def __init__(self):
        self._redis = None
        self._local_cache = {}
        self._local_ttl = {}
        self._use_redis = False

    async def _get_redis(self):
        if self._redis is None:
            try:
                from app.config import settings
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
                await self._redis.ping()
                self._use_redis = True
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis unavailable, using local cache: {e}")
                self._use_redis = False
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        try:
            r = await self._get_redis()
            if self._use_redis and r:
                value = await r.get(key)
                if value:
                    import json
                    return json.loads(value)
            else:
                if key in self._local_cache:
                    if key in self._local_ttl:
                        if (datetime.now() - self._local_ttl[key]).total_seconds() < 3600:
                            return self._local_cache[key]
                        else:
                            del self._local_cache[key]
                            del self._local_ttl[key]
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            r = await self._get_redis()
            import json
            serialized = json.dumps(value, default=str)
            if self._use_redis and r:
                await r.setex(key, ttl, serialized)
            else:
                self._local_cache[key] = value
                self._local_ttl[key] = datetime.now()
                if len(self._local_cache) > 1000:
                    oldest = min(self._local_ttl, key=self._local_ttl.get)
                    del self._local_cache[oldest]
                    del self._local_ttl[oldest]
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            r = await self._get_redis()
            if self._use_redis and r:
                await r.delete(key)
            else:
                self._local_cache.pop(key, None)
                self._local_ttl.pop(key, None)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        try:
            r = await self._get_redis()
            count = 0
            if self._use_redis and r:
                keys = await r.keys(pattern)
                if keys:
                    count = await r.delete(*keys)
            else:
                to_delete = [k for k in self._local_cache if pattern.replace("*", "") in k]
                for k in to_delete:
                    del self._local_cache[k]
                    del self._local_ttl[k]
                count = len(to_delete)
            return count
        except Exception as e:
            logger.debug(f"Cache clear pattern error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "type": "redis" if self._use_redis else "local",
            "local_entries": len(self._local_cache),
            "redis_connected": self._use_redis,
        }