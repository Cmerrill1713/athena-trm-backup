# 🚀 Production Runbook — OpenAI-Compatible RAG Stack

**Complete operational guide for production deployment and maintenance.**

---

## 📋 Quick Reference

### Service Status

```bash
# Check all services
docker-compose -f docker-compose.full-stack.yml ps

# Health checks
curl http://localhost:3000/healthz | jq .
curl http://localhost:8090/health | jq .
curl http://localhost:8088/health | jq .
```

### Metrics & Monitoring

- **Grafana Dashboard:** http://localhost:3001
- **Prometheus:** http://localhost:9090
- **Adapter Metrics:** http://localhost:3000/metrics

---

## 🔒 Security Hardening

### 1. TLS/SSL Configuration

**Using Nginx + Let's Encrypt:**

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Strong SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /v1/ {
        proxy_pass http://openai-compat:3000;
        # ... streaming config
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. Authentication

**Add Bearer Token Auth:**

```javascript
// Add to server.js before routes
app.use("/v1/", (req, res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  const validToken = process.env.API_KEY || "your-secret-key";

  if (!token || token !== validToken) {
    return res.status(401).json({
      error: {
        message: "Invalid API key",
        type: "invalid_request_error",
      },
    });
  }
  next();
});
```

### 3. Rate Limiting (Nginx)

```nginx
# Add to http block
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;
limit_req_zone $binary_remote_addr zone=burst_limit:10m rate=100r/m;

location /v1/chat/completions {
    limit_req zone=api_limit burst=20 nodelay;
    limit_req zone=burst_limit burst=50 nodelay;

    limit_req_status 429;
    limit_req_log_level warn;

    proxy_pass http://openai-compat:3000;
}
```

### 4. CORS Restrictions

**Update .env:**

```env
CORS_ORIGIN=https://your-ui-domain.com
# Or multiple: https://ui1.com,https://ui2.com
```

### 5. Resource Limits

**Add to docker-compose.full-stack.yml:**

```yaml
services:
  openai-compat:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "1.0"
          memory: 1G
```

---

## 🧪 Load Testing

### Run k6 Load Test

```bash
# Install k6
brew install k6  # macOS
# OR: docker run --rm -i grafana/k6 run - < k6-rag.js

# Run 5-minute test with 20 VUs
k6 run k6-rag.js

# Custom configuration
k6 run -e BASE=http://localhost:3000 -e VUS=50 -e DURATION=10m k6-rag.js
```

### Expected Results

**Success Thresholds:**

- ✅ p95 latency < 1500ms
- ✅ 5xx error rate < 0.3%
- ✅ Stream error rate < 2%
- ✅ No memory leaks (flat memory usage)

### Interpreting Results

```bash
# View summary
cat summary.json | jq .

# Check key metrics
cat summary.json | jq '.metrics | {
  p95: .http_req_duration.values["p(95)"],
  errors: .http_req_failed.values.rate,
  rps: .iterations.values.rate
}'
```

---

## 🔥 Chaos & Resilience Testing

### 1. Kill Weaviate (Test Graceful Degradation)

```bash
# Stop Weaviate
docker-compose -f docker-compose.full-stack.yml stop weaviate

# Monitor adapter behavior
watch -n 1 'curl -s http://localhost:3000/healthz | jq .backends'

# Expected: Errors logged, but adapter stays up
# Fallback: BM25 mode or structured error responses

# Restart
docker-compose -f docker-compose.full-stack.yml start weaviate
```

### 2. Throttle Ollama (Test Latency Handling)

```bash
# Add latency to Ollama container
docker-compose -f docker-compose.full-stack.yml exec ollama tc qdisc add dev eth0 root netem delay 200ms

# Monitor latency impact
watch -n 1 'curl -s http://localhost:3000/metrics | grep backend_request_duration'

# Remove throttle
docker-compose -f docker-compose.full-stack.yml exec ollama tc qdisc del dev eth0 root
```

### 3. Inject 5xx Errors (Test Retry/Fallback)

```bash
# TODO: Implement circuit breaker in adapter
# For now, manually stop backend and observe errors

docker-compose -f docker-compose.full-stack.yml stop rag-gateway

# Expected: Upstream errors tracked in metrics
# Circuit breaker (if implemented) should trip after threshold
```

---

## 📊 Observability

### Prometheus Setup

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Load alert rules
rule_files:
  - "prometheus-alerts.yml"

scrape_configs:
  - job_name: "openai-compat"
    static_configs:
      - targets: ["openai-compat:3000"]
    metrics_path: "/metrics"
```

### Grafana Dashboard

1. Import `grafana-dashboard.json`
2. Connect to Prometheus data source
3. View real-time metrics

**Key Panels:**

- Request Rate (by status code)
- Error Rate (5xx + upstream)
- Latency (p50, p95, p99)
- Model Usage Distribution
- Backend Latency
- Active Requests
- Memory Usage

### Alert Manager

**alertmanager.yml:**

```yaml
route:
  receiver: "slack"
  group_by: ["alertname", "severity"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: "slack"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        channel: "#alerts-rag"
        title: "{{ .GroupLabels.alertname }}"
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}\n{{ end }}'
```

---

## 🚨 Alerts & Runbooks

### Critical Alerts

#### High Error Rate (>0.5% for 5m)

**Runbook:**

1. Check adapter logs: `docker logs openai-compat`
2. Check backend health: `curl http://localhost:8090/health`
3. Verify Weaviate: `curl http://localhost:8080/v1/.well-known/ready`
4. If persistent, rollback to last known good version

#### High p95 Latency (>1.5s for 10m)

**Runbook:**

1. Check backend latency: `curl http://localhost:3000/metrics | grep backend_request`
2. Identify slow backend (RAG vs Chat)
3. Check Weaviate query performance
4. Check Ollama model loading
5. Consider scaling horizontally if persistent

#### No Requests (for 5m)

**Runbook:**

1. Check adapter is running: `docker ps | grep openai-compat`
2. Check networking: `docker network inspect github_athena`
3. Check load balancer/nginx configuration
4. Restart adapter if hung: `docker-compose restart openai-compat`

### Warning Alerts

#### High Stream Error Rate (>2% for 5m)

**Runbook:**

1. Check nginx buffering: `proxy_buffering off`
2. Check adapter logs for stream errors
3. Verify `ENABLE_STREAMING=true` in config
4. Test streaming manually: `curl -N http://localhost:3000/v1/chat/completions ...`

#### High Empty Response Rate (>5% for 10m)

**Runbook:**

1. Verify Weaviate has data: Check corpus size
2. Check RAG gateway logs
3. Verify embedding service is working
4. Consider restoring Weaviate data from backup

---

## 🔄 Deployment & Rollback

### Deployment Profiles

**Staging:**

```bash
docker-compose -f docker-compose.full-stack.yml \
  -f docker-compose.staging.yml \
  up -d
```

**Production:**

```bash
docker-compose -f docker-compose.full-stack.yml \
  -f docker-compose.prod.yml \
  up -d
```

### Canary Deployment

1. **Deploy new version as canary:**

```yaml
# docker-compose.canary.yml
services:
  openai-compat-canary:
    image: openai-compat:v2.0
    environment:
      - PORT=3001
```

2. **Route 5% traffic to canary (Nginx):**

```nginx
upstream openai_backend {
    server openai-compat:3000 weight=95;
    server openai-compat-canary:3001 weight=5;
}
```

3. **Monitor for 30min:**

```bash
# Compare metrics
watch -n 10 'curl -s http://localhost:3000/metrics | grep http_requests_total; curl -s http://localhost:3001/metrics | grep http_requests_total'
```

4. **Gates for promotion:**

- p95 latency ≤ +10% vs baseline
- 5xx delta ≤ +0.3%
- Stream error rate ≤ +1%

5. **If passed, promote:**

```bash
docker-compose -f docker-compose.full-stack.yml up -d --scale openai-compat=3
```

### Rollback Procedure

**Fast rollback (< 2 minutes):**

```bash
# Option 1: Docker service rollback
docker service update --rollback openai-compat

# Option 2: Compose with previous image
docker-compose -f docker-compose.full-stack.yml up -d \
  --force-recreate openai-compat

# Option 3: Switch nginx upstream
# Comment out new version in nginx.conf
# nginx -s reload
```

---

## 💾 Backup & Recovery

### Weaviate Backup

```bash
# Create snapshot
docker-compose -f docker-compose.full-stack.yml exec weaviate \
  weaviate-cli backup create --backend filesystem --backup-id prod-$(date +%Y%m%d)

# Backup volume
tar -czf weaviate-backup-$(date +%Y%m%d).tar.gz ./volumes/weaviate_data/

# Upload to S3 (example)
aws s3 cp weaviate-backup-$(date +%Y%m%d).tar.gz s3://your-bucket/backups/
```

### Restore Procedure

```bash
# Stop services
docker-compose -f docker-compose.full-stack.yml down

# Restore from backup
tar -xzf weaviate-backup-YYYYMMDD.tar.gz -C ./volumes/

# Restart
docker-compose -f docker-compose.full-stack.yml up -d
```

### Test Restore (Quarterly)

```bash
# Create test environment
docker-compose -f docker-compose.test.yml up -d

# Restore backup
# Run smoke tests
# Verify data integrity
```

---

## 🛠️ Troubleshooting

### Common Issues

| Issue                  | Symptoms           | Fix                                          |
| ---------------------- | ------------------ | -------------------------------------------- |
| **High Memory**        | Memory > 1.5GB     | Check for leaks; restart service             |
| **Slow Responses**     | p95 > 2s           | Check backend latency; scale horizontally    |
| **Connection Refused** | 502 errors         | Check backend health; restart if needed      |
| **Empty Responses**    | No RAG results     | Verify Weaviate data; check query logic      |
| **Stream Hangs**       | Incomplete streams | Check nginx timeout; verify ENABLE_STREAMING |

### Debug Commands

```bash
# View logs (last 100 lines)
docker logs --tail 100 openai-compat

# Follow logs in real-time
docker logs -f openai-compat

# Check resource usage
docker stats openai-compat

# Exec into container
docker exec -it openai-compat sh

# Test backend connectivity
docker exec openai-compat curl http://rag-gateway:8090/health
```

---

## ✅ Production Readiness Checklist

### Before Go-Live

- [ ] TLS enabled with valid certificates
- [ ] Authentication enforced (Bearer tokens)
- [ ] Rate limiting configured
- [ ] CORS restricted to UI origins
- [ ] Resource limits set (CPU, memory)
- [ ] Prometheus + Grafana configured
- [ ] Alert rules loaded in Prometheus
- [ ] Alert routing configured (Slack/PagerDuty)
- [ ] Backup procedure tested
- [ ] Rollback procedure tested
- [ ] Load test passed (k6)
- [ ] Chaos tests passed
- [ ] Runbook documented
- [ ] On-call rotation established

### Post-Launch (First Week)

- [ ] Monitor error rates daily
- [ ] Review latency trends
- [ ] Check for memory leaks
- [ ] Validate backup schedule
- [ ] Fine-tune rate limits
- [ ] Adjust resource limits if needed
- [ ] Document any incidents

---

## 📞 Support & Escalation

### Severity Levels

| Level | Description          | Response Time | Escalation            |
| ----- | -------------------- | ------------- | --------------------- |
| P0    | Complete outage      | Immediate     | Page on-call engineer |
| P1    | Critical degradation | 15 minutes    | Alert team lead       |
| P2    | Partial degradation  | 1 hour        | Create ticket         |
| P3    | Minor issue          | 4 hours       | Normal priority       |

### On-Call Runbook

1. **Acknowledge alert** within 5 minutes
2. **Assess severity** using metrics
3. **Follow runbook** for specific alert
4. **Document actions** in incident log
5. **Escalate** if not resolved in 30min
6. **Post-mortem** for P0/P1 incidents

---

**System production-ready.** 🚀

---

**Last Updated:** October 18, 2025
