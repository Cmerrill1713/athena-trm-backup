# 🧩 TRM Evolution Monitoring & Operations Setup

This document describes the complete monitoring and operations infrastructure for the TRM (Tiny Recursive Models) Evolution system.

## 📊 Overview

The monitoring stack includes:
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization dashboards
- **AlertManager** - Alert routing and notifications
- **Database Indexes** - Optimized query performance
- **Auto-approval** - Safe automated promotions

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
make monitoring-up
```

This starts:
- Prometheus at http://localhost:9090
- Grafana at http://localhost:3001 (admin/admin)
- AlertManager at http://localhost:9093

### 2. Initialize Database

```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
make init-routing-db
```

### 3. Import Grafana Dashboard

```bash
export GRAFANA_API_KEY="your-api-key"
make dash-import
```

To get an API key:
1. Log into Grafana at http://localhost:3001
2. Go to Configuration → API Keys
3. Create a new key with Admin role
4. Copy the key and export it

### 4. Check Metrics Endpoint

```bash
make check-metrics
```

## 📈 Metrics Collected

| Metric | Type | Description |
|--------|------|-------------|
| `routing_decisions_total` | Counter | Total routing decisions (by model) |
| `routing_success_total` | Counter | Successful routing decisions |
| `routing_latency_ms` | Histogram | Routing latency in milliseconds |
| `trm_promotions_total` | Counter | Total TRM promotions |
| `trm_accuracy_delta` | Counter | Accuracy delta vs baseline |

## 🎯 Dashboards

### TRM Evolution Overview

The main dashboard shows:
- **7-Day Success Rate** - Overall routing success percentage
- **Model Share** - Distribution of decisions across models
- **Latency p50/p95** - Latency percentiles over time
- **Promotions & Accuracy Lift** - Evolution activity and improvements
- **Last 20 Promotions** - Recent promotion history

Access at: http://localhost:3001/d/trm-evolution

## 🚨 Alerts

### Active Alert Rules

| Alert | Condition | Duration | Severity |
|-------|-----------|----------|----------|
| `TRMAccuracyDrop` | Avg accuracy delta < 0 | 30m | page |
| `RoutingSuccessLow` | Success rate < 70% | 15m | warn |
| `LatencyP95High` | p95 latency > 1500ms | 10m | warn |
| `NoRoutingActivity` | No decisions in 1h | 1h | info |
| `PromotionsSpike` | >3 promotions/hour | 5m | info |

### Configure Notifications

Edit `monitoring/alerts/alertmanager.yml` to add:
- Slack webhooks
- PagerDuty integration
- Email alerts

## 🤖 Auto-Approval

### Safe Promotion Gates

The `approve-and-promote` script checks:
1. ✅ `safety_regressions == 0` - No safety issues
2. ✅ `route_accuracy > baseline` - Improved accuracy
3. ✅ `delta <= TRM_MAX_DELTA` - Change is within bounds (default 0.15)

### Run Manually

```bash
make approve-promote
```

### Schedule Nightly (Optional)

```bash
# Add to crontab
crontab -e

# Add this line:
0 2 * * * cd ~/Documents/GitHub && make learn DAYS=7 >> logs/evolution.log 2>&1
```

## 🗄️ Database Optimization

### Indexes Created

```sql
-- Fast time-window & model pivots
CREATE INDEX idx_routing_outcomes_created_model
ON routing_outcomes (created_at DESC, selected_model);

-- Speed up recent success scans
CREATE INDEX idx_routing_outcomes_success_time
ON routing_outcomes (success, created_at DESC);
```

### Archival Strategy

Optional: Archive old data to keep queries fast:

```sql
-- Run monthly
INSERT INTO routing_outcomes_archive 
SELECT * FROM routing_outcomes 
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM routing_outcomes 
WHERE created_at < NOW() - INTERVAL '90 days';
```

## 🔧 Configuration

### Environment Variables

```bash
# TRM Settings
export TRM_RETRAIN_MIN=1000      # Minimum samples before training
export TRM_MAX_DELTA=0.15        # Maximum allowed accuracy change

# Database
export DATABASE_URL="postgresql://user:pass@localhost/dbname"

# Grafana
export GRAFANA_URL="http://127.0.0.1:3001"
export GRAFANA_API_KEY="your-api-key"
```

### Prometheus Targets

Edit `prometheus/prometheus.yml` to add your API endpoint:

```yaml
scrape_configs:
  - job_name: 'router'
    static_configs:
      - targets: ['127.0.0.1:8080']  # Change port as needed
    metrics_path: /metrics
