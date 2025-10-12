# 🚀 NeuroForge Real Mode – Go-Live Guide

**Status**: Ready to Ship
**Version**: bridge-1.0.0
**Last Updated**: 2025-10-12
**Owner**: Platform Team

---

## 🎯 Pre-Flight Checklist

### 1. Tag & Freeze
```bash
cd ~/Documents/GitHub
git tag -a bridge-1.0.0 -m "Real mode: UAT + Athena + Bridge with full integration tests"
git push origin bridge-1.0.0
```

### 2. Environment Lock
```bash
# Production environment
export ENV=prod
export USE_MOCK=0
export UAT_BASE=http://127.0.0.1:8181
export ATHENA_BASE=http://127.0.0.1:8090
export UAT_TOKEN=<prod-secret>
export ATH_TOKEN=<prod-secret>
```

### 3. Clean Startup
```bash
# Kill any squatters
lsof -ti:8014,8181,8090 | xargs -r kill -9

# Start real mode stack
./scripts/real_up.sh

# Wait for health
sleep 5
```

### 4. Smoke Tests (must pass)
```bash
# Quick acceptance
./scripts/acceptance_test.sh

# Contract validation
cd AI-Projects/universal-ai-tools
pytest tests/test_contract.py -v

# Integration suite (fast)
pytest tests/test_integration.py -v -m "not slow"
```

### 5. App Verification
```bash
# Launch with production bridge
API_BASE=http://127.0.0.1:8014 QA_MODE=0 swift run

# Verify in UI:
# - Footer shows: API=8014, mode=real, breaker=closed
# - Cmd+Shift+T loads real traces (170+)
# - Provider Inspector shows UAT route
```

### 6. Rollback Drill (practice now)
```bash
# Time this—should be < 30 seconds
time (
  make bridge-down
  USE_MOCK=1 make bridge-up
  ./scripts/acceptance_test.sh
)

# Expected: ~15-20 seconds, all green
```

---

## 📊 7-Day Post-Launch Plan

### Day 0 – Launch & Watch (15 min every 2 hours)
**Objective**: Catch immediate issues before they cascade.

```bash
# Health check
curl -I http://127.0.0.1:8014/health | grep "X-Mode\|X-Breaker"
# Expected: X-Mode: real, X-Breaker: closed

# Latency spot check
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://127.0.0.1:8014/traces
done | awk '{s+=$1; if($1>max)max=$1} END {print "avg:",s/NR,"max:",max}'
# Expected: avg < 0.15s, max < 0.25s

# Error rate
curl -s http://127.0.0.1:8014/traces | jq -r '.[] | .status' | grep -c error || echo 0
# Expected: 0
```

**Green Bars**:
- p95 latency ≤ 250ms
- Error rate ~0%
- Breaker state: closed
- No 401s (auth working)

**Red Flags**:
- Breaker opens → UAT/Athena down or flaky
- 401 spike → token rotation issue
- p95 > 500ms → backend choking or network issue

**Panic Button**:
```bash
make bridge-down
USE_MOCK=1 make bridge-up
# Announce: "Real mode paused for stabilization. Users on safe mock data."
```

---

### Day 1 – Observability Polish
**Objective**: Make metrics visible and actionable.

#### Export Prometheus Metrics
Add to `bridge.py`:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

