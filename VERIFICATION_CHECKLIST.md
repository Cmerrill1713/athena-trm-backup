# ✅ TRM Evolution Monitoring - Verification Checklist

Run these commands in order to verify your monitoring setup is working correctly.

## 📋 Pre-Flight Checks

- [ ] Docker is installed and running: `docker --version`
- [ ] PostgreSQL is accessible: `psql "$DATABASE_URL" -c "SELECT 1"`
- [ ] Python 3 is available: `python3 --version`
- [ ] jq is installed: `jq --version`

## 🚀 Step 1: Start Monitoring Stack

```bash
make monitoring-up
```

**Expected Output:**
```
✅ Monitoring stack started
   Prometheus: http://localhost:9090
   Grafana:    http://localhost:3001 (admin/admin)
```

**Verification:**
- [ ] Prometheus UI loads: http://localhost:9090
- [ ] Grafana UI loads: http://localhost:3001
- [ ] Can login to Grafana (admin/admin)

## 🗄️ Step 2: Initialize Database

```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
make init-routing-db
```

**Expected Output:**
```
🗄️  Initializing routing outcomes database...
✅ routing_outcomes schema + indexes applied
```

**Verification:**
```bash
# Check table exists
psql "$DATABASE_URL" -c "\dt routing_outcomes"

# Check indexes
psql "$DATABASE_URL" -c "\di idx_routing_outcomes*"
```

- [ ] `routing_outcomes` table exists
- [ ] Indexes are created

## 📊 Step 3: Import Grafana Dashboard

First, create an API key in Grafana:
1. Login to http://localhost:3001 (admin/admin)
2. Go to Configuration → API Keys
3. Click "New API Key"
4. Name: "Dashboard Import", Role: Admin
5. Copy the key

```bash
export GRAFANA_API_KEY="your_key_here"
make dash-import
```

**Expected Output:**
```
📊 Importing Grafana dashboard...
✅ Imported TRM Evolution Overview
```

**Verification:**
- [ ] Dashboard appears in Grafana: http://localhost:3001/dashboards
- [ ] "TRM Evolution Overview" is listed
- [ ] Dashboard opens without errors

## 📈 Step 4: Start Your Router API

If you haven't integrated the metrics endpoint yet:

```python
# In your main API file (e.g., main.py)
from fastapi import FastAPI
from src.api.metrics_mount import mount_metrics

app = FastAPI()
app = mount_metrics(app)

# ... rest of your app
```

Start your API:
```bash
# Example - adjust for your setup
uvicorn main:app --port 8080
```

## 🔍 Step 5: Check Metrics Endpoint

```bash
make check-metrics
```

**Expected Output:**
```
📈 Checking metrics endpoint...
# HELP routing_decisions_total Total routing decisions
# TYPE routing_decisions_total counter
routing_decisions_total{model="unknown"} 0.0
...
```

**Alternative check:**
```bash
curl http://127.0.0.1:8080/metrics | head -20
```

- [ ] Metrics endpoint responds (200 OK)
- [ ] Prometheus-formatted metrics are returned
- [ ] TRM metrics are present (routing_decisions_total, etc.)

## 🎯 Step 6: Verify Prometheus Scraping

1. Open http://localhost:9090/targets
2. Find the "router" job

**Verification:**
- [ ] Target shows as "UP"
- [ ] Last scrape shows recent timestamp
- [ ] No errors in "Errors" column

If target is DOWN:
- Check the port in `prometheus/prometheus.yml` matches your API
- Restart Prometheus: `docker-compose -f docker-compose.monitoring.yml restart prometheus`

## 🔥 Step 7: Generate Test Data

Create a test outcome to verify data flow:

```python
# Quick test script
from src.metrics.route_metrics import ROUTING_DECISIONS, ROUTING_SUCCESS, ROUTING_LATENCY
import time

# Generate some test metrics
ROUTING_DECISIONS.labels(model="test-model").inc()
ROUTING_SUCCESS.inc()
ROUTING_LATENCY.observe(123.45)

print("✅ Generated test metrics")
```

Or trigger a real routing decision if your system is ready.

## 📊 Step 8: View Dashboard

Open the dashboard: http://localhost:3001/d/trm-evolution

**Verification:**
- [ ] Dashboard loads without errors
- [ ] Panels show data (may be 0 initially)
- [ ] Time range selector works
- [ ] Graphs update as data comes in

## 🚨 Step 9: Check Alert Rules

1. Open http://localhost:9090/alerts
2. You should see the TRM alert rules