```

## 🔌 Integration

### FastAPI Integration

Add to your main application:

```python
from fastapi import FastAPI
from src.api.metrics_mount import mount_metrics

app = FastAPI()
app = mount_metrics(app)  # Adds /metrics endpoint
```

### Using Metrics in Code

```python
from src.metrics.route_metrics import (
    ROUTING_DECISIONS, 
    ROUTING_SUCCESS, 
    ROUTING_LATENCY
)

# Before routing
ROUTING_DECISIONS.labels(model=selected_model).inc()

# After execution
if success:
    ROUTING_SUCCESS.inc()
ROUTING_LATENCY.observe(latency_ms)
```

## 🧪 Verification Commands

```bash
# 1. Check database schema and indexes
make init-routing-db

# 2. Verify metrics endpoint is responding
make check-metrics

# 3. Import Grafana dashboard
export GRAFANA_API_KEY=YOUR_KEY
make dash-import

# 4. Generate test data
python3 scripts/learn/outcome_logger.py

# 5. View dashboard
open http://127.0.0.1:3001/d/trm-evolution

# 6. Check Prometheus targets
open http://localhost:9090/targets

# 7. View alerts
open http://localhost:9090/alerts
```

## 📦 File Structure

```
.
├── dashboards/
│   └── trm_evolution_overview.json          # Grafana dashboard
├── monitoring/
│   └── alerts/
│       ├── trm.rules.yml                    # Prometheus alert rules
│       └── alertmanager.yml                 # Alert routing config
├── prometheus/
│   └── prometheus.yml                       # Prometheus config
├── scripts/
│   ├── monitoring/
│   │   └── import_grafana_dashboard.sh      # Dashboard import script
│   └── learn/
│       ├── db_indexes.sql                   # Database indexes
│       └── approve_and_promote.sh           # Auto-approval script
├── src/
│   ├── api/
│   │   └── metrics_mount.py                 # Metrics endpoint
│   └── metrics/
│       └── route_metrics.py                 # Prometheus metrics definitions
└── docker-compose.monitoring.yml            # Monitoring stack
```

## 🛠️ Make Targets

```bash
make monitoring-up        # Start monitoring stack
make monitoring-down      # Stop monitoring stack
make monitoring-logs      # View logs
make dash-import          # Import Grafana dashboard
make init-routing-db      # Initialize database
make approve-promote      # Run auto-approval
make check-metrics        # Verify metrics endpoint
```

## 🔍 Troubleshooting

### Metrics endpoint returns 404

Check that your API has the metrics mount:
```python
from src.api.metrics_mount import mount_metrics
app = mount_metrics(app)
```

### Prometheus not scraping

1. Check targets: http://localhost:9090/targets
2. Verify port in `prometheus.yml` matches your API
3. Restart Prometheus: `docker-compose -f docker-compose.monitoring.yml restart prometheus`

### Grafana dashboard empty

1. Verify Prometheus datasource is configured
2. Check that metrics are being generated: `curl http://localhost:8080/metrics`
3. Verify time range in Grafana (try "Last 24 hours")

### Database connection fails

```bash
# Test connection
psql "$DATABASE_URL" -c "SELECT 1"

# Check if table exists
psql "$DATABASE_URL" -c "\\dt routing_outcomes"
```

## 🎓 Best Practices

1. **Start Simple** - Deploy monitoring stack first, add alerts gradually
2. **Test Alerts** - Manually trigger conditions to verify routing works
3. **Archive Old Data** - Keep queries fast by archiving data older than 90 days
4. **Monitor the Monitors** - Set up deadman alerts for monitoring stack itself
5. **Document Changes** - Track PRD IDs (ST-xxx) for all monitoring changes
6. **Review Weekly** - Check dashboards in weekly PRD sync meetings

## 📚 Related Documentation

- [PRD Integration](./START_HERE.md)
- [Evolution System](./EVOLUTION_SYSTEM_COMPLETE.md)
- [Autopilot Complete](./AUTOPILOT_COMPLETE.md)
- [Runbook](./RUNBOOK.md)

## 🆘 Support

For issues:
1. Check logs: `make monitoring-logs`
2. Review Prometheus targets: http://localhost:9090/targets
3. Check metrics endpoint: `make check-metrics`
4. Review recent promotions in database

---

✅ **Status**: Drop-in pack applied and ready for verification
🔗 **Dashboard**: http://localhost:3001/d/trm-evolution
📊 **Metrics**: http://localhost:8080/metrics

