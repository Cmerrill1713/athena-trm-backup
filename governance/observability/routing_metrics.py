"""
Routing-specific metrics for Athena model router.

Tracks routing requests, latency, confidence, and fallback behavior.
"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Optional

# Routing request counter
ROUTER_REQUESTS = Counter(
    'athena_router_requests_total',
    'Total routing requests',
    ['model', 'domain', 'status']
)

# Cloud usage tracking (should be 0 in local-first mode)
CLOUD_ATTEMPTS = Counter(
    'athena_router_cloud_attempts_total',
    'Total cloud model access attempts'
)

CLOUD_BLOCKED = Counter(
    'athena_router_cloud_blocked_total',
    'Total cloud model access blocked by policy'
)

LOCAL_SUCCESS = Counter(
    'athena_router_local_success_total',
    'Total successful local model inferences',
    ['backend']
)

FALLBACK_USED = Counter(
    'athena_router_fallback_used_total',
    'Total times fallback routing was used',
    ['from_backend', 'to_backend']
)

# Routing latency histogram
ROUTER_LATENCY = Histogram(
    'athena_router_latency_ms',
    'Router latency in milliseconds',
    ['model', 'domain'],
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000)
)

# Fallback counter
ROUTER_FALLBACKS = Counter(
    'athena_fallbacks_total',
    'Total fallback invocations',
    ['reason', 'from_model', 'to_model']
)

# Reflex agent errors
REFLEX_AGENT_ERRORS = Counter(
    'reflex_agent_errors_total',
    'Reflex agent errors',
    ['agent', 'error_type']
)

# Routing confidence gauge
ROUTING_CONFIDENCE = Gauge(
    'athena_routing_confidence',
    'Current routing confidence score',
    ['model', 'domain']
)

# Domain embedding cache hits/misses
EMBEDDING_CACHE_HITS = Counter(
    'athena_embedding_cache_hits_total',
    'Domain embedding cache hits',
    ['domain']
)

EMBEDDING_CACHE_MISSES = Counter(
    'athena_embedding_cache_misses_total',
    'Domain embedding cache misses',
    ['domain']
)

# Model profile loading
MODEL_PROFILE_LOADS = Counter(
    'athena_model_profile_loads_total',
    'Model profile loads',
    ['status']  # success, error, approximate
)


class RoutingMetricsCollector:
    """High-level metrics collector for routing operations."""
    
    @staticmethod
    def record_request(
        model: str,
        domain: str,
        status: str,
        latency_ms: float,
        confidence: Optional[float] = None
    ):
        """Record a routing request with all associated metrics."""
        ROUTER_REQUESTS.labels(
            model=model,
            domain=domain,
            status=status
        ).inc()
        
        ROUTER_LATENCY.labels(
            model=model,
            domain=domain
        ).observe(latency_ms)
        
        if confidence is not None:
            ROUTING_CONFIDENCE.labels(
                model=model,
                domain=domain
            ).set(confidence)
    
    @staticmethod
    def record_fallback(
        reason: str,
        from_model: str,
        to_model: str
    ):
        """Record a fallback event."""
        ROUTER_FALLBACKS.labels(
            reason=reason,
            from_model=from_model,
            to_model=to_model
        ).inc()
    
    @staticmethod
    def record_agent_error(
        agent: str,
        error_type: str
    ):
        """Record a reflex agent error."""
        REFLEX_AGENT_ERRORS.labels(
            agent=agent,
            error_type=error_type
        ).inc()
    
    @staticmethod
    def record_cache_hit(domain: str):
        """Record an embedding cache hit."""
        EMBEDDING_CACHE_HITS.labels(domain=domain).inc()
    
    @staticmethod
    def record_cache_miss(domain: str):
        """Record an embedding cache miss."""
        EMBEDDING_CACHE_MISSES.labels(domain=domain).inc()
    
    @staticmethod
    def record_profile_load(status: str):
        """Record a model profile load event."""
        MODEL_PROFILE_LOADS.labels(status=status).inc()

    @staticmethod
    def record_cloud_attempt():
        """Record a cloud model access attempt."""
        CLOUD_ATTEMPTS.inc()

    @staticmethod
    def record_cloud_blocked():
        """Record a blocked cloud access attempt."""
        CLOUD_BLOCKED.inc()

    @staticmethod
    def record_local_success(backend: str):
        """Record successful local inference."""
        LOCAL_SUCCESS.labels(backend=backend).inc()

    @staticmethod
    def record_fallback_used(from_backend: str, to_backend: str):
        """Record fallback routing usage."""
        FALLBACK_USED.labels(from_backend=from_backend, to_backend=to_backend).inc()

    @staticmethod
    def record_routing_error(error_type: str):
        """Record routing errors."""
        ROUTER_REQUESTS.labels(model="unknown", domain="unknown", status=f"error_{error_type}").inc()


# Convenience instance
routing_metrics = RoutingMetricsCollector()

