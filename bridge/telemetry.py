#!/usr/bin/env python3
"""
Production Telemetry - Tier 4
Provides: Metrics, Tracing, Structured Logging
"""
import logging
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
import asyncio

# ============================================================================
# Structured JSON Logging
# ============================================================================

class JsonFormatter(logging.Formatter):
    """JSON formatter with context injection"""

    def format(self, record):
        base = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }

        # Add context if available
        if hasattr(record, "ctx"):
            base.update(record.ctx)

        # Add exception if present
        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        # Add service info
        base["service"] = os.getenv("SERVICE_NAME", "unknown")
        base["pid"] = os.getpid()
        base["commit"] = os.getenv("GIT_COMMIT", "dev")[:8]
        base["mode"] = os.getenv("USE_MOCK", "1") == "0" and "real" or "mock"

        return json.dumps(base)

def setup_json_logging(service_name: str = "bridge"):
    """Configure JSON logging for production"""
    os.environ["SERVICE_NAME"] = service_name

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Root logger
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root

# ============================================================================
# Prometheus Metrics
# ============================================================================

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Watchdog metrics
watchdog_heals_total = Counter(
    "watchdog_heals_total",
    "Total watchdog recovery attempts",
    ["service", "outcome"]
)

watchdog_recovery_duration_seconds = Gauge(
    "watchdog_recovery_duration_seconds",
    "Time taken for last recovery",
    ["service"]
)

watchdog_max_retries_reached = Gauge(
    "watchdog_max_retries_reached",
    "Watchdog hit max retries (1=yes, 0=no)",
    ["service"]
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service", "backend"]
)

circuit_breaker_trips_total = Counter(
    "circuit_breaker_trips_total",
    "Total circuit breaker trips",
    ["service", "backend", "reason"]
)

# Service info
service_info = Info(
    "service_info",
    "Service metadata"
)

# Service health
service_up = Gauge(
    "up",
    "Service is up (1) or down (0)",
    ["service"]
)

# ============================================================================
# FastAPI Instrumentation
# ============================================================================

class MetricsMiddleware:
    """FastAPI middleware for automatic metrics collection"""

    def __init__(self, app: FastAPI, service_name: str = "bridge"):
        self.app = app
        self.service_name = service_name

        # Set service info
        service_info.info({
            "service": service_name,
            "version": os.getenv("VERSION", "dev"),
            "commit": os.getenv("GIT_COMMIT", "unknown")[:8],
            "mode": os.getenv("USE_MOCK", "1") == "0" and "real" or "mock",
        })

        # Mark service as up
        service_up.labels(service=service_name).set(1)

    async def __call__(self, request: Request, call_next):
        # Skip metrics endpoint from being counted
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track request
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time

            # Increment request counter
            http_requests_total.labels(
                service=self.service_name,
                method=request.method,
                endpoint=request.url.path,
                status=str(status)
            ).inc()

            # Record latency
            http_request_duration_seconds.labels(
                service=self.service_name,
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

        return response

def instrument_fastapi(app: FastAPI, service_name: str = "bridge"):
    """Add metrics, probes, and telemetry to FastAPI app"""

    # Add middleware
    app.add_middleware(MetricsMiddleware, service_name=service_name)

    # Metrics endpoint
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        """Prometheus metrics endpoint"""
        return generate_latest().decode("utf-8")

    # Liveness probe
    @app.get("/live")
    async def liveness():
        """Liveness probe - is the process alive?"""
        return {
            "status": "alive",
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    # Readiness probe
    @app.get("/ready")
    async def readiness():
        """Readiness probe - is the service ready to accept traffic?"""
        # Check that required env vars are set
        required_vars = ["UAT_BASE", "ATHENA_BASE"]
        missing = [v for v in required_vars if not os.getenv(v)]

        if missing:
            return Response(
                content=json.dumps({
                    "status": "not_ready",
                    "reason": f"Missing env vars: {missing}",
                    "service": service_name
                }),
                status_code=503,
                media_type="application/json"
            )

        # TODO: Add downstream health checks here

        return {
            "status": "ready",
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": os.getenv("USE_MOCK", "1") == "0" and "real" or "mock"
        }

    # Setup JSON logging
    setup_json_logging(service_name)

    return app

# ============================================================================
# Context Manager for Structured Logging
# ============================================================================

@contextmanager
def log_context(**kwargs):
    """Add context to all logs within this block"""
    logger = logging.getLogger()

    class ContextFilter(logging.Filter):
        def filter(self, record):
            if not hasattr(record, "ctx"):
                record.ctx = {}
            record.ctx.update(kwargs)
            return True

    filter_obj = ContextFilter()
    logger.addFilter(filter_obj)
    try:
        yield
    finally:
        logger.removeFilter(filter_obj)

# ============================================================================
# Helper Functions
# ============================================================================

def record_watchdog_heal(service: str, outcome: str, duration_seconds: float):
    """Record watchdog recovery event"""
    watchdog_heals_total.labels(service=service, outcome=outcome).inc()
    watchdog_recovery_duration_seconds.labels(service=service).set(duration_seconds)

    logger = logging.getLogger("watchdog")
    with log_context(recovery_duration=duration_seconds, outcome=outcome):
        if outcome == "success":
            logger.info(f"Watchdog recovery successful for {service}")
        else:
            logger.error(f"Watchdog recovery failed for {service}")

def record_circuit_breaker_trip(service: str, backend: str, reason: str):
    """Record circuit breaker trip"""
    circuit_breaker_trips_total.labels(
        service=service,
        backend=backend,
        reason=reason
    ).inc()

    circuit_breaker_state.labels(
        service=service,
        backend=backend
    ).set(1)  # Open

    logger = logging.getLogger("breaker")
    with log_context(backend=backend, reason=reason):
        logger.warning(f"Circuit breaker opened for {backend}")

def record_circuit_breaker_close(service: str, backend: str):
    """Record circuit breaker close"""
    circuit_breaker_state.labels(
        service=service,
        backend=backend
    ).set(0)  # Closed

    logger = logging.getLogger("breaker")
    with log_context(backend=backend):
        logger.info(f"Circuit breaker closed for {backend}")

# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Instrument a FastAPI app
    from fastapi import FastAPI

    app = FastAPI(title="Bridge Example")

    # Add telemetry
    instrument_fastapi(app, service_name="bridge")

    # Your endpoints...
    @app.get("/")
    def root():
        logger = logging.getLogger("bridge")
        with log_context(endpoint="/", method="GET"):
            logger.info("Root endpoint called")
        return {"status": "ok"}

    print("✅ Telemetry configured")
    print("   /metrics - Prometheus metrics")
    print("   /live    - Liveness probe")
    print("   /ready   - Readiness probe")
