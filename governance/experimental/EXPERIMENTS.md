# Experimental Remediation Framework

**Goal:** Prove that auto-remediation improves production outcomes, safely and measurably

---

## 🎯 **Overview**

7-phase experimental plan to validate auto-remediation:

| Phase | Name                     | Risk   | Duration | Success Metric          |
| ----- | ------------------------ | ------ | -------- | ----------------------- |
| 1     | Shadow Remediation       | None   | 1-2 days | ≥70% would promote      |
| 2     | Guarded Auto-Remediation | Low    | 3-4 days | ≥30% rollback reduction |
| 3     | A/B Policy Testing       | Low    | 1-2 days | Stat-sig improvement    |
| 4     | Adversarial Gates        | Medium | 2-3 days | ≥40% incident reduction |
| 5     | Cost-Aware Remediation   | Low    | 1-2 days | ≥25% cost reduction     |
| 6     | Human Fast-Track         | Low    | 1-2 days | ≥30% MTTR reduction     |
| 7     | Long-Run Drift           | None   | Weekly   | Stable accuracy         |

**Total Timeline:** 2 weeks for initial rollout + ongoing monitoring

---

## Phase 1: Shadow Remediation (NO IMPACT)

### Hypothesis

The Remediator can propose fixes that would pass canary gates on real incidents.

### Design

- Generate remediation plans on HARD_FAIL/SOFT_FAIL
- Run canary simulation in shadow mode (no actual changes)
- Measure agreement rate and canary pass rate
- Save artifacts for analysis

### Metrics

- `governance_shadow_experiments_total`
- `governance_shadow_would_promote_total`
- `governance_shadow_passed_gates_total`
- `governance_shadow_decision_agreement_rate`
- `governance_shadow_canary_pass_rate`

### Success Criteria

✅ ≥70% of shadow remediations would pass canary PROMOTE decision  
✅ No violations of safety gates  
✅ 20+ incidents tested

### Rollback

N/A (no production impact)

### Run It

```bash
make exp-shadow

# View results
ls artifacts/remediation_shadow/
```

### Artifacts

- `artifacts/remediation_shadow/*.json` - Plan, diffs, canary stats

---

## Phase 2: Guarded Auto-Remediation (1% CANARY)

### Hypothesis

Auto-remediation safely reduces rollback frequency without harming KPIs.

### Design

- Enable Remediator to apply patch to canary env (1% traffic)
- Canary window: 10-15 min, min 300 samples
- Gates: solve↑, violations↓, p95↓, ECE≤0.06
- Human notification via Slack on start/complete

### Metrics

- `governance_remediations_requested_total{verdict_type}`
- `governance_remediations_completed_total{decision}`
- `governance_remediation_time_seconds`
- `governance_rollback_rate`
- `governance_time_to_mitigation_seconds`

### Success Criteria

✅ ≥30% reduction in emergency rollbacks  
✅ No increase in violation rate  
✅ No increase in ECE over baseline  
✅ Run for 1 week

### Stop/Auto-Rollback

❌ Violations +0.5% → immediate ROLLBACK + freeze 30m  
❌ ECE > 0.06 → immediate ROLLBACK + freeze 30m

### Run It

```bash
make exp-remediate

# Monitor
watch -n 5 'curl -s http://localhost:9090/api/v1/query?query=governance_remediations_completed_total | jq'
```

### Artifacts

- Prometheus metrics
- Slack notifications
- Incident reports with canary data

---

## Phase 3: A/B Policy Testing

### Hypothesis

Structured plans (templates + rules) outperform free-form LLM plans.

### Design

- Split HARD_FAIL remediations 50/50:
  - **Arm A:** LLM free-form plan
  - **Arm B:** Rule-templated plan (playbooks)
- Both in canary only
- Measure: promote rate, time-to-mitigation, violations

### Metrics

- `governance_ab_experiments_total{arm}`
- `governance_ab_promote_rate{arm}`
- `governance_ab_human_approval_rate{arm}`

### Success Criteria

✅ Stat-sig (p<0.05) improvement of Arm B in ≥2 KPIs

### Stop

❌ Either arm trips hard gates twice in 24h → disable that arm

### Run It

```bash
make exp-ab
```

---

## Phase 4: Adversarial Gates

### Hypothesis

Injecting edge-case tests prevents brittle fixes from promoting.

### Design

- Extend gate with 10-20 adversarial probes:
  - Prompt attacks
  - Distribution shift
  - Malformed inputs
- Fail gate if edge-case score < 0.8
- Cap probe runtime at 90s

### Metrics

- `governance_edge_case_score{plan_id}`
- `governance_adversarial_probes_total`
- `governance_adversarial_failures_total{probe_type}`
- `governance_post_promotion_incidents_total{root_cause}`

### Success Criteria

✅ ≥40% drop in post-promotion incidents from brittle fixes

### Stop

❌ Probes slow gates >2min → reduce probe count

### Run It

```bash
make exp-devils-adv
```

---

## Phase 5: Cost-Aware Remediation

### Hypothesis

Keep safety and reduce spend by preferring low-cost playbooks.

### Design

- Add cost telemetry (tokens, build time, infra)
- Canary decider includes budget guardrails
- Prefer "cheap + safe" plans when tie

### Metrics

- `governance_remediation_cost_usd`
- `governance_cost_per_success_usd`
- `governance_budget_utilization`

