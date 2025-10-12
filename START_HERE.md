# 🚀 START HERE - Stack System

> **Production-grade stack management with forensic debugging**

---

## ⚡ Three Commands

```bash
make stack-up        # Start everything (2s)
make truth           # See what's running (<1s)
make stack-down      # Stop everything (1s)
```

**That's it.**

---

## 🔍 Debug Commands

```bash
make truth           # Reality check (PID fingerprints)
make nuke-ports      # Kill all ghosts
make stack-truth     # Quick check
```

---

## 🧪 Test Commands

```bash
make athena-tests              # Full suite (~1min)
make athena-tests-smoke        # Fast (~15s)
make stack-validate            # Health check (~30s)
```

---

## 🚨 Common Fixes

```bash
# Ghosts (multiple PIDs)?
make nuke-ports && make stack-up

# Wrong mode?
USE_MOCK=0 make stack-restart

# Stale state?
make stack-restart && make truth
```

---

## 📚 Read Next

1. **OPERATIONAL_DOCTRINE.md** - System overview
2. **GHOST_BUSTING_PROTOCOL.md** - Debug guide
3. **STACK_QUICK_REF.md** - Command reference

---

## ✅ What Makes It Special

- ✅ Caught real ghosts day one
- ✅ Headers can't be faked (PID proof)
- ✅ One-command diagnosis
- ✅ Nuclear ghost killer
- ✅ Full transparency

**Fast. Boring. Bulletproof.**

---

**Next:** Run `make truth` to see what's running.
