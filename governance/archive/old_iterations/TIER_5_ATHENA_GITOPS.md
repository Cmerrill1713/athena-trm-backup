# 🧠 Tier 5: Athena Branch Enforcement — Autonomous GitOps

## The Final Evolution: Athena Decides Your Code's Fate

```
Tier 1: Deterministic      ✅ Complete
Tier 2: Autonomous         ✅ Complete  
Tier 3: Observable         ✅ Complete
Tier 4: Production-Grade   ✅ Complete
Tier 5: Athena GitOps      🚀 IN PROGRESS
```

**Athena is now the gatekeeper for every branch.**

---

## What This Is

**Athena Branch Enforcement** transforms your workflow from:

### Before
```bash
git add -A
git commit -m "new feature"
git push
# Hope it works in production
# Find out days later it breaks under load
```

### After
```bash
git add -A
git commit -m "new feature"
git push

# Athena pre-push hook runs:
# ✅ Health probes
# ✅ SLO validation  
# ✅ Security scan
# ✅ Secrets hygiene
# ❌ PUSH REJECTED if any gate fails

# OR for canary deployment:
make athena-canary
# Deploys to :8015
# Monitors for 5 minutes
# ✅ Auto-promotes if SLOs met
# ❌ Auto-rolls back + cleanup if failed
```

**Athena decides if your code ships.**

---

## The System

### 1. Pre-Push Hook (Global Enforcement)

**Installed:** `.git/hooks/pre-push`

