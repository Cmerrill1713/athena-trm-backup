# Constitutional AI Framework - Production Validation Suite

This validation suite provides comprehensive, mathematically rigorous checks to ensure your Constitutional AI Framework is production-ready and audit-tight.

## 🚀 Quick Start

```bash
# Run the complete validation suite
./scripts/run_production_validation.sh

# Or run individual components
psql -f scripts/production_validation_suite.sql
```

## 📋 What Gets Validated

### 1. Router Net-Positive Validation (IPS/DR)
- **Inverse Propensity Scoring**: Statistically proves router improvements aren't random
- **Doubly-Robust Estimation**: Confirms improvements hold under different assumptions
- **Success Gate**: +0.3 judge points uplift with 95% CI excluding 0

### 2. Neural Context Encoder Effectiveness
- **Paired Cluster Testing**: Compares neural vs heuristic routing per intent/domain
- **Bootstrap Statistical Significance**: 1k resamples for robust confidence intervals
- **Success Gate**: 70%+ high-value clusters show ≥+0.3 improvement

### 3. CE vs Cosine Cost-Aware Optimization
- **Utility Function**: `U = α·helpfulness - β·latency_ms - γ·CE_cost_usd`
- **Parameter Calibration**: α=1.0, β=0.002, γ=1.0 (2μs per ms latency penalty)
- **Success Gate**: Constitutional AI beats best fixed policy

### 4. RAG Reranker Guardrails
- **Hard Floor Protection**: Keeps max(4, ⌊TOPK/2⌋) documents
- **Over-filter Detection**: Median docs used ≥ 3 under load
- **PromQL Alert**: Automatic rollback on violations

### 5. Federated Privacy Budget & Reputation
- **ε-Accounting**: Tracks differential privacy spend per deployment
- **Reputation-Weighted FedAvg**: Low-reputation deployments contribute less
- **Success Gate**: All deployments within ε ≤ 2.0 per 30 days

### 6. Constitutional Layer Provenance
- **Policy Versioning**: Every strategy tracks constitution version + hash
- **Signed Approvals**: Human interventions cryptographically verified
- **Drift Detection**: Blocks strategies violating rules N times in M minutes

### 7. Dynamic Constitutional Weighting
- **A/A/A/B Testing**: Compares static vs dynamic weighting effectiveness
- **Governance Score Improvement**: ≥20% better with preserved utility
- **Success Gate**: Dynamic weighting provides measurable benefits

### 8. Live Safety Trip-Wires
- **Latency Bounds**: P95 ≤ 800ms with automatic CE rollback
- **Quality Degradation**: Judge helpfulness drop triggers bandit reset
- **Monoculture Prevention**: No strategy >70% traffic
- **Over-filter Protection**: RAG guardrails with automatic fallback

### 9. Chaos Engineering & Rollback Drills
- **CE Disable Test**: Verifies cosine fallback works
- **Federation Poisoning**: Tests reputation weighting robustness
- **Constitution Flips**: Validates policy change handling
- **Bandit Resets**: Confirms exploration floor recovery

### 10. Minimal Gaps Closure
- **Probability Logging**: All bandit choices logged for IPS/DR validation
- **Model Reproducibility**: Version snapshots with constitution hashes
- **PII Canary Detection**: Regex guards prevent accidental data leakage

## 🎯 Expected Outcomes

After running validation, you should see:

- **+0.5–0.8 judge uplift** verified with IPS/DR (not just raw means)
- **Utility↑ despite CE costs** (Section 3 proves economic optimality)
- **No over-filtering**; median docs_used ≥3 under load
- **ε ≤ 2.0 per 30d per deployment**; low-rep sites have low weight
- **Zero unapproved drifts**; policy hash matches; signed interventions logged

## 📊 Success Criteria Matrix

