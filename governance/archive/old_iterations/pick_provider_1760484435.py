#!/usr/bin/env python3
"""
Provider Picker - Health + Latency Based Routing
Routes to best available provider based on health and latency metrics
"""

import time
import json
import requests
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ProviderHealth:
    name: str
    base_url: str
    is_healthy: bool
    latency_ms: float
    last_check: float
    consecutive_failures: int = 0

class HealthCache:
    """Cache provider health status with circuit breaker"""

    def __init__(self, check_interval_s: int = 15):
        self.cache: Dict[str, ProviderHealth] = {}
        self.check_interval = check_interval_s
        self.circuit_breaker_open: Dict[str, float] = {}

    def is_healthy(self, name: str, base_url: str) -> bool:
        """Check if provider is healthy (with circuit breaker)"""
        # Check circuit breaker
        if name in self.circuit_breaker_open:
            open_until = self.circuit_breaker_open[name]
            if time.time() < open_until:
                return False  # Circuit open
            else:
                # Half-open: try once
                del self.circuit_breaker_open[name]

        # Check cache freshness
        if name in self.cache:
            health = self.cache[name]
            if time.time() - health.last_check < self.check_interval:
                return health.is_healthy

        # Perform health check
        is_healthy, latency = self._check_health(base_url)

        # Update cache
        if name in self.cache:
            prev = self.cache[name]
            consecutive_failures = prev.consecutive_failures + 1 if not is_healthy else 0
        else:
            consecutive_failures = 0 if is_healthy else 1

        self.cache[name] = ProviderHealth(
            name=name,
            base_url=base_url,
            is_healthy=is_healthy,
            latency_ms=latency,
            last_check=time.time(),
            consecutive_failures=consecutive_failures
        )

        # Open circuit breaker after 5 failures
        if consecutive_failures >= 5:
            self.circuit_breaker_open[name] = time.time() + 30  # 30s open
            print(f"⚠️  Circuit breaker opened for {name} (30s)")

        return is_healthy

    def latency_ms(self, name: str) -> float:
        """Get cached latency for provider"""
        if name in self.cache:
            return self.cache[name].latency_ms
        return float('inf')

    def _check_health(self, base_url: str) -> Tuple[bool, float]:
        """Perform actual health check"""
        start = time.time()
        try:
            # Try common health endpoints
            for path in ["/health", "/v1/health", "/api/tags"]:
                try:
                    resp = requests.get(f"{base_url}{path}", timeout=0.8)
                    if resp.status_code == 200:
                        latency = (time.time() - start) * 1000
                        return True, latency
                except:
                    continue

            return False, float('inf')

        except Exception:
            return False, float('inf')

def pick_provider(task_type: str, policy: dict, health_cache: HealthCache) -> Optional[dict]:
    """
    Pick best provider based on health + latency

    Args:
        task_type: "vision", "chat", etc.
        policy: Routing policy configuration
        health_cache: Health status cache

    Returns:
        Provider config or None if none available
    """
    if task_type not in policy or not policy[task_type].get("enabled"):
        return None

    providers = policy[task_type].get("providers", [])
    strategy = policy[task_type].get("strategy", "health_then_latency")

    # Filter to healthy providers
    candidates = []
    for p in providers:
        if health_cache.is_healthy(p["name"], p["base"]):
            latency = health_cache.latency_ms(p["name"])
            weight = p.get("weight", 1.0)
            candidates.append((p, latency, weight))

    if not candidates:
        print(f"⚠️  No healthy providers for {task_type}")
        return None

    # Apply strategy
    if strategy == "health_then_latency":
        # Sort by latency (ascending)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    elif strategy == "bucket_then_latency":
        # Group by bucket, then pick lowest latency in preferred bucket
        # (Simplified: just pick lowest latency for now)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    # Default: lowest latency
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]

def fallback_for(task_type: str) -> Optional[dict]:
    """Get fallback provider when all primary providers fail"""
    fallbacks = {
        "vision": {"name": "ollama-vision", "base": "http://127.0.0.1:11434"},
        "chat": {"name": "ollama", "base": "http://127.0.0.1:11434"},
    }
    return fallbacks.get(task_type)

if __name__ == "__main__":
    # Test the provider picker
    policy_path = Path(__file__).parent.parent / "config" / "routing_policy.json"

    with open(policy_path) as f:
        policy = json.load(f)

    cache = HealthCache()

    print("Testing provider selection:")
    print()

    for task in ["vision", "chat"]:
        provider = pick_provider(task, policy, cache)
        if provider:
            print(f"✅ {task}: {provider['name']} @ {provider['base']}")
        else:
            fb = fallback_for(task)
            print(f"⚠️  {task}: fallback to {fb['name'] if fb else 'none'}")
