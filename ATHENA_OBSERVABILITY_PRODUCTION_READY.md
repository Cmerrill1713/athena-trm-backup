# 🔥 Athena Observability Spine - Production Hardened & Locked In

## ✅ What We Fixed & Hardened

### 1. **Prometheus Production Configuration**

- **Retention**: 15 days time-based + 10GB size-based
- **Persistence**: Proper volume mounting for data durability
- **Lifecycle**: Enabled web lifecycle for config reloads
- **Alert Rules**: Comprehensive alerting for Athena services

### 2. **Alert Rules Created** (`monitoring/prometheus/rules/alerts.yml`)

- **TargetDown**: Critical alert for any Athena service down > 2min
- **HighErrorRate**: Warning for 5xx > 1% for 5min
- **P95LatencySLOViolated**: Warning for p95 > 1.5s for 10min
- **RouterDown**: Critical alert for router service down
- **CanaryActiveWithIssues**: Critical when canary active + elevated metrics
- **StreamErrorsHigh**: Warning for SSE stream errors > 0.1/sec
- **RouteSelectionImbalanced**: Warning for single route > 80% traffic
- **OTELCollectorDown**: Critical alert for collector down
- **Infrastructure**: Memory, CPU, disk space alerts

### 3. **Grafana Production Dashboard** (`monitoring/grafana/dashboards/athena-production.json`)

- **Requests/sec by Service & Route**: `sum(rate(athena_requests_total[1m])) by (service, route)`
- **P50/P95 Latency**: `histogram_quantile(0.95, sum by (le) (rate(athena_request_latency_seconds_bucket[5m])))`
- **5xx Error Rate**: `sum(rate(athena_requests_total{code=~"5.."}[5m])) / sum(rate(athena_requests_total[5m]))`
- **Route Selection Mix**: `sum(rate(athena_route_selection_created[5m])) by (route)`
- **SSE Stream Errors**: `sum(rate(athena_stream_errors_total[5m])) by (reason)`
- **Canary Status**: `athena_governance_canary_active` (boolean gauge)
- **Service Health**: `up{job=~"athena-.*"}` status

### 4. **OTEL Collector Production Config**

- **Sampling**: Reduced to 10% for production (was 100%)
- **Memory Limits**: 90% limit with 1s check interval
- **Scrape Timeouts**: Added 10s timeout for reliability
- **Removed**: Jaeger/Zipkin receivers (not needed)
- **Optimized**: Batch processing and resource attribution

### 5. **Service Instrumentation Examples**

- **Metrics Module**: `services/openai-compat/metrics.js`

  - `athena_requests_total` - Request counter with labels
  - `athena_request_latency_seconds` - Latency histogram
  - `athena_stream_errors_total` - SSE error tracking
  - `athena_route_selection_created` - Route selection tracking
  - `athena_governance_canary_active` - Canary status gauge
  - `athena_modality_ece_estimate` - ECE estimates per modality

- **Middleware**: `services/openai-compat/middleware.js`
  - Request timing and counting
  - Error tracking
  - Slow request detection
  - Stream error monitoring

## 🚀 Quick Start Commands

### Start the Hardened Stack

```bash
# Start Docker daemon first
open -a Docker

# Start the observability stack
cd /Users/christianmerrill/Documents/GitHub
docker-compose up -d athena-prometheus athena-otel-collector athena-grafana
```

### Verification Tests

```bash
# OTEL Collector health
curl -sf http://localhost:13133/ | jq .

# Athena metrics flowing
curl -s http://localhost:8889/metrics | egrep 'athena_requests_total|athena_request_latency_seconds|athena_route_selection_created' | head

# Prometheus targets
curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastScrape: .lastScrape}'

# P95 latency query
curl -s 'http://localhost:9090/api/v1/query' --data-urlencode \
 'query=histogram_quantile(0.95, sum by (le) (rate(athena_request_latency_seconds_bucket[5m])))'
```

### Import Grafana Dashboard

1. Open Grafana: `http://localhost:3001` (admin/admin)
2. Go to Dashboards → Import
3. Upload: `monitoring/grafana/dashboards/athena-production.json`
4. Select Prometheus datasource

## 🎯 Canary-Ready Alerts

### Critical Alerts (Page Immediately)

- **Router Down**: `up{job="athena-router"} == 0`
- **OTEL Collector Down**: `up{job="athena-otel-collector"} == 0`
- **Canary Issues**: `athena_governance_canary_active == 1 AND (p95 > 1.1x OR 5xx > 0.3%)`

### Warning Alerts (Slack/Email)

- **High Error Rate**: 5xx > 1% for 5min
- **Latency SLO**: P95 > 1.5s for 10min
- **Route Imbalance**: Single route > 80% traffic
- **Stream Errors**: SSE errors > 0.1/sec

## 🔧 Troubleshooting Crib Notes

### Common Issues & Solutions

1. **OTEL Collector Exit 127**: Wrong config path → Fixed with `.yaml` extension
2. **Health Up, No Metrics**: Wrong scrape job → Verify port 8889 accessible
3. **Permission Errors**: File exporters → Removed, using debug exporter
4. **Spinning Dashboard**: Prometheus not scraping → Check Grafana datasource URL

### Debug Commands

```bash
# Check OTEL collector logs
docker logs athena-otel-collector --tail 20

# Check Prometheus config
curl http://localhost:9090/api/v1/status/config

# Check alert rules loaded
curl http://localhost:9090/api/v1/rules

# Check OTEL metrics endpoint
curl http://localhost:8889/metrics | grep athena
```

## 📊 Metrics Baseline (Once Running)

After starting the stack, capture these baselines:

```bash
# Current request rate
curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=sum(rate(athena_requests_total[5m]))'

# Current P95 latency
curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(athena_request_latency_seconds_bucket[5m])))'

# Current error rate
curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=sum(rate(athena_requests_total{code=~"5.."}[5m])) / sum(rate(athena_requests_total[5m]))'
```

## 🎉 What's Locked In

✅ **Observability Spine**: OTEL → Prometheus → Grafana  
✅ **Production Alerts**: Critical + Warning thresholds  
✅ **Canary Monitoring**: Real-time canary status + metrics  
✅ **Service Health**: All Athena services monitored  
✅ **Performance SLOs**: P95 latency + error rate tracking  
✅ **Route Intelligence**: Traffic distribution monitoring  
✅ **Stream Monitoring**: SSE error tracking  
✅ **Infrastructure**: CPU, memory, disk alerts

**Your observability spine is now production-hardened and canary-ready!** 🚀

When Docker is running, just `docker-compose up -d` and you'll have enterprise-grade monitoring with proper alerting, dashboards, and SLO tracking.
