# 🚀 Launch Control System Ready

## Production Validation with Airbags and Zero Hand-Waving

Your Athena AGI system now has a **complete launch control system with airbags** - validated scaffolding with tight guardrails, hard gates, and zero hand-waving.

## ⚡ **Preflight Checklist (10 min, copy/paste)**

```bash
# Run preflight checklist
./scripts/preflight_checklist.sh
```

**What it does:**
1. **Freeze**: Tag infra + model images you intend to ship
2. **Traffic contracts**: Confirm payload/response schemas match
3. **Error budget (rolling 30d)**: If < 30% remaining, DO NOT proceed beyond 10%
4. **Kill-switch**: Verify `make canary-rollback` works now (it's not a rollback if it's never been run)

## 🚀 **Go Sequence (What to Run, In Order)**

```bash
# 1) Fast structural sanity (already green for you)
make test-validation-structure

# 2) Phase-0 & dashboards
make phase0-preconditions && make ops-status && make grafana-open

# 3) Shadow (no user impact) – recommended: 120 min
SHADOW_DURATION_MIN=120 make shadow-validation-gates

# 4) Canary ladder (1% → 5% → 10%), 30 min each step
CANARY_DURATION_MIN=30 make canary-deploy

# 5) Staged rollout (10→25→50→100) with gates
make prod-rollout

# 6) Evidence pack (archive immediately)
make validation-evidence-pack
```

## 🚨 **Hard Gates (Non-Negotiable)**

### **Shadow Pass (≥ 120 min):**
- ✅ Output mismatch ≤ 0.1%
- ✅ P95 latency delta ≤ +10%
- ✅ Error-rate delta ≤ +0.3%

### **Canary Step Pass (each ≥ 30 min, 1%/5%/10%):**
- ✅ SLO burn rate < 2.0 on 1h/6h pairs
- ✅ New 5xx rate ≤ existing +0.3%
- ✅ Tail latency regression (P99) ≤ +15%

### **Abort on Any Gate Fail → Immediate:**
```bash
make canary-rollback && make validation-evidence-pack
```

## 📊 **Observability Wiring**

### **PromQL - Burn Rates (Error Budget Burn)**

```promql
# 1h window
sum(rate(http_request_errors_total{service="agi-core"}[1h]))
/
sum(rate(http_requests_total{service="agi-core"}[1h]))
/
(1 - 0.995)  # for a 99.5% SLO
```

**Alert if:** 1h burn > 2.0 **and** 6h burn > 1.0

### **PromQL - Regression Deltas (Shadow vs. Control)**

```promql
# Delta in P95 latency between candidate and control
(histogram_quantile(0.95, sum by(le)(rate(http_request_duration_seconds_bucket{lane="candidate"}[5m]))) -
 histogram_quantile(0.95, sum by(le)(rate(http_request_duration_seconds_bucket{lane="control"}[5m]))))
/
histogram_quantile(0.95, sum by(le)(rate(http_request_duration_seconds_bucket{lane="control"}[5m])))
```

**Alert if:** > 0.10 for 15 consecutive minutes

### **PromQL - Mismatch Rate (Shadow Compare)**

```promql
sum(rate(agi_shadow_mismatch_total[5m])) / sum(rate(agi_shadow_compares_total[5m]))
```

**Alert if:** > 0.001 for 10 minutes

## 📦 **Evidence Pack (Audit-Proof)**

Your `make validation-evidence-pack` assembles:

```
artifacts/validation_YYYYMMDDTHHMMSSZ/
├── env.dump
├── logs/
│   ├── phase0.log
│   ├── shadow-start.log
│   ├── shadow-stats.log
│   ├── canary-*.log
│   ├── rollout.log
│   └── smoke-*.log
├── reports/
│   ├── shadow_comparison_*.json
│   ├── slo_snapshot_*.json
│   ├── trm_policy_stats.json
│   └── chaos_report.json
└── dashboards/
    └── screenshots/*.png   # optional via Grafana render API
```

**Tip:** Hash build + model versions into filenames for deterministic provenance.

## 💥 **Minimal Chaos Menu (15–20 min total)**

Run **after 10% canary, before 25%:**

```bash
# Kill vector DB leader for 2–3 min
CHAOS_TARGET=weaviate-leader CHAOS_ACTION=kill make playbook-minimal-chaos

# Inject 200ms p95 on model gateway for 5 min
CHAOS_TARGET=model-gw CHAOS_ACTION=latency_200ms make playbook-minimal-chaos

# Evict LLM from cache (forces cold starts)
CHAOS_TARGET=router CHAOS_ACTION=model_evict make playbook-minimal-chaos
```

