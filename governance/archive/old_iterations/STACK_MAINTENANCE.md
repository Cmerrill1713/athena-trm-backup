# Stack Maintenance Guide 🔧

## When Things Get Weird — Your "Truth" Sources

### 1. `make truth` — Port + PID Fingerprint
**Use when:** Services won't start, tests fail mysteriously, or you suspect port conflicts.

```bash
make truth
```

**What it shows:**
- Which PIDs are listening on 8181, 8090, 8014
- Full process command lines
- Who's actually responding to health checks
- Which Python Athena is using for tests
- Actual pytest command being run

**Example output:**
```
UAT (8181):
  53191   python3 -m uvicorn uat.api:app --host 127.0.0.1 --port 8181

Athena (8090):
  63620   python3 -m uvicorn athena.api:app --host 127.0.0.1 --port 8090

Bridge (8014):
  55901   python3 -m uvicorn adapter:app --host 127.0.0.1 --port 8014

Health Check:
  HTTP/1.1 200 OK
  X-Mode: real
  X-Breaker: closed

Athena Test Runner:
  Python: python3
  CWD: /Users/christianmerrill/Documents/GitHub
  Cmd: python3 -m pytest tests/ -m smoke --maxfail=1 ...
```

### 2. `curl -I :8014/health` — Who's Answering?
**Use when:** You're not sure if you're talking to mock or real mode.

```bash
curl -sI http://127.0.0.1:8014/health | grep -E "HTTP|X-"
```

**What to check:**
- `HTTP/1.1 200 OK` → service is up
- `X-Mode: real` → using real backends (not mock)
- `X-Breaker: closed` → circuit breaker healthy

### 3. Athena Test Runner Args — Full Receipt
**Use when:** Tests aren't finding fixtures, wrong cwd, or env vars missing.

```bash
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke","env":{"DEBUG":"1"}}' \
  | jq '{cmd, cwd, env_passed: .report.environment}'
```

**What it shows:**
- Exact pytest command being run
- Working directory (should be repo root)
- Environment variables passed to subprocess

## Daily Dev Loop

### Fast Development Cycle
```bash
# Morning
make stack-up

# After code changes (10 seconds)
make athena-tests-smoke

# Before lunch / break
make athena-tests MARKERS="e2e,backends" MAXFAIL=20

# Before commit
make athena-tests

# End of day
make stack-down
```

### When Tests Fail

**Step 1: Check the stack**
```bash
make truth  # Are all services actually running?
```

**Step 2: Check logs**
```bash
tail -f /tmp/bridge_8014.log   # Bridge errors
tail -f /tmp/athena_8090.log   # Athena errors
tail -f /tmp/uat_8181.log      # UAT errors
```

**Step 3: Restart cleanly**
```bash
make stack-down
sleep 2
make stack-up
make athena-tests-smoke  # Verify it's working
```

**Step 4: Nuclear option**
```bash
make nuke-ports  # Kill everything on 8014/8090/8181
make stack-up
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start Stack
        run: make stack-up

      - name: Validate Stack
        run: make stack-validate

      - name: Run Full Suite
        run: make athena-tests MAXFAIL=100

      - name: Upload Test Artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: pytest_report.json

      - name: Shutdown Stack
        if: always()
        run: make stack-down
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | ✅ All tests passed | Deploy / merge |
| `1` | ❌ Tests failed | Review failures |
| `422` | 🔥 Config error | Fix setup |
| `504` | ⏱️ Timeout | Increase timeout or optimize tests |

### Artifacts for Debugging

**Pytest JSON Report:**
```bash
cat pytest_report.json | jq '.tests[] | select(.outcome=="failed")'
```

**Athena Response:**
```bash
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke"}' > athena_test_result.json
```

## Troubleshooting Cookbook

### "Port already in use"
```bash
make nuke-ports
# Or manually:
lsof -ti:8014,8090,8181 | xargs kill -9
```

### "401 Unauthorized" in tests
```bash
# Check tokens are being passed
make truth  # See Athena config
# Or manually verify:
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{"markers":"backends","env":{"UAT_TOKEN":"supersecret","ATH_TOKEN":"supersecret"}}'
```

### "No tests collected"
```bash
# Check cwd in Athena
make truth | grep "CWD:"
# Should be: /Users/christianmerrill/Documents/GitHub

# Verify tests exist
ls -la tests/interop/test_bridge.py
```

### "Tests hang / timeout"
```bash
# Check for stuck pytest processes
ps aux | grep pytest

# Kill and restart
pkill -9 pytest
make stack-restart
```

### "Wrong Python / imports fail"
```bash
# Check which Python Athena is using
make truth | grep "Python:"
# Should be: python3

# Verify pytest-json-report is installed
python3 -m pytest --help | grep json-report
```

### "Mock data when expecting real"
```bash
# Check Bridge mode
curl -sI http://127.0.0.1:8014/health | grep X-Mode
# Should show: X-Mode: real

# Check if USE_MOCK is set
env | grep USE_MOCK
# Should be empty or USE_MOCK=0
```

## Performance Benchmarks

| Operation | Expected Time | Threshold |
|-----------|--------------|-----------|
| `make stack-up` | < 10s | Fail if > 30s |
| `make athena-tests-smoke` | < 1s | Fail if > 5s |
| `make athena-tests-backends` | < 2s | Fail if > 10s |
| `make athena-tests` | < 30s | Fail if > 60s |
| `make stack-validate` | < 5s | Fail if > 15s |
| `make stack-down` | < 3s | N/A |

## Monitoring Commands

### Service Health Loop (1-liner)
```bash
while true; do
  echo "$(date): $(curl -s http://127.0.0.1:8014/health | jq -r .status) | $(curl -s http://127.0.0.1:8181/health | jq -r .status) | $(curl -s http://127.0.0.1:8090/health | jq -r .status)";
  sleep 5;
done
```

### Test Success Rate
```bash
# Run tests 10 times, count passes
for i in {1..10}; do
  make athena-tests-smoke 2>&1 | grep -q "Status: PASS" && echo "✅" || echo "❌"
done
```

### Port Activity
```bash
# Monitor connections to Bridge
lsof -i :8014 -r 2  # Refresh every 2 seconds
```

## Best Practices

### ✅ DO
- Run `make truth` when debugging
- Check logs before reporting issues
- Use `make stack-validate` before commits
- Keep services running during active development
- Use specific test markers for fast feedback

### ❌ DON'T
- Mix manual pytest with Athena-driven tests
- Leave services running overnight (resource waste)
- Ignore 401 errors (they indicate token issues)
- Skip `stack-down` (leaves orphan processes)
- Run tests without `make stack-up` first

## Quick Commands Reference

```bash
# Start / Stop
make stack-up                  # Start everything
make stack-down                # Stop everything
make stack-restart             # Restart all

# Validate
make truth                     # Show what's actually running
make stack-validate            # Health + smoke + backend tests
make athena-tests-smoke        # Quick smoke tests

# Test Suites
make athena-tests              # Full suite
make athena-tests-backends     # Backend integration
make athena-tests-all          # Full suite with JSON output

# Emergency
make nuke-ports                # Kill all services forcefully
```

## Getting Help

**Receipts not vibes:**
1. Run `make truth`
2. Check service logs: `tail -f /tmp/*.log`
3. Verify health: `curl -sI :8014/health`

These three commands will tell you exactly what's happening vs. what you think is happening.

---

**Remember:** Fast, boring, bulletproof. If it's not boring anymore, run `make truth`. 💪
