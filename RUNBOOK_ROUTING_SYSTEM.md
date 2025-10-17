# Athena Router Runbook

**Production Runbook for the Athena Intelligent Model Routing System**

## 🚨 Emergency Contacts

- **Primary On-Call:** System Admin
- **Secondary:** DevOps Team
- **Escalation:** Engineering Manager
- **Vendor Support:** Prometheus/Grafana Support

---

## 📊 System Overview

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Swift UI      │    │   Routing API   │    │   Prometheus    │
│   Client        │◄──►│   (Flask)       │◄──►│   + Grafana     │
│                 │    │   Port: 9113    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Model Router   │    │  Model Profiles │    │   Dashboards    │
│  (Python)       │    │  (JSON)         │    │   + Alerts      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **Routing API**: Flask-based REST API with production hardening
- **Model Router**: Intelligent routing based on domain embeddings
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Swift UI**: macOS client for testing and management

---

## 🚀 Quick Start

### Start Services

```bash
# 1. Start routing API
export ATHENA_ROUTER_TOKEN="your-secret-token"
export ATHENA_ROUTER_RATE_LIMIT=1000
python3 governance/routing/routing_api.py

# 2. Start monitoring stack
docker-compose -f docker-compose.athena-governance.yml up -d athena-prometheus athena-grafana

# 3. Start Swift UI (optional)
cd NeuroForgeApp && swift run
```

### Health Check

```bash
curl http://localhost:9113/health
curl http://localhost:9090/api/v1/targets
open http://localhost:3001  # Grafana (admin/admin)
```

---

## 📋 Daily Operations

### Morning Checklist

- [ ] Check system health: `curl http://localhost:9113/health`
- [ ] Verify Prometheus targets are up
- [ ] Check Grafana dashboards for anomalies
- [ ] Review overnight alerts and metrics
- [ ] Validate routing performance (latency < 50ms)

### Key Metrics to Monitor

- **Routing Latency**: p95 < 50ms
- **Success Rate**: > 99.5%
- **Cost per Request**: Track budget vs actual
- **Model Distribution**: Balanced load across models

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Routing API Down

**Symptoms:** 502/503 errors, health check fails
**Cause:** Service crash, port conflict, or resource exhaustion
**Solution:**

```bash
# Check service status
ps aux | grep routing_api.py

# Check logs
tail -f logs/routing_api_hardened.log

# Restart service
pkill -f routing_api.py
ATHENA_ROUTER_TOKEN=token python3 governance/routing/routing_api.py &
```

#### 2. High Latency

**Symptoms:** p95 latency > 50ms sustained
**Cause:** Model loading issues, network problems, or resource contention
**Actions:**

1. Check model profiles: `curl http://localhost:9113/models`
2. Review contrastive router performance
3. Check system resources (CPU/memory)
4. Consider fallback routing

#### 3. Authentication Failures

**Symptoms:** 401 errors from API calls
**Cause:** Missing or invalid ATHENA_ROUTER_TOKEN
**Solution:**

```bash
# Set environment variable
export ATHENA_ROUTER_TOKEN="correct-token-here"

# Or check current value
echo $ATHENA_ROUTER_TOKEN
```

#### 4. Rate Limiting Issues

**Symptoms:** 429 errors, "Rate limit exceeded"
**Cause:** Traffic spike or misconfigured limits
**Actions:**

1. Increase rate limit: `export ATHENA_ROUTER_RATE_LIMIT=2000`
2. Check client IPs hitting limits
3. Implement exponential backoff in clients

#### 5. Prometheus Not Scraping

**Symptoms:** No metrics in Grafana, targets show "down"
**Cause:** Network issues, port mismatches, or service down
**Solution:**

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Restart Prometheus
docker-compose restart athena-prometheus

# Verify scraping
curl http://localhost:9113/metrics | head -5
```

---

## 📈 Performance Tuning

### Routing Optimization

```bash
# Adjust cost weights (cost-focused)
curl -X POST http://localhost:9113/cost-weights \
  -H "Authorization: Bearer $ATHENA_ROUTER_TOKEN" \
  -d '{"cost": 0.8, "quality": 0.1, "latency": 0.1}'

# Enable/disable features
curl -X POST http://localhost:9113/features/contrastive_routing \
  -H "Authorization: Bearer $ATHENA_ROUTER_TOKEN" \
  -d '{"enabled": true, "rollout_percentage": 75}'
