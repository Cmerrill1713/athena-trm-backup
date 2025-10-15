# 🚀 T+48 Hour Post-Launch Stabilization Checklist

**Version:** 1.0 | **Platform:** NeuroForge AI | **Launch Date:** [INSERT DATE]
**Status:** Production Stabilization Active

---

## 📋 Executive Summary

This checklist ensures your self-learning AI platform stabilizes properly in the first 48 hours post-launch. It provides **idiot-proof monitoring procedures** with clear pass/fail criteria, escalation triggers, and automated commands.

### 🎯 Stabilization Goals
- **T+1h:** Platform stable, basic functionality confirmed
- **T+24h:** Learning systems activated, quality metrics improving
- **T+48h:** Full optimization active, autonomous operation achieved

### 🚨 Emergency Contacts
- **On-Call Engineer:** [YOUR NAME] | [PHONE] | [EMAIL]
- **Rollback Commander:** [BACKUP CONTACT]
- **Customer Success:** [STAKEHOLDER CONTACT]

---

## ⏰ T+0 to T+1 Hour: IMMEDIATE POST-LAUNCH

### T+5 Minutes: Service Health Verification
```bash
# Run comprehensive health check
./VALIDATE_PLATFORM.sh
```
**✅ PASS Criteria:**
- [ ] All 4 core services healthy (Bridge, Athena, UAT, Kokoro)
- [ ] No 5xx errors in logs
- [ ] Response times < 100ms average

**❌ FAIL Action:**
```bash
# Immediate rollback if services unstable
./scripts/ROLLBACK_PLAYBOOK.sh
```

### T+15 Minutes: Traffic Flow Validation
```bash
# Check canary traffic distribution
curl -s http://localhost:9090/api/v1/query?query=judge_requests_total | jq '.data.result[0].value[1]'

# Verify learning system engagement
./scripts/learn/verify_learning.sh
```
**✅ PASS Criteria:**
- [ ] 25% canary traffic active
- [ ] Judge scoring requests > 0
- [ ] Bandit feedback loop active

**⚠️ WARNING Triggers:**
- Judge requests = 0 → Investigate Athena connectivity
- Bandit feedback = 0 → Check feedback endpoint

### T+30 Minutes: Performance Baseline
```bash
# Capture baseline metrics
./scripts/monitoring/quick_verify.sh

# Check latency distribution
curl -s "http://localhost:9090/api/v1/query_range?query=http_request_duration_seconds%7Bquantile%3D%220.95%22%7D&start=$(date -v-30M +%s)&end=$(date +%s)&step=60s"
```
**✅ PASS Criteria:**
- [ ] P95 latency < 200ms
- [ ] Error rate < 2%
- [ ] Memory usage < 80% per service

**📊 Record Baseline Values:**
- P95 Latency: ________ ms
- Error Rate: ________ %
- Memory Usage: ________ %

### T+45 Minutes: Learning System Warmup
```bash
# Force initial learning cycle
curl -X POST http://localhost:8014/api/chat \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test learning system activation","kind":"smalltalk"}'

# Check if learning data recorded
docker-compose -f deploy/docker-compose.prod.yml exec db psql -U neuroforge -d neuroforge -c "SELECT COUNT(*) FROM evaluations WHERE created_at > NOW() - INTERVAL '1 hour';"
```
**✅ PASS Criteria:**
- [ ] Learning database receiving data
- [ ] Judge scores generated (> 0 records)
- [ ] No learning system errors in logs

### T+60 Minutes: First Hour Assessment
**🎯 GO/NO-GO DECISION POINT**

```bash
# Comprehensive T+1h validation
./scripts/post_ship_smoke.sh
```
**✅ STABILIZE Criteria (Continue to T+24h):**
- [ ] All services healthy for 60+ minutes
- [ ] Traffic flowing without 5xx errors
- [ ] Learning systems recording data
- [ ] No emergency alerts triggered

**❌ ROLLBACK Criteria (Execute immediately):**
- [ ] 3+ service restarts in first hour
- [ ] Persistent 5xx errors (>5% rate)
- [ ] Security/auth failures detected
- [ ] Memory leak >20% growth in 60m

---

## ⏰ T+1 to T+24 Hours: LEARNING ACTIVATION PHASE

### Hourly Monitoring Schedule (T+1h to T+24h)

#### Every 2 Hours: Core Health Check
```bash
# Automated health sweep
for hour in {1..12}; do
  echo "=== T+${hour}h Health Check ==="
  ./scripts/monitoring/quick_verify.sh

  # Check error rate trend
  ERROR_RATE=$(curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[1h])" | jq '.data.result[0].value[1]')
  echo "Error rate: ${ERROR_RATE}"

  sleep 7200  # 2 hours
done
```

