# 🎯 Power User Intents — Advanced Athena Commands

## 5 High-Leverage Commands for Production Operations

### 1. Shadow Traffic / Traffic Mirroring
```bash
athena "shadow traffic 10 percent"
athena "mirror 10 percent"
athena "split traffic"
```

**What it does:**
- Deploys canary to :8015
- Mirrors 10% of production traffic
- Monitors SLOs for comparison
- Auto-promotes if canary performs better

**Use when:**
- Testing performance optimizations
- Validating new features under real load
- A/B testing different implementations

---

### 2. Incident Report Generation
```bash
athena "generate incident report"
athena "create postmortem"
athena "what went wrong"
```

**What it does:**
- Pulls last 20 audit trail entries
- Extracts watchdog recovery events
- Shows failures, rollbacks, unhealthy states
- Creates incident timeline

**Use when:**
- Post-mortem analysis
- Understanding what happened during outage
- Compliance/audit requirements

**Output:**
```
=== INCIDENT REPORT ===
[2025-10-12T20:00:00Z] DEPLOY_START branch=feature/optimizer
[2025-10-12T20:00:30Z] unhealthy: Bridge not responding
[2025-10-12T20:00:35Z] recovery initiated
[2025-10-12T20:00:45Z] recovery successful
[2025-10-12T20:05:00Z] PROMOTE branch=feature/optimizer
```

---

### 3. Recent Errors Tail
```bash
athena "show recent errors"
athena "tail errors last 5 minutes"
athena "what's failing"
```

**What it does:**
- Scans last 100 lines of all service logs
- Filters for ERROR, EXCEPTION, FAIL, TRACEBACK
- Shows last 20 error lines
- Sorted by timestamp

**Use when:**
- Debugging failures
- Quick error triage
- Understanding what broke

**Output:**
```
=== RECENT ERRORS ===
/tmp/bridge_8014.log:
  [ERROR] Connection refused to UAT (attempt 1/3)
/tmp/athena_8090.log:
  [ERROR] Test suite failed: 2/10 tests
```

---

### 4. Create Rollback Point
```bash
athena "create rollback point"
athena "snapshot current state"
athena "save checkpoint"
```

**What it does:**
- Creates timestamped git tag
- Tag name: `rollback-YYYYMMDD-HHMMSS`
- Includes message: "Rollback point created via Athena"
- Shows restore command

**Use when:**
- Before risky changes
- Before major deployments
- Creating safety checkpoints

**Restore:**
```bash
git tag -l "rollback-*"  # List checkpoints
git reset --hard rollback-20251012-153000
```

---

### 5. Snapshot Traces
```bash
athena "snapshot traces"
athena "backup traces"
athena "export trace data"
```

**What it does:**
- Exports all traces from UAT (:8181/traces)
- Saves to `/tmp/traces_snapshot_YYYYMMDD_HHMMSS.json`
- Shows file size and location
- Timestamped for versioning

**Use when:**
- Before data migrations
- Creating test fixtures
- Compliance/audit exports
- Before schema changes

**Output:**
```
Traces exported to /tmp/traces_snapshot_*.json
-rw-r--r-- 1 user wheel 41K Oct 12 16:13 /tmp/traces_snapshot_20251012_161324.json
```

---

## Combined Workflows

### Pre-Deployment Safety
```bash
athena "create rollback point"
athena "snapshot traces"
athena "ship it"
# If canary fails, traces and rollback point are available
```

### Post-Incident Analysis
```bash
athena "generate incident report"
athena "show recent errors"
athena "what's running"
# Complete incident context
```

### Traffic Migration
```bash
athena "shadow traffic 10 percent"
# Monitor for 5 min
# If successful:
athena "ship it"  # Full canary deployment
```

---

## Customization Examples

### Add Custom Thresholds
```json
{
  "shadow_traffic_25": {
    "phrases": ["shadow 25 percent", "mirror quarter traffic"],
    "command": "make athena-canary MIRROR_PERCENT=25",
    "requires_confirmation": true
  }
}
```

### Chain Multiple Commands
```json
{
  "full_diagnostic": {
    "phrases": ["full diagnostic", "complete health check"],
    "command": "athena 'what's running' && athena 'show recent errors' && athena 'watchdog status'",
    "requires_confirmation": false
  }
}
```

### Service-Specific Control
```json
{
  "restart_bridge": {
    "phrases": ["restart bridge", "reboot adapter"],
    "command": "pkill -f 'uvicorn.*bridge' && sleep 2 && make stack-up",
    "requires_confirmation": true
  }
}
```

---

## Safety Features

All high-risk intents require confirmation:
- `shadow_traffic` — Canary deployment
- `deploy_canary` — Production canary
- `prod_deploy` — Full production
- `rollback` — System rollback

**Example:**
```
$ athena "shadow traffic 10 percent"
🧠 Athena: Enabling 10% traffic shadow to canary...

⚠️  This action requires confirmation.
Command: make athena-canary MIRROR_PERCENT=10
Proceed? (yes/no): yes

[Executes...]
```

---

## The Complete Intent List

**23 Total Intents:**

1. Stack: up, down, restart, truth, kill ghosts (5)
2. Autonomous: watchdog start/status (2)
3. Testing: smoke, full, chaos, security, tier4 (5)
4. Deployment: canary, rollback, prod, shadow (4)
5. Monitoring: dashboard, health, history (3)
6. Data & Audit: snapshot, rollback point, incident report, tail errors (4)

---

## Best Practices

### ✅ DO
- Use "snapshot traces" before schema changes
- Use "create rollback point" before risky deploys
- Use "generate incident report" for post-mortems
- Use "shadow traffic" to validate optimizations

### ❌ DON'T
- Override confirmations without reading the command
- Ignore "tail errors" output (it shows real issues)
- Create rollback points without descriptive context
- Shadow traffic during peak load (use off-hours)

---

## Integration with Full System

### With Pre-Push Hook
```bash
git push
# Athena pre-push validates
# No voice command needed

athena "create rollback point"
# Safety checkpoint before merge
```

### With Watchdog
```bash
athena "enable watchdog"
# Auto-healing active

athena "generate incident report"
# See what watchdog recovered
```

### With Canary System
```bash
athena "create rollback point"
athena "shadow traffic 10 percent"
# If fails, rollback available

athena "ship it"
# Full canary if shadow successful
```

---

## The Philosophy

**From:**
```bash
# Complex multi-step procedures
git tag -a rollback-$(date +%s) -m "checkpoint"
curl http://localhost:8181/traces > backup.json
tail -100 /tmp/*.log | grep ERROR
make athena-canary MIRROR_PERCENT=10
# ... remember exact syntax ...
```

**To:**
```bash
athena "create rollback point"
athena "snapshot traces"
athena "show recent errors"
athena "shadow traffic 10 percent"
```

**Natural language. Instant execution.**

---

## Status

```
Base Intents:    18
Power Intents:   5 (new!)
Total:           23
Confirmations:   8 high-risk
Categories:      6
```

---

**Built:** 2025-10-12  
**Status:** POWER USER INTENTS OPERATIONAL  
**Interface:** Conversational  
**Safety:** Confirmation gates active  

**Production operations via conversation.** 🎯🗣️

