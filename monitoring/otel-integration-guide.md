# OpenTelemetry Integration Guide for Athena Services

## Overview

The Athena stack now includes an OpenTelemetry Collector (`athena-otel-collector`) running on port 4317 (gRPC) and 4318 (HTTP) for receiving telemetry data from all services.

## Service Integration

### Python Services

For Python services, add these dependencies to your `requirements.txt`:

```txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-otlp==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-requests==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-redis==0.42b0
```

### Basic Python Integration

Add this to your service startup code:

```python
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Initialize OpenTelemetry
def init_telemetry():
    # Set up tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://athena-otel-collector:4317",
        insecure=True
    )

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Auto-instrument requests
    RequestsInstrumentor().instrument()

    return tracer

# Call this in your service startup
tracer = init_telemetry()
```

### Environment Variables

Add these environment variables to your service's Docker configuration:

```yaml
environment:
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://athena-otel-collector:4317
  - OTEL_SERVICE_NAME=your-service-name
  - OTEL_RESOURCE_ATTRIBUTES=service.name=your-service-name,service.version=1.0.0
```

### Custom Metrics

For custom metrics, use the Prometheus metrics endpoint that OTEL collector will scrape:

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')

# Start metrics server
start_http_server(8000)  # Use port 8000 for /metrics endpoint
```

### Node.js Services

For Node.js services (like the OpenAI-compat adapter):

```bash
npm install @opentelemetry/api @opentelemetry/sdk-node @opentelemetry/exporter-otlp-grpc @opentelemetry/instrumentation-http @opentelemetry/instrumentation-express
```

```javascript
const { NodeSDK } = require("@opentelemetry/sdk-node");
const { OTLPTraceExporter } = require("@opentelemetry/exporter-otlp-grpc");
const { HttpInstrumentation } = require("@opentelemetry/instrumentation-http");
const {
  ExpressInstrumentation,
} = require("@opentelemetry/instrumentation-express");

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: "http://athena-otel-collector:4317",
  }),
  instrumentations: [new HttpInstrumentation(), new ExpressInstrumentation()],
});

sdk.start();
```

## Service-Specific Configuration

### Router Service (Port 9113)

- Service name: `athena-router`
- Metrics endpoint: `/metrics` on port 9113
- Key metrics: routing decisions, model selection, latency

### API Service (Port 8888)

- Service name: `athena-api`
- Metrics endpoint: `/metrics` on port 8000
- Key metrics: request count, response times, error rates

### Governance Services

- Service name: `athena-governance`
- Metrics endpoint: `/metrics` on respective ports
- Key metrics: policy violations, remediation actions, canary results

### Knowledge Services

- Service name: `athena-knowledge`
- Metrics endpoint: `/metrics` on respective ports
- Key metrics: vector search latency, cache hit rates, document processing

## Verification

1. **Check OTEL Collector Health**: `curl http://localhost:13133/`
2. **View OTEL Metrics**: `curl http://localhost:8889/metrics`
3. **Check Prometheus Targets**: Visit `http://localhost:9090/targets`
4. **View Grafana Dashboards**: Visit `http://localhost:3001`

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure `athena-otel-collector` is running and accessible
2. **No Metrics**: Check that services are exposing `/metrics` endpoints
3. **High Memory Usage**: Adjust OTEL collector memory limits in config

### Debug Commands

```bash
# Check OTEL collector logs
docker logs athena-otel-collector

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check OTEL collector metrics
curl http://localhost:8889/metrics

# Test OTLP endpoint
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}'
```

## Next Steps

1. Add OTEL instrumentation to each service
2. Create custom dashboards in Grafana
3. Set up alerting rules for key metrics
4. Implement distributed tracing across service boundaries
