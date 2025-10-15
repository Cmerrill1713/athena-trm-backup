# Governance Operational Hardening

## Overview

Your governance system has been hardened for production operations with enterprise-grade reliability, observability, and operational procedures. This is now a mature control plane, not a science project.

## ✅ Implemented Features

### 1. **Immutable Audit Trail** 📋
- **Daily log rotation** with gzip compression and SHA256 checksums
- **Archive storage** with timestamped files
- **S3 mirroring** ready (add `rclone` config)
- **Retention locking** support for compliance

```bash
# Daily rotation (cron: 0 0 * * *)
./scripts/rotate_audit.sh

# Verify archives
ls -la logs/archive/*.gz.sha256
```

### 2. **Real-Time Notifications** 🔔
- **Slack alerts** for every governance decision (PROMOTE/ROLLBACK/HOLD)
- **Grafana annotations** marking decision points on dashboards
- **Alertmanager routing** ready for PagerDuty escalation
- **RBAC-scoped** channels for different severity levels

### 3. **Policy Drift Guards** 🔒
- **CI/CD blocking** if policy bundles change without review
- **Git diff checks** on `manifests/policy_bundle.json`
- **Automatic rebuild** verification in deployment pipeline

### 4. **Synthetic Testing** 🧪
- **Nightly Devil's Advocate** probes inject synthetic failures
- **Off-hours regression testing** keeps governance metrics warm
- **Automated scenario testing** (ECE spikes, entropy drift, etc.)
- **Shadow slice testing** without affecting production traffic

### 5. **Operational Runbook** 📖
- **Emergency procedures** for HARD_FAIL scenarios
- **Maintenance checklists** for daily/weekly/monthly operations
- **Troubleshooting guides** for common issues
- **Performance optimization** procedures

### 6. **Cost & Budget Controls** 💰
- **Per-minute cost tracking** with alerting
- **Automatic backpressure** when costs spike
- **Rate limiting** and budget caps
- **Optimization recommendations** based on usage patterns

## 🚀 Quick Start

### 1. Configure Secrets (GitHub Repository Settings)
```yaml
# Required
SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/..."
GRAFANA_URL: "https://your-grafana.com"
GRAFANA_TOKEN: "your-api-token"

# Optional (for remote deployments)
PROM_URL: "http://your-prometheus:9090"
DEPLOY_HOST: "your-server.com"
DEPLOY_USER: "deploy"
DEPLOY_SSH_KEY: "..."
```

### 2. Set Up Cron Jobs (Server)
```bash
# Daily log rotation at midnight
0 0 * * * /path/to/scripts/rotate_audit.sh

# Weekly S3 backup (Monday 01:00)
0 1 * * 1 rclone copy ./logs/archive s3:governance-audit/$(date +%Y-%U)/ --checksum --immutable
```

### 3. Enable Synthetic Testing
- **GitHub Actions**: `governance-nightly-probe.yml` runs automatically at 2 AM UTC
- **Manual testing**: `python3 scripts/devil_advocate_probe.py --all-scenarios`

### 4. Verify Setup
```bash
# Test notifications
make governance-gate  # Should pass with HOLD

# Test synthetic probe
python3 scripts/devil_advocate_probe.py --scenario random_good

# Check audit trail
tail -5 logs/canary_decisions.log
ls -la logs/archive/
```

## 📊 Monitoring Dashboard

### Key Metrics to Monitor

#### Governance Health
```
governance_ece < 0.06
governance_entropy_drift < 0.25
governance_violation_rate < 0.02
governance_canary_samples_total (increasing)
```

#### System Health
```
Container health: All governance services UP
Alertmanager: No pending governance alerts
Grafana: Annotations appearing on dashboards
Slack: Notifications delivered to channels
```

#### Cost Monitoring
```
governance_cost_usd_per_min < 2.0
Budget utilization < 80%
```

### Alert Thresholds

#### 🔴 CRITICAL (Page immediately)
- Governance service down
- HARD_FAIL with automatic rollback
- Audit log rotation failure
- Policy bundle drift detected

#### 🟡 WARNING (Slack notification)
- HOLD state > 3 windows
- Cost per minute > $2
- Decision confidence low

#### 🔵 INFO (Dashboard only)
- PROMOTE decisions
- Routine log rotations
- Synthetic probe completions

## 🔧 Maintenance Procedures

### Daily (Morning Check)
```bash
# Health verification
docker ps | grep governance
curl -f http://localhost:9109/health
curl -f http://localhost:9110/health
curl -f http://localhost:9111/health

# Recent decisions
tail -10 logs/canary_decisions.log
```

### Weekly (Monday Maintenance)
```bash
# Audit log backup to S3
rclone copy ./logs/archive s3:governance-audit/$(date +%Y-%U)/ --checksum

# Performance review
grep "ROLLBACK" logs/canary_decisions.log | tail -10
```