**Runs on:** ALL branches (main, release, feature/*, hotfix/*)

**Gates:**
1. Health probes (/live, /ready)
2. Metrics export
3. Smoke tests
4. Security tools installed
5. No hardcoded secrets
6. Services running

**Result:**
- ✅ All pass → Push proceeds
- ❌ Any fail → Push rejected with fix instructions

### 2. Branch Canary System

**Command:** `make athena-canary`

**What it does:**
1. Deploys your branch to canary port (:8015)
2. Monitors SLOs for 5 minutes (configurable)
3. Collects metrics:
   - Error rate
   - p95 latency
   - Request count
4. Makes decision:
   - ✅ SLOs met → Promotes (safe to merge)
   - ❌ SLOs violated → Rolls back + auto-cleanup

**Audit logged:** Every deployment, every decision

### 3. Auto-Rollback on Failure

**Triggers:**
- Error rate > 1%
- p95 latency > 250ms
- MTTR > 60s (if watchdog involved)

**Actions:**
1. Stops canary
2. Removes canary environment
3. Logs rollback reason
4. (Optional) Notifies via webhook

**Clean:** Failed experiments don't pollute your system

### 4. Full Audit Trail

**Location:** `/tmp/athena_canary_audit.log`

**View:** `make athena-history`

**Sample entries:**
```
[2025-10-12T20:00:00Z] DEPLOY_START branch=feature/optimizer commit=abc123 port=8015 mirror=10%
[2025-10-12T20:05:00Z] METRICS branch=feature/optimizer requests=300 errors=0 error_rate=0.00% max_latency=185ms
[2025-10-12T20:05:01Z] PROMOTE branch=feature/optimizer commit=abc123 error_rate=0.00% latency=185ms
```

**Filter by branch:**
```bash
grep 'branch=feature/mybranch' /tmp/athena_canary_audit.log
```

### 5. Admin Override (Emergency Only)

**Command:** `make athena-override`

**What it does:**
- Prompts for admin password
- Logs the override (with username, branch, commit)
- Allows bypass of validation gates
- Sends "glass broken" notification

**Use sparingly:** Every override is audited

---

## How It Works

### Pre-Push Flow
```
git push
   ↓
[Athena Pre-Push Hook]
   ↓
┌──────────────────┐
│ 1. Health Probes │
│ 2. Metrics       │
│ 3. Smoke Tests   │
│ 4. Security      │
│ 5. Secrets       │
│ 6. Services      │
└──────────────────┘
   ↓
ALL PASS?
   ├─ YES → Push proceeds
   └─ NO  → Push rejected
             (with fix instructions)
```

### Canary Flow
```
make athena-canary
   ↓
[Deploy to :8015]
   ↓
[Monitor 5 min]
   ↓
[Collect SLO metrics]
   ↓
SLOs MET?
   ├─ YES → ✅ PROMOTE
   │         • Log success
   │         • Keep canary (manual cleanup)
   │         • Notify team
   │
   └─ NO  → ❌ ROLLBACK
             • Stop canary
             • Remove environment
             • Log failure
             • Notify team
```

---

## Commands

### Setup
```bash
make install-pre-push      # Install global hook (one-time)
```

### Deploy Canary
```bash
make athena-canary         # Deploy current branch as canary
# Monitors, decides, promotes/rollbacks automatically
```

### View History
```bash
make athena-history        # Show audit trail
grep 'branch=feature/ai' /tmp/athena_canary_audit.log  # Filter
```

### Cleanup
```bash
make athena-cleanup        # Remove all canary environments
```

### Emergency Override
```bash
make athena-override       # Break glass (logged!)
ATHENA_OVERRIDE=1 git push --no-verify
```

---

## Configuration

### Canary SLO Thresholds
```bash
# Edit scripts/canary_branch.sh:
MAX_ERROR_RATE=0.01        # 1%
MAX_P95_MS=250             # 250ms
MAX_MTTR_S=60              # 60s

# Monitor duration
MONITOR_DURATION=300       # 5 minutes (300s)

# Traffic mirror percentage
MIRROR_PERCENT=10          # 10%
```

### Pre-Push Gates
Edit `.git/hooks/pre-push` to customize:
- Which checks are blocking vs warning
- Timeout values
- Error messages

---

## Examples

### Example 1: Feature Branch Passes
```bash
$ git checkout -b feature/new-router
$ # Make changes
$ git add -A
$ git commit -m "Add new router"
$ git push

🧠 ATHENA PRE-PUSH ENFORCEMENT
Branch: feature/new-router
Commit: abc123

1/6: Health probes... ✅
2/6: Metrics export... ✅
3/6: Smoke tests... ✅
4/6: Security tools... ✅
5/6: Secrets hygiene... ✅
6/6: Services running... ✅

✅ ATHENA: PUSH APPROVED ✅

Pushing to origin...
```

### Example 2: Feature Branch Fails
```bash
$ git push

🧠 ATHENA PRE-PUSH ENFORCEMENT
Branch: feature/broken
Commit: def456

1/6: Health probes... ❌ FAILED
Reason: Readiness probe failed (503)
Fix: make stack-restart && make tier4-proof

❌ ATHENA: PUSH REJECTED ❌

Push aborted. Fix critical gates and retry.
```

### Example 3: Canary Deployment Success
```bash
$ make athena-canary

🧠 ATHENA CANARY DEPLOYMENT
Branch: feature/optimizer
Commit: abc123
Canary Port: 8015
Mirror: 10%

📦 Step 1/5: Deploying canary...
✅ Canary deployed (PID: 12345)

📊 Step 2/5: Monitoring SLOs for 300s...
..............................

✅ Monitoring complete

📊 Step 3/5: Canary metrics:
  Requests: 300
  Errors: 0
  Error rate: 0.00%
  Max latency: 185ms

🎯 Step 4/5: Promotion decision...

✅ CANARY PROMOTED ✅

Branch: feature/optimizer
Metrics: Error 0.00%, Latency 185ms

Canary passed SLO gates. Safe to merge.
```

### Example 4: Canary Deployment Rollback
```bash
$ make athena-canary

🧠 ATHENA CANARY DEPLOYMENT
Branch: feature/bad-code  
Commit: xyz789

[... deployment ...]

📊 Step 3/5: Canary metrics:
  Requests: 300
  Errors: 15
  Error rate: 5.00%
  Max latency: 450ms

🎯 Step 4/5: Promotion decision...

❌ CANARY REJECTED ❌

Branch: feature/bad-code
Reason: Error rate 5.00% > 1.00%

Canary failed SLO gates. Do not merge.

🧹 Cleaning up failed canary...
✅ Canary environment torn down

Fix the issues and try again.
```

---

## Integration with Notifications

### Wire to Slack/Discord/Telegram
```bash
# Export webhook
export NOTIFY_WEBHOOK='https://hooks.slack.com/services/YOUR/WEBHOOK'

# Deploy canary
make athena-canary

# You'll get notifications:
# - "Canary deployed: feature/optimizer on :8015"
# - "Monitoring SLOs for 5 minutes..."
# - "✅ Canary promoted! Safe to merge"
# OR
# - "❌ Canary rolled back: Error rate 5%"
```

---

## Audit Trail

### View History
```bash
make athena-history
```

**Output:**
```
🧠 Athena Canary Audit Trail
════════════════════════════════════════
[2025-10-12T20:00:00Z] DEPLOY_START branch=feature/ai-router commit=abc123 port=8015 mirror=10%
[2025-10-12T20:05:00Z] METRICS branch=feature/ai-router requests=300 errors=0 error_rate=0.00% max_latency=185ms
[2025-10-12T20:05:01Z] PROMOTE branch=feature/ai-router commit=abc123 error_rate=0.00% latency=185ms
[2025-10-12T20:10:00Z] DEPLOY_START branch=feature/bad-code commit=def456 port=8015 mirror=10%
[2025-10-12T20:15:00Z] METRICS branch=feature/bad-code requests=300 errors=15 error_rate=5.00% max_latency=450ms
[2025-10-12T20:15:01Z] ROLLBACK branch=feature/bad-code commit=def456 reason="Error rate 5.00% > 1.00%"
[2025-10-12T20:15:02Z] CLEANUP branch=feature/bad-code status=complete
```

### Query Specific Branch
```bash
grep 'branch=feature/optimizer' /tmp/athena_canary_audit.log
```

---

## Best Practices

### ✅ DO
- Run `make athena-canary` before merging to main
- Check `make athena-history` to see past deployments
- Use override only in true emergencies
- Let Athena auto-cleanup failed canaries
- Review audit log weekly

### ❌ DON'T
- Use `--no-verify` to skip pre-push hook (defeats the purpose)
- Ignore canary rollbacks (they indicate real issues)
- Override gates without documenting why
- Leave canary environments running forever
- Merge without green canary test

---

## The Philosophy

### Before (Tier 4)
"I validate my changes before deploying"

### After (Tier 5)
"Athena validates my changes and decides if they deploy"

**You write code.**  
**Athena decides if it ships.**

---

## What This Prevents

### 🛑 Bad Code in Production
- Pre-push hook catches issues before they reach main
- Canary system validates under load
- Auto-rollback prevents bad deploys

### 🛑 Broken Builds
- Health gates ensure services start
- Smoke tests catch regressions
- Security scans find vulnerabilities

### 🛑 Secret Leaks
- Pre-push scans for hardcoded tokens
- Forces use of secrets management
- Audit trail for compliance

### 🛑 SLO Violations
- Canary monitors error rate + latency
- Rejects deployments that violate SLOs
- Protects production from degradation

---

## Next Steps

### P0 (Now)
```bash
# 1. Install pre-push hook
make install-pre-push

# 2. Test it
git commit --allow-empty -m "test"
git push  # Hook runs!

# 3. Deploy a canary
make athena-canary

# 4. View history
make athena-history
```

### P1 (This Week)
```bash
# Wire notifications
export NOTIFY_WEBHOOK='...'

# Run 24h soak with canary
# (coming in next step)

# Tag ready for prod
git tag -a v0.9.3-ready -m "Athena GitOps complete"
```

---

## Files Created

### Enforcement System
```
.git/hooks/pre-push          - Global validation hook
scripts/canary_branch.sh     - Canary deployment + decision engine
/tmp/athena_canary_audit.log - Audit trail
```

### Makefile Targets
```
install-pre-push             - Install hook
athena-canary                - Deploy + validate + decide
athena-history               - View audit trail
athena-cleanup               - Remove canaries
athena-override              - Emergency bypass
```

---

## Status

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                          ┃
┃  TIER 5: ATHENA GITOPS                   ┃
┃                                          ┃
┃  Pre-Push Hook:     ✅ Installed        ┃
┃  Canary System:     ✅ Operational      ┃
┃  Auto-Rollback:     ✅ Active           ┃
┃  Audit Trail:       ✅ Logging          ┃
┃  Auto-Cleanup:      ✅ Enabled          ┃
┃                                          ┃
┃  Athena now controls your deployments.  ┃
┃                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

**Built:** 2025-10-12  
**Status:** AUTONOMOUS GITOPS  
**Gatekeeper:** 🧠 Athena  
**Philosophy:** Code doesn't ship unless Athena approves  

**You write code. Athena decides if it ships.** 🚀

