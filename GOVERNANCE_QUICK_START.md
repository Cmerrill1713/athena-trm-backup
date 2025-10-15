# Governance System: Quick Start Guide

## 🚀 Get Started in 5 Minutes

This quick start gets your complete governance system running with predictive intelligence, adaptive learning, and automated operations.

## Step 1: Deploy the Stack (2 minutes)

```bash
cd /Users/christianmerrill/Documents/GitHub

# Start unified Athena + Governance stack
docker compose -f docker-compose.athena-governance.yml up -d

# Verify all services are healthy
docker ps | grep governance
```

Expected output: 4 governance services running
- `governance-metrics-exporter`
- `governance-orchestrator`
- `governance-canary-monitor`
- `governance-slack-bot`

## Step 2: Verify Health (1 minute)

```bash
# Check governance services
curl http://localhost:9109/health  # Metrics Exporter
curl http://localhost:9110/health  # Orchestrator
curl http://localhost:9111/health  # Canary Monitor
curl http://localhost:8082/health  # Slack Bot

# Check monitoring
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health  # Grafana
```

## Step 3: Run Test Deployment (2 minutes)

```bash
# Test the governance gate
make governance-gate

# Predict rollback probability
make governance-predict

# Run synthetic canary analysis
make governance-canary-watch
```

Expected output:
```
✅ Governance gate PASSED
🔮 Rollback Probability: 0.0% (Risk Level: UNKNOWN)
[decider] HOLD: samples=None < 200
```

## 🎯 Essential Commands

### Daily Operations
```bash
make governance-gate              # Health check
make governance-predict           # Risk forecast
tail -10 logs/canary_decisions.log  # Recent decisions
```

### Deployment
```bash
make governance-deploy            # Deploy with gates
make governance-canary-watch      # Analyze canary
make governance-rollback          # Emergency rollback
```

### Learning & Optimization
```bash
make governance-adaptive-thresholds  # Learn from history
make governance-tune-windows         # Optimize windows
make governance-insights             # Get recommendations
```

## 🔔 Slack Integration (Optional)

### Setup in 3 Steps
1. **Create Slack App**: https://api.slack.com/apps
2. **Add Commands**: `/governance-status`, `/governance-force-promote`, `/governance-force-rollback`
3. **Configure Webhook**: Set `SLACK_WEBHOOK_URL` in GitHub secrets

### Test Commands
```
/governance-status        # Show current system health
```

## 📊 Grafana Dashboards (Optional)

### Access Dashboards
1. Open http://localhost:3001 (admin/admin)
2. Navigate to Dashboards
3. View:
   - Governance Overview
   - Canary Analysis
   - Predictive Analytics

## 🚨 Emergency Procedures

### Immediate Rollback
```bash
make governance-rollback
```

### Force Promote (Override)
```bash
make governance-promote
# OR via Slack:
/governance-force-promote
```

### Pause Governance (Emergency)
```bash
touch .governance_paused
# Resume later:
rm .governance_paused
make governance-up
```

## 📈 Monitoring Your First Deployment

### Pre-Deploy
```bash
# 1. Check governance health
make governance-gate

# 2. Predict rollback risk
make governance-predict

# 3. If green, proceed
make governance-deploy
```

### During Deploy
```bash
# Watch logs in real-time
docker logs -f governance-orchestrator

# Monitor metrics
watch -n 5 'curl -s http://localhost:9109/metrics | grep governance_ece'
```

### Post-Deploy
```bash
# Run canary analysis
make governance-canary-watch

# Check decision
tail -5 logs/canary_decisions.log

# View audit trail
ls -la logs/archive/
```

## 🔍 Troubleshooting

### Services Not Starting
```bash
# Check Docker logs
docker logs governance-orchestrator

# Verify dependencies
docker ps | grep -E "(postgres|redis|prometheus)"

# Restart services
docker compose -f docker-compose.athena-governance.yml restart
```

### Metrics Not Appearing
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | grep governance

# Verify metrics endpoint
curl http://localhost:9109/metrics | head -20
```

### Predictions Show "Insufficient Data"
**This is normal initially!** The predictive system needs:
- Minimum 10 governance decisions
- At least 7 days of history
- Regular deployment activity

**Solution**: Continue deploying normally. The system learns automatically.

## 📚 Next Steps

### Immediate (First Day)
1. ✅ Deploy the stack
2. ✅ Verify health checks
3. ✅ Run test deployment
4. ⬜ Configure Slack integration
5. ⬜ Set up Grafana dashboards

### Short Term (First Week)
1. ⬜ Accumulate governance decision history
2. ⬜ Enable weekly threshold learning
3. ⬜ Configure S3 audit backup
4. ⬜ Run monthly drill

### Medium Term (First Month)
1. ⬜ Analyze predictive accuracy
2. ⬜ Optimize thresholds based on patterns
3. ⬜ Fine-tune canary windows
4. ⬜ Review incident automation

## 🎯 Success Metrics

### Week 1 Goals
- [ ] All governance services running healthy
- [ ] Prometheus collecting metrics
- [ ] Slack notifications working
- [ ] At least 5 deployment decisions logged

### Month 1 Goals
- [ ] Adaptive thresholds calculated
- [ ] Canary windows optimized
- [ ] Predictive insights available
- [ ] Zero manual incident investigations

### Quarter 1 Goals
- [ ] Rollback rate < 10%
- [ ] Prediction confidence > 70%
- [ ] Zero governance service downtime
- [ ] Complete audit trail compliance

---

## 🏁 You're Ready!

Your governance system is **production-ready** and will:
- ✅ Monitor every deployment automatically
- ✅ Predict and prevent rollbacks
- ✅ Learn and adapt over time
- ✅ Provide complete visibility
- ✅ Empower your team with intelligent tools

**Start your first governance-protected deployment now!** 🚀

```bash
make governance-deploy
```

The system will guide you through the rest! 🧠⚖️✨