#### Every 4 Hours: Learning Progress Check
```bash
# Learning system advancement
echo "=== Learning System Status ==="
curl -s http://localhost:9090/api/v1/query?query=judge_helpfulness_avg | jq '.data.result[0].value[1]'

# Check variant distribution
curl -s http://localhost:9090/api/v1/query?query=bandit_variant_usage | jq '.data.result'

# RAG performance
curl -s http://localhost:9090/api/v1/query?query=rag_reranker_threshold | jq '.data.result[0].value[1]'
```

### T+6 Hours: Traffic Scale Decision
**🎯 CANARY SCALE-UP DECISION**

```bash
# Assess stability for 50% rollout
STABILITY_SCORE=$(curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(up==1[6h])" | jq '.data.result[0].value[1]')

if (( $(echo "$STABILITY_SCORE > 0.95" | bc -l) )); then
  echo "✅ Stability >95% - Scaling to 50%"
  export CANARY_PERCENTAGE=50
  ./scripts/canary_branch.sh enable
else
  echo "⚠️ Stability <95% - Holding at 25%"
fi
```

**✅ SCALE-UP Criteria:**
- [ ] Uptime >95% for 6+ hours
- [ ] Error rate <2% sustained
- [ ] No critical alerts in 6h window

### T+12 Hours: Midday Learning Assessment
```bash
# Generate midday learning report
./scripts/learn/nightly_learning_report.py

# Check for learning trends
curl -s http://localhost:9090/api/v1/query_range?query=judge_helpfulness_avg&start=$(date -v-12H +%s)&end=$(date +%s)&step=3600s
```

**📊 Expected at T+12h:**
- Judge helpfulness scores stabilizing
- Bandit algorithm showing preference patterns
- RAG reranker threshold adjustments

### T+18 Hours: Evening Performance Review
```bash
# Performance trend analysis
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[24h]))"

# Memory and resource check
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}"
```

**⚠️ ESCALATION Triggers:**
- Memory growth >15% from baseline
- CPU usage >70% sustained
- Latency degradation >50ms from baseline

### T+24 Hours: Day 1 Completion Assessment
**🎯 FULL PRODUCTION DECISION**

```bash
# Comprehensive T+24h evaluation
echo "=== T+24h Final Assessment ==="

# Service stability
UPTIME_24h=$(curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(up[24h])" | jq '.data.result[0].value[1]')
echo "24h Uptime: ${UPTIME_24h}"

# Learning activation
LEARNING_ACTIVE=$(curl -s "http://localhost:9090/api/v1/query?query=judge_evaluations_total" | jq '.data.result[0].value[1]')
echo "Learning Events: ${LEARNING_ACTIVE}"

# Quality improvement
QUALITY_DELTA=$(curl -s "http://localhost:9090/api/v1/query?query=delta(judge_helpfulness_avg[24h])" | jq '.data.result[0].value[1]')
echo "Quality Delta: ${QUALITY_DELTA}"
```

**✅ FULL PRODUCTION Criteria:**
- [ ] 24h uptime >99%
- [ ] Learning events >100
- [ ] Quality delta >0 (improvement)
- [ ] Error rate <1%
- [ ] No critical alerts in 24h

---

## ⏰ T+24 to T+48 Hours: OPTIMIZATION ACTIVATION

### Daily Monitoring Schedule (T+24h to T+48h)

#### T+30 Hours: Auto-Tuning Activation Check
```bash
# Verify auto-tuning active
curl -s http://localhost:9090/api/v1/query?query=bandit_promotions_total | jq '.data.result[0].value[1]'

# Check if promotions happening
docker-compose -f deploy/docker-compose.prod.yml exec db psql -U neuroforge -d neuroforge -c "
SELECT variant_name, is_promoted, promotion_score
FROM bandit_variants
WHERE updated_at > NOW() - INTERVAL '6 hours'
ORDER BY promotion_score DESC LIMIT 5;
"
```

**✅ Auto-Tuning Active:**
- [ ] Promotions detected (>0)
- [ ] Variant scores updating
- [ ] Traffic shifting toward better variants

#### T+36 Hours: Quality Uplift Measurement
```bash
# Measure learning impact
INITIAL_SCORE=$(curl -s "http://localhost:9090/api/v1/query?query=judge_helpfulness_avg offset 24h" | jq '.data.result[0].value[1]')
CURRENT_SCORE=$(curl -s "http://localhost:9090/api/v1/query?query=judge_helpfulness_avg" | jq '.data.result[0].value[1]')

IMPROVEMENT=$(echo "scale=2; ($CURRENT_SCORE - $INITIAL_SCORE) / $INITIAL_SCORE * 100" | bc)
echo "Quality Improvement: ${IMPROVEMENT}%"

# Expected: 5-15% improvement in first 24h of learning
```

