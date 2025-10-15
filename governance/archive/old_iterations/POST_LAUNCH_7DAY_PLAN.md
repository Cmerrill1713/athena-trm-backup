# 📅 Post-Launch 7-Day Plan

**Release**: v0.9.2-green
**Launch Date**: October 12, 2025
**Status**: Production 🟢

---

## 🎯 Overview

**Goal**: Validate stability, collect metrics, optimize performance
**Duration**: 7 days
**Effort**: 15-30 min/day

---

## 📊 Day 0 (Launch Day) - 2 hours

### Immediate Actions
```bash
# 1. Verify all services
cd ~/Documents/GitHub/AI-Projects/universal-ai-tools
make green
make health  # All 8 services should be green

# 2. Check Dashboard
open http://localhost:8787
# Verify: p50 < 1000ms, p95 < 1500ms

# 3. Run eval sweep
curl http://localhost:8788/eval/run -d '{"capability":"summarize"}' | jq .
# Expected: 10/10 passing (100%)

# 4. Launch app and test
cd ~/Documents/GitHub/NeuroForgeApp
API_BASE=http://localhost:8014 QA_MODE=1 swift run
# Run First-Run Wizard → All green
```

### Monitoring Setup
- [ ] Dashboard bookmarked (localhost:8787)
- [ ] GitHub Actions notifications enabled
- [ ] Slack/Teams channel created
- [ ] Issue template ready

### Metrics Baseline (Record These)
```bash
# Latency baseline
curl "http://localhost:8787/metrics/latency?capability=summarize" | jq .
# Record: p50, p95

# Eval pass rate
curl "http://localhost:8788/eval/history?limit=10" | jq .
# Record: Pass rate %

# Service count
ps aux | grep -E "(rag_service|vision_rag|dashboard|eval_api)" | grep -v grep | wc -l
# Expected: 4 processes
```

### Criteria for Day 0 Success
- ✅ All 8 services healthy
- ✅ Dashboard accessible
- ✅ Evals: 10/10 passing
- ✅ First-Run Wizard: All steps green
- ✅ Trace Panel: Export works
- ✅ p95 < 1500ms

### If Anything Wobbles
**High latency (p95 > 1500ms)**:
```bash
# Check which provider is slow
# Dashboard → Win rates tab
# Temporarily disable slow provider if needed
```

**Eval failures**:
```bash
# Check which fixture failed
curl http://localhost:8788/eval/history | jq '.history | map(select(.passed == 0))'
# Review fixture expectations vs actual output
```

**Service down**:
```bash
# Restart all services
cd ~/Documents/GitHub/AI-Projects/universal-ai-tools
docker-compose down && make green
```

---

## 📈 Days 1-3 (Stabilization) - 15 min/day

### Daily Check (Morning)
```bash
# 1. Health check
make health

# 2. Dashboard metrics
open http://localhost:8787
# Check: p50, p95, win rates, shadow deltas

# 3. Eval run
curl http://localhost:8788/eval/run -d '{"capability":"summarize"}' | jq '.passed, .total'
# Target: ≥ 80% (currently 100%)

# 4. GitHub Actions
# Visit: https://github.com/YOUR_REPO/actions
# Verify: All workflows green
```

### Targets for Days 1-3
- **Eval pass rate**: ≥ 85%
- **p95 latency**: < 1500ms
- **Error rate**: < 1%
- **Service uptime**: 99%+
- **Telemetry DB**: < 200MB

### Data Collection
**Log These Daily**:
```bash
# Latency trend
echo "$(date),$(curl -s 'http://localhost:8787/metrics/latency?capability=summarize' | jq '.p50, .p95')" >> metrics.csv

# Eval pass rate
echo "$(date),$(curl -s http://localhost:8788/eval/history | jq '[.history[] | select(.passed == 1)] | length')" >> evals.csv

# Service health
echo "$(date),$(make health | grep '✅' | wc -l)" >> health.csv
```

### Weekly Actions
**Wednesday (Day 3)**:
```bash
# 1. Memory hygiene (if telemetry > 100MB)
cd ~/Documents/GitHub/AI-Projects/universal-ai-tools
# Backup
cp state/telemetry.sqlite state/telemetry.backup.$(date +%Y%m%d).sqlite

# 2. Review top latency traces
sqlite3 state/telemetry.sqlite \
  "SELECT capability, duration_ms, started_at FROM traces ORDER BY duration_ms DESC LIMIT 10;"

# 3. Snapshot bandit state
cp state/bandit.json state/bandit.$(date +%Y%m%d).json
```

---

## 🔬 Days 4-7 (Optimization) - 20 min/day