**Verification:**
- [ ] All 5 alert rules are loaded:
  - TRMAccuracyDrop
  - RoutingSuccessLow
  - LatencyP95High
  - NoRoutingActivity
  - PromotionsSpike
- [ ] Rules show as "Inactive" (green) or "Pending" (yellow)
- [ ] No rules show errors

## 🤖 Step 10: Test Auto-Approval (Optional)

If you have a candidate ready:

```bash
export TRM_MAX_DELTA=0.15
make approve-promote
```

**Expected Output:**
```
🤖 Running auto-approval and promotion...
✅ promoted artifacts/trm/candidate_20251012_123456
```

Or if no candidate:
```
No candidate found in artifacts/trm/
```

## 🧪 Step 11: End-to-End Test

Run a complete evolution cycle:

```bash
# Train, evaluate, and promote
make learn DAYS=7
```

**Expected Output:**
```
🧠 Training TRM from routing outcomes (7 days)...
📊 Evaluating candidate vs baseline...
🚀 Promoting candidate if better + safe...
✅ Full evolution loop complete
```

**Verification:**
- [ ] Training completes without errors
- [ ] Evaluation produces metrics.json
- [ ] Promotion logic executes
- [ ] Prometheus counter `trm_promotions_total` increments
- [ ] Dashboard shows the promotion

## 📈 Step 12: Verify Metrics Flow

Wait 30 seconds, then check Prometheus:

```bash
# Query Prometheus API
curl -s 'http://localhost:9090/api/v1/query?query=routing_decisions_total' | jq
```

**Expected**: JSON response with metric values

Open Grafana dashboard and verify:
- [ ] Success rate panel shows percentage
- [ ] Model share shows distribution
- [ ] Latency graph shows data points
- [ ] Promotions counter updates

## 🔄 Step 13: Test Alert (Optional)

Manually trigger an alert to test routing:

```python
# Lower success rate artificially to trigger alert
from src.metrics.route_metrics import ROUTING_DECISIONS, ROUTING_SUCCESS

for i in range(100):
    ROUTING_DECISIONS.labels(model="test").inc()
    if i < 60:  # 60% success - below 70% threshold
        ROUTING_SUCCESS.inc()
```

Wait 15 minutes, then check:
- [ ] Alert fires in Prometheus: http://localhost:9090/alerts
- [ ] Alert appears in AlertManager: http://localhost:9093

## 🎉 Final Checks

- [ ] All monitoring containers are running: `docker ps`
- [ ] No errors in logs: `make monitoring-logs`
- [ ] Metrics endpoint is stable
- [ ] Dashboard updates in real-time
- [ ] Database queries are fast (check with `\timing on` in psql)

## 📝 Document Your Setup

Record these values for your team:

```bash
# My Monitoring Setup
Grafana URL: http://localhost:3001
Prometheus URL: http://localhost:9090
AlertManager URL: http://localhost:9093
Router Metrics: http://localhost:8080/metrics
Database: [your DATABASE_URL]
```

## 🆘 Troubleshooting

### Prometheus can't reach router
- Check port: `netstat -an | grep 8080`
- Update `prometheus/prometheus.yml` with correct port
- Restart: `docker-compose -f docker-compose.monitoring.yml restart prometheus`

### Grafana dashboard shows no data
- Verify Prometheus datasource is configured in Grafana
- Check time range (try "Last 6 hours")
- Verify metrics exist: `curl http://localhost:8080/metrics | grep routing`

### Database connection fails
- Test connection: `psql "$DATABASE_URL" -c "SELECT version()"`
- Check credentials in DATABASE_URL
- Verify database exists

### Alerts not firing
- Check alert rules loaded: http://localhost:9090/rules
- Verify evaluation interval in prometheus.yml
- Check alert conditions are met

## ✅ Success Criteria

You're done when:
1. ✅ All containers are running (`docker ps` shows 3 containers)
2. ✅ Metrics endpoint responds with TRM metrics
3. ✅ Prometheus shows router target as UP
4. ✅ Grafana dashboard displays data
5. ✅ Alert rules are loaded and evaluating
6. ✅ Database has indexes and can query quickly
7. ✅ `make learn` completes full cycle
8. ✅ Auto-approval works with test candidate

---

**Next Steps:**
- Schedule nightly evolution: `crontab -e` (see MONITORING_SETUP.md)
- Configure Slack/PagerDuty alerts
- Set up log aggregation
- Document in PRD (tag with ST-xxx)

**Support:**
- Check logs: `make monitoring-logs`
- Review: [MONITORING_SETUP.md](./MONITORING_SETUP.md)
- PRD Reference: [START_HERE.md](./START_HERE.md)

