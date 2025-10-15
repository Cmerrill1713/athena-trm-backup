# ✅ v1.0.2-ghost Post-Ship Checklist

**Ship Date**: October 14, 2025  
**Tags**: `v1.0.2-ghost`, `v1.0.2-ghost-gold`  
**Status**: 🚀 **SHIPPED**

---

## 📋 Immediate Actions (Next 15 min)

### 1. Create GitHub Release
- [ ] Go to: https://github.com/Cmerrill1713/athena-trm-backup/releases/new
- [ ] Select tag: `v1.0.2-ghost`
- [ ] Title: **Athena v1.0.2 — Ghost Mode**
- [ ] Body: Copy from `RELEASE_NOTES_v1.0.2.md`
- [ ] Mark as **Latest Release**
- [ ] Publish

### 2. Sanity Checks
```bash
# Backend health
curl -sS http://localhost:8035/health || echo "⚠️ backend down"

# Avatar status (should be ghost)
curl -sS http://localhost:8035/v1/avatar/status | jq '.state'
# Expected: "ghost"

# Metrics endpoint
curl -sS http://localhost:9108/metrics | grep athena_avatar_state
# Expected: athena_avatar_state 0.0 (ghost=0, photoreal=1)
```

### 3. Verify Tags
```bash
# List all v1.0.2 tags
git ls-remote --tags origin | grep v1.0.2

# Expected:
# v1.0.2-ghost
# v1.0.2-ghost-gold
```

---

## 📊 Monitoring (First 24 Hours)

### Prometheus Queries

**Error Rate** (target: <1%)
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m]))
```

**Request Latency p95** (target: <500ms)
```promql
histogram_quantile(0.95, rate(http_request_latency_seconds_bucket[5m]))
```

**Avatar State** (should be 0=ghost)
```promql
athena_avatar_state
```

**Request Rate**
```promql
rate(http_requests_total[5m])
```

### Grafana Dashboards

1. **Avatar Health**
   - Avatar State Distribution (should be 100% ghost)
   - Transition Success Rate (should be ~100%)
   - State Change Frequency

2. **System Health**
   - Request throughput
   - Error rate
   - Latency percentiles (p50, p95, p99)
   - Active connections

3. **Alerts**
   - Check no alerts firing
   - Verify thresholds (2%, 5%)

### Key Metrics to Watch

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Error Rate | <1% | >5% |
| P95 Latency | <500ms | >1s |
| Avatar State | 0 (ghost) | ≠0 |
| Uptime | 100% | <99% |
| Memory Usage | <200MB | >1GB |

---

## 🔥 Rollback Procedures

### Quick Rollback (Avatar Only)
```bash
# Force ghost mode
make avatar-rollback-force

# Disable rollout
make avatar-rollout-disable

# Verify
curl http://localhost:8035/v1/avatar/status | jq '.state'
```

### Full System Rollback
```bash
# Stop services
make stop-all

# Checkout previous version
git checkout v1.0.1

# Rebuild
make clean && make backend

# Verify
curl http://localhost:8035/health
```

### Emergency Contact
- On-Call: [Your contact]
- Escalation: [Senior engineer]
- Runbook: `OPERATORS_RUNBOOK.md`

---

## 🛡️ Drift Guard Setup

### Nightly Audit Cron
```bash
# Add to crontab
( crontab -l 2>/dev/null; echo "0 2 * * * cd /Users/christianmerrill/Documents/GitHub && make audit-quick >/tmp/audit_\$(date +\%F).log 2>&1" ) | crontab -

# Verify cron
crontab -l | grep audit

# Check logs next day
cat /tmp/audit_$(date +%F).log
```

### Weekly Drift Checks
- [ ] Compare prod config vs git
- [ ] Verify no manual changes
- [ ] Check Redis state consistency
- [ ] Review audit logs

---

## 🔒 Repository Protection

### Branch Protection (main)
- [ ] Go to: Settings → Branches → Add rule for `main`
- [ ] Require pull request reviews (1 reviewer)
- [ ] Require status checks:
  - [x] `lint-syntax` (Required)
  - [x] `guard-single-ui` (if restored)
- [ ] Include administrators
- [ ] Allow force pushes: NO
- [ ] Allow deletions: NO

### Tag Protection
- [ ] Settings → Tags → Add rule for `v*`
- [ ] Prevent tag deletion
- [ ] Require signed commits (optional)

### CODEOWNERS Enforcement
Already configured in `.github/CODEOWNERS`:
- AppEntry.swift
- guard_single_ui.sh
- lint.yml
- Makefile
- .flake8
- .pre-commit-config.yaml
- Package.swift

---

## 📝 Documentation Updates

### CHANGELOG.md
```markdown
## [1.0.2-ghost] - 2025-10-14

### Added
- Ghost avatar as default (rights-safe)
- Two-tier lint system (syntax required, style advisory)
- Single-UI architecture lockdown (7 layers)
- Avatar state API endpoints
- Comprehensive operator's runbook
- Pre-commit hooks for all contributors