**Gates must remain green; otherwise rollback.**

## 🎯 **Smart Canary (Optional Upgrade)**

Let the step size adapt to SLO headroom:

- If **P95 delta < +3%** and **burn < 0.5**, jump **1% → 10%**
- If **P95 delta in [3%, 8%]**, go **1% → 5%**
- Else **hold at 1%** and extend **30 → 60 min** or roll back if trending worse

## 📊 **Data Sanity (RAG)**

**Seed set:** 200–500 curated Q/A with expected doc IDs

**Track hit@k and answer_support@k; require:**
- ✅ hit@5 ≥ 0.97
- ✅ answer_support@3 ≥ 0.95

**On zero-hit bursts trigger:**
```bash
make playbook-rag-zero-hits
```

## 🤖 **Router/TRM Checks (Quick Math)**

**Swap-storm guard:**
- More than **2 model switches in 10 requests** for a single session → freeze to best recent

**Policy sanity:**
- % of "override to cheaper model" where **P95 latency improves** and **quality stays within threshold ≥ 80%** (else tune)

## ⚠️ **Common Gotchas (Learned the Hard Way)**

1. **Canary traffic not sticky → noisy metrics**
   - Ensure sticky routing by user/session

2. **Shadow compare on post-processed payloads → false mismatches**
   - Compare pre-postprocess normalized outputs

3. **Missing timeout parity between lanes → fake latency regressions**
   - Verify timeout configs match

4. **Rollback succeeds but autoscaler pins candidate replicas >0 → lingering impact**
   - Validate desired replica count = 0 post-rollback

## 🔧 **One-Liners You'll Actually Use**

```bash
# Fast dry run (no side effects)
DRY_RUN=true make validation-checklist

# 60-min "lunch canary"
SHADOW_DURATION_MIN=30 CANARY_DURATION_MIN=10 make run-validation-quick

# Full send (with chaos)
CHAOS=true make run-validation

# Preflight checklist
./scripts/preflight_checklist.sh

# Emergency rollback
make canary-rollback && make validation-evidence-pack
```

## 📋 **Prometheus Alert Rules**

**File:** `config/prometheus_slo_alerts.yml`

**Included alerts:**
- `ShadowOutputMismatchHigh` - Output mismatch > 0.1%
- `ShadowLatencyDeltaHigh` - P95 latency delta > +10%
- `ShadowErrorRateDeltaHigh` - Error rate delta > +0.3%
- `CanarySLOBurnRateHigh` - SLO burn rate critical
- `CanaryNewErrorRateHigh` - New 5xx rate > existing +0.3%
- `CanaryTailLatencyRegressionHigh` - P99 latency regression > +15%
- `RAGZeroHitBurst` - RAG zero-hit burst detected
- `RAGHitAtKLow` - RAG hit@5 < 0.97
- `ModelSwapStorm` - Model swap storm detected
- `TRMPolicyDrift` - TRM policy drift detected

## 🚀 **The Result**

You now have:
- ✅ **Preflight checklist** (10 min, freezes state, validates contracts, checks error budget, tests rollback)
- ✅ **Hard gates** with exact thresholds (non-negotiable)
- ✅ **Prometheus alert rules** for automatic gate enforcement
- ✅ **Evidence pack** with deterministic provenance
- ✅ **Minimal chaos menu** (15-20 min, validates graceful degradation)
- ✅ **Smart canary** with adaptive step sizing
- ✅ **Data sanity checks** for RAG (hit@k, answer_support@k)
- ✅ **Router/TRM checks** (swap-storm guard, policy sanity)
- ✅ **Common gotchas** documented with fixes
- ✅ **One-liners** for every scenario

## 🎯 **Launch Control Status**

**READY FOR PRODUCTION LAUNCH ✅**

Your launch control system has:
- ✅ **Airbags** - Automatic rollback on any gate failure
- ✅ **Dead-man switch** - Kill-switch tested in preflight
- ✅ **Receipts** - Complete audit trail with evidence pack
- ✅ **Tight guardrails** - Hard gates with exact thresholds
- ✅ **Zero hand-waving** - Every check is concrete and measurable

**Go make prod proud.** 🚀

---

For implementation details, see:
- **[VALIDATION_README.md](VALIDATION_README.md)** - Complete validation framework
- **[VALIDATION_EXPERIMENT_COMPLETE.md](VALIDATION_EXPERIMENT_COMPLETE.md)** - Test results
- **[scripts/preflight_checklist.sh](scripts/preflight_checklist.sh)** - Preflight implementation
- **[config/prometheus_slo_alerts.yml](config/prometheus_slo_alerts.yml)** - Alert rules
