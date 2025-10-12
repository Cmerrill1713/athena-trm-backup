"""
Circuit Breaker Metrics

Prometheus metrics for circuit breaker state tracking.
Separated from main metrics to avoid circular imports.
"""

try:
    from prometheus_client import Gauge, Counter
    
    BREAKER_OPEN = Gauge(
        'circuit_breaker_open',
        'Circuit breaker state (1=open, 0=closed)',
        ['model', 'env', 'build']
    )
    
    BREAKER_TRIPS_TOTAL = Counter(
        'circuit_breaker_trips_total',
        'Total number of circuit breaker trips',
        ['model', 'reason', 'env', 'build']
    )
    
    BREAKER_FAILURES = Gauge(
        'circuit_breaker_failures',
        'Number of failures in current window',
        ['model', 'env', 'build']
    )
    
    BREAKER_WINDOW_SIZE = Gauge(
        'circuit_breaker_window_size',
        'Number of events in current window',
        ['model', 'env', 'build']
    )
    
    METRICS_AVAILABLE = True

except ImportError:
    METRICS_AVAILABLE = False
    
    # Dummy classes for when prometheus_client not available
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self
        def set(self, value):
            pass
        def inc(self):
            pass
    
    BREAKER_OPEN = DummyMetric()
    BREAKER_TRIPS_TOTAL = DummyMetric()
    BREAKER_FAILURES = DummyMetric()
    BREAKER_WINDOW_SIZE = DummyMetric()
