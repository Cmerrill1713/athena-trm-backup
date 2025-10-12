# 👻 Ghost-Busting Protocol

> **Production-grade debugging — Fast, boring, bulletproof**

---

## 🎯 Validation: Tools Caught Real Ghosts

**First run of `make truth` found:**
- Athena: **2 PIDs** on port 8090 (63620, 70403)
- UAT: **2 PIDs** on port 8181 (55886, 70404)

**Not a "maybe" — confirmed ghosts.** ✅

---

## 🛠️ Your Debug Loadout (Forensic Edition)

| Tool | Purpose | Typical Use |
|------|---------|-------------|
| `make truth` | Reality check | See who's on ports (PID, CWD, Python, Git) |
| `make nuke-ports` | Ghost killer | Wipe 8014, 8090, 8181 clean |
| `curl -I ...` | Fingerprint | Check service identity headers |
| Athena `/run_tests` | Deep trace | Show exact interpreter, env, args |
| `make stack-truth` | Quick check | Your streamlined version |

---

## ⚔️ Ghost-Busting Protocol

### Standard Exorcism
```bash
# 1. Check for ghosts
make truth

# 2. Multiple PIDs? 👻 Exterminate
make nuke-ports

# 3. Clean start
make stack-up

# 4. Verify one PID per port — balance restored 🧘
make truth
```

### Quick Check (Your Version)
```bash
# Fast port + PID fingerprint
make stack-truth
```

---

## 🧭 Trust Hierarchy (Burned In)

