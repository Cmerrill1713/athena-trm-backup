"""
Rate Limiting for Athena Dev Daemon
Per-user and per-route sliding window rate limits
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter
    
    Limits requests per user per route within a time window
    """
    
    def __init__(self):
        # {(user, route): [(timestamp, timestamp, ...)]}
        self.requests: Dict[Tuple[str, str], list] = defaultdict(list)
        
        # Rate limits per route (requests per minute)
        self.limits = {
            "/assist": {"burst": 10, "sustained": 5},  # 10 burst, 5/min sustained
            "/ctx/suggest": {"burst": 20, "sustained": 10},
            "/index/rebuild": {"burst": 1, "sustained": 1}  # Very limited
        }
        
        # Global concurrent request limit per user
        self.max_concurrent_per_user = 3
        self.active_requests: Dict[str, int] = defaultdict(int)
    
    async def check_rate_limit(self, user: str, route: str):
        """
        Check if request is within rate limits
        
        Args:
            user: User ID
            route: Route path
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        now = time.time()
        key = (user, route)
        
        # Get limits for this route (or default)
        limits = self.limits.get(route, {"burst": 30, "sustained": 15})
        
        # Clean old requests (older than 60 seconds)
        if key in self.requests:
            self.requests[key] = [
                ts for ts in self.requests[key]
                if now - ts < 60
            ]
        
        # Check burst limit (last second)
        recent_requests = [ts for ts in self.requests[key] if now - ts < 1]
        if len(recent_requests) >= limits["burst"]:
            logger.warning(f"Burst limit exceeded for {user} on {route}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {limits['burst']} requests/second"
            )
        
        # Check sustained limit (last minute)
        if len(self.requests[key]) >= limits["sustained"]:
            logger.warning(f"Sustained limit exceeded for {user} on {route}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {limits['sustained']} requests/minute"
            )
        
        # Check concurrent requests
        if self.active_requests[user] >= self.max_concurrent_per_user:
            logger.warning(f"Concurrent limit exceeded for {user}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many concurrent requests: max {self.max_concurrent_per_user}"
            )
        
        # Add this request
        self.requests[key].append(now)
        self.active_requests[user] += 1
        
        logger.debug(f"Rate limit check passed for {user} on {route}")
    
    def release(self, user: str):
        """Release a concurrent request slot"""
        if self.active_requests[user] > 0:
            self.active_requests[user] -= 1


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()


async def check_rate_limit(user: str, route: str):
    """
    Middleware function to check rate limits
    
    Usage:
        await check_rate_limit(user_id, request.url.path)
    """
    await rate_limiter.check_rate_limit(user, route)


def release_rate_limit(user: str):
    """
    Release a concurrent request slot
    
    Usage (in finally block):
        release_rate_limit(user_id)
    """
    rate_limiter.release(user)

