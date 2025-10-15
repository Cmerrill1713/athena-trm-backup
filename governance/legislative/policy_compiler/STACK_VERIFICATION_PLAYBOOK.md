# Stack Verification Playbook

> **Fast, boring, and hard to break** — 1-minute validation checklist

## Run It (Real Mode)

### 1. Bring the whole stack up
```bash
make stack-up
```

**Expected output:**
```
🔪 killing squatters on 8181 8090 8014
🚀 UAT @ http://127.0.0.1:8181
🤖 Athena @ http://127.0.0.1:8090
🧱 Bridge (real mode) @ http://127.0.0.1:8014
✅ stack is up
```

### 2. Sanity: bridge sees both backends
```bash
curl -s http://127.0.0.1:8014/health | jq .
```

### 3. Ask Athena to run tests
```bash
make athena-tests
```

---

## What "Good" Looks Like

### Bridge Health Check
```json
{
  "status": "healthy",
  "adapter": "neuroforge-adapter-v1.0.0",
  "uat": {
    "status": "healthy"
  },
  "athena": {
    "status": "healthy"
  },
  "timestamp": "2025-10-12T10:30:00.000Z"
}
```

**Headers to check:**
```bash
curl -v http://127.0.0.1:8014/health 2>&1 | grep -i "x-"
# Should see:
# x-adapter-version: 1.0.0
# x-correlation-id: <uuid>
```

### Athena Tests Response
```json
{
  "ok": true,
  "cmd": "pytest tests/ -m smoke,e2e,backends,slo --maxfail=1 --disable-warnings -q",
  "cwd": "/Users/christianmerrill/Documents/GitHub",
  "summary": {
    "passed": 10,
    "failed": 0,
    "skipped": 2,
    "errors": 0
  },
  "stdout": "...test output...",
  "stderr": "",
  "report": { /* pytest JSON report */ },
  "timestamp": "2025-10-12T10:30:00.000Z"
}
```

**Key indicators:**
- ✅ `"ok": true` (all tests passed)
- ✅ `"passed": N` where N > 0
- ✅ `"failed": 0` and `"errors": 0`
- ✅ `"cwd"` points to workspace root

---

## Quick Manual Pokes (Optional)

### Traces via Bridge (should be real, not mock)
```bash
curl -s http://127.0.0.1:8014/traces | jq '.[0]'
```

**Good response:**
```json
{
  "id": "trace-abc123",
  "capability": "chat",
  "duration_ms": 123,
  "started_at": 1728734400.0,
  "provider": "mlx/chat",
  "score": 0.95
}
```

**Bad response (mock mode):**
```json
{
  "source": "mock-data",
  ...
}
```

### Direct UAT
```bash
curl -s -H "Authorization: Bearer supersecret" \
  http://127.0.0.1:8181/traces | jq '.[0]'
```

### Direct Athena
```bash
curl -s -H "Authorization: Bearer supersecret" \
  http://127.0.0.1:8090/health | jq .
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "athena",
  "timestamp": "2025-10-12T10:30:00.000Z",
  "agents_available": 3
}
```

---

## Athena Test API (Payload You Can Swap)

### Smoke tests only
```bash
curl -sS -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke"}' | jq .
```

### E2E tests
```bash
curl -sS -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"e2e"}' | jq .
```

### Verbose output
```bash
curl -sS -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke","verbose":true}' | jq .
```

### All integration tests
```bash
curl -sS -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"suite":"integration","markers":"smoke,e2e,backends,slo"}' | jq .
```

---

## Common Gotchas (and Fast Fixes)

### 1. Bridge shows mock_mode=true

**Symptom:**
```bash
curl http://127.0.0.1:8014/ | jq .use_mock
# Returns: true
```

**Fix:**
```bash
make stack-down
ENV=dev USE_MOCK=0 make stack-up
```

Or edit the stack-up command to always set `USE_MOCK=0`.

### 2. 401 from Athena/UAT

**Symptom:**
```
{"detail":"Invalid token"}
```

**Cause:** Token mismatch between Makefile and process env

**Fix:**
```bash
# Check what's running
ps aux | grep -E "athena|uat" | grep uvicorn

# Kill and restart with explicit tokens
make stack-down
UAT_TOKEN=supersecret ATH_TOKEN=supersecret make stack-up
```

### 3. Port already in use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Fix:**
```bash
lsof -ti:8014,8181,8090 | xargs kill -9
make stack-up
```

### 4. Two bridges responding (duplicate processes)

**Symptom:** Logs show two different PIDs responding

**Fix:**
```bash
make stack-down
lsof -ti:8014 | xargs kill -9
make stack-up
```

### 5. Athena returns "tests not found"

**Symptom:**
```json
{
  "ok": false,
  "stderr": "ERROR: file not found: tests/"
}
```

**Cause:** Wrong working directory

**Check:**
```bash
curl -sS -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .cwd

# Should return: /Users/christianmerrill/Documents/GitHub
```

