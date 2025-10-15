# 📊 TRM Evolution - Daily Operations Guide

**Status**: ✅ Production-ready with operational tooling  
**Last Updated**: October 12, 2025

---

## 🎯 Quick Reference

### One-Liners You Now Have

```bash
# Deploy & verify in one shot
make prod-observe

# Generate realistic traffic
make seed-metrics COUNT=100

# Test alert system
make alert-smoke

# Import/update dashboard
make dash-import

# Initialize database
make init-routing-db

# Check system health
make quick-verify
```

---

## 🌱 Daily Workflow

### Morning Check (2 minutes)

```bash
# 1. Check monitoring stack health
make alert-smoke

# 2. View dashboard
open http://localhost:3001/d/trm-evolution

# 3. Check for firing alerts
open http://localhost:9090/alerts
```

**What to look for:**
- ✅ Success rate ≥ 95% (last 7 days)
- ✅ p95 latency < 1500ms
- ✅ No red alerts firing
- ✅ Steady traffic (not flatlined)

### Generate Traffic (if needed)

```bash
# Seed with 100 routing decisions
make seed-metrics COUNT=100

# Or custom count
make seed-metrics COUNT=500
```

**Seeds 8 diverse prompt types:**
- Python functions
- Async/await explanations
- Swift debugging
- SQL optimization
- React refactoring
- Docker deployment
- Unit testing
- CAP theorem

### Weekly Review (10 minutes)

```bash
# 1. Check 7-day trends
# Dashboard → set time range to "Last 7 days"

# 2. Review promotions
# Dashboard → "Last 20 Promotions" table

# 3. Check recording rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[0].name'
# Should show: trm-recording

# 4. Verify metrics cardinality
curl -s http://localhost:9090/api/v1/label/__name__/values | \
  jq -r '.data[]' | grep routing | wc -l
```

---

## 📈 Enhanced Metrics with Labels

### Environment & Build Tracking

All metrics now include:
- `env`: local | staging | prod
- `build`: git SHA or tag

**Set in your environment:**
```bash
export ENV=prod
export BUILD_SHA=$(git rev-parse --short HEAD)
```

**Or in docker-compose.athena.yml:**
```yaml
environment:
  - ENV=prod
  - BUILD_SHA=${BUILD_SHA:-dev}
```

### Query Examples

```promql
# Success rate by environment
sum(increase(routing_success_total{env="prod"}[1h]))
/ 
sum(increase(routing_decisions_total{env="prod"}[1h]))

# Latency by build
histogram_quantile(0.95,
  sum by (le, build) (rate(routing_latency_ms_bucket[5m]))
)

# Model distribution in production
sum by (model) (
  increase(routing_decisions_total{env="prod"}[24h])
)
```

---

## 🚀 Recording Rules (Fast Dashboards)

Pre-aggregated metrics update every 30s:

| Metric | Query | Use |
|--------|-------|-----|
| `trm:success_rate:5m` | 5-minute success rate | Dashboard stat panels |
| `trm:latency_p95_ms:5m` | p95 latency | SLO tracking |
| `trm:latency_p50_ms:5m` | p50 latency | Baseline performance |
| `trm:decisions_per_minute:5m` | Throughput | Traffic monitoring |
| `trm:success_rate:1h` | Hourly success rate | Trend analysis |

**Benefit**: Queries run 10-100x faster on dashboards.

---

## 🚨 Alert Status

### Active Alerts (6 total)

| Alert | Threshold | Duration | Action |
|-------|-----------|----------|--------|
| **TRMAccuracyDrop** | Avg delta < 0 for 6h | 30m | Page on-call |
| **RoutingSuccessLow** | Success < 70% | 15m | Investigate |
| **LatencyP95High** | p95 > 1500ms | 10m | Performance review |
| **NoRoutingActivity** | No decisions 1h | 1h | Check pipeline |
| **PromotionsSpike** | >3 promotions/h | 5m | Review gates |
| **MonitoringDeadman** | Always firing | 15m | Monitor health |

