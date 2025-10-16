# Governance System Wiring Guide

## Overview

This guide provides a systematic approach to verify that all governance system components are properly connected and functioning.

## Quick Validation

### One-Command Check
```bash
make -f Makefile.governance wire-check
```

### Quick Smoke Test
```bash
make -f Makefile.governance smoke-test
```

---

## Complete Checklist

### 0. Fast Context

**Repository Root**: `/Users/christianmerrill/Documents/GitHub`

**Docker Compose**: `docker-compose.athena-governance.yml`

**Expected Services**:
| Service | Port | Purpose |
|---------|------|---------|
| governance-orchestrator | 9110 | Main verdict processing |
| governance-canary | 9111 | Canary window management |
| governance-metrics | 9109 | Metrics export |
| prometheus | 9090 | Metrics collection |
| grafana | 3001 | Visualization |

---

### 1. Inventory

Generate complete system inventory:

```bash
# Run inventory
make -f Makefile.governance inventory

# View results
cat docs/inventory/endpoints.txt
```

**Manual inventory commands:**

```bash
# 1.1 List containers and ports
docker ps --format 'table {{.Names}}\t{{.Ports}}'

# 1.2 Find all HTTP routes
rg -n "app\.route|@app\.(get|post)|/verdict|/health|/metrics" \
  --glob '!**/archive/**' --hidden

# 1.3 Find schemas
rg -n "openapi|swagger|schema\.json" --hidden

# 1.4 Find event topics
rg -n "emit\(|publish\(|\"exec\.|\"judicial\.|\"release\.canary" --hidden

# 1.5 Find metrics names
rg "governance_[a-zA-Z0-9_]+" --hidden | \
  grep -oE 'governance_[a-zA-Z0-9_]+' | sort -u
```

---

### 2. Health, Ready, Version Triad

Every service must have all three endpoints:

```bash
# Test orchestrator
curl http://localhost:9110/health
curl http://localhost:9110/ready
curl http://localhost:9110/version

# Test canary
curl http://localhost:9111/health
curl http://localhost:9111/ready
curl http://localhost:9111/version

# Test metrics
curl http://localhost:9109/health
curl http://localhost:9109/metrics
```

**Pass Criteria**:
- ✅ `/health` returns 200 quickly
- ✅ `/ready` ensures dependencies are reachable
- ✅ `/version` returns build id/commit/time

**Added to orchestrator** (orchestrator/app.py):
- ✅ `GET /health`
- ✅ `GET /ready` (checks state file access)
- ✅ `GET /version` (returns version, build time, commit)

---

### 3. Contract Checks

Test required endpoints with proper payloads:

#### Verdict Endpoint

```bash
# Test PASS verdict
curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "T-test-001",
    "verdict": "PASS",
    "ece_estimate": 0.045,
    "entropy_drift": 0.1,
    "violation_rate_delta": 0.001,
    "latency_p95_delta": -0.02,
    "actions": ["HOLD"]
  }' | jq .

# Test HARD_FAIL verdict
curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "T-test-002",
    "verdict": "HARD_FAIL",
    "ece_estimate": 0.09,
    "entropy_drift": 0.3,
    "actions": ["ROLLBACK"]
  }' | jq .
```

#### Canary Window Endpoint (if implemented)

```bash
curl -X POST http://localhost:9111/canary-window \
  -H "Content-Type: application/json" \
  -d '{
    "window_id": "w-test-001",
    "decision": "PROMOTE",
    "samples": 250,
    "deltas": {
      "solve_rate": 0.03,
      "violation_rate": -0.001,
      "latency_p95": -0.12
    },
    "ece_post": 0.045,
    "confidence": 0.9
  }' | jq .
```

**Pass Criteria**:
- ✅ Returns 2xx status code
- ✅ Returns structured JSON response
- ✅ Side effects occur (state updated, metrics incremented)

---

### 4. State, Idempotence, Action Binding

#### State Persistence

```bash
# Check state file
cat state/exec_state.json | jq .

# Or
cat exec_state.json | jq .
```

#### Idempotence Test

```bash
# Submit same verdict twice
TASK_ID="T-idempotence-$(date +%s)"

curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"$TASK_ID\",\"verdict\":\"PASS\",\"ece_estimate\":0.04}"

sleep 1

# Submit again (should be idempotent)
curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"$TASK_ID\",\"verdict\":\"PASS\",\"ece_estimate\":0.04}"

# Check state - should not have double-applied
cat exec_state.json | jq .
```

