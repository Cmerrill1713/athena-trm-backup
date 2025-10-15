# Governance System Runbook

## Overview

This runbook provides operational procedures for the Governance Control Plane. The system automatically enforces AI policy compliance, manages canary deployments, and provides real-time visibility into governance decisions.

## 🚨 Emergency Procedures

### Immediate Rollback (HARD_FAIL Detected)

```bash
# Emergency rollback - stops all governance services and restores safe state
make governance-rollback

# Verify rollback completed
docker ps | grep governance  # Should show services restarting
tail -5 logs/canary_decisions.log  # Check latest decision
```

### Freeze All Promotions (Circuit Breaker)

```bash
# Temporarily disable governance checks for emergency manual override
touch .governance_paused

# Resume governance after emergency resolved
rm .governance_paused
make governance-up
```

### Unquarantine Service (After Investigation)

```bash
# Restore service after root cause identified and fixed
make governance-deploy

# Monitor for 10 minutes, then run canary watch
sleep 600
make governance-canary-watch
```

## 🔧 Maintenance Procedures

### Daily Operations

#### 1. Health Check (Morning)
```bash
# Check all governance services are running
docker ps | grep governance

# Verify Prometheus targets are UP
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("governance")) | .health'

# Check recent decisions
tail -10 logs/canary_decisions.log
```

#### 2. Log Rotation (Automated - Daily at 00:00)
```bash
# Manual rotation if needed
./scripts/rotate_audit.sh

# Verify rotation
ls -la logs/archive/
```

#### 3. Policy Bundle Audit
```bash
# Check for unauthorized policy changes
git status manifests/policy_bundle.json

# Rebuild if needed
python legislative/policy_compiler.py policy/governance_policy.yaml policy/god_judge_verdict_mapping.yaml
```

### Weekly Operations

#### 1. Audit Log Backup (Monday 01:00)
```bash
# Mirror audit logs to S3 with retention lock
rclone copy ./logs/archive s3:governance-audit/$(date +%Y-%U)/ --checksum --immutable
```

#### 2. Performance Review
```bash
# Analyze decision patterns last week
grep "$(date -d 'last monday' +%Y-%m-%d)" logs/canary_decisions.log | grep "DECISION:" | cut -d' ' -f4 | sort | uniq -c

# Check for governance cost spikes
curl -s "http://localhost:9090/api/v1/query?query=governance_cost_usd_per_min" | jq '.data.result[0].value[1]'
```

#### 3. Alertmanager Configuration Review
```bash
# Verify alert routing
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | select(.labels.job | contains("governance"))'
```

### Monthly Operations

#### 1. Drill Execution (First Monday, 15 minutes)
- **Objective**: Verify team can execute emergency procedures under time pressure
- **Procedure**:
  1. Force a synthetic HARD_FAIL: `REQ_ECE_POST_LE=0.01 make governance-canary-watch`
  2. Execute rollback: `make governance-rollback`
  3. Verify Slack notifications arrived
  4. Verify Grafana annotations appeared
  5. Restore normal operation: `make governance-deploy`

#### 2. Policy Review
```bash
# Review governance thresholds vs business requirements
cat policy/governance_policy.yaml

# Check threshold effectiveness
grep "ROLLBACK" logs/canary_decisions.log | tail -20 | grep -o '"ece_post":[^,}]*' | sort | uniq -c
```

#### 3. Cost Optimization
```bash
# Review governance costs over month
curl -s "http://localhost:9090/api/v1/query_range?query=governance_cost_usd_per_min&start=$(date -d 'last month' +%s)&end=$(date +%s)&step=3600" | jq '.data.result[0].values'
```

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

#### Governance Health
- `governance_ece`: Should be < 0.06
- `governance_entropy_drift`: Should be < 0.25
- `governance_violation_rate`: Should be < 0.02

#### System Health
- `governance_canary_samples_total`: Should increase under traffic
- Container health checks: All governance services should be healthy
- Alertmanager alerts: Should not have pending governance alerts

### Alert Severity Levels

#### 🔴 CRITICAL (Page Immediately)
- Governance service down
- HARD_FAIL detected (automatic rollback)
- Audit log rotation failed
- Policy bundle drift detected

#### 🟡 WARNING (Slack Notification)
- HOLD state persists > 3 windows
- Cost per minute > $2
- Decision confidence low

#### 🔵 INFO (Dashboard Only)
- PROMOTE decisions
- Routine log rotations
- Synthetic probe completions

### Alert Response Times

- **CRITICAL**: < 5 minutes
- **WARNING**: < 30 minutes
- **INFO**: Best effort

## 🔍 Troubleshooting

