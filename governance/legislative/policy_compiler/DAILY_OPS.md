# 📅 Daily Operations Checklist

**Quick reference for daily operations**

---

## 🌅 Morning Startup (5 minutes)

### 1. Start Services
```bash
cd ~/Documents/GitHub
make real-up
```

**Wait**: 5 seconds for services to initialize

### 2. Health Check
```bash
make status
```

**Expected**:
- Bridge: 🟢 UP
- UAT: 🟢 UP
- Athena: 🟢 UP
- Mode: real
- Breaker: closed
- Traces: 170+

### 3. Smoke Test
```bash
make smoke
```

**Expected**: All tests pass ✅

### 4. Launch App
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 swift run
```

**Verify in UI**:
- Footer shows: `API=8014`, `mode=real`, `breaker=closed`
- Cmd+Shift+T loads trace panel with 170+ traces
- Provider Inspector shows UAT route

---

## 🕐 Hourly Checks (1 minute)

### Quick Status
```bash
make status
```

### Check Logs for Errors
```bash
tail -n 50 /tmp/bridge_8014.log | grep -i error
```

**Expected**: No errors (or only expected/handled errors)

### Latency Spot Check
```bash
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://127.0.0.1:8014/traces
done | awk '{if($1>0.25)print "⚠️  Slow:",$1; s+=$1} END {print "avg:",s/NR}'
```

**Expected**: avg < 0.15s, no individual > 0.25s

---

## 🌆 End of Day (3 minutes)

### 1. Check Error Rate
```bash
grep -c error /tmp/bridge_8014.log | awk '{if($1>10)print "⚠️  ",$1,"errors today"; else print "✅ "$1" errors (acceptable)"}'
```

### 2. Verify Breaker State
```bash
curl -I http://127.0.0.1:8014/health | grep X-Breaker
```

**Expected**: `X-Breaker: closed`

### 3. Check Trace Count
```bash
curl -s http://127.0.0.1:8014/traces | jq 'length'
```

**Expected**: Stable at 170+ (unless you've added more)

### 4. Review Logs (optional)
```bash
tail -n 100 /tmp/bridge_8014.log | less
```

Look for:
- Unusual patterns
- Repeated errors
- Performance anomalies

### 5. Backup Status (if nightly backup configured)
```bash
ls -lht backups/uat_traces_*.json | head -n 1
```

**Expected**: Recent backup from last night

---

## 📊 Weekly Review (15 minutes)

### Monday Morning

#### 1. Review Last Week's Metrics
```bash
# If you have Prometheus/Grafana
# Open dashboard: http://localhost:3000

# Or manual log analysis:
grep "latency_ms" /tmp/bridge_8014.log | awk '{sum+=$NF; if($NF>max)max=$NF} END {
  print "Last week:"
  print "  avg latency:", sum/NR "ms"
  print "  max latency:", max "ms"
  print "  total requests:", NR
}'
```

#### 2. Check for Tech Debt
```bash
grep -r "TODO\|FIXME\|HACK" AI-Projects/universal-ai-tools/{bridge,uat,athena}/ | wc -l
```

**Goal**: Trending down or stable

#### 3. Review Integration Test Pass Rate
```bash
# Check last 10 CI runs
gh run list --workflow=integration_tests.yml --limit=10
```

**Expected**: All green ✅

#### 4. Update SHIPLOG.md
```bash
echo "## Week of $(date +%Y-%m-%d)" >> SHIPLOG.md
echo "- Uptime: X%" >> SHIPLOG.md
echo "- p95 latency: Xms" >> SHIPLOG.md
echo "- Error rate: X%" >> SHIPLOG.md
echo "- Notable events: [describe any incidents]" >> SHIPLOG.md
echo "" >> SHIPLOG.md
```

---

## 🚨 Incident Response

### When Things Go Wrong

#### Symptoms: Services Won't Start
```bash
# 1. Check for port conflicts
lsof -iTCP:8014,8181,8090 -sTCP:LISTEN

# 2. Kill squatters
lsof -ti:8014,8181,8090 | xargs -r kill -9

# 3. Retry
make real-up
```

#### Symptoms: High Latency (p95 > 500ms)
```bash
# 1. Check breaker state
curl -I http://127.0.0.1:8014/health | grep X-Breaker

# 2. If open, check backends
curl http://127.0.0.1:8181/health
curl http://127.0.0.1:8090/health

# 3. If backends are down, flip to mock temporarily
make bridge-down
USE_MOCK=1 make bridge-up

# 4. Investigate backend issue
# 5. Once fixed, flip back
make bridge-down
USE_MOCK=0 make bridge-up
```

#### Symptoms: 401 Errors
```bash
# 1. Verify tokens
echo $UAT_TOKEN $ATH_TOKEN

# 2. Re-export if missing
export UAT_TOKEN=<token>
export ATH_TOKEN=<token>

# 3. Restart bridge
make bridge-down
make bridge-up

