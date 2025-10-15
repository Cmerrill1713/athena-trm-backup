# Constitutional Auto-Evolution Hardening Bundle

**Production-ready validation and monitoring for ethical federated bandit routing.**

This bundle implements 10 hardening checks to pressure-test and validate the constitutional auto-evolution system in production environments.

## 🚀 Quick Start

### 1. Deploy Database Schema
```bash
# Deploy the hardening bundle to PostgreSQL
psql -f constitutional_hardening_bundle.sql
```

### 2. Configure Prometheus Alerts
```yaml
# Add to your Prometheus alerting rules
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

rule_files:
  - "constitutional_hardening_alerts.yml"
```

### 3. Run Validation Sprint
```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"

# Run 30-minute validation
python3 run_constitutional_validation.py --format table
```

## 📋 The 10 Hardening Checks

### 1. **Causal Proof (CUPED)**
- **What**: Variance-reduced causal inference on router performance
- **Why**: Confirms constitutional auto-evolution actually improves outcomes
- **Threshold**: CUPED-adjusted uplift ≥ +0.3 judge points with 95% CI excluding 0

### 2. **Governance Quality (FP/FN Rates)**
- **What**: Measures false positives/negatives in constitutional decisions
- **Why**: Ensures governance doesn't block good strategies or pass bad ones
- **Threshold**: FP ≤ 10%, FN ≤ 10%

### 3. **Privacy Math (ε-Accounting)**
- **What**: Tracks differential privacy budget consumption
- **Why**: Prevents privacy budget exhaustion across federation
- **Threshold**: Per-deployment 30-day ε ≤ 2.0

### 4. **Non-Stationarity (Drift Detection)**
- **What**: Online drift detection using Page-Hinkley test
- **Why**: Detects when bandit assumptions break (reward distribution changes)
- **Action**: Auto-reduce exploration by 50% on drift detection

### 5. **Byzantine-Robust Federation**
- **What**: Trimmed mean aggregation with reputation weighting
- **Why**: Resists poisoning attacks and malicious deployments
- **Method**: 20% outlier trimming + reputation-based weighting

### 6. **Constitutional Invariants**
- **What**: Never-violate safety constraints
- **Checks**:
  - No monoculture (max strategy ≤70% traffic)
  - Privacy floor (ε ≤ 2.0/deployment)
  - Latency budget (p95 ≤ 800ms)
  - CE delta (≤ +200ms vs cosine)
  - Over-filtering (median docs ≥ 3)

### 7. **Cost-Aware Policy KPI**
- **What**: Utility function balancing quality, latency, and cost
- **Formula**: U = α·quality - β·latency - γ·cost
- **Threshold**: Constitutional policy ≥ 10% better than best static

### 8. **Fair-Use & Stability**
- **What**: Proxy fairness checks across strata (hours, query length, domain)
- **Why**: Catches disparate impact without requiring demographics
- **Threshold**: No stratum deviates >0.5 points from global mean

### 9. **Break-Glass Automations**
- **Strategy Quarantine**: Auto-cap traffic to 5% if:
  - Reward drift < -0.5 in 30m
  - Latency p95 +200ms in 30m
  - Governance warnings >3 in 30m
- **Federation Integrity**: Halt ingestion if signature/policy mismatches

### 10. **30-Minute Validation Sprint**
- **Policy integrity**: All strategies have valid constitution hash
- **Exploration sanity**: Medium-confidence exploration ∈ [5%, 20%]
- **Utility scoreboard**: Constitutional policy ≥ static +10%
- **Federation DP**: ε_30d ≤ 2.0 for all deployments
- **Over-filtering**: Median docs ≥ 3
- **Monoculture**: Max traffic ≤70%
- **CUPED uplift**: ≥ +0.3 points

## 🎯 Key Metrics to Monitor

### Database Views
```sql
-- Governance quality
SELECT * FROM governance_quality;

-- Constitutional invariants
SELECT * FROM constitutional_invariants WHERE NOT satisfied;

-- Fairness analysis
SELECT * FROM fairness_analysis WHERE status = 'INVESTIGATE';

-- Privacy accounting
SELECT * FROM privacy_accounting ORDER BY epsilon_30d_total DESC;
```