### Fixed
- "Can't type" input bug (KeyCatchingTextEditor)
- Focus stealing in pop-out windows
- 5 critical syntax errors
- ServiceStatus type conflict
- Import order violations

### Changed
- Quarantined iOS code for macOS-only build
- Updated .flake8 with pragmatic exclusions
- Improved error handling and logging

### Security
- All API keys stored securely
- Feature flags for safe rollout
- Audit logging enabled

[1.0.2-ghost]: https://github.com/Cmerrill1713/athena-trm-backup/releases/tag/v1.0.2-ghost
```

### Update README.md
- [ ] Add v1.0.2 to version list
- [ ] Update installation instructions
- [ ] Link to release notes
- [ ] Update status badges

---

## 🎯 v1.0.3 Preparation

### Branch Setup
```bash
# Create/switch to v1.0.3 branch
git checkout -b feature/v1.0.3-morph-cleanup

# Verify clean state
git status

# Create task board
# (See V1_0_3_TASK_BOARD.md)
```

### Planning
- [ ] Review v1.0.2 production metrics (wait 24-48h)
- [ ] Prioritize iOS compatibility fixes
- [ ] Plan lint debt paydown strategy
- [ ] Schedule photoreal avatar rights review
- [ ] Design cinematic morph UX

---

## 📈 Success Metrics (7 Days)

### Technical
- [ ] Uptime: >99.5%
- [ ] Error rate: <1%
- [ ] P95 latency: <500ms
- [ ] Zero critical incidents
- [ ] Zero rollbacks needed

### Quality
- [ ] No syntax errors introduced
- [ ] Lint warnings decreasing
- [ ] Pre-commit adoption: 100%
- [ ] CI success rate: >95%

### Process
- [ ] All changes via PR
- [ ] Code review on every change
- [ ] Runbook followed for incidents
- [ ] Post-mortems for any issues

---

## 🔔 Alert Routing (This Week)

### Setup Alertmanager
```yaml
# alertmanager.yml
route:
  receiver: 'team-pager'
  routes:
    - match:
        severity: critical
      receiver: 'pager-critical'
    - match:
        severity: warning
      receiver: 'slack-warnings'

receivers:
  - name: 'pager-critical'
    pagerduty_configs:
      - service_key: '<your-key>'

  - name: 'slack-warnings'
    slack_configs:
      - api_url: '<webhook-url>'
        channel: '#athena-alerts'
```

### iOS Notifications
- [ ] Set up PagerDuty app
- [ ] Test critical alert delivery
- [ ] Configure quiet hours
- [ ] Set up escalation policy

---

## 🔐 Security Checklist

### Immediate
- [ ] Verify PHOTOREAL_RIGHTS_VERIFIED=false in prod
- [ ] Check Redis not externally accessible
- [ ] Review API key rotation schedule
- [ ] Audit recent access logs

### This Week
- [ ] Run security scan (`make security-scan`)
- [ ] Update dependencies
- [ ] Review GitHub security alerts
- [ ] Check for exposed secrets

---

## 🎊 Team Communication

### Announcement Template
```markdown
🚀 **Athena v1.0.2-ghost is LIVE!**

Key features:
- Ghost avatar (rights-safe, professional)
- Rock-solid single-UI architecture
- Sustainable two-tier CI/lint system
- Complete observability

What's working:
✅ Zero syntax errors
✅ CI green across all checks
✅ Comprehensive monitoring
✅ Clear rollback procedures

Links:
- Release: https://github.com/.../releases/tag/v1.0.2-ghost
- Runbook: OPERATORS_RUNBOOK.md
- Metrics: http://localhost:3001

Next up (v1.0.3):
- iOS compatibility
- Lint debt paydown
- Photoreal avatar (rights-pending)

Questions? Check the runbook or ping [your name]!
```

### Channels to Update
- [ ] Team Slack/Discord
- [ ] Project board
- [ ] Status page
- [ ] Stakeholder email

---

## 📊 Week 1 Review Meeting

### Agenda
1. Production metrics review (15 min)
2. Incidents & rollbacks (if any) (10 min)
3. Monitoring insights (10 min)
4. User feedback (10 min)
5. v1.0.3 planning (15 min)

### Prepare
- [ ] Screenshot key Grafana dashboards
- [ ] Export Prometheus query results
- [ ] List any incidents/alerts
- [ ] Gather user feedback
- [ ] Draft v1.0.3 priorities

---

## ✅ Final Verification

Before marking complete:
- [ ] GitHub Release created
- [ ] Golden snapshot tagged
- [ ] Sanity checks passed
- [ ] Monitoring confirmed
- [ ] Rollback tested
- [ ] Drift guard scheduled
- [ ] Branch protection enabled
- [ ] CHANGELOG updated
- [ ] Team notified
- [ ] v1.0.3 branch created

---

**Checklist Owner**: [Your Name]  
**Review Date**: October 21, 2025 (7 days)  
**Status**: 🚀 **IN PRODUCTION**

*"Ship fast, monitor closely, iterate continuously."*