### Monthly (First Monday, 15-min drill)
```bash
# Emergency rollback drill
REQ_ECE_POST_LE=0.01 make governance-canary-watch  # Force rollback
make governance-rollback                           # Execute rollback
# Verify: Slack notification + Grafana annotation
make governance-deploy                             # Restore service
```

## 🚨 Emergency Procedures

### HARD_FAIL Detected
```bash
# Immediate rollback
make governance-rollback

# Verify rollback
docker logs governance-orchestrator | tail -10
tail -5 logs/canary_decisions.log
```

### Circuit Breaker (Freeze All)
```bash
# Emergency pause
touch .governance_paused

# Manual override for emergency deploy
# (Remove pause after root cause fixed)
rm .governance_paused
```

### Service Unquarantine
```bash
# After investigation and fix
make governance-deploy
sleep 600  # Wait for stabilization
make governance-canary-watch
```

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Notifications Not Working
```bash
# Test Slack
SLACK_WEBHOOK_URL="your-webhook" ./scripts/gov_notify_slack.sh TEST "Test"

# Test Grafana
GRAFANA_URL="your-url" GRAFANA_TOKEN="your-token" ./scripts/gov_notify_grafana.sh TEST "Test"
```

#### Metrics Not Appearing
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("governance"))'

# Verify service endpoints
curl -s http://localhost:9109/metrics | head -5
```

#### Policy Drift Errors
```bash
# Rebuild and check
python legislative/policy_compiler.py policy/governance_policy.yaml policy/god_judge_verdict_mapping.yaml
git diff manifests/policy_bundle.json

# If intentional, commit changes
git add manifests/policy_bundle.json
git commit -m "Policy update after review"
```

#### Log Rotation Issues
```bash
# Manual rotation
./scripts/rotate_audit.sh

# Check archives
ls -la logs/archive/
sha256sum -c logs/archive/*.sha256
```

## 📈 Performance Optimization

### Automatic Backpressure
When HOLD persists > 3 windows:
```bash
# Reduce canary percentage
echo "0.1" > canary_percentage.txt

# Or widen observation window
WINDOW_MINUTES=30 make governance-canary-watch
```

### Cost Optimization
```bash
# Set budget caps
echo "5.0" > governance_cost_cap_usd_per_hour.txt

# Monitor utilization
curl -s "http://localhost:9090/api/v1/query?query=governance_cost_usd_per_min"
```

## 🧪 Testing Procedures

### Synthetic Probe Testing
```bash
# Single scenario
python3 scripts/devil_advocate_probe.py --scenario ece_spike

# All scenarios
python3 scripts/devil_advocate_probe.py --all-scenarios

# With canary trigger
python3 scripts/devil_advocate_probe.py --scenario random_good --canary-trigger
```

### Integration Testing
```bash
# Full pipeline test
make governance-gate
make governance-deploy
sleep 300
make governance-canary-watch
```

### Load Testing
```bash
# Stress test governance
ab -n 10000 -c 50 http://localhost:8888/api/endpoint

# Monitor governance response
watch -n 5 'curl -s "http://localhost:9090/api/v1/query?query=governance_ece" | jq ".data.result[0].value[1]"'
```

## 📋 Production Readiness Checklist

### Day-2 Operations
- [ ] Governance services healthy in production
- [ ] Prometheus targets UP for all governance metrics
- [ ] Alertmanager routes configured for Slack/PagerDuty
- [ ] Slack notifications working in production channels
- [ ] Grafana annotations appearing on dashboards
- [ ] Audit logs rotating and archiving properly
- [ ] Synthetic probes running nightly without issues
- [ ] Runbook procedures tested by team members
- [ ] Monthly drills scheduled and documented

### Security & Compliance
- [ ] Slack webhook scoped to governance-only channel
- [ ] Grafana token with minimal required permissions
- [ ] GitHub secrets encrypted and access-controlled
- [ ] Audit logs mirrored to immutable storage
- [ ] Policy changes require dual approval

### Monitoring & Alerting
- [ ] All governance KPIs visible in Grafana
- [ ] Alert thresholds configured appropriately
- [ ] Notification channels tested end-to-end
- [ ] Cost monitoring and budget alerts active
- [ ] Performance metrics trending in expected ranges

---

## 🎯 Impact Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Reliability** | Science project | Production control plane |
| **Visibility** | Logs only | Real-time notifications + dashboards |
| **Accountability** | Manual tracking | Complete audit trail |
| **Operations** | Ad-hoc | Runbook-driven procedures |
| **Testing** | Manual | Automated synthetic probes |
| **Compliance** | Basic logging | Immutable audit trails + retention |

Your governance system is now **enterprise-hardened** with production-grade reliability, observability, and operational procedures. This is a mature control plane ready for serious production workloads! 🚀⚖️🛡️
