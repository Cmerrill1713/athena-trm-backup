# common/ops.py
"""
Production-grade operational tooling for FastAPI services
- OpenTelemetry tracing (OTLP export)
- Rate limiting & guardrails
- Graceful shutdown with drain
- Secrets management
"""
import logging
import os
import signal
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# === OpenTelemetry tracing ===
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# === Rate limiting / guardrails ===
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger("ops")

# ----------------
# Tracing
# ----------------
def wire_tracing(app: FastAPI, service_name: str):
    """Wire OpenTelemetry tracing to FastAPI app (gracefully degrades if collector unavailable)"""
    # Skip tracing if explicitly disabled
    if os.getenv("OTEL_DISABLED", "0") == "1":
        logger.info(f"[Tracing] Disabled for {service_name} (OTEL_DISABLED=1)")
        app.state.tracing = False
        return

    try:
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        )

        # Set global provider
        from opentelemetry import trace
        trace.set_tracer_provider(provider)

        # Instrument frameworks
        RequestsInstrumentor().instrument()  # outbound HTTP
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

        app.state.tracing = True
        logger.info(f"[Tracing] {service_name} -> {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"[Tracing] Failed to initialize for {service_name}: {e}")
        logger.warning("[Tracing] Continuing without tracing (set OTEL_DISABLED=1 to suppress)")
        app.state.tracing = False

# ----------------
# Rate limit & guardrails
# ----------------
def attach_guardrails(
    app: FastAPI,
    per_ip_rate: str = "100/minute",
    max_body_mb: int = 5,
    request_timeout_s: int = 30,
):
    """Attach rate limiting, payload limits, and timeout middleware"""
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    def rate_limit_decorator(route_func):
        """Use as: @app.get("/...")(rate_limit(route_func))"""
        return limiter.limit(per_ip_rate)(route_func)

    # Payload size limit
    max_bytes = max_body_mb * 1024 * 1024

    class SizeLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Only enforce when content-length advertised
            cl = request.headers.get("content-length")
            if cl and int(cl) > max_bytes:
                return JSONResponse({"detail": "Payload too large"}, status_code=413)
            return await call_next(request)

    # Global request timeout (best-effort)
    class TimeoutMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            try:
                return await asyncio.wait_for(call_next(request), timeout=request_timeout_s)
            except asyncio.TimeoutError:
                return JSONResponse({"detail": "Request timeout"}, status_code=504)

    app.add_middleware(SizeLimitMiddleware)
    app.add_middleware(TimeoutMiddleware)

    # Expose decorator on app.state for consistent usage
    app.state.rate_limit = rate_limit_decorator

    logger.info(
        f"[Guardrails] rate={per_ip_rate}, max_body={max_body_mb}MB, "
        f"timeout={request_timeout_s}s"
    )

# ----------------
# Graceful shutdown
# ----------------
def install_graceful_shutdown(
    app: FastAPI,
    drain_seconds: int = 5,
    on_shutdown: Optional[Callable[[], "asyncio.Future|None"]] = None
):
    """
    Adds SIGTERM/SIGINT handlers to drain in-flight work and run optional cleanup.
    """

    async def _drain_and_cleanup():
        logger.info(f"[Shutdown] Draining for {drain_seconds}s ...")
        try:
            if on_shutdown:
                maybe = on_shutdown()
                if asyncio.iscoroutine(maybe):
                    await maybe
        finally:
            await asyncio.sleep(drain_seconds)
            logger.info("[Shutdown] Done.")

    # Starlette/FastAPI shutdown event
    @app.on_event("shutdown")
    async def _on_shutdown():
        await _drain_and_cleanup()

    # For uvicorn signal path (defensive)
    def _signal_handler(*_):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_drain_and_cleanup())
        except RuntimeError:
            # No running loop; best effort
            pass

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

# ----------------
# Lightweight liveness/readiness
# ----------------
def add_health_endpoints(app: FastAPI):
    """Add /live, /ready, and /metrics endpoints for K8s-style health checks"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    @app.get("/live")
    async def live():
        """Liveness probe - is the process alive?"""
        return {"status": "ok"}

    @app.get("/ready")
    async def ready():
        """Readiness probe - is the service ready to accept traffic?"""
        # Simple readiness; extend with dependency checks as needed
        return {"status": "ready"}
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