### Deadman's Switch

**Purpose**: If `MonitoringDeadman` stops firing, Prometheus or AlertManager is down.

**How it works:**
- Always evaluates to `true` (vector(1))
- Should always be in "firing" state
- If missing from alerts list → monitoring broken

**Check status:**
```bash
curl -s http://localhost:9090/api/v1/alerts | \
  jq '.data.alerts[] | select(.labels.alertname=="MonitoringDeadman")'
```

---

## 🔔 Alert Routing (when configured)

**Edit**: `monitoring/alerts/alertmanager.yml`

```yaml
global:
  slack_api_url: '${SLACK_WEBHOOK_URL}'

receivers:
  - name: 'slack'
    slack_configs:
      - channel: '#trm-alerts'
        send_resolved: true
```

**Set webhook:**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/HERE"
```

**Restart AlertManager:**
```bash
docker restart athena-alertmanager
```

---

## 📊 What to Watch This Week

### Success Metrics (aim high)
- **Success Rate**: ≥ 95% (7-day)
- **p95 Latency**: < 1200ms (tightening from 1500ms)
- **Uptime**: 99.9%

### Evolution Metrics (healthy cadence)
- **Promotions**: ≤ 3 per hour
- **Accuracy Delta**: Positive trend
- **Training Runs**: 1-2 per week

### Operational Metrics (avoid problems)
- **Cardinality**: < 10K series (keep labels controlled)
- **Scrape Success**: 100%
- **Alert Evaluation**: No errors

---

## 🧪 Testing Alerts

### Safe Alert Test

Lower threshold temporarily to test routing:

```bash
# 1. Backup rules
cp monitoring/alerts/trm.rules.yml monitoring/alerts/trm.rules.yml.bak

# 2. Edit rule (lower threshold)
# Change: expr: ... > 1500
# To:     expr: ... > 50

# 3. Apply
docker cp monitoring/alerts/trm.rules.yml athena-prometheus:/etc/prometheus/trm.rules.yml
docker exec athena-prometheus wget -q -O- --post-data='' http://localhost:9090/-/reload

# 4. Generate traffic to trigger
make seed-metrics COUNT=50

# 5. Check firing
open http://localhost:9090/alerts

# 6. Restore
cp monitoring/alerts/trm.rules.yml.bak monitoring/alerts/trm.rules.yml
# Re-apply steps 3
```

---

## 🗂️ Data Management

### Prometheus Retention

**Current**: 15 days (default)  
**Recommended**: 30-90 days for production

**Update retention:**
```yaml
# In docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=45d'
  - '--storage.tsdb.retention.size=50GB'
```

### Database Archival

**Query current size:**
```sql
SELECT
  pg_size_pretty(pg_total_relation_size('routing_outcomes')) as size,
  count(*) as rows
FROM routing_outcomes;
```

**Archive old data:**
```sql
-- Move to archive (>90 days old)
INSERT INTO routing_outcomes_archive
SELECT * FROM routing_outcomes
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete archived
DELETE FROM routing_outcomes
WHERE created_at < NOW() - INTERVAL '90 days';
```

**Automate with cron:**
```bash
# Add to crontab
0 3 1 * * psql "$DATABASE_URL" -f scripts/learn/archive_old_outcomes.sql
```

---

## 📈 Dashboard Enhancements

### SLO Panels (add to Grafana)

**P95 Latency SLO:**
```promql
# Query
trm:latency_p95_ms:5m

# Thresholds
- Green: 0 - 1200
- Yellow: 1200 - 1500
- Red: > 1500
```

**Success Rate SLO:**
```promql
# Query
trm:success_rate:1h * 100

