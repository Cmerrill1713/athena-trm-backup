"""
Simple token bucket rate limiter for bridge endpoints
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
import threading

class TokenBucket:
    """Token bucket rate limiter"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket

        Returns:
            True if tokens available, False if rate limited
        """
        with self.lock:
            now = time.time()
            # Refill tokens based on time elapsed
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimiter:
    """Per-token rate limiter using token buckets"""

    def __init__(self, requests_per_minute: int = 60):
        """
        Args:
            requests_per_minute: Max requests per token per minute
        """
        self.buckets: Dict[str, TokenBucket] = {}
        self.capacity = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # per second
        self.lock = threading.Lock()

    def is_allowed(self, token: str) -> bool:
        """
        Check if request is allowed for this token

        Args:
            token: Client token or identifier

        Returns:
            True if allowed, False if rate limited
        """
        with self.lock:
            if token not in self.buckets:
                self.buckets[token] = TokenBucket(self.capacity, self.refill_rate)

        return self.buckets[token].consume()

    def get_stats(self, token: str) -> Tuple[float, int]:
        """
        Get current stats for a token

        Returns:
            (remaining_tokens, capacity)
        """
        with self.lock:
            if token not in self.buckets:
                return (self.capacity, self.capacity)
            bucket = self.buckets[token]
            return (bucket.tokens, bucket.capacity)
