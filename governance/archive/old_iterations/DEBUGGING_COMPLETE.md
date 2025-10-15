# 🔍 Debugging Tools - COMPLETE

> **"Receipts, not vibes"** — Trust what's actually running, not what the IDE thinks

---

## ✅ What's Implemented

### 1. Truth Script (`scripts/truth.sh`)
**One-command reality check** showing:
- Which PIDs are on which ports
- HTTP headers from each service (PID, CWD, Python, Git hash, Mode)
- Python/pytest versions
- Environment variables
- PID file status
- Git branch and commit

**Usage:**
```bash
make truth
```

### 2. Service Self-Identification
**All services now include identity headers:**
- `x-service` - Service name
- `x-pid` - Process ID
- `x-cwd` - Working directory
- `x-py` - Python interpreter path
- `x-build` - Git commit hash
- `x-boot` - Boot timestamp
- `x-mode` - Real or mock mode (bridge only)

**Can't be faked** - headers show actual running process.

### 3. Nuclear Port Killer (`make nuke-ports`)
**Kills all ghosts:**
```bash
make nuke-ports
```

Mercilessly kills anything on ports 8014, 8090, 8181.

### 4. Transparent Test Execution
**Athena now returns full transparency:**
- `args` - Exact pytest arguments
- `python` - Which Python interpreter
- `cwd` - Working directory
- `env_used` - All environment variables used

**No more guessing** what Athena is doing.

---

## 🎯 Fast Debugging Workflow

### Problem: "Cursor says X but reality is Y"
```bash
# Step 1: See what's ACTUALLY running
make truth

# Step 2: Check service headers
curl -I http://127.0.0.1:8014/health | grep ^x-

# Step 3: Compare with Cursor
```

### Problem: Tests failing mysteriously
```bash
# Step 1: Kill all ghosts
make nuke-ports

# Step 2: Clean restart
make stack-up

# Step 3: Verify
make truth

# Step 4: Run tests with full transparency
make athena-tests | jq '.'
```

### Problem: Port conflicts
```bash
# Nuclear option
make nuke-ports
make stack-up
```

### Problem: Wrong Python/environment
```bash
# Check terminal Python
which python3

# Check Athena's Python
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq -r .python

# Should match!
```

---

## 📊 Reading Service Headers

### Example: Bridge Health Check
```bash
curl -I http://127.0.0.1:8014/health
```

**Expected output:**
```
HTTP/1.1 200 OK
x-service: neuroforge-bridge
x-pid: 12345
x-cwd: /Users/christianmerrill/Documents/GitHub/bridge
x-py: /usr/local/bin/python3
x-build: abc1234
x-boot: 2025-10-12T14:30:00Z
x-mode: real
x-correlation-id: ...
x-adapter-version: 1.0.0
```

**What to check:**
- ✅ `x-pid` matches `lsof` output
- ✅ `x-cwd` is correct directory
- ✅ `x-py` matches your Python
- ✅ `x-build` shows git commit
- ✅ `x-mode` is "real" (not "mock")

**🚨 Red flags:**
- Missing headers → old process
- Wrong PID → ghost process
- Wrong mode → env var not set
- "nogit" build → not in git repo

---

## 🧪 Test Transparency Example

### Run tests:
```bash
make athena-tests
```

### Response includes:
```json
{
  "ok": true,
  "cmd": "python3 -m pytest tests/ -m 'smoke or e2e' ...",
  "args": ["python3", "-m", "pytest", "tests/", "-m", "smoke or e2e"],
  "cwd": "/Users/christianmerrill/Documents/GitHub",
  "python": "/usr/local/bin/python3",
  "env_used": {
    "BRIDGE_BASE": "http://127.0.0.1:8014",
    "UAT_BASE": "http://127.0.0.1:8181",
    "ATHENA_BASE": "http://127.0.0.1:8090",
    "UAT_TOKEN": "supersecret",
    "ATH_TOKEN": "supersecret",
    "PYTEST_ADDOPTS": "(not set)"
  },
  "summary": {
    "passed": 48,
    "failed": 0
  }
}
```

**Verify:**
- ✅ `python` matches your terminal
- ✅ `cwd` is workspace root
- ✅ `env_used` shows correct URLs/tokens
- ✅ `args` shows actual pytest command

