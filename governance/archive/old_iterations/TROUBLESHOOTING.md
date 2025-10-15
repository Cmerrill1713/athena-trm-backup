# Troubleshooting Guide - "If It Ever Breaks"

## Quick Diagnostics

```bash
# Check what's running
lsof -i:8181 -i:8090 -i:8014

# Check service health
curl -s http://127.0.0.1:8014/health | jq .
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/health | jq .
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8090/health | jq .

# Check mode
curl -s http://127.0.0.1:8014/ | jq '.mock_mode, .circuit_breaker'

# Check logs
tail -f /tmp/bridge_8014.log
tail -f /tmp/uat_8181.log
tail -f /tmp/athena_8090.log
```

---

## Common Issues & Fixes

### 🔴 401 Unauthorized Errors

**Symptom**: Bridge logs show 401 from UAT or Athena

**Root Cause**: Token mismatch

**Fix**:
```bash
# Verify tokens are set
echo "UAT_TOKEN: $UAT_TOKEN"
echo "ATH_TOKEN: $ATH_TOKEN"

# Restart with correct tokens
./scripts/real_down.sh
UAT_TOKEN=supersecret ATH_TOKEN=supersecret ./scripts/real_up.sh
```

**Prevention**: Store tokens in environment or .env file

---

### 🔴 JSON Decode Errors in App

**Symptom**: Swift app shows decode errors for traces

**Root Cause**: Schema mismatch between UAT and app TraceDTO

**Diagnosis**:
```bash
# Check UAT trace schema
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/traces | jq '.[0]'

# Check what bridge returns
curl -s http://127.0.0.1:8014/traces | jq '.traces[0]'
```

**Fix**: Update TraceDTO in Swift app to match UAT schema

**Prevention**: Add contract test that validates schema

---

### 🔴 Latency Spike / Slow Responses

**Symptom**: Requests taking > 250ms

**Diagnosis**:
```bash
# Check circuit breaker
curl -s http://127.0.0.1:8014/ | jq '.circuit_breaker'

# Check UAT latency
time curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/traces > /dev/null

# Check Athena latency
time curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8090/health > /dev/null
```

**Fix**:
```bash
# If circuit breaker is open:
# Option 1: Wait 30 seconds for auto-recovery
# Option 2: Flip to mock mode temporarily
make bridge-down
USE_MOCK=1 make bridge-up

# If backends are slow:
# Check logs for bottlenecks
grep "duration_ms" /tmp/uat_8181.log | tail -20
```

**Prevention**: Add latency alerting in Grafana

---

### 🔴 Port Already in Use

**Symptom**: Service fails to start with "Address already in use"

**Diagnosis**:
```bash
# Find what's on the port
lsof -i:8181  # or 8090, 8014
```

**Fix**:
```bash
# Kill the squatter
kill -9 $(lsof -ti:8181)

# Or use nuclear option for all ports
lsof -ti:8014,8181,8090 | xargs -r kill -9

# Restart
./scripts/real_up.sh
```

**Prevention**: Use `scripts/real_up.sh` which handles conflicts

---

### 🔴 Circuit Breaker Stuck Open

**Symptom**: Bridge shows `circuit_breaker.is_open: true`

**Root Cause**: Backend failures accumulated

**Diagnosis**:
```bash
# Check failure count
curl -s http://127.0.0.1:8014/ | jq '.circuit_breaker'

# Check backend health
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/health
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8090/health
```

**Fix**:
```bash
# If backends are healthy, wait 30 seconds for auto-recovery
sleep 30
curl -s http://127.0.0.1:8014/ | jq '.circuit_breaker.is_open'

# Or restart bridge to reset
make bridge-down
sleep 2
USE_MOCK=0 UAT_BASE=http://127.0.0.1:8181 ATHENA_BASE=http://127.0.0.1:8090 make bridge-up
```

**Prevention**: Monitor backend health proactively

---

### 🔴 No Traces Returned

**Symptom**: `/traces` returns empty list or error

**Diagnosis**:
```bash
# Check if UAT has data
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/traces | jq 'length'

# Check bridge source
curl -s http://127.0.0.1:8014/traces | jq '.source'
```

