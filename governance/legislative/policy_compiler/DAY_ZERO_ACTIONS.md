# ✅ Day-0 Actions - v1.0.2-ghost

**Status**: 🚀 **Code Shipped, Services Need Start**  
**Date**: October 14, 2025

---

## 🎯 Immediate Actions (Next 10 min)

### 1. Start Backend Services
```bash
cd /Users/christianmerrill/Documents/GitHub

# Start backend
make backend

# Wait 10 seconds, then verify
sleep 10
curl -sS http://localhost:8035/health
curl -sS http://localhost:8035/v1/avatar/status | jq
```

**Expected**:
- Health: `{"status": "ok", "timestamp": <unix_ts>}`
- Avatar: `{"state": "ghost", "morph_enabled": false, ...}`

---

### 2. Verify Tags (DONE ✅)
```bash
git fetch --tags
git tag -l 'v1.0.2-ghost*'
```

**Result**:
```
v1.0.2-ghost
v1.0.2-ghost-gold
```

✅ **Both tags pushed to GitHub**

---

### 3. Create GitHub Release

**URL**: https://github.com/Cmerrill1713/athena-trm-backup/releases/new

**Settings**:
- **Tag**: `v1.0.2-ghost`
- **Title**: `Athena v1.0.2 — Ghost Mode`
- **Body**: Copy from `RELEASE_NOTES_v1.0.2.md` (lines 1-200)
- **Mark as**: Latest release
- **Pre-release**: No

**Key Sections to Include**:
- Overview
- Key Features
- What's New
- Installation & Setup
- Known Limitations
- Bug Fixes

---

### 4. Verify Metrics (After Backend Start)
```bash
# Check Prometheus metrics
curl -sS http://localhost:9108/metrics | grep athena_avatar_state
# Expected: athena_avatar_state 0.0 (ghost=0, photoreal=1)

curl -sS http://localhost:9108/metrics | grep http_requests_total
# Should show request counts
```

---

### 5. Snapshot Dashboards (Optional)
```bash
# Create baseline directory
mkdir -p ops/baselines/v1.0.2-ghost

# Open Grafana
open http://localhost:3001

# Export dashboards as PNG to ops/baselines/v1.0.2-ghost/
# - avatar_health.png
# - system_metrics.png
# - error_rates.png
```

---

## 📊 Day-1 Actions (24 Hours)

### Monitor Production Health
```bash
# Error rate (target: <1%)
curl -sS http://localhost:9108/metrics | grep http_requests_total | grep '5..'

# Check logs
tail -f logs/backend.log

# Verify avatar state stable
watch -n 10 'curl -sS http://localhost:8035/v1/avatar/status | jq .state'
```

### Run Audit
```bash
make audit-quick > AUDIT_REPORT_v1.0.2.md

# Attach to GitHub release
git add AUDIT_REPORT_v1.0.2.md
git commit -m "docs: add v1.0.2 audit report"
git push
```

### Check Sentry (if configured)
- Review new issues in avatar endpoints
- Check error frequency
- Verify no regressions

---

## 🛡️ Guardrails Locked In

✅ **Active**:
1. Two-tier lint CI (syntax required, style advisory)
2. Golden tags (v1.0.2-ghost, v1.0.2-ghost-gold)
3. Pre-commit hooks (auto syntax check)
4. Operator's runbook (OPERATORS_RUNBOOK.md)
5. Rollback procedures (one command)
6. Post-ship checklist (POST_SHIP_CHECKLIST.md)
7. Monitoring queries (Prometheus/Grafana)

---

## 🚀 v1.0.3 Kickoff (This Week)

### Branch
```bash
git checkout feature/v1.0.3-morph-cleanup
# Already created and ready
```

### 7-Commit Plan
1. **Platform Split** - AvatarKit / AvatarMobileKit
2. **iOS Migration** - Move iOS code with platform guards
3. **Resolve Duplicates** - Namespace + typealiases
4. **CI Guards** - Platform-specific SwiftLint rules
5. **Reactivate Morph** - Runtime-flagged, MORPH_ENABLED=false
6. **Integration Tests** - macOS ghost, iOS full
7. **Docs Update** - Migration guide, ADR

### First Sprint (Sprint 1)
- iOS compatibility restored
- Lint warnings: 1,673 → <1,000
- Platform guards added
- PromptEngineerService fixed

**Task Board**: `V1_0_3_TASK_BOARD.md`

---

## ⚠️ Legal/Rights Reminder

**PHOTOREAL_RIGHTS_VERIFIED**: `false` (MUST STAY FALSE)

**Do NOT enable** photoreal avatar for commercial use until:
- [ ] Rights/consent verified
- [ ] Legal clearance received
- [ ] Documentation complete
- [ ] Flag set to `true`

**Ghost mode is safe** - already live and rights-cleared ✅

---

## 🔧 Quick Commands Reference

```bash
# Health checks
curl -sS http://localhost:8035/health
curl -sS http://localhost:8035/v1/avatar/status

# Metrics
curl -sS http://localhost:9108/metrics | grep athena_

# Daily QA
make audit-quick

# Rollout (v1.0.3)
NONINTERACTIVE=1 make avatar-go-live

# Emergency rollback
make avatar-rollback-force      # <5s to ghost
make avatar-rollout-disable     # kill switch

# Backend restart
make backend-restart

# Logs
tail -f logs/backend.log
make logs-backend
```

---

## 📋 Checklist

### Day-0 (Today)
- [ ] Start backend services
- [ ] Verify health endpoints
- [ ] Create GitHub Release
- [ ] Snapshot dashboards (optional)
- [ ] Verify tags pushed
- [ ] Check metrics available

### Day-1 (Tomorrow)
- [ ] Review 24h metrics
- [ ] Check error rates
- [ ] Run audit report
- [ ] Check Sentry (if configured)
- [ ] Verify no alerts

### This Week
- [ ] Start v1.0.3 Sprint 1
- [ ] Set up drift guard cron
- [ ] Enable branch protection
- [ ] Team announcement
- [ ] Begin iOS compatibility work

---

## 🎯 Success Criteria

**v1.0.2-ghost is successful if**:
- ✅ Backend health: 200 OK
- ✅ Avatar state: "ghost"
- ✅ Error rate: <1%
- ✅ No critical incidents
- ✅ Metrics flowing
- ✅ Rollback tested
- ✅ Team confident

---

## 📞 Support

**On-Call**: See `OPERATORS_RUNBOOK.md`  
**Rollback**: One command (`make avatar-rollback-force`)  
**Monitoring**: http://localhost:3001 (Grafana)  
**Logs**: `logs/backend.log`

---

**Status**: 🚀 **READY FOR DAY-0 VERIFICATION**

*Start the backend, verify health, create the release, and we're done!*

