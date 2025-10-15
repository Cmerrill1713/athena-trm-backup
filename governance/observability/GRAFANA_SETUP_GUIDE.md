# 🎨 Grafana Dashboard Setup Guide

> **30-minute observability setup for production clarity**

---

## 📊 What You Get

### 3 Dashboards
1. **Redaction Security** - Track secret exposure attempts
2. **Ops Window Analytics** - Log request patterns  
3. **RAG Performance** - Latency + hit ratio

### 5 Alert Rules
1. High error rate (5m/1h)
2. p95 latency degraded (>800ms)
3. SLO burn rate (fast/slow)
4. Redaction spike
5. Log read failures

---

## 🚀 Quick Setup (5 Minutes)

### 1. Start Monitoring Stack
```bash
cd /Users/christianmerrill/Documents/GitHub
make monitoring-up
```

This starts:
- Prometheus (:9090)
- Grafana (:3000)
- AlertManager (:9093)

### 2. Get Grafana API Key
```bash
# Open Grafana
open http://localhost:3000

# Default login: admin / admin
# Go to: Configuration → API Keys → Add API key
# Role: Admin
# Copy the key
```

### 3. Import Dashboards
```bash
export GRAFANA_URL=http://localhost:3000
export GRAFANA_API_KEY="your-key-here"

make obs-quick-setup
```

**Expected output:**
```
✅ Imported: redaction_dashboard
✅ Imported: ops_window_dashboard  
✅ Imported: rag_performance_dashboard
♻️  Prometheus reloaded
╔════════════════════════════════════════════════════════════╗
║        OBSERVABILITY SETUP COMPLETE ✅                     ║
╚════════════════════════════════════════════════════════════╝
```

### 4. Generate Traffic (Optional)
```bash
# Smoke the endpoints to see data flow
make stack-up
./VALIDATE_PLATFORM.sh

# Or generate load
for i in {1..100}; do 
  curl -s http://127.0.0.1:8014/health >/dev/null
done
```

### 5. View Dashboards
```bash
open http://localhost:3000/dashboards
```

---

## 📊 Dashboard Details

### Redaction Security
**UID:** `redaction-security`

**Panels:**
- Redaction events / 5m (stat)
- Redaction events rate (timeseries)
- Top redaction sources (table)
- Total redactions 24h (stat)

**Use Cases:**
- Spot secret exposure attempts
- Track redaction patterns by service
- Monitor security effectiveness

### Ops Window Analytics
**UID:** `ops-window-analytics`

**Panels:**
- Log requests 5m (stat)
- Ops log requests rate by service (timeseries)
- Log tail requests clamped (timeseries)
- Log read errors 5m (stat)

**Use Cases:**
- Track log viewer usage
- Spot abuse (high request rates)
- Monitor service health

### RAG Performance
**UID:** `rag-performance`

**Panels:**
- RAG hit ratio 5m (stat)
- RAG latency p95 + p50 (timeseries)
- RAG queries per second (timeseries)
- Embedding queue depth (timeseries)

**Use Cases:**
- Optimize RAG cache
- Monitor query latency
- Track embedding backlog

---

## 🚨 Alert Rules

### Service SLO Alerts

**HighErrorRate5m** (page)
- Trigger: 5xx rate > 2% for 10min
- Action: Check logs immediately

**HighErrorRate1h** (ticket)
- Trigger: 5xx rate > 1% for 30min
- Action: Investigate sustained issues

**LatencyP95Degraded** (page)
- Trigger: p95 latency > 800ms for 15min
- Action: Check service health

**SLOBurnFast** (page)
- Trigger: Error budget burning >14.4x
- Action: Immediate intervention
- Impact: Budget exhausted in ~6h

**SLOBurnSlow** (ticket)
- Trigger: Error budget burning >6x for 2h
- Action: Plan remediation
- Impact: Budget exhausted in ~5 days

### Security Alerts

**RedactionSpike** (page)
- Trigger: >5 redactions in 5min for 10min
- Action: Check for secret exposure attempts
- Runbook: `RUNBOOKS/LOG_SECURITY_RUNBOOK.md`

**LogRequestRateHigh** (warning)
- Trigger: >10 log req/s for 2min
- Action: Check for abuse

**LogReadFailures** (warning)
- Trigger: >0.1 errors/s for 2min
- Action: Check file permissions

