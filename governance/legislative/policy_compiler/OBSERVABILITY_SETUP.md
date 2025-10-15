# Observability Setup - Grafana Dashboards + Prometheus Alerts

**Time to Setup**: 30-40 minutes  
**Value**: Instant "is anything burning?" clarity  
**Status**: Ready to deploy

---

## WHAT YOU GET

### 3 Grafana Dashboards

1. **Redaction Security** (`redaction_dashboard.json`)
   - Redaction events per 5m
   - Redaction rate timeline
   - Top sources (by service/route)

2. **Ops Window Analytics** (`ops_window_dashboard.json`)
   - Active sessions
   - Manual vs auto-open rates
   - Session cap usage %
   - Auto-open block reasons
   - Confidence distribution

3. **RAG Performance** (`rag_performance_dashboard.json`)
   - RAG hit ratio
   - Latency p50/p95
   - Embedding queue depth
   - Query rate
   - Citation validity %
   - Top queries

### Prometheus Alert Rules (`slo_rules.yaml`)

**Service SLO**:
- HighErrorRate5m: Error rate > 2% for 10m (PAGE)
- HighErrorRate1h: Error rate > 1% for 30m (TICKET)
- LatencyP95Degraded: p95 > 800ms for 15m (PAGE)
- SLOBurnFast: Burning error budget 14.4x (PAGE)
- SLOBurnSlow: Burning error budget 6x (TICKET)

**Security**:
- RedactionSpike: >5 events in 5m (PAGE)
- RedactionRateSustained: >0.1/sec for 1h (TICKET)

**Ops Window**:
- OpsWindowSessionLimitHit: Frequent cap hits (WARNING)
- LowConfidenceSpike: >25% responses <45% confidence (TICKET)

**RAG**:
- RAGRecallDegraded: Hit rate <60% (WARNING)
- RAGLatencyHigh: p95 >2s (WARNING)
- EmbeddingQueueBackup: Queue depth >100 (WARNING)

---

## QUICK SETUP (30-40 minutes)

### Step 1: Validate Alert Rules (2 min)

```bash
cd /Users/christianmerrill/Documents/GitHub
make prom-rules-validate
```

**Expected**: `OK: Rules valid` or `WARN: promtool not found`

**If WARN**: Install promtool:
```bash
brew install prometheus
```

---

### Step 2: Load Alert Rules into Prometheus (5 min)

**Option A: Mount as volume** (Docker)

Edit `docker-compose.monitoring.yml`:
```yaml
prometheus:
  volumes:
    - ./prometheus/alerts:/etc/prometheus/alerts:ro
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/usr/share/prometheus/console_libraries'
    - '--web.console.templates=/usr/share/prometheus/consoles'
    - '--web.enable-lifecycle'
```

Then add to `prometheus/prometheus.yml`:
```yaml
rule_files:
  - '/etc/prometheus/alerts/*.yaml'
```

**Option B: Copy to running container**:
```bash
docker cp prometheus/alerts/slo_rules.yaml prometheus:/etc/prometheus/alerts/
docker exec prometheus promtool check rules /etc/prometheus/alerts/slo_rules.yaml
```

**Reload**:
```bash
make prom-reload
```

---

### Step 3: Create Grafana API Key (3 min)

1. Open Grafana: `http://localhost:3000`
2. Login (default: admin/admin)
3. **Settings** (gear icon) → **API Keys**
4. Click **Add API Key**
   - Name: `dashboard-import`
   - Role: `Admin`
   - Time to live: `Never` (or 1 year)