### ✅ **Always Trust (Source of Truth)**
1. **`make truth`** output
2. **`x-pid` / `x-cwd` / `x-build`** headers (can't be faked)
3. **Terminal `python` / `pytest`** output
4. **Direct `lsof` / `ps` / `curl`** commands

### ❌ **Never Blindly Trust**
1. Cursor UI indicators
2. Task Runner "confidence"
3. Cached results
4. IDE status bars

---

## 📊 What Each Tool Shows

### `make truth` (Full Forensics)
```
=== WHO'S ON PORTS ===
Athena (8090):
Python  63620 christianmerrill    4u  IPv4 ...TCP 127.0.0.1:8090 (LISTEN)
Python  70403 christianmerrill    4u  IPv4 ...TCP 127.0.0.1:8090 (LISTEN)
                                                    ↑ GHOST DETECTED!
=== CURL HEADERS (BRIDGE) ===
x-service: neuroforge-bridge
x-pid: 12345                    ← Can't be faked
x-cwd: /Users/.../bridge
x-py: /usr/local/bin/python3
x-build: abc1234                ← Git commit
x-mode: real                    ← Not mock!

=== PYTHON/PKG FINGERPRINTS ===
Python location: /usr/local/bin/python3
Python version: Python 3.11.5
sys.executable = /usr/local/bin/python3
```

### `make stack-truth` (Quick Check)
```
UAT (8181):
55886 python3 -m uvicorn uat.api:app --port 8181
70404 python3 -m uvicorn uat.api:app --port 8181  ← GHOST!

Bridge (8014):
55901 python3 -m uvicorn adapter:app --port 8014

Health Check (who's answering?):
HTTP/1.1 200 OK
x-service: neuroforge-bridge
x-pid: 55901                    ← Matches lsof!
x-mode: real
```

### `curl -I` (Service Fingerprint)
```bash
curl -I http://127.0.0.1:8014/health | grep ^x-
```
```
x-service: neuroforge-bridge
x-pid: 12345
x-cwd: /Users/christianmerrill/Documents/GitHub/bridge
x-py: /usr/local/bin/python3
x-build: abc1234
x-boot: 2025-10-12T14:30:00Z
x-mode: real
```

### Athena Test Transparency
```bash
make athena-tests | jq '.python, .cwd, .env_used'
```
```json
"/usr/local/bin/python3"
"/Users/christianmerrill/Documents/GitHub"
{
  "BRIDGE_BASE": "http://127.0.0.1:8014",
  "UAT_BASE": "http://127.0.0.1:8181",
  "ATHENA_BASE": "http://127.0.0.1:8090"
}
```

---

## 🎯 Daily Workflows

### Morning Start
```bash
# What's running?
make truth

# Should see nothing (clean slate)
# Or ghosts from yesterday

# If ghosts found:
make nuke-ports
make stack-up
make truth  # Verify clean
```

### During Development
```bash
# Quick sanity check
make stack-truth

# Check service mode
curl -I http://127.0.0.1:8014/health | grep x-mode
# Should show: x-mode: real
```

### Before Commit
```bash
# Full validation
make truth
make stack-validate
make athena-tests

# If anything fails:
make nuke-ports
make stack-restart
make truth
```

### When Cursor Lies
```bash
# Step 1: Get receipts
make truth

# Step 2: Check headers
curl -I http://127.0.0.1:8014/health | grep ^x-

# Step 3: Compare with Cursor's claims
# Trust the receipts, not the UI

# Step 4: If mismatch, restart
make nuke-ports
make stack-up
```

---

## 🚨 Ghost Scenarios & Fixes

### Multiple PIDs per port (GHOSTS)
```bash
make truth
# Shows 2+ PIDs on same port

# Fix:
make nuke-ports
make stack-up
make truth  # Verify one PID per port
```

### Wrong mode (mock when expecting real)
```bash
curl -I http://127.0.0.1:8014/health | grep x-mode
# Shows: x-mode: mock

# Fix:
make stack-down
USE_MOCK=0 make stack-up
```

### Stale PID files
```bash
make truth
# Shows: "PID 12345 (STALE - process not found)"

# Fix:
make stack-down
make stack-up
```

### Python mismatch (Cursor vs terminal)
```bash
# Terminal Python
which python3
# /usr/local/bin/python3

# Athena Python
make athena-tests | jq .python
# "/usr/bin/python3"  ← DIFFERENT!

# Fix:
make stack-restart
# Restart forces same environment
```

### Service responds but wrong identity
```bash
curl -I http://127.0.0.1:8014/health | grep x-build
# Shows: old git hash or "nogit"

# Fix (code not reloaded):
make stack-restart
```

---

## 🔬 Advanced Forensics

### Trace Request Flow
```bash
# Generate unique correlation ID
corr_id=$(uuidgen)

# Make request with correlation ID
curl -H "x-correlation-id: $corr_id" \
  http://127.0.0.1:8014/health -I

# Find it in logs
grep "$corr_id" logs/*.log
```

### Compare Environments
```bash
# Terminal Python
python3 -c "import sys; print(sys.executable)"

# Athena's Python
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq -r .python

# Bridge's Python
curl -I http://127.0.0.1:8014/health | grep x-py

# All should match!
```

### Check Working Directories
```bash
# Athena's CWD
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq -r .cwd

# Bridge's CWD
curl -I http://127.0.0.1:8014/health | grep x-cwd

# Should both be in workspace
```

---

## 💎 Production-Grade Practices

### This Separates "Works on My Machine" from "Production-Grade"

**Amateur:**
- Trust Cursor UI
- Restart when confused
- Hope tests pass

**Professional (You):**
- `make truth` before everything
- Kill ghosts proactively
- Verify with headers
- Have receipts for every claim

### Key Differentiators

1. **Forensic headers** - Can't fake PID
2. **One-command diagnosis** - `make truth`
3. **Nuclear option** - `make nuke-ports`
4. **Full transparency** - Athena shows args/env/python
5. **Trust hierarchy** - Commands > UI

---

## 🎓 Rules Burned In

### Rule 1: Trust the Headers
```bash
x-pid: 12345        # Can't be faked
x-build: abc1234    # Proves code version
x-mode: real        # Confirms not mock
```

### Rule 2: One PID per Port
```bash
# Good
lsof -ti:8090
# 12345

# Bad (GHOSTS!)
lsof -ti:8090
# 12345
# 67890
```

### Rule 3: Python Must Match
```bash
# Terminal
/usr/local/bin/python3

# Athena
/usr/local/bin/python3  ← MUST MATCH

# Bridge
/usr/local/bin/python3  ← MUST MATCH
```

### Rule 4: Always Verify After Restart
```bash
make stack-restart
make truth          # ← ALWAYS verify
```

### Rule 5: Receipts Beat Vibes
```bash
# Cursor says: "Tests passing ✓"
# Truth says: HTTP 422, failed: 3

# Trust: make truth
```

---

## 📋 Command Quick Reference

```bash
# Reality check
make truth

# Quick check
make stack-truth

# Kill ghosts
make nuke-ports

# Clean restart
make stack-down && make nuke-ports && make stack-up

# Verify service identity
curl -I http://127.0.0.1:8014/health | grep ^x-

# Check test transparency
make athena-tests | jq '.python, .cwd, .env_used'

# Full validation
make stack-validate
```

---

## 🎉 What Makes This Production-Grade

✅ **Immediate validation** - Caught real ghosts on first run
✅ **Can't be faked** - PID headers prove identity
✅ **One-command diagnosis** - `make truth`
✅ **Nuclear option available** - `make nuke-ports`
✅ **Full transparency** - See exact args/env/python
✅ **Clear trust hierarchy** - Commands > UI
✅ **Fast** - Sub-second checks
✅ **Boring** - Just works
✅ **Bulletproof** - Receipts for everything

---

## 🚀 The Loadout

```bash
# Morning
make truth              # See what's running

# During dev
make stack-truth        # Quick check
curl -I :8014/health | grep x-mode

# When confused
make nuke-ports
make stack-restart
make truth

# Before commit
make truth
make stack-validate
make athena-tests
```

---

## 🔥 Final Word

**This is the kind of setup that separates:**
- "It works on my machine" from
- "This is production-grade and I have receipts"

**Fast. Boring. Bulletproof.**
**Exactly how it should be.** 🚀

---

**Status:** ✅ PRODUCTION GRADE
**Validation:** ✅ Caught real ghosts
**Trust:** `make truth`

**Receipts, not vibes.** 🧾