#### T+42 Hours: Final Resource Check
```bash
# Resource utilization assessment
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.NetIO}}"

# Check for resource leaks
MEMORY_TREND=$(curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(process_resident_memory_bytes[48h])" | jq '.data.result[0].values')
echo "Memory trend stable: $(echo $MEMORY_TREND | jq 'length > 1')"
```

### T+48 Hours: Stabilization Complete
**🎯 FINAL SUCCESS ASSESSMENT**

```bash
# Generate final T+48h report
echo "=== T+48h STABILIZATION COMPLETE ==="

# Overall health score
HEALTH_SCORE=$(curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(up[48h])" | jq '.data.result[0].value[1]')
echo "Overall Health: $(echo "scale=2; $HEALTH_SCORE * 100" | bc)%"

# Learning effectiveness
LEARNING_EVENTS=$(curl -s "http://localhost:9090/api/v1/query?query=judge_evaluations_total" | jq '.data.result[0].value[1]')
echo "Learning Events: $LEARNING_EVENTS"

# Quality improvement
QUALITY_IMPROVEMENT=$(curl -s "http://localhost:9090/api/v1/query?query=delta(judge_helpfulness_avg[48h])" | jq '.data.result[0].value[1]')
echo "Quality Improvement: $QUALITY_IMPROVEMENT"

# Autonomous operation
AUTONOMOUS_PROMOTIONS=$(curl -s "http://localhost:9090/api/v1/query?query=bandit_promotions_total" | jq '.data.result[0].value[1]')
echo "Auto-Promotions: $AUTONOMOUS_PROMOTIONS"
```

**✅ STABILIZATION SUCCESS Criteria:**
- [ ] 48h uptime >99.5%
- [ ] Learning events >500
- [ ] Quality improvement >0.1 (10-20% uplift)
- [ ] Auto-promotions >5
- [ ] No manual interventions required
- [ ] Resource usage stable

---

## 🚨 Emergency Escalation Matrix

### Level 1: Monitor (Continue Stabilization)
- Error rate <5% sustained
- Latency degradation <100ms
- Single service restart needed

### Level 2: Investigate (T+4h Response Required)
- Error rate 5-10% sustained
- Latency >300ms P95
- Multiple service restarts
- Learning system stalled

### Level 3: Rollback (T+1h Response Required)
- Error rate >10% sustained
- Persistent 5xx errors
- Security incidents detected
- Complete service failure

### Rollback Commands
```bash
# Emergency rollback
./scripts/ROLLBACK_PLAYBOOK.sh

# Service-specific restart
docker-compose -f deploy/docker-compose.prod.yml restart <service_name>

# Full system reset
docker-compose -f deploy/docker-compose.prod.yml down
docker-compose -f deploy/docker-compose.prod.yml up -d
```

---

## 📊 Success Metrics Dashboard

### Real-Time Monitoring URLs
- **Grafana:** http://localhost:3001
- **Prometheus:** http://localhost:9090
- **AlertManager:** http://localhost:9093

### Key Metrics to Watch
```
✅ Uptime >99.5%
✅ Error Rate <1%
✅ P95 Latency <200ms
✅ Memory <80%
✅ Learning Events >10/hour
✅ Quality Score >7.0
✅ Auto-Promotions Active
```

### Daily Report Generation
```bash
# Generate daily stabilization report
./scripts/learn/nightly_learning_report.py

# Export metrics snapshot
curl -s http://localhost:9090/api/v1/query_range?query=up&start=$(date -v-24H +%s)&end=$(date +%s)&step=3600s > stabilization_uptime.json
```

---

## 🎯 Post-Stabilization Actions

### Immediate Next Steps (T+48h+)
1. **Scale to 100%** if not already there
2. **Enable advanced features** (personalization, cross-encoder)
3. **Set up weekly reviews** of learning effectiveness
4. **Document lessons learned** from stabilization period

### Long-Term Monitoring
- **Weekly:** Learning effectiveness reviews
- **Monthly:** Platform performance audits
- **Quarterly:** Architecture optimization reviews

---

## 📞 Communication Plan

### Internal Updates
- **Hourly (T+0 to T+24):** Slack updates with key metrics
- **Daily:** Email summary with stabilization progress
- **T+48:** Full stabilization report to stakeholders

### Customer Communications
- **No communications** during stabilization (internal only)
- **Post-stabilization:** Announce quality improvements from learning

---

**🎉 Stabilization Complete: Your AI platform is now autonomously optimizing in production!**

**Next: Choose your upgrade path - Cross-Encoder Precision or Personalization v1**
