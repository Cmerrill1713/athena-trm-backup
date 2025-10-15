# 🧠 ATHENA GITOPS — BATTLE CARD

**Print this. Laminate it. Keep it visible.**

---

## The New Reality

```
You code. You push. Athena decides.
```

**No manual gates. No babysitting. No late-night fires.**

---

## Daily Workflow

```bash
# Morning
make stack-up
make auto-heal-start

# Code & commit
git add -A
git commit -m "new feature"

# Push (Athena validates automatically)
git push
# ✅ Approved → proceeds
# ❌ Rejected → fix and retry

# End of day
make auto-heal-stop
make stack-down
```

**That's it. Athena handles the rest.**

---

## Athena Pre-Push Gates (Automatic)

Every `git push` triggers:

```
🧠 Athena validates:
  1. Health probes (/ready)
  2. Smoke tests (via Athena API)
  3. Ghost detection (PID count)

✅ All pass → Push proceeds
❌ Any fail → Push blocked with fix instructions
```

**No garbage branches. No broken builds.**

---

## Canary Deployment (On-Demand)

```bash
make athena-canary
```

**What happens:**
1. Deploys your branch to :8015
2. Monitors SLOs for 5 minutes
3. Collects: error rate, latency, requests
4. Decides:
   - ✅ SLOs met → Promotes (safe to merge)
   - ❌ SLOs violated → Rolls back + auto-cleanup

**No unstable code in production.**

---

## Commands You'll Use Daily

### Stack
```bash
make stack-up              # Start everything
make stack-down            # Stop everything
make truth                 # Reality check
```

### Autonomous
```bash
make auto-heal-start       # Enable watchdog
make auto-heal-logs        # Watch recoveries
```

### GitOps
```bash
git push                   # Athena validates
make athena-canary         # Test branch as canary
make athena-history        # View decisions
make athena-cleanup        # Remove canaries
```

### Emergency
```bash
make nuke-ports            # Kill ghosts
make athena-override       # Break glass (logged!)
```

---

## When Athena Rejects Your Push

```
❌ Athena: Push rejected
Reason: Smoke tests failed
Fix: make athena-tests-smoke
```

**What to do:**
1. Run the fix command shown
2. Check what failed
3. Fix the issue
4. Try `git push` again

**Athena won't let broken code through.**

---

## Canary SLO Thresholds

| Metric | Threshold | Action if Violated |
|--------|-----------|-------------------|
| Error rate | < 1% | ❌ Rollback |
| p95 Latency | < 250ms | ❌ Rollback |
| MTTR | < 60s | ❌ Rollback |

**Athena promotes only if ALL thresholds met.**

---

## Audit Trail

```bash
make athena-history
```

**Shows:**
- Every canary deployment
- SLO metrics collected
- Promote/rollback decisions
- Auto-cleanup events
- Admin overrides

**Filter by branch:**
```bash
grep 'branch=feature/myfeature' /tmp/athena_canary_audit.log
```

---

## Truth Sources (When Confused)

```bash
1. make truth              # What's running?
2. make athena-history     # What did Athena decide?
3. make auto-heal-logs     # What did watchdog do?
4. curl -I :8014/health    # Who's answering?
```

**Receipts not vibes.**

---

## Emergency Override

```bash
make athena-override
ATHENA_OVERRIDE=1 git push --no-verify
```

**Use sparingly:**
- Logged with username, branch, commit
- Team gets "glass broken" notification
- Audit trail preserved

---

## The Discipline

### ✅ DO
- Let Athena validate every push
- Run `make athena-canary` before merging
- Check `make athena-history` weekly
- Trust the gates (they're there for a reason)

### ❌ DON'T
- Use `--no-verify` (defeats Athena)
- Ignore rollback decisions
- Override without documenting why
- Skip canary testing on critical changes

---

## What Athena Prevents

- 🛑 Broken builds reaching main
- 🛑 SLO violations in production
- 🛑 Secret leaks
- 🛑 Ghost process pollution
- 🛑 Unstable deployments
- 🛑 Extended downtime

---

## Notifications

```bash
# Wire your platform
export NOTIFY_WEBHOOK='https://hooks.slack.com/...'

# Athena will notify on:
# - Canary deployed
# - SLO monitoring
# - Promote/rollback decisions
# - Watchdog recoveries
# - Admin overrides
```

---

## Quick Reference

| Situation | Command | Result |
|-----------|---------|--------|
| Start working | `make stack-up` | Services start |
| Enable guardian | `make auto-heal-start` | Watchdog active |
| Push code | `git push` | Athena validates |
| Test as canary | `make athena-canary` | Deploy + decide |
| View decisions | `make athena-history` | Audit trail |
| Emergency | `make athena-override` | Bypass (logged) |
| Clean up | `make athena-cleanup` | Remove canaries |
| End of day | `make stack-down` | Services stop |

---

## The Philosophy

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                   ┃
┃  You write code.                  ┃
┃  Athena decides if it ships.      ┃
┃                                   ┃
┃  Fast • Boring • Bulletproof      ┃
┃  Receipts Not Vibes               ┃
┃                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Status

```
System:      🧠 Athena-Controlled
Gatekeeper:  Every push, every branch
Downtime:    Near-zero (watchdog)
Bad Deploys: Prevented (canary gates)
Manual Work: ↓ 99%
Philosophy:  Autonomous GitOps
```

---

**Athena controls everything.**  
**And that's exactly how it should be.** 👑

---

*Built: 2025-10-12*  
*Tiers: 5/5 COMPLETE*  
*Status: OPERATIONAL*  
*Gatekeeper: 🧠 Athena*