#### Ledger Verification

```bash
# Run ledger verification
python3 scripts/diagnostic/action_ledger.py --verify

# Show statistics
python3 scripts/diagnostic/action_ledger.py --stats
```

**Pass Criteria**:
- ✅ State updates are idempotent
- ✅ Ledger shows 0 duplicates
- ✅ Ledger shows 0 conflicts
- ✅ All hashes are valid

---

### 5. Event Bus Emissions

Check that events are being emitted:

```bash
# Check logs for event emissions
rg -i "exec\.verdict_applied|judicial\.verdict|release\.canary" logs/ || \
  echo "No events found in logs"

# Check orchestrator output
docker compose -f docker-compose.athena-governance.yml logs governance-orchestrator | \
  grep "EVENT:"
```

**Expected Events**:
- `exec.verdict_applied` - When verdict is applied
- `judicial.verdict` - From judicial component
- `release.canary` - Canary decisions

**Pass Criteria**:
- ✅ Events emitted after verdicts
- ✅ Events contain required fields (task_id, verdict, actions, state)

---

### 6. Prometheus: Scrape + Series

#### Check Scrape Targets

```bash
# List all targets
curl -s "http://localhost:9090/api/v1/targets" | \
  jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

#### Check Series Exist

```bash
# Check for governance metrics
curl -s "http://localhost:9090/api/v1/series?match[]=governance_*" | \
  jq '.data | length'

# Query specific metric
curl -s "http://localhost:9090/api/v1/query?query=governance_verdicts_total" | \
  jq '.data.result'
```

#### Critical Series Checklist

Must be present in Prometheus:
- ✅ `governance_verdicts_total{verdict_type=...}`
- ✅ `governance_actions_total{action=...}`
- ✅ `governance_ece_post`
- ✅ `governance_entropy_drift`
- ✅ `governance_violation_rate_delta`
- ✅ `governance_latency_p95_delta`
- ✅ `governance_orchestrator_up`

**Check script:**
```bash
for metric in governance_verdicts_total governance_actions_total governance_ece_post; do
  echo -n "Checking $metric: "
  curl -s "http://localhost:9090/api/v1/series?match[]=$metric" | \
    grep -q "$metric" && echo "✓ present" || echo "✗ missing"
done
```

---

### 7. Grafana Panels & Alerts

#### Import Dashboard

```bash
# Copy dashboard to Grafana provisioning
cp dashboards/governance_dashboard.json \
   /path/to/grafana/provisioning/dashboards/
```

#### Force ECE Critical for Alert Testing

```bash
# Submit high ECE verdict
curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "T-alert-test",
    "verdict": "HARD_FAIL",
    "ece_estimate": 0.095,
    "entropy_drift": 0.4
  }'

# Check alerts fired
sleep 5
curl -s "http://localhost:9090/api/v1/alerts" | \
  jq '.data.alerts[] | {name: .labels.alertname, state: .state}'
```

---

### 8. Auth, CORS, Rate-Limits

#### CORS Check

```bash
curl -X OPTIONS http://localhost:9110/verdict \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -I
```

#### Rate Limit Check

```bash
# Send rapid requests
for i in {1..20}; do
  curl -s -X POST http://localhost:9110/verdict \
    -H "Content-Type: application/json" \
    -d "{\"task_id\":\"T-rate-$i\",\"verdict\":\"PASS\"}" &
done
wait

# Check if any were rate-limited (429 responses)
```

---

### 9. Failure Drills

#### Orchestrator Restart

```bash
# Kill and restart
docker compose -f docker-compose.athena-governance.yml kill governance-orchestrator
sleep 2
docker compose -f docker-compose.athena-governance.yml up -d governance-orchestrator

# Wait for startup
sleep 5

# Verify state is consistent
curl http://localhost:9110/state | jq .

# Re-submit verdict
curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "T-recovery-001",
    "verdict": "PASS",
    "ece_estimate": 0.04
  }'
```

---

### 10. One-Button Smoke Test

```bash
# Run smoke test
./scripts/smoke_integration.sh

