"""
Health monitoring for router providers.

Heartbeats every 5s, exponential backoff on failures.
"""
import asyncio
import time
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ProviderStatus:
    """Status tracking for a single provider."""
    
    def __init__(self, name: str, backoff_schedule: List[int]):
        self.name = name
        self.backoff_schedule = backoff_schedule
        
        self.available = False
        self.consecutive_failures = 0
        self.last_check = None
        self.last_success = None
        self.backoff_until = None
        
        # Metrics
        self.total_requests = 0
        self.total_failures = 0
        self.p95_latency_ms = 0.0
        self.recent_latencies: List[float] = []
    
    def record_success(self, latency_ms: float):
        """Record successful request."""
        self.available = True
        self.consecutive_failures = 0
        self.last_success = time.time()
        self.backoff_until = None
        
        self.total_requests += 1
        self.recent_latencies.append(latency_ms)
        
        # Keep last 100 latencies
        if len(self.recent_latencies) > 100:
            self.recent_latencies.pop(0)
        
        # Calculate p95
        if self.recent_latencies:
            sorted_latencies = sorted(self.recent_latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            self.p95_latency_ms = sorted_latencies[p95_idx]
    
    def record_failure(self):
        """Record failed request."""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.total_requests += 1
        
        # Apply backoff
        backoff_idx = min(self.consecutive_failures - 1, len(self.backoff_schedule) - 1)
        backoff_seconds = self.backoff_schedule[backoff_idx]
        self.backoff_until = time.time() + backoff_seconds
        
        # Mark unavailable after 3 consecutive failures
        if self.consecutive_failures >= 3:
            self.available = False
        
        logger.warning(
            f"Provider {self.name} failure #{self.consecutive_failures}, "
            f"backing off {backoff_seconds}s"
        )
    
    def is_in_backoff(self) -> bool:
        """Check if provider is in backoff period."""
        if self.backoff_until is None:
            return False
        return time.time() < self.backoff_until
    
    def get_error_rate(self) -> float:
        """Calculate error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Export status as dict."""
        return {
            "available": self.available and not self.is_in_backoff(),
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "error_rate": self.get_error_rate(),
            "p95_latency_ms": self.p95_latency_ms,
            "last_check": datetime.fromtimestamp(self.last_check).isoformat() if self.last_check else None,
            "last_success": datetime.fromtimestamp(self.last_success).isoformat() if self.last_success else None,
            "in_backoff": self.is_in_backoff(),
            "backoff_until": datetime.fromtimestamp(self.backoff_until).isoformat() if self.backoff_until else None
        }


class HealthMonitor:
    """Monitors health of all providers with heartbeats."""
    
    def __init__(
        self,
        providers: Dict[str, Any],
        backoff_schedule: List[int] = [1, 2, 5, 15, 60],
        heartbeat_interval: int = 5
    ):
        self.providers = providers
        self.backoff_schedule = backoff_schedule
        self.heartbeat_interval = heartbeat_interval
        
        self.status: Dict[str, ProviderStatus] = {}
        for name in providers.keys():
            self.status[name] = ProviderStatus(name, backoff_schedule)
        
        self.running = False
        self.heartbeat_task = None
        self.start_time = time.time()
    
    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time
    
    async def start(self):
        """Start health monitoring."""
        self.running = True
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"❤️  Health monitor started (interval={self.heartbeat_interval}s)")
    
    async def stop(self):
        """Stop health monitoring."""
        self.running = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")
    
    async def _heartbeat_loop(self):
        """Heartbeat loop - check all providers."""
        while self.running:
            try:
                await self._check_all_providers()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _check_all_providers(self):
        """Check health of all providers."""
        for name, provider in self.providers.items():
            status = self.status[name]
            
            # Skip if in backoff
            if status.is_in_backoff():
                continue
            
            status.last_check = time.time()
            
            try:
                # Simple health check
                start = time.time()
                is_healthy = await provider.health_check()
                latency_ms = (time.time() - start) * 1000
                
                if is_healthy:
                    status.record_success(latency_ms)
                    if status.consecutive_failures > 0:
                        logger.info(f"✅ Provider {name} recovered")
                else:
                    status.record_failure()
            
            except Exception as e:
                logger.debug(f"Provider {name} health check failed: {e}")
                status.record_failure()
    
    def record_failure(self, provider_name: str):
        """Record a provider failure from external source."""
        if provider_name in self.status:
            self.status[provider_name].record_failure()
    
    def record_success(self, provider_name: str, latency_ms: float):
        """Record a provider success from external source."""
        if provider_name in self.status:
            self.status[provider_name].record_success(latency_ms)
    
    def get_status(self, provider_name: str) -> Dict[str, Any]:
        """Get status of a specific provider."""
        if provider_name not in self.status:
            return {"available": False, "error": "Unknown provider"}
        return self.status[provider_name].to_dict()
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        return {
            name: status.to_dict()
            for name, status in self.status.items()
        }
    
    def is_available(self, provider_name: str) -> bool:
        """Check if provider is available."""
        if provider_name not in self.status:
            return False
        status = self.status[provider_name]
        return status.available and not status.is_in_backoff()


