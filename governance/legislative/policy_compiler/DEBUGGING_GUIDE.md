# Debugging Guide: Cursor vs Reality

> **"Receipts, not vibes"** — When Cursor says one thing but reality says another

---

## 🎯 The Problem

Cursor (or any IDE) can show you stale/cached information that doesn't match what's actually running:

**Common lies:**
- ❌ Shows tests passing when they're actually failing
- ❌ Says service is on port X when it's actually on port Y
- ❌ Reports Python version that doesn't match terminal
- ❌ Thinks mock mode is off when it's on
- ❌ Shows old process still running (ghost)

**Why this happens:**
1. Cursor runs different Python than your terminal (pyenv/conda/system)
2. Tasks run from different working directory
3. Old processes still serving on same port (ghosts)
4. Environment not loaded in Cursor task (no `.env.stack`)
5. Cursor caching stale task config

---

## 🔍 Solution: Truth Commands

### Quick Reality Check
```bash
# One command to see what's ACTUALLY running
make truth
```

**What it shows:**
- ✅ Which PIDs are on which ports
- ✅ HTTP headers from each service (PID, CWD, Python, Git hash)
- ✅ Python/pytest versions in your terminal
- ✅ Environment variables loaded
- ✅ PID file status (running or stale)

### Kill All Ghosts
```bash
# Nuclear option: kill everything on stack ports
make nuke-ports

# Then restart clean
make stack-up
```

### Full Diagnostic
```bash
# If things are really weird
make stack-down
make nuke-ports
make stack-up
make truth
```

---

## 📊 Reading the Truth

### 1. Port Check
```bash
=== WHO'S ON PORTS ===
Bridge (8014):
python3  12345 user   TCP 127.0.0.1:8014 (LISTEN)

Athena (8090):
python3  12346 user   TCP 127.0.0.1:8090 (LISTEN)

UAT (8181):
python3  12347 user   TCP 127.0.0.1:8181 (LISTEN)
```

**🚨 Red flags:**
- Multiple PIDs per port → **GHOSTS** (old processes still running)
- No processes shown → Service not started
- Different user/python → Wrong environment

### 2. HTTP Headers
```bash
=== CURL HEADERS (BRIDGE) ===
HTTP/1.1 200 OK
x-service: neuroforge-bridge
x-pid: 12345
x-cwd: /Users/christianmerrill/Documents/GitHub/bridge
x-py: /usr/local/bin/python3
x-build: abc1234
x-boot: 2025-10-12T14:30:00Z
x-mode: real
```

**What to check:**
- ✅ `x-service` confirms which service answered
- ✅ `x-pid` should match lsof output
- ✅ `x-cwd` should be bridge directory
- ✅ `x-py` should match your `which python3`
- ✅ `x-build` shows git commit (not "nogit")
- ✅ `x-mode` should be "real" (not "mock")
- ✅ `x-boot` shows when process started

**🚨 If headers missing:**
- Old process or different binary
- Not running through our middleware
- Wrong port (hitting something else)

### 3. Python Environment
```bash
=== PYTHON/PKG FINGERPRINTS ===
Python location: /usr/local/bin/python3
Python version: Python 3.11.5
Pytest location: /usr/local/bin/pytest
Pytest version: pytest 7.4.0
sys.executable = /usr/local/bin/python3
site packages  = ['/usr/local/lib/python3.11/site-packages']
```

**What to verify:**
- ✅ Python path matches what services use
- ✅ Pytest is installed and found
- ✅ Site packages path looks right

**🚨 If Cursor shows different:**
- Cursor is using different Python
- Check Cursor's Python interpreter setting
- Check terminal vs Cursor task environment

### 4. Environment Variables
```bash
=== ENV SNAPSHOT ===
ATH_TOKEN=supersecret
BRIDGE_PORT=8014
ENV=dev
UAT_BASE=http://127.0.0.1:8181
UAT_TOKEN=supersecret
USE_MOCK=0
```

**Verify:**
- ✅ Tokens are set
- ✅ Ports match expectations
- ✅ `USE_MOCK=0` (not 1)
- ✅ `ENV=dev` (or appropriate)

**🚨 If variables missing:**
- `.env.stack` not loaded
- Run `source .env.stack` before commands
- Check Cursor task loads environment

### 5. PID Files
```bash
=== PID FILES ===
Stack PIDs:
  ✓ uat: PID 12347 (running)
  ✓ athena: PID 12346 (running)
  ✓ bridge: PID 12345 (running)
```

**Or if stale:**
```bash
  ✗ bridge: PID 12300 (STALE - process not found)
```

**Fix stale PIDs:**
```bash
make stack-down
make stack-up
```

---

## 🧪 Testing Transparency

When you run `make athena-tests`, Athena now returns **full transparency**:

```json
{
  "ok": true,
  "cmd": "python3 -m pytest tests/ -m 'smoke or e2e' ...",
  "args": ["python3", "-m", "pytest", "tests/", ...],
  "cwd": "/Users/christianmerrill/Documents/GitHub",
  "python": "/usr/local/bin/python3",
  "env_used": {
    "BRIDGE_BASE": "http://127.0.0.1:8014",
    "UAT_BASE": "http://127.0.0.1:8181",
    "ATHENA_BASE": "http://127.0.0.1:8090",
    "UAT_TOKEN": "supersecret",
    "ATH_TOKEN": "supersecret"
  },
  "summary": {
    "passed": 48,
    "failed": 0
  }
}
```