---

## 🔧 Common Issues & Fixes

### Multiple PIDs per port (ghosts)
```bash
make truth | grep "8014\|8090\|8181"
# If you see multiple PIDs:
make nuke-ports
make stack-up
```

### Wrong mode (mock when expecting real)
```bash
curl -I http://127.0.0.1:8014/health | grep x-mode
# If shows "mock":
make stack-down
USE_MOCK=0 make stack-up
```

### Stale PID files
```bash
make truth
# Look for "(STALE - process not found)"
# Fix:
make stack-down
make stack-up
```

### Python mismatch
```bash
# Terminal Python
which python3

# Athena Python
make athena-tests | jq -r .python

# If different, restart services
make stack-restart
```

---

## 📋 New Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `make truth` | Reality check | When Cursor seems off |
| `make nuke-ports` | Kill all on 8014/8090/8181 | Port conflicts |
| `curl -I http://127.0.0.1:8014/health` | Check service identity | Verify which process answered |
| `make athena-tests \| jq .` | Transparent test run | See exact args/env/python |

---

## ✅ Updated Files

### Modified
- ✅ `Makefile` - Added `nuke-ports` and `truth` targets
- ✅ `bridge/adapter.py` - Added self-identification headers
- ✅ `athena/api.py` - Added transparency to test responses

### Created
- ✅ `scripts/truth.sh` - Reality check script
- ✅ `DEBUGGING_GUIDE.md` - Complete debugging reference

---

## 🎯 Daily Use

### Morning Start
```bash
make truth              # Verify nothing running
make stack-up           # Start fresh
make truth              # Verify everything started
```

### During Development
```bash
make truth              # Quick sanity check
curl -I http://127.0.0.1:8014/health | grep x-mode
```

### When Things Seem Off
```bash
make nuke-ports         # Kill ghosts
make stack-restart      # Fresh start
make truth              # Verify
```

### Before Commit
```bash
make truth              # Check state
make stack-validate     # Full validation
make athena-tests       # Run tests
```

---

## 📚 Documentation

- **DEBUGGING_GUIDE.md** - Complete troubleshooting guide
- **scripts/truth.sh** - Reality check script
- **FULL_STACK_VALIDATION_PLAYBOOK.md** - Testing playbook

---

## 🎓 Trust Hierarchy

### ✅ Always Trust (Source of Truth)
1. `make truth` output
2. HTTP `x-*` headers from services
3. Direct terminal commands (`lsof`, `ps`, `curl`)
4. PID files vs actual process list

### ❌ Never Trust Blindly
1. Cursor UI indicators
2. IDE terminal (different env)
3. Cached task results
4. Old log files

---

## 🚨 Emergency Procedures

### Nothing works, start over:
```bash
make stack-down
make nuke-ports
rm .stack/*.pid
rm pytest_report.json
make stack-up
make truth
```

### Services responding but wrong:
```bash
make truth | grep "x-build\|x-mode\|x-py"
# Check if headers match expectations
# If not:
make stack-restart
```

### Tests work in terminal, fail in Cursor:
```bash
# Compare environments
make truth
# vs Cursor's Python/env settings
# Fix Cursor tasks to match
```

---

## ✨ Benefits

✅ **No more guessing** - Headers show exact process
✅ **Fast diagnosis** - One `make truth` command
✅ **Kill ghosts** - `make nuke-ports` is merciless
✅ **Full transparency** - Athena shows exact args/env/python
✅ **Trust the headers** - Can't be faked

---

## 🎉 Summary

You now have **forensic-grade debugging tools**:

1. **`make truth`** - One-command reality check
2. **Service headers** - Self-identifying (PID, CWD, Python, Git, Mode)
3. **`make nuke-ports`** - Nuclear ghost killer
4. **Test transparency** - See exact args/env/python used

**When Cursor lies, `make truth` tells the truth.** 🔍

---

**Quick reference:**
```bash
make truth          # See what's actually running
make nuke-ports     # Kill all ghosts
make stack-restart  # Fresh start
curl -I http://127.0.0.1:8014/health | grep x-  # Check identity
```

**Receipts, not vibes.** ✅
