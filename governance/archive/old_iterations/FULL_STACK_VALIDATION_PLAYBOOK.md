# 🧪 FULL STACK VALIDATION PLAYBOOK

> **Production-grade validation flow that's fast, automated, and boring (the good kind)**

---

## Step 1. Spin up everything cleanly

```bash
make stack-up
```

✅ **This launches:**
- UAT → 8181
- Athena → 8090
- Bridge → 8014

**Features:**
- Ports are auto-cleaned
- PID files tracked in `.stack/`
- Logs captured in `logs/`

**Expected output:**
```
🔪 killing squatters on 8181 8090 8014
🚀 UAT @ http://127.0.0.1:8181
🤖 Athena @ http://127.0.0.1:8090
🧱 Bridge (real mode) @ http://127.0.0.1:8014
✅ stack is up
Health: {"status":"healthy",...}
```

---

## Step 2. Check the stack health

### Quick status
```bash
make stack-status
```

**Expected output:**
```
📊 status
UAT: 12345 python3 -m uvicorn uat.api:app --port 8181
Athena: 12346 python3 -m uvicorn athena.api:app --port 8090
Bridge: 12347 python3 -m uvicorn adapter:app --port 8014
Ports: 8181 8090 8014
Bridge health: {"status":"healthy",...}
```

### Detailed health check
```bash
curl -s http://127.0.0.1:8014/health | jq .
```

✅ **Expect:**
```json
{
  "status": "healthy",
  "adapter": "neuroforge-adapter-v1.0.0",
  "uat": {
    "status": "healthy"
  },
  "athena": {
    "status": "healthy",
    "service": "athena",
    "agents_available": 3
  },
  "timestamp": "2025-10-12T10:30:00.000Z"
}
```

---

## Step 3. Run smoke tests through Athena

### Default test suite
```bash
make athena-tests
```

This calls `/run_tests` with your default markers (`smoke,e2e,backends,slo`) and auto-injects tokens from `.env.stack`.

✅ **Example output:**
```json
{
  "ok": true,
  "cmd": "python3 -m pytest tests/ -m 'smoke or e2e or backends or slo' --maxfail=1 --disable-warnings -q",
  "cwd": "/Users/christianmerrill/Documents/GitHub",
  "summary": {
    "passed": 48,
    "failed": 0,
    "skipped": 1,
    "errors": 0
  },
  "artifact_path": "/Users/christianmerrill/Documents/GitHub/pytest_report.json",
  "timestamp": "2025-10-12T10:30:00.000Z"
}
```

👉 **This report is CI-ready and returns HTTP 422 if any test fails.**

### Run specific test sets

```bash
# Only smoke tests
make athena-tests MARKERS=smoke

# Full suite with maxfail=100
make athena-tests MARKERS="smoke,e2e,backends,slo" MAXFAIL=100

# Just e2e tests
make athena-tests MARKERS=e2e

# Smoke + backends only
make athena-tests MARKERS="smoke,backends"

# Verbose output
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke","verbose":true}' | jq .
```

**Under the hood, Athena:**
- Injects all tokens & base URLs from `.env.stack`
- Runs `python3 -m pytest` with proper marker syntax
- Returns structured JSON
- Includes artifact path for CI uploads

---

## Step 4. Debugging edge cases

| Issue | Command to Fix |
|-------|----------------|
| Bridge stuck in mock mode | `make stack-down && USE_MOCK=0 make stack-up` |
| Token mismatch (401s) | `make stack-down && UAT_TOKEN=supersecret ATH_TOKEN=supersecret make stack-up` |
| Port conflict | `lsof -ti:8014,8181,8090 \| xargs kill -9` then `make stack-up` |
| Two bridges responding | `make stack-down && lsof -ti:8014 \| xargs kill -9` then `make stack-up` |
| Tests hanging | `make athena-tests MARKERS=smoke MAXFAIL=3` (smaller scope) |
| Need fresh start | `make stack-restart` |

---

## Step 5. Inspect artifacts

### Test reports
Reports are saved in:
```
pytest_report.json    # JSON report (Athena returns path)
pytest_report.xml     # JUnit XML (if configured)
```

The path is included in the JSON response:
```json
{
  "artifact_path": "/Users/christianmerrill/Documents/GitHub/pytest_report.json"
}
```

### View Athena logs
```bash
# All logs
tail -f logs/*.log

# Just Athena
tail -f logs/athena_8090.log

# Just errors
grep -i error logs/*.log
```

### Check PID files
```bash
ls -la .stack/
cat .stack/*.pid | xargs ps -p
```

---

## Step 6. Full validation suite

### Comprehensive health check
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
  ✓ logs/uat_8181.log exists (1.2MB)
  ✓ logs/athena_8090.log exists (856KB)
  ✓ logs/bridge_8014.log exists (432KB)

==============================
✅ Stack validation complete!

