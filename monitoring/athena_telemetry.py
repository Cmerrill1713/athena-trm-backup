"""
OpenTelemetry Integration Example for Athena Services

This module provides a simple way to integrate OpenTelemetry tracing and metrics
into Athena services.
"""

import os
import logging
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

logger = logging.getLogger(__name__)

class AthenaTelemetry:
    """Athena OpenTelemetry integration helper."""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.tracer: Optional[trace.Tracer] = None
        self.meter: Optional[metrics.Meter] = None
        
    def initialize(self, app=None):
        """Initialize OpenTelemetry for the service."""
        try:
            # Get OTEL endpoint from environment
            otel_endpoint = os.getenv(
                'OTEL_EXPORTER_OTLP_ENDPOINT', 
                'http://athena-otel-collector:4317'
            )
            
            # Initialize tracing
            self._setup_tracing(otel_endpoint)
            
            # Initialize metrics
            self._setup_metrics(otel_endpoint)
            
            # Auto-instrument FastAPI if app is provided
            if app:
                FastAPIInstrumentor.instrument_app(app)
                logger.info(f"FastAPI instrumentation enabled for {self.service_name}")
            
            # Auto-instrument other libraries
            RequestsInstrumentor().instrument()
            SQLAlchemyInstrumentor().instrument()
            RedisInstrumentor().instrument()
            
            logger.info(f"OpenTelemetry initialized for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            # Continue without telemetry rather than failing
    
    def _setup_tracing(self, endpoint: str):
        """Set up tracing."""
        trace.set_tracer_provider(TracerProvider())
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=True
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Get tracer
        self.tracer = trace.get_tracer(
            self.service_name,
            version=self.service_version
        )
    
    def _setup_metrics(self, endpoint: str):
        """Set up metrics."""
        # Configure OTLP metric exporter
        metric_exporter = OTLPMetricExporter(
            endpoint=endpoint,
            insecure=True
        )
        
        # Create metric reader
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=30000  # Export every 30 seconds
        )
        
        # Set up meter provider
        meter_provider = MeterProvider(
            metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(meter_provider)
        
        # Get meter
        self.meter = metrics.get_meter(
            self.service_name,
            version=self.service_version
        )
    
    def get_tracer(self) -> trace.Tracer:
        """Get the tracer instance."""
        if not self.tracer:
            self.tracer = trace.get_tracer(self.service_name)
        return self.tracer
    
    def get_meter(self) -> metrics.Meter:
        """Get the meter instance."""
        if not self.meter:
            self.meter = metrics.get_meter(self.service_name)
        return self.meter
    
    def create_counter(self, name: str, description: str = "", unit: str = ""):
        """Create a counter metric."""
        meter = self.get_meter()
        return meter.create_counter(
            name=name,
            description=description,
            unit=unit
        )
    
    def create_histogram(self, name: str, description: str = "", unit: str = ""):
        """Create a histogram metric."""
        meter = self.get_meter()
        return meter.create_histogram(
            name=name,
            description=description,
            unit=unit
        )
    
    def create_gauge(self, name: str, description: str = "", unit: str = ""):
        """Create a gauge metric."""
        meter = self.get_meter()
        return meter.create_up_down_counter(
            name=name,
            description=description,
            unit=unit
        )

# Global instance
telemetry = AthenaTelemetry(
    service_name=os.getenv('OTEL_SERVICE_NAME', 'athena-service'),
    service_version=os.getenv('OTEL_SERVICE_VERSION', '1.0.0')
)

# Convenience functions
def get_tracer() -> trace.Tracer:
    """Get the global tracer."""
    return telemetry.get_tracer()

def get_meter() -> metrics.Meter:
    """Get the global meter."""
    return telemetry.get_meter()

def initialize_telemetry(app=None):
    """Initialize telemetry for the service."""
    telemetry.initialize(app)

# Example usage:
"""
from athena_telemetry import initialize_telemetry, get_tracer, get_meter

# Initialize telemetry
initialize_telemetry(app)

# Use tracing
tracer = get_tracer()
with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("user.id", "123")
    # Your code here

# Use metrics
meter = get_meter()
counter = meter.create_counter("requests_total", "Total requests")
counter.add(1, {"method": "GET", "endpoint": "/api/users"})
"""