**LogReadTimeout** (warning)
- Trigger: Any timeouts for 1min
- Action: Check disk I/O

---

## 🔧 Customization

### Update Metric Names

If your metrics use different names, edit the dashboards:

```bash
# Example: Change bridge_logs_* to app_logs_*
cd grafana/dashboards
sed -i '' 's/bridge_logs_/app_logs_/g' *.json

# Re-import
make grafana-import
```

### Add Custom Panels

1. Edit dashboard JSON in `grafana/dashboards/`
2. Add panel object to `panels` array
3. Re-import: `make grafana-import`

### Modify Alert Thresholds

```bash
# Edit alert rules
vim prometheus/alerts/slo_rules.yml

# Example: Change error rate from 2% to 3%
# expr: ... > 0.02  →  expr: ... > 0.03

# Validate
make prom-rules-validate

# Reload
make prom-reload
```

---

## 🧪 Testing Alerts

### Trigger Error Rate Alert
```bash
# Generate 5xx errors
for i in {1..50}; do
  curl -s http://127.0.0.1:8014/nonexistent >/dev/null
done

# Check Prometheus
open http://localhost:9090/alerts
```

### Trigger Redaction Alert
```bash
# Generate redaction events
for i in {1..10}; do
  curl -s "http://127.0.0.1:8014/ops/logs?service=athena&tail=500" >/dev/null
done
```

### Check Alert Status
```bash
# Prometheus alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# AlertManager
open http://localhost:9093
```

---

## 📈 Metrics Reference

### Required Metrics

**For error rate alerts:**
- `http_requests_total{code=~"5.."}` - 5xx errors
- `http_requests_total` - Total requests

**For latency alerts:**
- `bridge_request_latency_seconds_bucket` - Latency histogram

**For redaction dashboard:**
- `bridge_logs_redactions_total` - Redaction events
- `bridge_logs_requests_total` - Log requests
- `bridge_logs_clamped_total` - Tail clamps
- `bridge_logs_errors_total` - Read errors
- `bridge_logs_timeout_total` - Timeouts

**For RAG dashboard:**
- `rag_queries_total` - RAG queries
- `rag_hits_total` - Cache hits
- `rag_latency_seconds_bucket` - Latency histogram
- `embedding_queue_depth` - Queue size

### Adding Metrics

**In Bridge/Athena/UAT:**
```python
from prometheus_client import Counter, Histogram

# Add counter
requests_total = Counter('http_requests_total', 'Total HTTP requests', ['code', 'route'])

# Add histogram
latency = Histogram('bridge_request_latency_seconds', 'Request latency', ['route'])

# Instrument
@app.get("/health")
async def health():
    with latency.labels(route="/health").time():
        requests_total.labels(code="200", route="/health").inc()
        return {"status": "ok"}
```

---

## 🎯 Quick Commands

```bash
# Setup everything
make obs-quick-setup

# Individual commands
make prom-rules-validate  # Check rules
make prom-reload          # Reload Prometheus
make grafana-import       # Import dashboards

# Check status
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health # Grafana
```

---

## 🐛 Troubleshooting

### Dashboards won't import
```bash
# Check Grafana is running
curl http://localhost:3000/api/health

# Verify API key
echo $GRAFANA_API_KEY

# Check import script
chmod +x grafana/import_dashboards.sh
./grafana/import_dashboards.sh
```

### No data in panels
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Verify metrics exist
curl http://localhost:9090/api/v1/label/__name__/values | jq . | grep bridge

# Generate test data
./VALIDATE_PLATFORM.sh
```

### Alerts not firing
```bash
# Validate rules
make prom-rules-validate

# Check Prometheus config
curl http://localhost:9090/api/v1/status/config | jq .

# Reload rules
make prom-reload

# Check alert status
open http://localhost:9090/alerts
```

---

## 🏆 Success Criteria

✅ **All dashboards imported**
- Visit http://localhost:3000/dashboards
- See 3 dashboards listed

✅ **All alerts loaded**
- Visit http://localhost:9090/alerts
- See 9 alert rules

✅ **Data flowing**
- Open any dashboard
- See recent data (last 5min)

✅ **Alerts can fire**
- Trigger test alert
- See in Prometheus + AlertManager

---

**Status:** Production-Ready  
**Setup Time:** 5-30 minutes  
**Maintenance:** Low (auto-reload on config changes)

🎨 **Observability complete!**