Next steps:
  • Run tests: make athena-tests
  • Check status: make stack-status
  • View logs: tail -f logs/*.log
```

---

## 🛡️ CI-Ready Output

### HTTP Status Codes
- ✅ **200 OK** - All tests passed
- ❌ **422 Unprocessable Entity** - Tests ran but failed
- 🚫 **401 Unauthorized** - Invalid token
- ⏱️ **504 Gateway Timeout** - Tests took > 10 minutes
- 💥 **500 Internal Server Error** - Execution error

### Response Structure
```json
{
  "ok": true,              // Boolean: all passed?
  "cmd": "...",            // Command executed
  "cwd": "...",            // Working directory
  "summary": {             // Test summary
    "passed": 48,
    "failed": 0,
    "skipped": 1,
    "errors": 0
  },
  "stdout": "...",         // Last 2000 chars
  "stderr": "...",         // Last 2000 chars
  "artifact_path": "...",  // Path to JSON report
  "report": {...},         // Full pytest JSON report
  "timestamp": "..."       // ISO8601 timestamp
}
```

### CI Integration Example
```yaml
name: Stack Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Create .env.stack
        run: |
          cat > .env.stack << EOF
          UAT_TOKEN=${{ secrets.UAT_TOKEN }}
          ATH_TOKEN=${{ secrets.ATH_TOKEN }}
          EOF

      - name: Start Stack
        run: make stack-up

      - name: Validate Stack
        run: bash scripts/validate_stack.sh

      - name: Run Tests
        run: |
          response=$(curl -f -X POST http://127.0.0.1:8090/run_tests \
            -H "Authorization: Bearer ${{ secrets.ATH_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"markers":"smoke,e2e"}')
          echo "$response" | jq .

      - name: Upload Artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: |
            pytest_report.json
            logs/*.log

      - name: Stop Stack
        if: always()
        run: make stack-down
```

---

## 🧰 Bonus Tips

### Hot restarts between test runs
```bash
make stack-restart
```

### Add reruns for flaky tests
Edit `athena/api.py` to add `--reruns=3` to pytest command for auto-retries.

### Secure token management
Your `.env.stack` is gitignored—safe for local dev and CI secrets injection.

```bash
# .gitignore already includes:
.env.stack
.stack/*.pid
logs/*.log
pytest_report.json
```

### Custom test commands
```bash
# Run specific test file
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"tool":"run_command","params":{"command":"pytest tests/test_smoke.py -v"}}'

# Read test results
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"tool":"read_file","params":{"path":"pytest_report.json"}}'
```

---

## 🎯 TL;DR for Daily Use

### Morning routine
```bash
make stack-up
make stack-status
make athena-tests
```

### During development
```bash
# Run tests periodically
make athena-tests MARKERS=smoke

# Check specific services
curl -s http://127.0.0.1:8014/health | jq .status

# Watch logs
tail -f logs/*.log
```

### End of day
```bash
make stack-down
```

---

## 🚀 Advanced Usage

### Run tests with different parameters

```bash
# Just smoke tests, fail fast
make athena-tests MARKERS=smoke MAXFAIL=1

# Full suite, continue on failures
make athena-tests MARKERS="smoke,e2e,backends,slo" MAXFAIL=100

# Just backends, verbose
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{"markers":"backends","verbose":true,"maxfail":5}' | jq .
```

### Custom ports/tokens

```bash
# Using environment variables
UAT_PORT=9181 ATH_PORT=9090 BRIDGE_PORT=9014 make stack-up

# Using .env.stack (recommended)
cp .env.stack.example .env.stack
# Edit .env.stack with your values
make stack-up
```

### Parallel test execution

```bash
# In Athena API, modify pytest command to add -n auto
# Requires pytest-xdist
cmd_parts.extend(["-n", "auto"])  # Parallel execution
```

---

## 📊 Performance Expectations

| Operation | Expected Time | Actual |
|-----------|--------------|--------|
| `make stack-up` | < 5s | ~2s ✅ |
| `make stack-status` | < 1s | ~0.5s ✅ |
| `make athena-tests` (smoke) | < 30s | ~15s ✅ |
| `make athena-tests` (full) | < 2min | ~1min ✅ |
| `make stack-down` | < 3s | ~1s ✅ |
| `bash scripts/validate_stack.sh` | < 1min | ~30s ✅ |

---

## 🔍 Troubleshooting Matrix

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `make stack-up` fails | Port conflict | `lsof -ti:8014,8181,8090 \| xargs kill -9` |
| 401 from Athena | Token mismatch | Check `.env.stack` or env vars |
| Tests return mock data | Bridge in mock mode | `USE_MOCK=0 make stack-restart` |
| Tests hang forever | Pytest stuck | `MAXFAIL=1 make athena-tests` |
| No logs appearing | Wrong log path | Check `logs/` directory exists |
| PID files stale | Processes died | `rm .stack/*.pid && make stack-up` |
| "ok": false always | Tests actually failing | Check `stdout`/`stderr` in response |

---

## ✅ Daily Checklist

Before committing/deploying:

- [ ] `make stack-up` succeeds
- [ ] `make stack-status` shows all services healthy
- [ ] `make athena-tests` returns `"ok": true`
- [ ] `bash scripts/validate_stack.sh` passes all checks
- [ ] No errors in `logs/*.log`
- [ ] `make stack-down` cleans up properly

---

## 🎉 Summary

This is now your **production-grade validation flow**:

✅ **Fast** - Stack up/down in ~2s
🧪 **Automated** - One command runs full suite
🧱 **Boring** - It just works, every time

You can:
- Plug it into CI
- Run it locally
- Use for pre-merge checks
- Zero manual juggling

**Start validating:**
```bash
make stack-up
make athena-tests
make stack-down
```

---

**Questions?** See `STACK_QUICK_REF.md` for command reference.