**What to check:**
- ✅ `python` matches your terminal's Python
- ✅ `cwd` is workspace root
- ✅ `env_used` shows correct base URLs and tokens
- ✅ `args` shows actual pytest command

**🚨 If mismatch:**
- Athena using different Python → restart services
- Wrong `cwd` → check Athena startup directory
- Missing env vars → not passing through correctly

---

## 🔧 Common Fixes

### Problem: Cursor says tests pass, terminal says fail
```bash
# Check which Python each uses
make truth | grep "Python location"
# vs
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq .python
```

**Fix:** Make sure both use same Python

### Problem: Service responds but wrong mode (mock vs real)
```bash
# Check mode
curl -I http://127.0.0.1:8014/health | grep x-mode
```

**Fix:**
```bash
make stack-down
USE_MOCK=0 make stack-up
```

### Problem: Multiple processes on same port
```bash
# See all processes
lsof -n -iTCP:8014 -sTCP:LISTEN

# Nuclear fix
make nuke-ports
make stack-up
```

### Problem: Cursor task fails but terminal works
**Check Cursor task:**
1. Working directory → should be `${workspaceFolder}`
2. Environment → should load `.env.stack`
3. Shell → use `/bin/bash -lc` or explicit source

**Example task:**
```json
{
  "label": "Stack: Truth Check",
  "type": "shell",
  "command": "make truth",
  "options": {
    "cwd": "${workspaceFolder}"
  }
}
```

### Problem: Tests can't find fixtures/modules
```bash
# Check working directory
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq .cwd

# Should be: /Users/christianmerrill/Documents/GitHub
# Not:       /Users/christianmerrill/Documents/GitHub/AI-Projects/...
```

---

## 🎯 Daily Debugging Workflow

### Morning (fresh start)
```bash
# Clean slate
make stack-down
make nuke-ports
make stack-up

# Verify
make truth
```

### During Development
```bash
# Quick sanity check
make truth | grep "x-mode"
# Should see: x-mode: real

# If things seem off
make stack-restart
make truth
```

### Before Commit
```bash
# Full validation
make truth
make stack-validate
make athena-tests

# If any issues
make nuke-ports
make stack-up
# Try again
```

---

## 📋 Troubleshooting Matrix

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Tests pass in Cursor, fail in terminal | Different Python | Check `make truth` vs Athena `.python` |
| Service 401 errors | Token mismatch | Check `.env.stack` loaded: `env \| grep TOKEN` |
| "Port in use" error | Ghost process | `make nuke-ports && make stack-up` |
| Wrong mode (mock when expecting real) | Env var not set | `USE_MOCK=0 make stack-restart` |
| Stale PID files | Process crashed | `make stack-down && make stack-up` |
| Multiple PIDs per port | Old processes | `make nuke-ports` |
| Tests hang forever | Wrong working dir | Check Athena `.cwd` in response |
| Headers missing | Old binary | `make stack-restart` |
| Different git hash | Code not reloaded | `make stack-restart` |

---

## 🔍 Advanced: Deep Inspection

### Check Service Identity
```bash
# Bridge
curl -I http://127.0.0.1:8014/health | grep ^x-

# Athena (needs auth)
curl -I -H "Authorization: Bearer supersecret" \
  http://127.0.0.1:8090/health | grep ^x-

# UAT (needs auth)
curl -I -H "Authorization: Bearer supersecret" \
  http://127.0.0.1:8181/health | grep ^x-
```

### Compare Environments
```bash
# Terminal Python
which python3
python3 -c "import sys; print(sys.executable)"

# Athena's Python (from test response)
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq -r .python

# Should match!
```

### Trace Request Flow
```bash
# Check correlation ID flows through
corr_id=$(uuidgen)
curl -H "x-correlation-id: $corr_id" \
  http://127.0.0.1:8014/health -I | grep x-correlation-id

# Check logs
grep "$corr_id" logs/*.log
```

---

## ✅ Trust This, Not That

### ✅ Trust (source of truth)
- `make truth` output
- `x-*` HTTP headers from services
- Terminal commands (direct curl)
- PID from `lsof`
- Process list from `ps`

### ❌ Don't trust (can be stale)
- Cursor UI indicators
- IDE terminal (might use different env)
- Cached task results
- Old log files
- Status bars

---

## 🚨 Emergency: Nothing Works

```bash
# The nuclear option
make stack-down
make nuke-ports
pkill -9 python3  # DANGER: kills ALL Python processes
rm .stack/*.pid
rm pytest_report.json

# Fresh start
make stack-up

# Verify
make truth

# Test
make athena-tests
```

---

## 📞 Quick Reference

```bash
# See what's actually running
make truth

# Kill all stack processes
make nuke-ports

# Full restart
make stack-restart

# Validate everything
make stack-validate

# Check single service
curl -I http://127.0.0.1:8014/health | grep x-
```

---

**Remember:** When in doubt, trust `make truth` over what Cursor shows. The headers don't lie. 🔍
