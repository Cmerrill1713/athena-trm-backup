# Stack Tools - Quick Start

> **One-command stack control with forensic debugging**

## 🎯 The Three Commands You Need

```bash
make stack-up        # Start everything
make truth           # See what's actually running
make stack-down      # Stop everything
```

**Fast, boring, bulletproof.** ✅

---

## 🔍 Debug Tools (Receipts Not Vibes)

```bash
make truth           # Full forensic check
make stack-truth     # Quick PID fingerprint
make nuke-ports      # Kill all ghosts
```

---

## 🧪 Testing

```bash
make athena-tests              # Full suite
make athena-tests-smoke        # Fast smoke tests
make athena-tests-backends     # Backend tests only
make stack-validate            # Full health check
```

---

## 📊 Trust Hierarchy

### ✅ Always Trust
1. `make truth` output
2. `x-pid` / `x-cwd` / `x-build` headers
3. Terminal commands

### ❌ Never Blindly Trust
1. Cursor UI
2. IDE status bars
3. Cached results

---

## 🚨 Common Issues

```bash
# Multiple PIDs (ghosts)
make nuke-ports && make stack-up

# Wrong mode (mock vs real)
USE_MOCK=0 make stack-restart

# Python mismatch
make stack-restart && make truth

# Port conflicts
make nuke-ports && make stack-up
```

---

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| **GHOST_BUSTING_PROTOCOL.md** | Complete debugging guide |
| **FULL_STACK_VALIDATION_PLAYBOOK.md** | Testing playbook |
| **STACK_QUICK_REF.md** | Command reference |

---

## ✨ What Makes It Production-Grade

- ✅ Caught real ghosts on first run
- ✅ Headers can't be faked (PID proof)
- ✅ One-command diagnosis
- ✅ Nuclear option available
- ✅ Full transparency

**Receipts, not vibes.** 🧾