```

### Memory Management

- Monitor contrastive router embedding cache
- Reload model profiles without restart: `POST /reload`
- Check cache hit rates in metrics

### Scaling Considerations

- Horizontal scaling: Multiple router instances behind load balancer
- Vertical scaling: Increase CPU/memory for embedding calculations
- Caching: Redis for shared model profiles

---

## 🔐 Security

### Authentication

- **Token Required:** Set `ATHENA_ROUTER_TOKEN` environment variable
- **Header Format:** `Authorization: Bearer <token>`
- **Scopes:** Full API access with valid token

### Rate Limiting

- **Default:** 1000 requests/minute per IP
- **Config:** `ATHENA_ROUTER_RATE_LIMIT` environment variable
- **Headers:** `Retry-After` on 429 responses

### SSL/TLS

```bash
# Enable SSL
export ATHENA_ROUTER_SSL_CERT=/path/to/cert.pem
export ATHENA_ROUTER_SSL_KEY=/path/to/key.pem

# Service will start with HTTPS automatically
```

### Security Monitoring

- Authentication failures logged and metered
- Rate limit violations tracked
- Suspicious patterns flagged in logs

---

## 📊 Monitoring & Alerting

### Key Dashboards

- **Routing Overview**: Request rates, latency, success rates
- **Model Performance**: Per-model metrics and costs
- **A/B Tests**: Test progress and winner determination
- **Cost Analysis**: Budget vs actual spending

### Alert Rules

```yaml
# Critical alerts
- HighRoutingLatency: p95 > 50ms for 5m
- RoutingServiceDown: Service unreachable for 1m
- AuthFailuresSpike: >10 auth failures/min

# Warning alerts
- LowRoutingConfidence: Confidence < 0.7 for 2m
- HighFallbackRate: Fallback rate > 30% for 10m
```

### Log Analysis

```bash
# Recent errors
grep "ERROR" logs/routing_api_hardened.log | tail -10

# Routing patterns
grep "Routed query" logs/routing_api_hardened.log | tail -20

# Performance issues
grep "latency" logs/routing_api_hardened.log | tail -10
```

---

## 🚀 Deployment

### Environment Variables

```bash
# Required
ATHENA_ROUTER_TOKEN=your-secret-token

# Optional
ROUTER_PORT=9113
ROUTER_HOST=0.0.0.0
ATHENA_ROUTER_RATE_LIMIT=1000
ATHENA_ROUTER_SSL_CERT=/path/to/cert.pem
ATHENA_ROUTER_SSL_KEY=/path/to/key.pem
```

### Docker Deployment

```bash
# Build and run
docker build -f Dockerfile.router -t athena-router .
docker run -p 9113:9113 -e ATHENA_ROUTER_TOKEN=token athena-router
```

### Blue-Green Deployment

1. Deploy new version to staging
2. Run integration tests
3. Update load balancer to route traffic
4. Monitor for 15 minutes
5. Complete cutover or rollback

---

## 🧪 Testing

### Integration Tests

```bash
# Run full test suite
pytest tests/test_routing.py -v
pytest tests/test_contrastive_routing.py -v

# Canary tests
python governance/ci/canary_test_suite.py --router contrastive
```

### Load Testing

```bash
# Basic load test
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" http://localhost:9113/route

# With JSON payload
# (Use more sophisticated load testing tools for complex payloads)
```

### A/B Testing

```bash
# Create test
curl -X POST http://localhost:9113/ab-test \
  -d '{"test_id": "perf-test-001", "strategy": "basic_vs_contrastive"}'

# Monitor progress
curl http://localhost:9113/ab-test/perf-test-001

# Complete test
curl -X POST http://localhost:9113/ab-test/perf-test-001/complete
```

---

## 📞 Support

### Getting Help

1. Check this runbook first
2. Review logs: `tail -f logs/routing_api_hardened.log`
3. Check metrics in Grafana
4. Escalate to on-call engineer

### Common Support Queries

- **"Routing is slow"**: Check latency metrics and model profiles
- **"Service won't start"**: Verify environment variables and port availability
- **"Metrics missing"**: Check Prometheus targets and scraping configuration
- **"Auth not working"**: Verify token format and environment variable

### Emergency Procedures

1. **Service Down**: Restart immediately, investigate root cause
2. **Data Loss**: Check backups, restore from last good state
3. **Security Breach**: Isolate service, notify security team, preserve logs

---

## 📈 Future Improvements

### Short Term (Next Sprint)

- [ ] Multi-region deployment
- [ ] Advanced caching (Redis)
- [ ] Request tracing (OpenTelemetry)

### Medium Term (Next Quarter)

- [ ] Auto-scaling based on load
- [ ] Machine learning for routing optimization
- [ ] Advanced A/B testing features

### Long Term (Next Year)

- [ ] Multi-cloud deployment
- [ ] Real-time model performance adaptation
- [ ] Predictive scaling

---

**Last Updated:** 2025-10-16
**Version:** 1.0
**Authors:** Athena Governance Team