# Or via Makefile
make -f Makefile.governance smoke-test
```

**Expected output:**
```
================================
Governance System Smoke Test
================================

OK: Prometheus ready
OK: Core services healthy
OK: Verdict accepted
OK: Wait complete
OK: Verdict metrics visible in Prometheus
OK: State file exists and updated

================================
ALL GREEN: verdict→action→metrics loop is healthy
================================
```

---

## Troubleshooting

### Services Not Responding

```bash
# Check which containers are running
docker compose -f docker-compose.athena-governance.yml ps

# Check specific service logs
docker compose -f docker-compose.athena-governance.yml logs governance-orchestrator

# Restart all services
docker compose -f docker-compose.athena-governance.yml restart
```

### Metrics Not Showing in Prometheus

```bash
# Check Prometheus scrape config
cat prometheus/prometheus.yml

# Verify targets
curl -s "http://localhost:9090/api/v1/targets" | \
  jq '.data.activeTargets[] | select(.labels.job | contains("governance"))'

# Check if metrics endpoint is accessible
curl http://localhost:9110/metrics | grep governance_
```

**Common fixes:**
- Use service DNS name in prometheus.yml (e.g., `governance-orchestrator:9110`)
- Ensure service port is exposed in docker-compose.yml
- Check metrics are actually being incremented

### Events Not Being Consumed

```bash
# Check event emissions
docker compose logs governance-orchestrator | grep "EVENT:"

# Verify topic names match
rg "exec\.verdict_applied" orchestrator/
rg "exec\.verdict_applied" <consumer-service>/

# Add temporary logging
# In orchestrator/app.py emit_event():
print(f"EMITTING EVENT: {event_type} -> {payload}")
```

### Idempotence Failures

Add uniqueness constraint:
```python
# In orchestrator/app.py
def ledger_append(record):
    # Check for duplicate before appending
    task_id = record.get("task_id")
    actions_hash = hashlib.md5(
        json.dumps(record.get("actions_taken", []), sort_keys=True).encode()
    ).hexdigest()
    
    # Check if already in ledger (optional - requires reading ledger)
    # ... upsert logic ...
```

---

## Acceptance Criteria

All checks must be ✅ green:

- [x] `/health`, `/ready`, `/version` on every service
- [x] `/verdict` returns 2xx and updates state + events + metrics
- [x] `/canary-window` (if implemented) works correctly
- [x] `exec_state.json` writes are idempotent
- [x] `exec.verdict_applied` event emitted
- [x] Prometheus sees all `governance_*` series
- [x] Alerts fire when ECE > 0.08
- [x] Smoke script prints "ALL GREEN"

---

## Available Commands

```bash
# Comprehensive wiring check
./scripts/wire_check.sh

# Quick smoke test
./scripts/smoke_integration.sh

# Detailed endpoint probe
python3 scripts/diagnostic/endpoint_probe.py

# Ledger verification
python3 scripts/diagnostic/action_ledger.py --verify

# Makefile targets
make -f Makefile.governance wire-check
make -f Makefile.governance smoke-test
make -f Makefile.governance health-check
make -f Makefile.governance metrics-check
make -f Makefile.governance inventory
```

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/wire_check.sh` | Comprehensive wiring validation |
| `scripts/smoke_integration.sh` | Quick smoke test |
| `scripts/diagnostic/endpoint_probe.py` | Detailed endpoint testing |
| `scripts/diagnostic/action_ledger.py` | Ledger verification |
| `Makefile.governance` | Makefile targets for validation |
| `GOVERNANCE_WIRING_GUIDE.md` | This guide |
| `orchestrator/app.py` | Added /ready and /version endpoints |

---

## Next Steps

1. **Run wire check**: `./scripts/wire_check.sh`
2. **Review inventory**: `cat wire_check_inventory.txt`
3. **Fix any failures**: See troubleshooting section
4. **Run smoke test**: `./scripts/smoke_integration.sh`
5. **Validate metrics**: `make -f Makefile.governance metrics-check`

---

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/governance-test.yml
- name: Wire Check
  run: |
    docker compose -f docker-compose.athena-governance.yml up -d
    sleep 10
    make -f Makefile.governance wire-check

- name: Smoke Test
  run: make -f Makefile.governance smoke-test
```

---

**Ready to validate your governance system!** 🚀

