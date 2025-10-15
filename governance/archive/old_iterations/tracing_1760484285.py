# OpenTelemetry Tracing Setup
# Add to Bridge and Athena for distributed tracing

import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def init_tracing(service_name: str, endpoint: str = None):
    """
    Initialize OpenTelemetry tracing for a service.

    Args:
        service_name: Name of the service (e.g., 'bridge', 'athena')
        endpoint: OTLP endpoint (defaults to otel-collector)
    """
    if endpoint is None:
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

    # Create resource with service metadata
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "v0.9.7"),
        "deployment.environment": os.getenv("DEPLOYMENT_ENV", "development"),
    })

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=endpoint,
        insecure=True,  # For development; use TLS in production
    )

    # Add batch processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument libraries
    try:
        HTTPXClientInstrumentor().instrument()
    except Exception:
        pass  # httpx might not be available

    try:
        RequestsInstrumentor().instrument()
    except Exception:
        pass  # requests might not be available

    print(f"✅ Tracing initialized for {service_name} → {endpoint}")


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance for creating spans."""
    return trace.get_tracer(name)


def create_span(name: str, attributes: dict = None) -> trace.Span:
    """Create a new span with optional attributes."""
    tracer = get_tracer(__name__)
    span = tracer.start_span(name)

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


# Context manager for spans
class traced:
    """Context manager for tracing function calls."""

    def __init__(self, name: str, attributes: dict = None):
        self.name = name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self):
        self.span = create_span(self.name, self.attributes)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.record_exception(exc_val)
            self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        else:
            self.span.set_status(trace.StatusCode.OK)
        self.span.end()


def instrument_fastapi(app):
    """Instrument a FastAPI app for tracing."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        print("✅ FastAPI tracing instrumented")
    except Exception as e:
        print(f"⚠️  FastAPI tracing failed: {e}")
