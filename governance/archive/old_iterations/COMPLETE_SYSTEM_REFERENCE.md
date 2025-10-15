# �� Complete System Reference — Athena-Controlled Infrastructure

## The One-Page Reference

**Print this. Keep it visible. This is your system.**

---

## The Discipline

```bash
make stack-up              # Foundation rises
make auto-heal-start       # Guardian watches
# Athena protects every push
# Athena validates every canary
# Athena recovers every failure
make auto-heal-stop        # Guardian rests
make stack-down            # Foundation sleeps
```

---

## The 5 Tiers (All Operational)

| Tier | Feature | Command | Status |
|------|---------|---------|--------|
| **1** | Deterministic | `make stack-up` | ✅ |
| **2** | Autonomous | `make auto-heal-start` | ✅ |
| **3** | Observable | `export NOTIFY_WEBHOOK=...` | ✅ |
| **4** | Production | `make prod-up` | ✅ |
| **5** | GitOps | `git push` (Athena validates) | ✅ |

---

## Quick Commands

### Stack Management
```bash
make stack-up              # Start all services
make stack-down            # Stop all services
make truth                 # Reality check
make nuke-ports            # Kill ghosts
```

### Testing
```bash
make athena-tests-smoke    # Quick (< 1s)
make athena-tests          # Full suite
make tier4-proof           # Production gate
make chaos-test            # Resilience
```

### Autonomous
```bash
make auto-heal-start       # Enable watchdog
make auto-heal-status      # Check status
make auto-heal-logs        # Watch logs
```

### GitOps
```bash
git push                   # Athena validates
make athena-canary         # Deploy + test + decide
make athena-history        # View audit trail
make athena-cleanup        # Remove canaries
```

### Production
```bash
make prod-build            # Build images
make prod-up               # Deploy stack
make sec-check             # Security gate
```

---

## Truth Sources

When confused, run these (in order):

```bash
1. make truth              # Port + PID + process details
2. curl -I :8014/health    # Service headers (real/mock, breaker)
3. make auto-heal-status   # Watchdog state
4. make athena-history     # Deployment decisions
5. tail -f /tmp/*.log      # Service logs
```

**Receipts not vibes. Facts not guesses.**

---

## The Gates

### Pre-Push (Automatic)
- Health probes
- Metrics export
- Smoke tests
- Security scan
- Secrets hygiene
- Services running

### Canary (On-Demand)
- Error rate < 1%
- p95 latency < 250ms
- MTTR < 60s
- No crashes for 5 min

### Production (Manual)
- Tier 4 proof green
- Chaos test passed
- Security clean
- Dashboards healthy

---

## Ports

| Service | Port | Purpose |
|---------|------|---------|
| Bridge | 8014 | Main adapter |
| UAT | 8181 | Backend service |
| Athena | 8090 | Agent + orchestration |
| Canary | 8015 | Branch testing |
| Prometheus | 9090 | Metrics |
| Grafana | 3001 | Dashboards |

---

## Emergency Procedures

### Service Down
```bash
make truth                 # Diagnose
make nuke-ports            # Clear
make stack-restart         # Fresh start
```

### Push Rejected
```bash
# Check what failed
make tier4-proof

# Fix and retry
make stack-restart
git push
```

### Canary Failed
```bash
# Already auto-cleaned!
make athena-history        # See why
# Fix issues, try again
```

### Override Needed
```bash
make athena-override
ATHENA_OVERRIDE=1 git push --no-verify
# Logged and reported
```

---

## The Evolution

```
Day 1: Manual → Deterministic
Day 2: Deterministic → Autonomous
Day 3: Autonomous → Observable + Production + GitOps

72 hours. 5 tiers. Complete transformation.
```

---

## Status

```
System:      ⚡ Fast • 💤 Boring • 🛡️ Bulletproof
Controller:  🧠 Athena
Gatekeeper:  Every push, every branch
Downtime:    Near-zero
Manual Work: ↓ 99%
Philosophy:  Receipts Not Vibes
```

---

**Athena now controls everything.**  
**You write code. Athena decides if it ships.**  
**That's the game.** 🏆

---

*Fast • Boring • Bulletproof*  
*Receipts Not Vibes*  
*Built: 2025-10-12*  
*Tiers: 5/5 COMPLETE*