5. Click **Add**
6. **Copy the key** (you'll only see it once)

---

### Step 4: Import Dashboards (2 min)

```bash
cd /Users/christianmerrill/Documents/GitHub

export GRAFANA_URL=http://localhost:3000
export GRAFANA_API_KEY=your-api-key-here

make grafana-import
```

**Expected**:
```
NeuroForge Dashboard Import
===========================

Importing redaction_dashboard.json ... OK
Importing ops_window_dashboard.json ... OK
Importing rag_performance_dashboard.json ... OK

========================================
OK: All dashboards imported

Access at: http://localhost:3000/dashboards
```

---

### Step 5: Verify Dashboards (5 min)

1. Open Grafana: `http://localhost:3000`
2. Click **Dashboards** (squares icon)
3. You should see:
   - Redaction Security
   - Ops Window Analytics
   - RAG Performance

4. Open each, verify panels load

---

### Step 6: Generate Some Traffic (10 min)

**Option A: Use the app**
```bash
cd NeuroForgeApp
# Press Cmd-R
# Send 10-20 messages
# Tap [Health], [RAG] buttons
# Press Cmd-Opt-O (Ops window)
```

**Option B: Load test**
```bash
# If hey is installed
hey -z 60s -q 50 http://127.0.0.1:8014/ready

# Or ab
ab -n 1000 -c 10 http://127.0.0.1:8014/ready
```

---

### Step 7: Watch Panels Update (5 min)

**Redaction Dashboard**:
- Redaction events: Should show activity if any secrets detected
- Rate: Should be low (spikes = investigate)

**Ops Window Dashboard**:
- Active sessions: Should match running app instances
- Openings: Should tick up as you use Cmd-Opt-O
- Confidence: Should show distribution

**RAG Performance**:
- Hit ratio: Should be >60% (healthy)
- Latency: Should be <2s p95
- Queue: Should be low (<10)

---

### Step 8: Test Alerts (5 min)

**Trigger a test alert**:
```bash
# In Prometheus
http://localhost:9090/alerts

# Look for alerts in "Pending" or "Firing" state
```

**Or force a spike**:
```bash
# Rapidly query RAG to trigger latency alert
for i in {1..50}; do
  curl -X POST http://127.0.0.1:8015/api/rag/query \
    -d '{"query":"test","k":5}' &
done
wait
```

---

## DASHBOARDS EXPLAINED

### Redaction Security

**Purpose**: Catch secret exposure attempts

**Key Panels**:
- **Redaction events / 5m**: Stat showing count
  - Green: 0-2
  - Yellow: 3-4
  - Red: 5+

- **Redaction rate**: Timeline showing events/second
  - Normal: Near zero
  - Spike: Investigate immediately

- **Top sources**: Table of which services/routes redacting
  - Helps identify misconfigured components

**Action on Red**:
1. Check service logs for exposed secrets
2. Review code that triggered redaction
3. Verify secrets are in vault, not code

---

### Ops Window Analytics

**Purpose**: Monitor user experience and auto-open behavior

**Key Panels**:
- **Active sessions**: How many users connected
- **Openings**: Manual vs auto-open rates
  - Healthy: Low auto-open rate
  - Issue: High auto-open = low confidence responses

- **Session cap usage**: % of 5-opens limit
  - Green: <70%
  - Yellow: 70-90%
  - Red: >90% (users hitting limit)

- **Block reasons**: Why auto-opens are blocked
  - Should mostly be "debounce"
  - If "limit" is high, consider raising cap

- **Confidence distribution**: p50/p95 of response confidence
  - Healthy: p50 >0.75, p95 >0.85
  - Issue: p50 <0.60 = model struggling

**Action on Red**:
1. Check why confidence is low
2. Review red turn captures
3. Consider distillation or model tuning

---

### RAG Performance

**Purpose**: Ensure knowledge base is helping, not hurting

**Key Panels**:
- **Hit ratio**: % of queries that found relevant docs
  - Green: >80%
  - Yellow: 60-80%
  - Red: <60% (RAG not helping)

- **Latency**: p50/p95 query time
  - Target: p95 <2s
  - Red: >2s (vector DB slow)

- **Queue depth**: Embedding backlog
  - Healthy: <10
  - Issue: >100 (can't keep up)

- **Citation validity**: % of valid citations
  - Target: >95%
  - Issue: <80% (model hallucinating)

**Action on Red**:
1. RAG recall low: Check index quality, query rewriting
2. Latency high: Scale vector DB, add caching
3. Queue backup: Add embedding workers
4. Citations bad: Enforce schema, tune model

---

## ALERT RULES EXPLAINED

### Severity Levels

**PAGE**: Wake someone up (critical)
- HighErrorRate5m
- LatencyP95Degraded
- SLOBurnFast
- RedactionSpike

**TICKET**: Create issue, fix soon
- HighErrorRate1h
- SLOBurnSlow
- RedactionRateSustained
- LowConfidenceSpike

**WARNING**: Investigate, not urgent
- OpsWindowSessionLimitHit
- RAGRecallDegraded
- RAGLatencyHigh
- EmbeddingQueueBackup

---

### SLO Burn Rate

**Why**: Catches problems early before budget exhausted

**Fast burn** (5m window):
- Burning 14.4x faster than sustainable
- Alert after 5 minutes
- Severity: PAGE (immediate response)

**Slow burn** (1h window):
- Burning 6x faster than sustainable
- Alert after 2 hours
- Severity: TICKET (fix soon)

**Example**:
```
Target error rate: 1% (99% success SLO)
Fast burn: >14.4% errors in 5m
Slow burn: >6% errors in 1h
```

---

## METRICS REFERENCE

### HTTP Metrics (Bridge/Athena)
```
http_requests_total{code="200|500|..."}
bridge_request_latency_seconds_bucket{le="0.1|0.5|..."}
```

### Redaction Metrics
```
app_redaction_events_total{service="bridge|athena",type="api_key|token"}
```

### Ops Window Metrics
```
app_active_sessions
app_ops_window_open_total{method="manual|auto"}
app_ops_window_auto_open_blocked_total{reason="debounce|limit|snooze"}
app_session_cap
app_response_confidence_bucket{le="0.35|0.45|..."}
```

### RAG Metrics
```
rag_queries_total
rag_hits_total
rag_latency_seconds_bucket{le="0.1|0.5|1.0|2.0|..."}
rag_valid_citations_total
rag_total_citations_total
embedding_queue_depth
```

---

## QUICK COMMANDS

```bash
# Validate alert rules
make prom-rules-validate

# Reload Prometheus
make prom-reload

# Import dashboards (needs env vars)
export GRAFANA_URL=http://localhost:3000
export GRAFANA_API_KEY=your-key
make grafana-import

# Full setup
make obs-quick-setup
```

---

## CUSTOMIZATION

### Adjust Thresholds

Edit `prometheus/alerts/slo_rules.yaml`:

```yaml
# Change error rate threshold
- alert: HighErrorRate5m
  expr: ... > 0.02  # Change from 2% to your SLO
```

### Add New Dashboard

1. Create in Grafana UI
2. Export JSON
3. Save to `grafana/dashboards/your_dashboard.json`
4. Add to `grafana/import_dashboards.sh`

### Modify Metric Names

If your metrics differ, update queries:

```json
// In dashboard JSON
"targets": [
  {
    "expr": "your_actual_metric_name"
  }
]
```

---

## TROUBLESHOOTING

### Dashboards Show "No Data"

**Check**:
1. Prometheus scraping your services?
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Metrics being exported?
   ```bash
   curl http://127.0.0.1:8014/metrics | grep redaction
   ```

3. Datasource configured in Grafana?
   - Settings → Data Sources → Prometheus

### Alerts Not Firing

**Check**:
1. Rules loaded in Prometheus?
   ```bash
   curl http://localhost:9090/api/v1/rules
   ```

2. Rules valid syntax?
   ```bash
   make prom-rules-validate
   ```

3. Thresholds too high?
   - Adjust in `slo_rules.yaml`

### Import Script Fails

**Check**:
1. Grafana running?
   ```bash
   curl http://localhost:3000/api/health
   ```

2. API key valid?
   - Regenerate in Grafana UI

3. JSON valid?
   ```bash
   cat grafana/dashboards/*.json | jq .
   ```

---

## POST-DEPLOY VERIFICATION

**After importing dashboards**:

1. Open each dashboard
2. Verify panels load
3. Generate traffic (use app or load test)
4. Watch metrics update
5. Trigger test alert
6. Verify alert fires

**Time**: 10 minutes total

---

## MAINTENANCE

### Weekly
- Review alert noise (any false positives?)
- Adjust thresholds if needed
- Add new panels for new features

### Monthly
- Archive old dashboard versions
- Review SLO targets vs actual
- Tune burn rate multipliers

---

## FILES CREATED

```
grafana/
  dashboards/
    redaction_dashboard.json       # Security monitoring
    ops_window_dashboard.json      # UX analytics
    rag_performance_dashboard.json # RAG health
  import_dashboards.sh             # Auto-import script

prometheus/
  alerts/
    slo_rules.yaml                 # SLO alerts

Makefile                           # Updated with obs targets

OBSERVABILITY_SETUP.md             # This file
```

---

## NEXT STEPS

1. Validate rules: `make prom-rules-validate`
2. Reload Prometheus: `make prom-reload`
3. Get Grafana API key
4. Import dashboards: `make grafana-import`
5. Verify panels load
6. Ship with confidence!

---

OBSERVABILITY READY  
3 Dashboards + 11 Alerts  
30-40 minute setup  
Instant visibility post-deploy

Run make obs-quick-setup to configure!

---

End of Observability Setup Guide