REQUEST_COUNT = Counter('bridge_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('bridge_latency_seconds', 'Request latency', ['endpoint'])
BREAKER_STATE = Gauge('bridge_breaker_state', 'Circuit breaker state', ['backend'])

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Wire Grafana Panels
```bash
# If you don't have Grafana yet, quick Prometheus + Grafana:
docker run -d -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
docker run -d -p 3000:3000 grafana/grafana

# Add datasource: Prometheus at http://localhost:9090
# Import dashboard: upload dashboards/bridge_dashboard.json
```

**Panels to add**:
- Request rate (req/min)
- p50/p95/p99 latency
- Error rate (5xx, 4xx)
- Breaker state timeline
- Auth failures (401s)

**Exit Criteria**: Can answer "is it slow?" in < 10 seconds via dashboard.

---

### Day 2 – Security Hygiene
**Objective**: Ensure secrets are safe and audit trail is clean.

#### Token Rotation Test
```bash
# Generate new token
NEW_TOKEN=$(openssl rand -base64 32)

# Update env
export UAT_TOKEN=$NEW_TOKEN

# Restart bridge
make bridge-down
make bridge-up

# Verify
./scripts/acceptance_test.sh
# Expected: green
```

#### Log Redaction Audit
```bash
# Check logs for leaked secrets
grep -rE '(Bearer|token|secret|password).{0,50}' /tmp/*.log | grep -v 'Authorization: Bearer ***'
# Expected: no matches or only redacted
```

#### Immutable Audit Log
Ensure trace logs include:
- Timestamp (UTC)
- Correlation ID
- User/token hash (not raw token)
- Endpoint + method
- Status code
- Latency

**Exit Criteria**: No secrets in logs, tokens rotate cleanly.

---

### Day 3 – Data Integrity
**Objective**: Backups are automatic and verified.

#### Schedule Nightly Backup
```bash
# Add to crontab
crontab -e
# Add line:
0 2 * * * /Users/christianmerrill/Documents/GitHub/scripts/backup_traces.sh
```

#### Verify Backup
```bash
# Run manually first
./scripts/backup_traces.sh

# Check output
ls -lh backups/uat_traces_*.json
# Expected: file with 170+ traces

# Verify checksum
jq -r '.[] | .id' backups/uat_traces_latest.json | sort | sha256sum
# Compare to golden checksum in tests
```

**Exit Criteria**: Backup runs nightly, checksum validates.

---

### Day 4 – Chaos Hour
**Objective**: Verify graceful degradation under failure.

```bash
# Kill UAT (simulate backend failure)
pkill -f "uvicorn uat.api"

# Bridge should fallback to mock
curl -I http://127.0.0.1:8014/traces | grep X-Mode
# Expected: X-Mode: mock

curl -I http://127.0.0.1:8014/health | grep X-Breaker
# Expected: X-Breaker: open

# Recover UAT
uvicorn uat.api:app --host 127.0.0.1 --port 8181 &

# Wait for recovery (should auto-heal)
sleep 30

# Verify closed
curl -I http://127.0.0.1:8014/traces | grep X-Mode
# Expected: X-Mode: real
```

**Simulate**:
- UAT down for 2 minutes → fallback + recover
- Athena down → /chat degrades, /traces unaffected
- Bridge restart → no data loss, app reconnects

**Exit Criteria**: Zero manual intervention, app never hard-crashes.

---

### Day 5 – Load Sanity
**Objective**: Sustained load doesn't degrade performance.

```bash
# 5-minute sustained load (200 req/min)
# Install hey if needed: brew install hey

hey -z 5m -q 3.33 -c 10 http://127.0.0.1:8014/traces

# Check p95 in output
# Expected: p95 < 250ms

# Small chat load
for i in {1..100}; do
  curl -s -X POST http://127.0.0.1:8014/chat \
    -H 'content-type: application/json' \
    -d '{"text":"quick test"}' &
done
wait

# Check bridge logs
tail -n 100 /tmp/bridge_8014.log | grep ERROR
# Expected: 0 errors
```

**Exit Criteria**: p95 < 250ms under load, no errors.

---

### Day 6 – CI Discipline
**Objective**: Make integration tests mandatory.

#### Update Branch Protection
```bash
# GitHub CLI
gh api repos/:owner/:repo/branches/main/protection -X PUT -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]=integration-tests-mock \
  -f required_status_checks[contexts][]=integration-tests-real
```

#### Or via GitHub UI:
1. Settings → Branches → main → Edit
2. Check "Require status checks to pass"
3. Select: `integration-tests-mock`, `integration-tests-real`

**Exit Criteria**: No PR merges without green integration tests.

---

### Day 7 – Debrief & Tighten SLO
**Objective**: Learn from week 1, set tighter budgets.

#### Collect Week 1 Metrics
```bash
# If you have Prometheus/Grafana
# Export p50/p95/p99 for past 7 days

# Or manual:
grep "latency_ms" /tmp/bridge_8014.log | awk '{sum+=$NF; if($NF>max)max=$NF} END {print "avg:",sum/NR,"max:",max}'
```

#### Update SLO if Stable
If p95 is consistently < 50ms:
```python
# tests/test_integration.py
def test_latency_slo_traces(bridge):
    # ... existing code ...
    p95 = sorted(latencies)[int(0.95 * len(latencies)) - 1]
    assert p95 < 150, f"p95 latency {p95}ms exceeds tightened SLO 150ms"  # was 250ms
```

#### Team Retrospective
- What broke? (hopefully nothing)
- What was confusing? (documentation gaps)
- What do we wish we had? (metrics, alerts)
- What surprised us? (performance, load patterns)

**Exit Criteria**: SLO tightened, learnings documented, next sprint planned.

---

## 🛠️ Operational Shortcuts

### One-Command Operations
```bash
# Full real mode startup
make real-up

# Full shutdown
make real-down

# Quick acceptance test
make smoke

# Full test suite
make test-all

# Bridge logs
make logs

# Check breaker state
make status
```

### Manual Commands
```bash
# Health checks
curl -I http://127.0.0.1:8014/health | grep "X-Mode\|X-Breaker"
curl http://127.0.0.1:8181/health
curl http://127.0.0.1:8090/health

# Trace validation
curl -s http://127.0.0.1:8014/traces | jq '.[0]'
curl -s http://127.0.0.1:8014/traces | jq 'length'  # Expected: 170+

# Chat smoke
curl -X POST http://127.0.0.1:8014/chat -H 'content-type: application/json' -d '{"text":"ping"}' | jq .
```

---

## 🚨 "If It Breaks" Cheatsheet

### 401s Everywhere
**Symptom**: Bridge, UAT, Athena all returning 401.

**Diagnosis**:
```bash
# Check token env vars
echo $UAT_TOKEN $ATH_TOKEN
# Should be set and non-empty

# Check bridge logs
tail -n 50 /tmp/bridge_8014.log | grep 401
```

**Fix**:
```bash
# Re-export tokens
export UAT_TOKEN=<correct-token>
export ATH_TOKEN=<correct-token>

# Restart bridge
make bridge-down
make bridge-up
```

---

### mock_mode=true Unexpectedly
**Symptom**: Headers show `X-Mode: mock` when you expect real.

**Diagnosis**:
```bash
# Check if old bridge process still running
lsof -iTCP:8014 -sTCP:LISTEN
```

**Fix**:
```bash
# Nuclear option
make bridge-down
lsof -ti:8014 | xargs -r kill -9

# Restart with correct env
USE_MOCK=0 make bridge-up

# Verify
curl -I http://127.0.0.1:8014/health | grep X-Mode
```

---

### Decode Errors in Swift
**Symptom**: App crashes with JSON decode error.

**Diagnosis**:
```bash
# Check contract version
curl http://127.0.0.1:8014/contract | jq .version

# Compare to app expectation (in Swift code)
```

**Fix**:
1. If contract version mismatched, update `TraceDTO` in Swift
2. If schema changed, update both sides
3. Add forward compatibility (ignore unknown fields)

---

### Latency Spike
**Symptom**: p95 > 500ms, users complaining of slowness.

**Diagnosis**:
```bash
# Check breaker state
curl -I http://127.0.0.1:8014/health | grep X-Breaker

# If open, check backends
curl http://127.0.0.1:8181/health  # UAT
curl http://127.0.0.1:8090/health  # Athena
```

**Fix**:
```bash
# If backends are slow/down, flip to mock
make bridge-down
USE_MOCK=1 make bridge-up

# Investigate backend issue
# Once fixed, flip back
make bridge-down
USE_MOCK=0 make bridge-up
```

---

### Breaker Won't Close
**Symptom**: Breaker stuck open, won't recover to real mode.

**Diagnosis**:
```bash
# Check backend health
curl http://127.0.0.1:8181/health
curl http://127.0.0.1:8090/health

# Check bridge logs for repeated failures
grep "circuit" /tmp/bridge_8014.log | tail -n 20
```

**Fix**:
1. Ensure backends are actually healthy (200s consistently)
2. Restart bridge to reset breaker state
3. If backends are flaky, increase failure threshold in `bridge.py`

---

## 📋 Nice-to-Have (P2)

### Rate-Limit Metrics
Add to `bridge.py`:
```python
RATE_LIMIT_HITS = Counter('bridge_rate_limit_hits_total', 'Rate limit 429s', ['endpoint'])

@app.post("/chat")
def chat(...):
    # ... existing code ...
    if rate_limited:
        RATE_LIMIT_HITS.labels(endpoint="/chat").inc()
        return Response(status_code=429, headers={"Retry-After": "60"})
```

Expose in Grafana: 429 rate, retry-after histogram.

---

### Idempotency on /chat
Add to `bridge.py`:
```python
from cachetools import TTLCache

idempotency_cache = TTLCache(maxsize=1000, ttl=300)  # 5 min window

@app.post("/chat")
def chat(request: Request, body: ChatRequest):
    idem_key = request.headers.get("x-idempotency-key")
    if idem_key and idem_key in idempotency_cache:
        return idempotency_cache[idem_key]  # return cached response

    response = process_chat(body)
    if idem_key:
        idempotency_cache[idem_key] = response
    return response
```

Uncomment tests in `test_integration.py` → verify.

---

### Canary Flag
Add canary mode for partial rollout:
```python
@app.get("/mode")
def set_mode(target: str = "real"):
    global CANARY_MODE
    if target == "canary":
        CANARY_MODE = 0.1  # 10% real, 90% mock
    elif target == "real":
        CANARY_MODE = 1.0
    return {"canary_mode": CANARY_MODE}
```

Use in routing:
```python
if random.random() < CANARY_MODE:
    return real_backend()
else:
    return mock_backend()
```

---

## 🎓 Key Learnings

### What Made This Work
1. **Mock/Real Toggle**: Zero-code cutover, instant rollback.
2. **Circuit Breaker**: Graceful degradation, no hard failures.
3. **Observability Headers**: Debugging in 10 seconds, not 10 minutes.
4. **Integration Tests**: 48 automated guards prevent regressions.
5. **One-Command Ops**: `make real-up`, `make smoke`, `make real-down`.

### What to Avoid
1. **Guessing Environment State**: Always check headers, logs, ports.
2. **Manual Token Entry**: Use env vars, avoid copy-paste errors.
3. **Skipping Rollback Drills**: Practice = muscle memory.
4. **Ignoring Slow Tests**: p95 creep is the canary in the coal mine.

---

## ✅ Final Verification (Run Now)

```bash
# 1. Full stack up
./scripts/real_up.sh

# 2. Acceptance test
./scripts/acceptance_test.sh

# 3. Contract validation
cd AI-Projects/universal-ai-tools
pytest tests/test_contract.py -v

# 4. Integration suite
pytest tests/test_integration.py -v -m "not slow"

# 5. App smoke
API_BASE=http://127.0.0.1:8014 QA_MODE=0 swift run

# 6. Observability check
curl -I http://127.0.0.1:8014/health | grep "X-Mode\|X-Breaker"

# 7. Rollback drill
make bridge-down
USE_MOCK=1 make bridge-up
./scripts/acceptance_test.sh
```

**Expected**: All green ✅

---

## 🏆 Ship Criteria (All Met)

- [x] Tag pushed: `bridge-1.0.0`
- [x] Acceptance tests pass (mock + real)
- [x] Contract tests pass
- [x] Integration tests pass (25+)
- [x] App loads real traces (170+)
- [x] Breaker works (fail + recover)
- [x] Rollback < 30 seconds
- [x] Observability headers present
- [x] Auth enforced (401 on bad token)
- [x] CI automated (mock + real matrix)
- [x] Documentation complete (this file)
- [x] 7-day plan documented
- [x] Runbooks ready

---

## 🚀 **READY TO SHIP**

**Status**: 🟢 GREEN
**Risk**: 🟢 LOW
**Rollback**: 🟢 < 30s
**Coverage**: 🎯 HIGH (48 guards)
**Confidence**: 💯 MAXIMUM

**Next**: Run final verification above, then:
```bash
# Ship it
echo "🚀 Shipped bridge-1.0.0 on $(date)" >> SHIPLOG.md
git add SHIPLOG.md GO_LIVE_GUIDE.md
git commit -m "docs: add go-live guide for bridge-1.0.0"
git push
```

**Post-Ship**: Follow 7-day plan, watch metrics, sleep well. 🍾
