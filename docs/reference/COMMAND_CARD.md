# 🎯 Command Card - Stack System

> **Your complete operational reference**

---

## ⚡ Essential Commands (The Trifecta)

```bash
make stack-up        # Start everything (2s)
make truth           # See what's running (<1s)
make stack-down      # Stop everything (1s)
```

---

## 🔍 Debug Commands (Forensic)

```bash
make truth           # Full reality check (PID + headers + env)
make stack-truth     # Quick PID fingerprint
make nuke-ports      # Kill ALL on 8014/8090/8181
curl -I http://127.0.0.1:8014/health | grep ^x-  # Service identity
```

---

## 🧪 Test Commands

```bash
make athena-tests              # Full suite (1min)
make athena-tests-smoke        # Fast (15s)
make athena-tests-backends     # Backend-specific (30s)
make athena-tests-all          # All + verbose (2min)
make stack-validate            # Health check (30s)
```

---

## 🤖 Self-Healing (Autopilot)

```bash
make watchdog-start      # Start in background
make watchdog-stop       # Stop watchdog
make watchdog-status     # Check status
make watchdog-logs       # Tail logs
make watchdog-incidents  # View incident history
make watchdog-install    # Install as LaunchAgent (auto-start)
make watchdog-uninstall  # Remove LaunchAgent
```

---

## 🚨 Emergency Commands

```bash
# Nuclear option (kill all ghosts)
make nuke-ports

# Full clean restart
make stack-down && make nuke-ports && make stack-up

# Verify clean
make truth

# Check service identity
curl -I http://127.0.0.1:8014/health | grep "x-pid\|x-mode"
```

---

## 📊 Status & Info

```bash
make stack-status        # Show PIDs, ports, health
make truth               # Full forensic check
make watchdog-status     # Watchdog status + restart count
tail -f logs/*.log       # Watch all logs
cat /tmp/stack_incidents.log  # Incident history
```

---

## 🎯 Daily Workflow

### Morning
```bash
make truth
make stack-up
```

### During Dev
```bash
make stack-truth
make athena-tests-smoke
```

### Before Commit
```bash
make truth
make stack-validate
make athena-tests
```

### Enable Autopilot
```bash
make watchdog-install
```

---

## 🔧 Configuration

```bash
# Use .env.stack for custom config
cp .env.stack.example .env.stack
# Edit with your tokens/ports

# Or override inline
UAT_PORT=9181 make stack-up
```

---

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| START_HERE.md | Quick start |
| OPERATIONAL_DOCTRINE.md | System overview |
| GHOST_BUSTING_PROTOCOL.md | Debug guide |
| SELF_HEALING_GUIDE.md | Watchdog reference |
| STACK_QUICK_REF.md | Full command list |

---

## ✅ Trust Hierarchy

1. ✅ `make truth` - Source of truth
2. ✅ `x-pid` headers - Can't be faked
3. ✅ Terminal commands - Direct
4. ❌ Cursor UI - Verify first

**Receipts, not vibes.** 🧾

---

**Quick help:** `make help | grep -A 15 Stack`
