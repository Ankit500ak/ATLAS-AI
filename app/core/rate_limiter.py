import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    Supports per-user and global rate limiting.
    """

    def __init__(self, max_clients: int = 10000):
        self._requests: Dict[str, list] = defaultdict(list)
        self._max_clients = max_clients
        self._limits = {
            "default": {"requests": 30, "window": 60},
            "ai_heavy": {"requests": 10, "window": 60},
            "financial_data": {"requests": 50, "window": 60},
        }

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host}"

    def _cleanup_old_requests(self, client_id: str, window: int):
        """Remove requests outside the time window."""
        now = time.time()
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if now - req_time < window
        ]

    def is_allowed(self, client_id: str, limit_type: str = "default") -> bool:
        """Check if request is allowed under rate limit."""
        if len(self._requests) >= self._max_clients:
            self._cleanup_stale_clients()

        limit_config = self._limits.get(limit_type, self._limits["default"])
        window = limit_config["window"]
        max_requests = limit_config["requests"]

        self._cleanup_old_requests(client_id, window)

        if len(self._requests[client_id]) >= max_requests:
            return False

        self._requests[client_id].append(time.time())
        return True

    def _cleanup_stale_clients(self):
        """Remove clients with no recent requests."""
        now = time.time()
        stale = [
            cid for cid, reqs in self._requests.items()
            if not reqs or (now - max(reqs)) > 300
        ]
        for cid in stale[:len(stale) // 2]:
            del self._requests[cid]

    def get_remaining(self, client_id: str, limit_type: str = "default") -> int:
        """Get remaining requests for client."""
        limit_config = self._limits.get(limit_type, self._limits["default"])
        window = limit_config["window"]
        max_requests = limit_config["requests"]

        self._cleanup_old_requests(client_id, window)
        return max(0, max_requests - len(self._requests[client_id]))

    def get_reset_time(self, client_id: str, limit_type: str = "default") -> float:
        """Get time until rate limit resets."""
        if not self._requests[client_id]:
            return 0
        oldest = min(self._requests[client_id])
        limit_config = self._limits.get(limit_type, self._limits["default"])
        return max(0, limit_config["window"] - (time.time() - oldest))


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    async def dispatch(self, request: Request, call_next):
        client_id = rate_limiter._get_client_id(request)

        if "/api/" in request.url.path:
            if not rate_limiter.is_allowed(client_id, "default"):
                reset_time = rate_limiter.get_reset_time(client_id)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": int(reset_time),
                    },
                )

        response = await call_next(request)

        remaining = rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = "30"

        return response