# 4. Verify
./scripts/acceptance_test.sh
```

#### Symptoms: Bridge Stuck in Mock Mode
```bash
# 1. Kill all bridge processes
make bridge-down
lsof -ti:8014 | xargs -r kill -9

# 2. Start fresh with correct env
USE_MOCK=0 make bridge-up

# 3. Verify mode
curl -I http://127.0.0.1:8014/health | grep X-Mode
```

---

## 📈 Performance Monitoring

### Daily Latency Snapshot
Create a file: `~/bin/daily-latency-check.sh`
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
LOG="/tmp/bridge_8014.log"

echo "=== Latency Report: $DATE ===" >> ~/latency-history.txt
grep "latency_ms" $LOG | awk '{sum+=$NF; count++; if($NF>max)max=$NF} END {
  p95_idx = int(count * 0.95)
  print "  Requests:", count
  print "  Avg:", sum/count "ms"
  print "  Max:", max "ms"
}' >> ~/latency-history.txt
echo "" >> ~/latency-history.txt
```

Run daily:
```bash
~/bin/daily-latency-check.sh
```

### Weekly Trend Analysis
```bash
tail -n 70 ~/latency-history.txt | grep -A3 "==="
```

---

## 🎯 SLO Tracking

### Current SLOs
- **Availability**: > 99.9%
- **p95 Latency**: < 250ms
- **Error Rate**: < 0.1%
- **Breaker Uptime**: > 99% (closed state)

### Daily SLO Check
```bash
# Add to your daily script
~/bin/check-slo.sh
```

```bash
#!/bin/bash
# ~/bin/check-slo.sh

# Latency check
LATENCY=$(for i in {1..100}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://127.0.0.1:8014/traces
done | sort -n | awk 'NR==95 {print $1}')

# Error check
ERRORS=$(tail -n 1000 /tmp/bridge_8014.log | grep -c error)
TOTAL=$(tail -n 1000 /tmp/bridge_8014.log | wc -l)
ERROR_RATE=$(echo "scale=4; $ERRORS / $TOTAL" | bc)

# Breaker check
BREAKER=$(curl -sI http://127.0.0.1:8014/health | grep -i x-breaker | awk '{print $2}')

echo "=== SLO Check: $(date) ==="
echo "p95 Latency: ${LATENCY}s (SLO: < 0.25s)"
echo "Error Rate: ${ERROR_RATE} (SLO: < 0.001)"
echo "Breaker: ${BREAKER} (SLO: closed)"

# Alert if SLO violated
if (( $(echo "$LATENCY > 0.25" | bc -l) )); then
  echo "⚠️  ALERT: Latency SLO violated!"
fi

if (( $(echo "$ERROR_RATE > 0.001" | bc -l) )); then
  echo "⚠️  ALERT: Error rate SLO violated!"
fi

if [ "$BREAKER" != "closed" ]; then
  echo "⚠️  ALERT: Breaker not closed!"
fi
```

---

## 🔐 Security Checks

### Weekly Security Audit (Fridays)

#### 1. Check for Leaked Secrets
```bash
grep -rE '(Bearer|token|secret|password).{0,50}' /tmp/*.log | grep -v '***'
```

**Expected**: Empty or only redacted

#### 2. Verify Token Rotation Works
```bash
# Generate test token
TEST_TOKEN=$(openssl rand -base64 32)

# Update and restart
export UAT_TOKEN=$TEST_TOKEN
make bridge-down
make bridge-up

# Verify (should fail with 401)
curl http://127.0.0.1:8014/traces

# Restore real token
export UAT_TOKEN=<real-token>
make bridge-down
make bridge-up
```

#### 3. Review Access Logs
```bash
grep "401\|403" /tmp/bridge_8014.log | tail -n 20
```

Look for:
- Unusual patterns
- Repeated failures from same source
- Brute force attempts

---

## 📚 Documentation Updates

### When to Update Docs

**Add to SHIPLOG.md**:
- New releases/tags
- Major incidents
- SLO violations
- Configuration changes

**Update GO_LIVE_GUIDE.md**:
- New operational procedures
- Lessons learned from incidents
- Updated SLOs
- New tooling

**Update QUICK_SHIP_REF.md**:
- New one-liners discovered
- Frequently used commands
- Common troubleshooting steps

---

## ✅ Daily Checklist Summary

```
Morning:
[ ] make real-up
[ ] make status (all green)
[ ] make smoke (pass)
[ ] Launch app and verify UI

Hourly:
[ ] make status
[ ] Check logs for errors

End of Day:
[ ] Review error count
[ ] Verify breaker state
[ ] Check trace count
[ ] (Optional) Review logs

Weekly (Monday):
[ ] Review last week's metrics
[ ] Check tech debt trend
[ ] Review CI pass rate
[ ] Update SHIPLOG.md

Weekly (Friday):
[ ] Security audit
[ ] Token rotation test
[ ] Review access logs
```

---

**Last Updated**: 2025-10-12
**Version**: bridge-1.0.0
**Owner**: Platform Team

🎯 **Boring operations = successful operations**