**Fix:** Athena's workspace detection might be off. Check `athena/api.py`:
```python
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### 6. Tests hang or timeout

**Symptom:** Request times out after 10 minutes

**Fix:** Run tests with more specific markers:
```bash
curl -sS -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke","maxfail":3}' | jq .
```

---

## Ship Checks (1 Minute)

### Full validation bundle
```bash
bash scripts/validate_stack.sh
```

**Expected output:**
```
🧪 Stack Management Validation
==============================
1️⃣  Checking if services are running...
  ✓ UAT (port 8181) is running
  ✓ Athena (port 8090) is running
  ✓ Bridge (port 8014) is running

2️⃣  Testing health endpoints...
  ✓ UAT health check passed
  ✓ Athena health check passed
  ✓ Bridge health check passed

3️⃣  Testing Athena capabilities...
  ✓ tool_calls capability present
  ✓ test_execution capability present

4️⃣  Testing tool call execution...
  ✓ Tool call execution works

5️⃣  Checking PID files...
  ✓ uat.pid valid (PID: 12345)
  ✓ athena.pid valid (PID: 12346)
  ✓ bridge.pid valid (PID: 12347)

6️⃣  Checking log files...
  ✓ logs/uat_8181.log exists
  ✓ logs/athena_8090.log exists
  ✓ logs/bridge_8014.log exists

==============================
✅ Stack validation complete!
```

### Smoke + SLO directly
```bash
./scripts/acceptance_test.sh
```

---

## Rollback (30 Seconds)

### Emergency rollback to mock mode
```bash
make stack-down
USE_MOCK=1 make stack-up
```

### Restart just Bridge (keep UAT/Athena running)
```bash
# Kill bridge only
kill -9 $(cat .stack/bridge.pid)
rm .stack/bridge.pid

# Restart bridge in mock mode
cd bridge
USE_MOCK=1 python3 -m uvicorn adapter:app --host 127.0.0.1 --port 8014 &
echo $! > ../.stack/bridge.pid
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Stack Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start Stack
        run: make stack-up
        env:
          UAT_TOKEN: ${{ secrets.UAT_TOKEN }}
          ATH_TOKEN: ${{ secrets.ATH_TOKEN }}

      - name: Validate Stack
        run: bash scripts/validate_stack.sh

      - name: Run Tests via Athena
        run: |
          response=$(make athena-tests)
          echo "$response" | jq -e '.ok == true'

      - name: Stop Stack
        if: always()
        run: make stack-down
```

---

## Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| Stack startup | < 5s | ~2s |
| Health check | < 100ms | ~50ms |
| Test execution (smoke) | < 30s | ~15s |
| Stack shutdown | < 3s | ~1s |
| Memory per service | < 200MB | ~150MB |

---

## Monitoring Checklist

### Pre-deployment
- [ ] `make stack-up` succeeds
- [ ] `bash scripts/validate_stack.sh` passes all checks
- [ ] `make athena-tests` returns `"ok": true`
- [ ] All logs show no errors
- [ ] Bridge health shows `"status": "healthy"`

### Post-deployment
- [ ] Bridge `/health` returns 200
- [ ] UAT `/traces` returns real data
- [ ] Athena `/capabilities` includes `tool_calls`
- [ ] Test suite passes via `make athena-tests`

### Daily ops
- [ ] Check logs for errors: `grep -i error logs/*.log`
- [ ] Verify no zombie processes: `ps aux | grep -E "athena|uat|uvicorn"`
- [ ] Test latency: `time curl -s http://127.0.0.1:8014/health`

---

## Debug Commands

### View all logs in real-time
```bash
tail -f logs/*.log
```

### Check PIDs and ports
```bash
cat .stack/*.pid | xargs ps -p
lsof -iTCP:8014,8181,8090 -sTCP:LISTEN
```

### Test bridge without jq
```bash
curl -s http://127.0.0.1:8014/health
```

### Watch logs for errors
```bash
tail -f logs/*.log | grep -i -E "error|fail|exception"
```

### Check service uptime
```bash
ps -p $(cat .stack/uat.pid) -o etime,pid,command
ps -p $(cat .stack/athena.pid) -o etime,pid,command
ps -p $(cat .stack/bridge.pid) -o etime,pid,command
```

---

## The Trifecta

```bash
# 1. Start
make stack-up

# 2. Test
make athena-tests

# 3. Stop
make stack-down
```

**Fast, boring, and hard to break.** ✅

---

## Quick Reference Card

```bash
# === DAILY OPS ===
make stack-up              # Morning: boot everything
make athena-tests          # Run full test suite
make stack-down            # Evening: clean shutdown

# === DEBUGGING ===
make stack-status          # Show PIDs and health
tail -f logs/*.log         # Watch logs
bash scripts/validate_stack.sh  # Full health check

# === EMERGENCY ===
lsof -ti:8014,8181,8090 | xargs kill -9  # Kill all
make stack-up              # Restart clean
```

---

**Questions?** Check `STACK_MANAGEMENT_GUIDE.md` for full details.