| Component | Success Threshold | Validation Method |
|-----------|------------------|-------------------|
| Router Uplift | +0.3 pts with 95% CI | IPS/DR estimation |
| Neural Encoder | 70%+ clusters ≥+0.3Δ | Paired bootstrap testing |
| CE Utility | Beats fixed policies | Cost-aware optimization |
| RAG Guardrails | median ≥3 docs | Statistical monitoring |
| Federated Privacy | ε ≤ 2.0/30d | Differential privacy accounting |
| Constitution | 100% versioned + signed | Provenance tracking |
| Dynamic Weighting | ≥20% governance improvement | A/B testing |
| Safety Trip-wires | All metrics collected | Prometheus validation |
| Chaos Drills | 100% success rate | Automated testing |
| Minimal Gaps | 95%+ complete | Gap analysis |

## 🔧 Prerequisites

### Database Setup
Ensure your PostgreSQL database has these tables populated with recent data:

```sql
-- Core optimization tables
bandit_decisions, routing_outcomes, rag_retrieval, judge_metrics

-- Governance tables
governance_assessments, generated_strategies, strategy_deployments

-- Federated learning tables
federated_updates, model_snapshots

-- Safety monitoring tables
router_metrics, chaos_experiments, rollback_incidents, pii_canary_checks
```

### Prometheus Setup
Load the safety alerts into your Prometheus Alertmanager:

```bash
# Copy alerts to your Prometheus configuration
cp monitoring/alerts/production_safety_alerts.yml /path/to/prometheus/alerts/

# Reload Prometheus configuration
curl -X POST http://your-prometheus:9090/-/reload
```

### Dependencies
```bash
# Required for validation runner
sudo apt-get install postgresql-client yamllint  # Ubuntu/Debian
# or
brew install postgresql yamllint  # macOS
```

## 📈 Interpreting Results

### ✅ PASS Status
- **100% pass rate**: System is production-ready
- **80%+ pass rate**: Mostly ready with minor fixes needed
- **60%+ pass rate**: Significant issues requiring attention

### ⚠️ WARNING Status
- Missing data for some checks (insufficient history)
- Marginal statistical significance
- Minor configuration issues

### ❌ FAIL Status
- Core functionality not working
- Safety violations detected
- Statistical tests failing

## 🔄 Continuous Validation

Set up automated validation in your CI/CD pipeline:

```yaml
# .github/workflows/production-validation.yml
name: Production Validation
on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Validation Suite
        run: ./scripts/run_production_validation.sh
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## 🚨 Common Issues & Fixes

### "psql: command not found"
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql

# Or use Docker
docker run --rm -it -v $(pwd):/work postgres:alpine psql -f /work/scripts/production_validation_suite.sql
```

### "FATAL: database does not exist"
Ensure your `DATABASE_URL` environment variable is set correctly:
```bash
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
```

### "Insufficient data for validation"
The system needs 7-30 days of operation data. For new deployments:
- Run with synthetic data first
- Gradually increase traffic while monitoring validation scores
- Expect full statistical power after 2-4 weeks

### "Prometheus alerts not working"
- Verify alert file syntax: `yamllint monitoring/alerts/production_safety_alerts.yml`
- Check Prometheus configuration includes the alerts directory
- Ensure metrics are being exported from your application

## 📞 Support

If validation reveals issues:

1. **Check the detailed output** for specific failing components
2. **Review table schemas** match your actual database structure
3. **Verify data freshness** - old data may give false negatives
4. **Run individual sections** by commenting out parts of the SQL file

## 🎯 Final Production Readiness Checklist

- [ ] Validation suite passes with ≥80% success rate
- [ ] Prometheus alerts loaded and tested
- [ ] Chaos drills executed successfully
- [ ] Rollback procedures documented and tested
- [ ] Monitoring dashboards configured
- [ ] On-call rotation established
- [ ] Incident response playbooks ready

---

**Remember**: This validation suite doesn't just check if your system works—it mathematically proves it's safer, more effective, and more trustworthy than traditional approaches. Run it regularly to maintain production excellence.