### Prometheus Metrics
```promql
# Governance health
governance_false_positive_rate
governance_false_negative_rate

# Privacy compliance
max_over_time(privacy_epsilon_30d[30d])

# System invariants
max(strategy_traffic_pct)
quantile(0.5, docs_used)

# Federation health
federation_contributions_total
federation_sync_success_total
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Privacy parameters
PRIVACY_EPSILON=0.5
PRIVACY_DELTA=1e-6

# Governance thresholds
GOVERNANCE_FP_THRESHOLD=0.1
GOVERNANCE_FN_THRESHOLD=0.1

# System invariants
MAX_STRATEGY_TRAFFIC_PCT=0.7
LATENCY_BUDGET_MS=800
CE_LATENCY_DELTA_MS=200
MIN_MEDIAN_DOCS=3

# Cost weights (for utility function)
UTILITY_ALPHA=1.0      # Quality weight
UTILITY_BETA=0.002     # Latency weight (ms)
UTILITY_GAMMA=0.001    # Cost weight (USD)
```

### Alert Tuning
Adjust thresholds in `constitutional_hardening_alerts.yml` based on your traffic patterns and risk tolerance.

## 📊 Sample Validation Output

```
🛡️  CONSTITUTIONAL AUTO-EVOLUTION VALIDATION
=======================================================
Timestamp: 2024-01-15T10:30:00Z

📋 CHECK RESULTS:
-------------------------------------------------------
Check                      Status   Value      Threshold
-------------------------------------------------------
policy_integrity          ✅       0          0
exploration_sanity        ✅       0.125      0.05-0.20
utility_scoreboard        ✅       1.45       1.32
federation_dp             ✅       1.8        2.0
over_filtering           ✅       4.2        3.0
monoculture              ✅       0.65       0.70
governance_fp_rate       ✅       8.5        10.0
governance_fn_rate       ✅       6.2        10.0

📊 SUMMARY:
  Total Checks: 8
  Passed: 8
  Failed: 0
  Compliance Rate: 100.0%
  Overall Status: ✅ PASS
```

## 🚨 Alert Response Guide

### ConstitutionalUpliftInsufficient
- **Cause**: CUPED-adjusted judge score uplift < 0.3 points
- **Action**: Investigate confounders, consider rolling back, check for data drift
- **SLA**: Respond within 2 hours

### GovernanceFalsePositiveRateHigh
- **Cause**: Governance blocking >10% of good strategies
- **Action**: Review constitutional rules, reduce severity thresholds
- **SLA**: Respond within 4 hours

### PrivacyBudgetExceeded
- **Cause**: Differential privacy ε > 2.0 over 30 days
- **Action**: Reduce federation participation, increase noise, audit usage
- **SLA**: Respond within 1 hour (critical)

### StrategyQuarantineTriggered
- **Cause**: New strategy showing performance degradation
- **Action**: Auto-cap traffic to 5%, notify team, prepare rollback
- **SLA**: Respond within 15 minutes

## 🔄 Maintenance

### Daily
- Monitor compliance dashboard
- Review failed validation checks
- Update reputation scores

### Weekly
- Analyze governance FP/FN trends
- Review fairness analysis
- Tune exploration rates

### Monthly
- Audit privacy budget consumption
- Review constitutional rule effectiveness
- Update cost weights in utility function

## 📈 Success Metrics

### Primary KPIs
- **Compliance Rate**: >95% of validation checks passing
- **Governance Quality**: FP/FN rates <10%
- **Privacy Budget**: All deployments ε < 2.0
- **System Stability**: <5% traffic to quarantined strategies

### Secondary KPIs
- **Federation Health**: >80% deployments actively contributing
- **Fairness Score**: <5% strata with significant deviations
- **Utility Improvement**: Constitutional policy >10% better than static

## 🛠️ Troubleshooting

### Common Issues

**High FP Rate in Governance**
- Rule too strict: Reduce severity or adjust thresholds
- Training data bias: Retrain on more diverse examples

**Privacy Budget Exceeded**
- High participation: Reduce federation sync frequency
- Large contributions: Implement contribution size limits

**Monoculture Risk**
- Dominant strategy: Force exploration, reduce exploitation confidence
- Poor diversity: Add strategy variety, review selection criteria

**Reward Drift**
- Environment change: Auto-reduce exploration, monitor recovery
- Strategy degradation: Quarantine, investigate root cause

## 📚 Related Files

- `constitutional_hardening_bundle.sql` - Database schema and functions
- `constitutional_hardening_alerts.yml` - Prometheus alerting rules
- `run_constitutional_validation.py` - Validation runner script
- `test_constitutional_governance.py` - Unit tests

## 🤝 Contributing

When adding new hardening checks:
1. Add database schema changes to `constitutional_hardening_bundle.sql`
2. Add Prometheus alerts to `constitutional_hardening_alerts.yml`
3. Update validation runner in `run_constitutional_validation.py`
4. Add unit tests to `test_constitutional_governance.py`
5. Update this README

---

**This hardening bundle transforms your ethical federated brain from "hope it works" to "mathematically validated production excellence."** 🎯🛡️
