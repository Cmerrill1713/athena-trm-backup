# Constitutional Operations Runbooks

**Incident response playbooks for constitutional auto-evolution alerts.**

## 🚨 Alert Response Matrix

| Alert | Severity | Primary Response | Secondary Response | SLA |
|-------|----------|------------------|-------------------|-----|
| ConstitutionalUpliftInsufficient | Warning | Investigate CUPED confounders | Rollback if no root cause | 2h |
| PrivacyBudgetExceeded | Critical | Halt federation | Audit usage patterns | 1h |
| StrategyQuarantineTriggered | Critical | Verify quarantine | Prepare rollback | 15min |
| FederationIntegrityBreach | Critical | Halt all federation | Security review | 1min |
| GovernanceFalsePositiveRateHigh | Warning | Review constitutional rules | Adjust severity | 4h |
| RewardDriftDetected | Warning | Reduce exploration | Monitor recovery | 1h |

---

## 🚨 ConstitutionalUpliftInsufficient

**"CUPED-adjusted judge score uplift < 0.3 points"**

### Immediate Actions (30 minutes)
1. **Check CUPED calculation validity**
   ```bash
   # Re-run CUPED with different baselines
   python3 run_cuped_analysis.py --baseline recent --treatment current
   ```

2. **Verify treatment implementation**
   ```sql
   -- Check if constitutional routing is actually active
   SELECT COUNT(*) FILTER (WHERE reranker_type = 'crossencoder') as ce_usage
   FROM routing_outcomes
   WHERE ts > NOW() - INTERVAL '1 hour';
   ```

3. **Assess external confounders**
   - Traffic pattern changes
   - Query distribution shifts
   - Upstream system issues

### Investigation (2 hours)
1. **Compare pre/post metrics**
   ```sql
   SELECT
       DATE_TRUNC('hour', ts) as hour,
       AVG(judge_helpfulness) as avg_score,
       COUNT(*) as queries
   FROM routing_outcomes
   WHERE ts > NOW() - INTERVAL '48 hours'
   GROUP BY 1 ORDER BY 1;
   ```

2. **Check for Simpson's paradox**
   - Segment by query type, time of day, user segments
   - Look for hidden subpopulations driving results

### Resolution Options
- **Accept**: Uplift is real but below threshold (document rationale)
- **Rollback**: Temporarily disable constitutional routing
- **Investigate**: Deeper analysis of confounders

### Prevention
- Implement A/A tests to establish baseline variance
- Add more granular CUPED segmentation
- Monitor uplift trends over time

---

## 🚨 PrivacyBudgetExceeded

**"Differential privacy ε > 2.0 over 30 days"**

### Immediate Actions (15 minutes)
1. **Halt federation contributions**
   ```bash
   # Emergency federation shutdown
   bash constitutional_operations_automation.sh federation-emergency-stop
   ```

2. **Assess breach severity**
   ```sql
   SELECT
       deployment_id,
       epsilon_30d_total,
       federation_contributions_count,
       last_contribution
   FROM privacy_accounting
   WHERE epsilon_30d_total > 2.0
   ORDER BY epsilon_30d_total DESC;
   ```

### Investigation (1 hour)
1. **Analyze contribution patterns**
   ```sql
   SELECT
       DATE_TRUNC('day', ts) as day,
       COUNT(*) as contributions,
       AVG(sample_count) as avg_samples,
       SUM(privacy_budget) as daily_epsilon
   FROM federation_contributions
   WHERE deployment_id = 'VIOLATING_DEPLOYMENT_ID'
       AND ts > NOW() - INTERVAL '30 days'
   GROUP BY 1 ORDER BY 1;
   ```

2. **Check for abusive usage**
   - Unusually high contribution frequency
   - Large sample counts per contribution
   - Suspicious query patterns

### Resolution Options
- **Reduce participation**: Limit contributions from violating deployments
- **Increase noise**: Add more differential privacy noise
- **Block deployment**: Remove from federation temporarily

### Prevention
- Implement per-deployment rate limiting
- Add privacy budget monitoring alerts
- Regular privacy audits

---

## 🚨 StrategyQuarantineTriggered

**"Auto-quarantining strategy due to performance degradation"**

### Immediate Actions (5 minutes)
1. **Verify quarantine activation**
   ```sql
   SELECT
       strategy_id,
       quarantine_reason,
       traffic_cap_pct,
       triggered_at
   FROM strategy_quarantine_events
   WHERE ts > NOW() - INTERVAL '10 minutes'
   ORDER BY ts DESC LIMIT 5;
   ```

2. **Check current traffic distribution**
   ```sql
   SELECT
       strategy_id,
       COUNT(*) as current_traffic,
       ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) as traffic_pct
   FROM routing_outcomes
   WHERE ts > NOW() - INTERVAL '5 minutes'
   GROUP BY strategy_id
   ORDER BY traffic_pct DESC;
   ```

### Investigation (15 minutes)
1. **Analyze degradation cause**
   ```sql
   SELECT
       DATE_TRUNC('minute', ts) as minute,
       AVG(judge_helpfulness) as avg_score,
       COUNT(*) as queries
   FROM routing_outcomes
   WHERE strategy_id = 'QUARANTINED_STRATEGY_ID'
       AND ts > NOW() - INTERVAL '1 hour'
   GROUP BY 1 ORDER BY 1;
   ```

2. **Check for correlated events**
   - Upstream system changes
   - Query pattern shifts
   - External API issues