### Performance Analysis
```bash
# 1. Provider win rates
curl "http://localhost:8787/metrics/winrates?capability=summarize" | jq .

# 2. Identify slow providers
# Dashboard → Sort by p95
# Consider: Adjust bandit weights or unregister

# 3. Shadow delta analysis
curl "http://localhost:8787/metrics/shadow-delta?capability=summarize" | jq .
# If shadow wins consistently → promote
# If shadow loses → keep primary
```

### Optimization Actions
**If Provider Underperforms**:
```bash
# Check win rate
# If win_rate < 0.5 after 50+ samples → consider unregister

# Gradual reduction:
# Reduce shadow_percent from 0.5 → 0.2 if stable
```

**If Everything Stable**:
```bash
# Reduce monitoring frequency
# Shadow: 0.5 → 0.2 (still collecting data)
# Health checks: Every 6h → Every 12h (optional)
```

### Weekly Snapshot (Day 7)
```bash
# 1. Full backup
cd ~/Documents/GitHub/AI-Projects/universal-ai-tools
tar -czf backups/state-week1-$(date +%Y%m%d).tar.gz state/

# 2. Rotate telemetry (if > 500MB)
mv state/telemetry.sqlite state/telemetry.week1.sqlite
# Restart services to create fresh DB

# 3. Export metrics summary
echo "Week 1 Summary:" > week1-summary.txt
echo "Avg p50: $(awk -F, '{sum+=$2; count++} END {print sum/count}' metrics.csv)" >> week1-summary.txt
echo "Avg p95: $(awk -F, '{sum+=$3; count++} END {print sum/count}' metrics.csv)" >> week1-summary.txt
echo "Eval pass rate: $(awk '{sum+=$2; count++} END {print sum/count*100"%"}' evals.csv)" >> week1-summary.txt
```

---

## 🎯 Success Criteria (Week 1)

### Must Have ✅
- [ ] Services: 99%+ uptime
- [ ] Latency: p95 < 1500ms
- [ ] Evals: ≥ 80% pass rate
- [ ] GitHub Actions: All green
- [ ] Zero security incidents

### Nice to Have 🌟
- [ ] p95 < 1000ms (better than target)
- [ ] Eval pass rate > 90%
- [ ] User feedback collected
- [ ] Performance optimizations identified

### Red Flags 🚨
- ❌ p95 > 2000ms consistently
- ❌ Eval pass rate < 70%
- ❌ Service crashes (> 1 per day)
- ❌ Memory leak (DB > 1GB)
- ❌ Security issue reported

---

## 📋 Daily Checklist Template

**Morning Check (5 min)**:
```
[ ] make health → All green?
[ ] Dashboard → p95 < 1500ms?
[ ] GitHub Actions → All green?
[ ] Eval run → Pass rate ≥ 80%?
```

**Evening Review (10 min)**:
```
[ ] Log metrics to CSV
[ ] Review Trace Panel (spot check)
[ ] Check for new GitHub issues
[ ] Update team in Slack
```

**Weekly Deep Dive (30 min)**:
```
[ ] Analyze performance trends
[ ] Review provider win rates
[ ] Snapshot state/ directory
[ ] Rotate telemetry if needed
[ ] Plan optimizations for next week
```

---

## 🚨 Incident Response

### High Latency (p95 > 2000ms)
1. Check Dashboard → Identify slow provider
2. Trace Panel → Export slow trace JSON
3. Review provider configuration
4. Consider temporary unregister
5. Document in GitHub issue

### Eval Failures (< 70%)
1. Run full eval: `curl http://localhost:8788/eval/run`
2. Check history: `curl http://localhost:8788/eval/history`
3. Identify failing fixtures
4. Review fixture expectations
5. Fix provider or update fixtures

### Service Crash
1. Check logs: `docker-compose logs -f [service]`
2. Restart: `docker-compose restart [service]`
3. If persistent: `docker-compose down && make green`
4. Document root cause
5. Add monitoring alert

---

## 📞 Escalation

### Severity Levels

**P0 (Critical)** - All services down
- Response: Immediate
- Action: Full restart, check Docker
- Notify: Team immediately

**P1 (High)** - Major feature broken
- Response: < 1 hour
- Action: Identify root cause, rollback if needed
- Notify: Team within 2 hours

**P2 (Medium)** - Performance degraded
- Response: Same day
- Action: Investigate, optimize
- Notify: Daily standup

**P3 (Low)** - Minor issue
- Response: < 3 days
- Action: Log, prioritize
- Notify: Weekly review

---

## 🎉 Week 1 Success!

**If All Green**:
- ✅ Document lessons learned
- ✅ Share metrics with team
- ✅ Plan Week 2 optimizations
- ✅ Celebrate! 🎉

**Next Steps**:
- Week 2: Add more eval fixtures
- Week 3: Expand knowledge base
- Week 4: Enable branch protection

---

*Post-Launch Plan v1.0*
*Created: October 12, 2025*
*Status: Active 🟢*
