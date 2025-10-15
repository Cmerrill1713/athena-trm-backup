# 🚀 TRM Monitoring - 5 Minute Quick Start

Get your monitoring stack running in 5 minutes.

## Step 1: Start Monitoring Stack (30 seconds)

```bash
make monitoring-up
```

Expected output:
```
✅ Monitoring stack started
   Prometheus: http://localhost:9090
   Grafana:    http://localhost:3001 (admin/admin)
```

## Step 2: Verify Installation (10 seconds)

```bash
make quick-verify
```

This checks:
- ✅ Docker is running
- ✅ All 3 containers are up
- ✅ Services are healthy
- ✅ Configuration files exist

## Step 3: Initialize Database (1 minute)

```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
make init-routing-db
```

Expected output:
```
✅ routing_outcomes schema + indexes applied
```

## Step 4: Import Dashboard (30 seconds)

First, get a Grafana API key:
1. Open http://localhost:3001 (login: admin/admin)
2. Click the gear icon → API Keys
3. Click "New API Key" (name: Import, role: Admin)
4. Copy the key

Then import:
```bash
export GRAFANA_API_KEY="your_key_here"
make dash-import
```

## Step 5: Integrate Your API (2 minutes)

Add these lines to your main API file (e.g., `main.py`):

```python
from fastapi import FastAPI
from src.api.metrics_mount import mount_metrics

app = FastAPI()
app = mount_metrics(app)  # Adds /metrics endpoint

# ... rest of your app code
```

Start your API:
```bash
uvicorn main:app --port 8080
```

## Step 6: Verify Metrics (10 seconds)

```bash
make check-metrics
```

Should show Prometheus-formatted metrics.

## Step 7: View Dashboard (10 seconds)

```bash
open http://localhost:3001/dashboards
```

Click "TRM Evolution Overview"

## ✅ You're Done!

**What you now have:**
- 📊 Real-time dashboard with 5 panels
- 🚨 5 active alert rules
- 📈 Metrics endpoint at /metrics
- 🗄️ Optimized database with indexes
- 🤖 Auto-approval ready

**Quick Links:**
- Dashboard: http://localhost:3001/d/trm-evolution
- Prometheus: http://localhost:9090
- Metrics: http://localhost:8080/metrics

**Next Steps:**
1. Add metrics to your routing code (see `MONITORING_SETUP.md`)
2. Configure Slack alerts (edit `monitoring/alerts/alertmanager.yml`)
3. Schedule nightly runs: `crontab -e` (see `crontab.example`)

**Need Help?**
- Full guide: `MONITORING_SETUP.md`
- Verification: `VERIFICATION_CHECKLIST.md`
- Troubleshooting: `make monitoring-logs`

---

**Total Time**: ~5 minutes  
**Status**: ✅ Production-ready

