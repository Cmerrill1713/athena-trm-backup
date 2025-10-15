# Governance CI/CD Integration

## Overview

Your governance system now integrates with CI/CD to block bad releases before they hit production and enable one-command rollbacks.

## 🚀 What Was Implemented

### 1. Pre-Deploy Governance Gate (`scripts/gov_predeploy_gate.py`)
- **Purpose**: Blocks deployment if governance health is red
- **Checks**: ECE, entropy drift, violation rates against live Prometheus
- **Failure Modes**: Returns exit code 1 if any threshold exceeded

### 2. Deployment Scripts
- **`scripts/gov_deploy.sh`**: Runs gate → pulls images → starts stack → verifies health
- **`scripts/gov_promote.sh`**: Logical promote hook (customize for your traffic shifting)
- **`scripts/gov_rollback.sh`**: Fast rollback via service restart + state reset

### 3. GitHub Actions Workflow (`.github/workflows/governance-deploy.yml`)
- **Triggers**: Push to main branch or manual dispatch
- **Jobs**:
  - `gate-and-deploy`: Runs pre-deploy checks, then deploys via SSH
  - `promote-or-rollback`: Decides next action based on canary results

### 4. Makefile Shortcuts
```bash
make governance-gate      # Test pre-deploy health
make governance-deploy    # Full deploy with gate
make governance-promote   # Promote canary to production
make governance-rollback  # Emergency rollback
```

## 🔧 Configuration

### Environment Variables
Set these in your deployment environment:

```bash
# Prometheus endpoint
PROM_URL=http://localhost:9090

# Governance thresholds
ECE_MAX=0.06
ENTROPY_CRIT=0.25
VIOLATION_SPIKE=0.02

# Deployment config
COMPOSE_FILE=docker-compose.athena-governance.yml
```

### GitHub Secrets (for remote deployment)
```yaml
PROM_URL: http://your-prometheus:9090
DEPLOY_HOST: your.server.com
DEPLOY_USER: deploy-user
DEPLOY_SSH_KEY: your-ssh-private-key
DEPLOY_PATH: /path/to/deployment/directory
```

## 🚦 Workflow

### Automatic CI/CD Flow
1. **Push to main** → GitHub Actions triggers
2. **Pre-deploy gate** → Query Prometheus for governance KPIs
3. **If gate passes** → Deploy via SSH to production host
4. **Post-deploy** → Monitor canary window (manual decision for now)
5. **Promote or rollback** → Based on governance alerts/metrics

### Manual Operations
```bash
# Test gate locally
make governance-gate

# Full deploy (with gate)
make governance-deploy

# Emergency rollback
make governance-rollback
```

## 🔍 Testing

### Local Testing
```bash
# Test gate against local Prometheus
make governance-gate

# Force a bad verdict to test rollback
curl -s -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"smoke-1","verdict":"HARD_FAIL","ece_estimate":0.09,"actions":["ROLLBACK"]}'
```

### CI/CD Testing
- Push a test branch to trigger the workflow
- Check GitHub Actions logs for gate results
- Verify deployment succeeds/fails as expected

## 🛡️ Safety Features

### Pre-Deploy Blocking
- **ECE > 6%**: Blocks deploy (evolutionary computation efficiency)
- **Entropy drift ≥ 25%**: Blocks deploy (behavior instability)
- **Violation rate > 2%**: Blocks deploy (policy breaches)

### Fast Rollback
- **Service restart**: Restarts governance-orchestrator
- **State reset**: Resets exec_state.json to safe version
- **One command**: `make governance-rollback`

### Monitoring Integration
- **Prometheus queries**: Real-time health checks
- **AlertManager**: Governance alerts trigger notifications
- **Grafana dashboards**: Visual governance KPIs

## 🚨 Alert Integration

Configure AlertManager to notify on governance events:
- Slack/Discord webhooks for critical alerts
- PagerDuty for production incidents
- Email notifications for team awareness

## 🔄 Next Steps

### Immediate
1. **Configure secrets** in GitHub repository settings
2. **Test workflow** with a feature branch push
3. **Customize promote script** for your traffic management

### Advanced Features
- **Auto-promote**: Add post-deploy canary watcher that auto-promotes on green
- **Gradual rollout**: Implement percentage-based traffic shifting
- **Multi-environment**: Extend to staging/production with different thresholds
- **Rollback automation**: Trigger rollback on governance alert webhooks

## 🐛 Troubleshooting

### Gate Always Passes (0.000 metrics)
- **Cause**: Prometheus not running or metrics not available
- **Fix**: Ensure governance stack is running: `make governance-up`

### SSH Deployment Fails
- **Cause**: Missing SSH secrets or wrong host config
- **Fix**: Verify GitHub secrets and server connectivity

### Rollback Doesn't Restore State
- **Cause**: Custom state persistence not implemented
- **Fix**: Modify `gov_rollback.sh` to restore your state format

---

Your governance system now prevents bad deployments and enables confident rollbacks. The verdict pipeline runs on real production traffic, not test events! 🧠⚖️⚡
