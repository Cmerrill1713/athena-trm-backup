# Athena Router Metrics Exporter

A lightweight Go-based Prometheus exporter for Athena router metrics.

## Quick Start

```bash
# Run locally
go run main.go

# Or build and run
go build -o exporter
./exporter
```

## Endpoints

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /simulate` - Simulate metrics for testing

## Environment Variables

- `EXPORTER_PORT` - Port to listen on (default: 9091)

## Metrics Exposed

- `athena_router_requests_total{status,model,domain}` - Routing requests
- `athena_router_latency_ms{model,domain}` - Request latency
- `athena_routing_confidence{model,domain}` - Confidence scores
- `athena_fallbacks_total{from_backend,to_backend}` - Fallback events
- `athena_router_local_success_total{backend}` - Local inference success
- `athena_router_cloud_attempts_total` - Cloud access attempts (should be 0)
- `athena_router_cloud_blocked_total` - Cloud access blocked

## Docker

```bash
docker build -t athena-router-exporter .
docker run -p 9091:9091 athena-router-exporter
```

## Integration

Add to Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: "athena-router-exporter"
    static_configs:
      - targets: ["localhost:9091"]
```