### Resolution Options
- **Monitor**: Let quarantine run for observation period
- **Rollback**: Remove strategy from production
- **Investigate**: Deeper analysis if quarantine was false positive

### Prevention
- Implement gradual rollout for new strategies
- Add more sophisticated health checks
- Regular strategy performance reviews

---

## 🚨 FederationIntegrityBreach

**"Federation integrity breach detected"**

### Immediate Actions (1 minute)
1. **Complete federation shutdown**
   ```bash
   # Nuclear option - halt all federation
   bash constitutional_operations_automation.sh federation-nuclear-shutdown
   ```

2. **Isolate affected systems**
   - Block federation network traffic
   - Disable federation endpoints
   - Alert security team

### Investigation (30 minutes)
1. **Audit integrity violations**
   ```sql
   SELECT
       violation_type,
       affected_resources,
       evidence_hash,
       detected_at
   FROM federation_integrity_violations
   WHERE ts > NOW() - INTERVAL '1 hour'
   ORDER BY ts DESC;
   ```

2. **Check signature validation**
   ```sql
   SELECT
       strategy_id,
       constitution_version,
       policy_hash,
       signature_valid
   FROM active_strategies
   WHERE signature_valid = false;
   ```

### Resolution Options
- **Security review**: Complete audit before reactivation
- **Partial restoration**: Re-enable trusted deployments only
- **Full reset**: Wipe federation state and restart

### Prevention
- Implement zero-trust federation protocol
- Regular signature rotation
- Continuous integrity monitoring

---

## 📋 Daily Operations Checklist

### Morning (6:00 AM UTC)
- [ ] Review overnight constitutional validation results
- [ ] Check alert status in monitoring dashboard
- [ ] Verify federation health metrics
- [ ] Review privacy budget consumption

### Midday (12:00 PM UTC)
- [ ] Monitor governance quality metrics
- [ ] Check strategy quarantine status
- [ ] Review fairness analysis results
- [ ] Validate invariant compliance

### Evening (6:00 PM UTC)
- [ ] Review daily CUPED uplift analysis
- [ ] Check for emerging reward drift patterns
- [ ] Monitor federation reputation changes
- [ ] Prepare daily operations report

### Weekly (Monday 9:00 AM UTC)
- [ ] Run chaos drill (strategy quarantine)
- [ ] Review constitutional rule effectiveness
- [ ] Update adaptive thresholds based on maturity
- [ ] Audit federation participation

### Monthly (1st 10:00 AM UTC)
- [ ] Run all three chaos drill types
- [ ] Complete privacy budget audit
- [ ] Review and update constitutional rules
- [ ] Performance optimization review

---

## 📊 Key Performance Indicators

### Primary KPIs
- **Constitutional Compliance**: >95% validation pass rate
- **Governance Quality**: FP/FN rates <10%
- **Privacy Budget**: All deployments ε < 2.0
- **System Stability**: <5% traffic to quarantined strategies

### Secondary KPIs
- **Federation Health**: >80% deployments actively contributing
- **Alert Response**: 100% alerts acknowledged within SLA
- **Chaos Drill Success**: >90% drills pass
- **Operational Efficiency**: <15min mean time to resolution

---

## 🆘 Emergency Contacts

| Role | Contact | Escalation Path |
|------|---------|-----------------|
| **On-call Engineer** | @constitutional-oncall | → Engineering Manager |
| **Security Lead** | @security-lead | → CISO |
| **ML Platform Lead** | @ml-platform-lead | → VP Engineering |
| **Legal/Compliance** | @legal-compliance | → General Counsel |

### Escalation Triggers
- **Immediate**: Federation integrity breach, privacy budget >3.0
- **Urgent**: Constitutional compliance <80%, multiple strategy quarantines
- **High**: Governance quality degradation, repeated false positives

---

## 🔧 Troubleshooting Quick Reference

### Common Issues

**Constitutional validation crashes**
```bash
# Check database connectivity
psql "$DATABASE_URL" -c "SELECT 1;"

# Verify schema exists
psql "$DATABASE_URL" -c "\dt constitutional_*"

# Check Python dependencies
python3 -c "import psycopg2, requests"
```

**Federation sync failures**
```bash
# Check federation service health
curl -f http://federation-coordinator:8080/health

# Verify encryption keys
bash check_federation_keys.sh

# Check network connectivity
telnet federation-coordinator 8080
```

**Alert false positives**
```bash
# Review alert thresholds
grep "thresholds:" constitutional_hardening_alerts.yml

# Check metric calculations
curl "http://prometheus:9090/api/v1/query?query=governance_false_positive_rate"

# Adjust thresholds if needed
vim constitutional_config.sql
```

**Strategy quarantine storms**
```bash
# Check quarantine criteria
psql "$DATABASE_URL" -c "SELECT * FROM quarantine_criteria;"

# Review recent performance
psql "$DATABASE_URL" -c "
  SELECT strategy_id, AVG(judge_helpfulness), COUNT(*)
  FROM routing_outcomes
  WHERE ts > NOW() - INTERVAL '1 hour'
  GROUP BY strategy_id
  ORDER BY 2 DESC;
"

# Temporarily adjust sensitivity
psql "$DATABASE_URL" -c "UPDATE quarantine_config SET sensitivity = 0.8;"
```

---

**Remember: These runbooks transform alerts from "fire drills" to "routine operations."** Practice them regularly, especially the chaos drills. Your system's constitutional immune system gets stronger with every response. 🛡️⚡