### Common Issues

#### Governance Services Not Starting
```bash
# Check logs
docker logs governance-orchestrator

# Verify dependencies
docker ps | grep -E "(postgres|redis|prometheus)"

# Check network
docker network inspect athena-network
```

#### Metrics Not Appearing in Prometheus
```bash
# Check service health
curl -f http://localhost:9109/health

# Verify Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("governance"))'

# Check metrics endpoint
curl -s http://localhost:9109/metrics | head -10
```

#### Slack Notifications Not Working
```bash
# Test webhook
SLACK_WEBHOOK_URL="your-webhook-url" ./scripts/gov_notify_slack.sh TEST "Test message"

# Check webhook validity
curl -X POST -H 'Content-type: application/json' -d '{"text":"Test"}' "your-webhook-url"
```

#### Grafana Annotations Missing
```bash
# Test Grafana API
curl -H "Authorization: Bearer YOUR_TOKEN" "YOUR_GRAFANA_URL/api/annotations"

# Check token permissions
curl -H "Authorization: Bearer YOUR_TOKEN" "YOUR_GRAFANA_URL/api/user"
```

#### Policy Bundle Drift
```bash
# Rebuild and check
python legislative/policy_compiler.py policy/governance_policy.yaml policy/god_judge_verdict_mapping.yaml
git diff manifests/policy_bundle.json

# If changes are intentional, commit them
git add manifests/policy_bundle.json
git commit -m "Update policy bundle after review"
```

## 🔐 Security & Compliance

### RBAC Configuration
- Slack webhook scoped to governance-only channel
- Grafana token with annotation-only permissions
- GitHub secrets encrypted and rotated quarterly

### Audit Requirements
- All governance decisions logged with timestamps
- Logs rotated daily with SHA256 checksums
- Immutable storage in S3 with retention locks
- Monthly audit reviews for compliance

### Secret Management
```bash
# Rotate Slack webhook
# 1. Create new webhook in Slack
# 2. Update GitHub secret SLACK_WEBHOOK_URL
# 3. Delete old webhook
# 4. Update Alertmanager configuration if used

# Rotate Grafana token
# 1. Create new API token in Grafana
# 2. Update GitHub secret GRAFANA_TOKEN
# 3. Revoke old token
```

## 📈 Performance Optimization

### Backpressure Handling
When HOLD persists > 3 windows:
```bash
# Automatically reduce canary percentage
echo "0.1" > canary_percentage.txt  # Reduce to 10%

# Or widen observation window
WINDOW_MINUTES=30 make governance-canary-watch
```

### Cost Controls
```bash
# Set cost caps
echo "5.0" > governance_cost_cap_usd_per_hour.txt

# Monitor and alert on breaches
curl -s "http://localhost:9090/api/v1/query?query=governance_cost_usd_per_min > 2" | jq '.data.result | length'
```

## 🧪 Testing Procedures

### Synthetic Probe (Nightly)
```bash
# Run Devil's Advocate suite
python scripts/devil_advocate_probe.py --shadow-slice --canary-trigger

# Verify canary activated
tail -f logs/canary_decisions.log | grep "SYNTHETIC"
```

### Integration Testing
```bash
# Full pipeline test (non-production)
make governance-gate
make governance-deploy
sleep 300  # Wait for canary
make governance-canary-watch
```

### Load Testing
```bash
# Test governance under load
ab -n 10000 -c 50 http://localhost:8888/api/endpoint

# Monitor governance response
watch -n 5 'curl -s "http://localhost:9090/api/v1/query?query=governance_ece" | jq ".data.result[0].value[1]"'
```

## 📋 Checklist Templates

### Pre-Deployment Checklist
- [ ] Governance services healthy
- [ ] Prometheus targets UP
- [ ] Alertmanager configured
- [ ] Slack webhook valid
- [ ] Grafana token active
- [ ] Policy bundle unchanged
- [ ] Audit log rotated recently

### Post-Deployment Checklist
- [ ] Governance KPIs within bounds
- [ ] Slack notifications working
- [ ] Grafana annotations appearing
- [ ] Audit log has new entries
- [ ] No pending alerts

### Incident Response Checklist
- [ ] Acknowledge alert
- [ ] Assess impact (rollback needed?)
- [ ] Execute runbook procedure
- [ ] Notify stakeholders
- [ ] Document root cause
- [ ] Update runbook if needed

---

## 📞 Support Contacts

- **Primary**: Governance team Slack channel
- **Escalation**: On-call engineer (PagerDuty)
- **Vendor**: Grafana/Prometheus support for infrastructure issues

**Last Updated**: October 2025
**Version**: 1.0