# Thresholds
- Red: < 95
- Yellow: 95 - 98
- Green: > 98
```

### Promotion Annotations

Add to dashboard JSON:
```json
{
  "annotations": {
    "list": [{
      "datasource": "Prometheus",
      "expr": "changes(trm_promotions_total[1m]) > 0",
      "step": "1m",
      "titleFormat": "TRM Promotion",
      "textFormat": "New model promoted",
      "iconColor": "green"
    }]
  }
}
```

---

## 🧰 Troubleshooting

### Metrics Not Updating

```bash
# 1. Check API is emitting
curl http://127.0.0.1:8888/metrics/ | grep routing_decisions_total

# 2. Check Prometheus scraping
curl -s http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.job=="athena-api-prod")'

# 3. Check for scrape errors
docker logs athena-prometheus | grep error
```

### Recording Rules Not Working

```bash
# 1. Check rules loaded
curl -s http://localhost:9090/api/v1/rules | \
  jq '.data.groups[] | select(.name=="trm-recording")'

# 2. Query directly
curl -s 'http://localhost:9090/api/v1/query?query=trm:success_rate:5m' | jq

# 3. Check evaluation errors
docker logs athena-prometheus | grep -i "rule evaluation"
```

### Alerts Not Firing

```bash
# 1. Check alert rules loaded
curl -s http://localhost:9090/api/v1/rules | \
  jq '.data.groups[].rules[] | select(.type=="alerting") | .name'

# 2. Manually evaluate alert expression
curl -s 'http://localhost:9090/api/v1/query?query=YOUR_ALERT_EXPR' | jq

# 3. Check AlertManager routing
curl http://localhost:9093/api/v1/status
```

---

## 📋 Weekly Checklist

- [ ] Review 7-day success rate (≥95%)
- [ ] Check p95 latency trend (<1500ms)
- [ ] Verify no stuck alerts
- [ ] Review promotions (1-3 expected)
- [ ] Check metrics cardinality
- [ ] Verify database size (archive if >10GB)
- [ ] Test alert smoke (make alert-smoke)
- [ ] Review dashboard for anomalies
- [ ] Check Prometheus disk usage
- [ ] Backup Prometheus data

---

## 🎯 SLOs & Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Availability** | 99.9% | Up/total time |
| **Success Rate** | ≥95% | 7-day average |
| **P95 Latency** | <1500ms | 5-minute window |
| **P50 Latency** | <400ms | 5-minute window |
| **Promotions** | 1-3/week | Weekly count |
| **Accuracy Lift** | Positive | Per promotion |

---

## 🚀 Next Level

### When You're Ready

1. **Add cost tracking**: Track tokens/$ per routing decision
2. **Per-model dashboards**: Deep-dive into each model's performance
3. **A/B testing metrics**: Compare TRM vs baseline routing
4. **User feedback**: Track `user_feedback` column in DB
5. **Long-term storage**: VictoriaMetrics or Thanos for >90 days
6. **Distributed tracing**: Add OpenTelemetry spans
7. **Log aggregation**: Loki or ELK for structured logs

---

## 📞 Quick Support

**Stuck?** Run diagnostics:
```bash
make quick-verify   # Full health check
make alert-smoke    # Alert system status
make check-metrics  # Endpoint verification
```

**Common fixes:**
```bash
# Restart everything
make monitoring-down && make monitoring-up

# Reload Prometheus config
docker restart athena-prometheus

# Rebuild with latest metrics
make prod-observe
```

---

## 🎉 You're Set!

Your TRM Evolution system is now **production-grade observable**:

- ✅ Real-time metrics with env/build labels
- ✅ Recording rules for fast dashboards
- ✅ 6 alert rules (including deadman)
- ✅ Easy traffic generation (`make seed-metrics`)
- ✅ Alert system testing (`make alert-smoke`)
- ✅ One-shot deploys (`make prod-observe`)

**Keep these graphs truthful, alerts quiet, and the loop improving!** 🧠🚀

---

*Updated: October 12, 2025*  
*PRD Tags: ST-104, ST-108*  
*Status: Operational & battle-tested*