**Fix**:
```bash
# If UAT is empty, reseed
curl -s -X POST -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/seed

# Verify
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/traces | jq 'length'
```

**Prevention**: Backup trace data to `data/uat_traces.json`

---

### 🔴 Bridge Returns Mock Data in Real Mode

**Symptom**: `source: "mock-mode"` when `USE_MOCK=0`

**Root Cause**: Environment variable not set or old process still running

**Diagnosis**:
```bash
# Check if old bridge is running
ps aux | grep "python3 bridge.py"

# Check environment
curl -s http://127.0.0.1:8014/ | jq '.mock_mode'
```

**Fix**:
```bash
# Kill all bridge processes
pkill -f "python3 bridge.py"
make bridge-down

# Start fresh with explicit mode
cd AI-Projects/universal-ai-tools
USE_MOCK=0 UAT_BASE=http://127.0.0.1:8181 ATHENA_BASE=http://127.0.0.1:8090 \
UAT_TOKEN=supersecret ATH_TOKEN=supersecret \
python3 bridge.py > /tmp/bridge_8014.log 2>&1 &

# Verify
sleep 3
curl -s http://127.0.0.1:8014/ | jq '.mock_mode'
# Should return: false
```

**Prevention**: Always use `./scripts/real_up.sh` for clean starts

---

## Emergency Procedures

### Total System Restart
```bash
# Stop everything
./scripts/real_down.sh

# Wait for ports to clear
sleep 5

# Start everything fresh
./scripts/real_up.sh

# Verify
curl -s http://127.0.0.1:8014/ | jq '.mock_mode, .circuit_breaker'
```

### Rollback to Mock (Safe Mode)
```bash
# Immediate rollback
make bridge-down
USE_MOCK=1 make bridge-up

# Verify
curl -s http://127.0.0.1:8014/ | jq '.mock_mode'
# Should return: true
```

### Nuclear Option (Kill Everything)
```bash
# Kill all services
lsof -ti:8014,8181,8090 | xargs -r kill -9
pkill -f "uvicorn"
pkill -f "bridge.py"

# Clear PIDs
rm -f /tmp/bridge.pid

# Start fresh
./scripts/real_up.sh
```

---

## Health Checks

### Full System Check
```bash
#!/bin/bash
echo "🔍 System Health Check"
echo "====================="

# Bridge
echo -n "Bridge (8014): "
curl -sf http://127.0.0.1:8014/health > /dev/null && echo "✅ OK" || echo "❌ DOWN"

# UAT
echo -n "UAT (8181): "
curl -sf -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/health > /dev/null && echo "✅ OK" || echo "❌ DOWN"

# Athena
echo -n "Athena (8090): "
curl -sf -H "Authorization: Bearer supersecret" http://127.0.0.1:8090/health > /dev/null && echo "✅ OK" || echo "❌ DOWN"

# Mode
MODE=$(curl -s http://127.0.0.1:8014/ | jq -r '.mock_mode')
echo "Mode: $([ "$MODE" = "false" ] && echo "Real ✅" || echo "Mock ⚠️")"

# Circuit Breaker
BREAKER=$(curl -s http://127.0.0.1:8014/ | jq -r '.circuit_breaker.is_open')
echo "Breaker: $([ "$BREAKER" = "false" ] && echo "Closed ✅" || echo "Open ⚠️")"
```

---

## Escalation

If none of these fixes work:

1. **Gather diagnostics**:
   ```bash
   # Save all logs
   mkdir -p incident_logs
   cp /tmp/*_{8014,8181,8090}.log incident_logs/

   # Capture state
   curl -s http://127.0.0.1:8014/ > incident_logs/bridge_state.json
   lsof -i:8014,8181,8090 > incident_logs/ports.txt
   ```

2. **Rollback to safe state**:
   ```bash
   ./scripts/real_down.sh
   USE_MOCK=1 make bridge-up
   ```

3. **Create incident**:
   - Use `RUNBOOKS/POSTMORTEM.md` template
   - Include logs from `incident_logs/`
   - Document what was tried

---

**Last Updated**: 2025-10-12
**Owner**: Platform Team
**Quick Help**: See REAL_MODE_QUICK_REF.md