### Success Criteria

✅ ≥25% cost reduction with no KPI regression

### Run It

```bash
make exp-cost
```

---

## Phase 6: Human Fast-Track

### Hypothesis

Expert approvals can safely bypass long windows for critical fixes.

### Design

- Slack `/governance-approve plan:{id} window=5m`
- Shorter window + higher sample rate
- Track MTTR improvement

### Metrics

- `governance_fasttrack_requests_total`
- `governance_fasttrack_approved_total`
- `governance_mttr_seconds`

### Success Criteria

✅ MTTR down ≥30% without increased violations

### Run It

```bash
make exp-fasttrack
```

---

## Phase 7: Long-Run Drift & Adaptation

### Hypothesis

Adaptive thresholds stay calibrated over time.

### Design

- Run adaptive learner weekly
- Compare learned vs. static thresholds
- Track ECE trend, false-pos/neg rates

### Metrics

- `governance_threshold_drift{threshold_name}`
- `governance_false_positive_rate`
- `governance_false_negative_rate`
- `governance_adaptive_learning_runs_total`

### Success Criteria

✅ Stable or improved decision accuracy  
✅ Unchanged safety alerts

### Run It

```bash
make exp-longrun
```

---

## 🗓️ **Rollout Schedule**

### Week 1

- **Day 1-2:** Phase 1 (Shadow) - Collect baseline data
- **Day 3-4:** Phase 2 (Canary 1%) - Enable auto-remediation
- **Day 5:** Phase 3 (A/B) + Phase 4 (Adversarial)

### Week 2

- **Day 6:** Phase 5 (Cost-aware)
- **Day 7+:** Phase 6 (Fast-track) + Phase 7 (Weekly)

---

## 📊 **Event Bus Schema**

### Topics

```
exec.remediation.requested
exec.remediation.started
exec.remediation.completed
release.canary.window_result
devils_adv.probe.report
```

### Payload Example

```json
{
  "task_id": "incident-2025-001",
  "plan_id": "abc123def456",
  "source": "remediator|shadow",
  "decision": "PROMOTE|HOLD|ROLLBACK",
  "samples": 350,
  "ece_post": 0.045,
  "violation_delta": -0.003,
  "latency_p95_delta": -0.12,
  "edge_case_score": 0.86,
  "cost_estimate_usd": 0.12,
  "timestamp": "2025-10-15T12:34:56Z"
}
```

---

## 🚨 **Alert Rules**

### Critical

```yaml
- alert: RemediationStuck
  expr: governance_remediations_requested_total - governance_remediations_completed_total > 0
  for: 10m
  severity: critical

- alert: ECERegression
  expr: governance_ece_post > 0.06
  for: 5m
  severity: critical
```

### Warning

```yaml
- alert: EdgeCaseDrop
  expr: governance_edge_case_score < 0.8
  for: 5m
  severity: warning

- alert: CostSpike
  expr: governance_remediation_cost_usd > (avg_over_time(governance_remediation_cost_usd[1h]) + 3 * stddev_over_time(governance_remediation_cost_usd[1h]))
  for: 10m
  severity: warning
```

---

## ⚠️ **Risks & Mitigations**

| Risk                | Mitigation                                   |
| ------------------- | -------------------------------------------- |
| Oscillation         | Add hysteresis; min 15m cool-down            |
| Probe flakiness     | Set timeout/parallelism; cache fails         |
| Plan overreach      | Restrict to sandboxed patch + file allowlist |
| Metrics blind spots | Fail-safe to HOLD if any KPI missing         |

---

## 🔧 **Configuration**

### Canary Gate Defaults

```python
MIN_SAMPLES = 300
WINDOW_MINUTES = 15
SOLVE_DELTA_MIN = 0.02
VIOL_DELTA_MAX = 0.005
P95_DELTA_MAX = 0.25
ECE_POST_MAX = 0.06
ENTROPY_MAX = 0.30
```

### Event Bus

- **Type:** Redis pub/sub
- **Host:** localhost:6379 (or athena-redis in Docker)

### Slack Channel

- **Channel:** `#governance-auto-remediation`
- **Notifications:** Start, complete, fast-track requests

---

## 📚 **Related Files**

- `governance/experimental/remediation_shadow.py` - Phase 1 implementation
- `governance/observability/experimental_metrics.py` - All metrics
- `monitoring/prometheus/alerts_experimental.yml` - Alert rules
- `artifacts/remediation_shadow/` - Shadow results

---

## 🚀 **Quick Start**

```bash
# Run Phase 1 (safe, no impact)
make exp-shadow

# View results
cat artifacts/remediation_shadow/*.json | jq

# Check metrics
curl http://localhost:9090/api/v1/query?query=governance_shadow_experiments_total | jq
```

---

## ✅ **Success Criteria Summary**

| Phase | Metric             | Target |
| ----- | ------------------ | ------ |
| 1     | Would promote rate | ≥70%   |
| 2     | Rollback reduction | ≥30%   |
| 3     | A/B stat-sig       | p<0.05 |
| 4     | Incident reduction | ≥40%   |
| 5     | Cost reduction     | ≥25%   |
| 6     | MTTR reduction     | ≥30%   |
| 7     | Accuracy stable    | ✓      |

---

**Ready to prove auto-remediation works! Start with Phase 1:**

```bash
make exp-shadow
```
