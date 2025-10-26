# 🧪 Production Testing Guide

## Battle-Tested Production Validation Framework

Your Athena AGI system now has a comprehensive production testing framework that goes far beyond local "green" checks. This guide covers real-world validation against actual user patterns, data drift, and cascading failures.

## 🎯 Testing Philosophy

**Local "green" means nothing once real users, real data, and real failures show up.**

This framework implements:

- **Production-mirror staging** with chaos testing
- **Shadow traffic mirroring** with drift detection
- **Risk-based canary deployment** with automated rollbacks
- **Human-in-the-loop validation** and red team testing
- **SLO-driven automation** with kill switches

## 🚀 Quick Start - "Do It Now" Commands

```bash
# 0) Stage burn-in (production-mirror testing)
make stage-chaos-test

# 1) Start shadow traffic for 24h
make traffic-shadow-start

# 2) Start 5% canary for 1h
make canary-deploy

# 3) Monitor the big three (repeat every 10m)
make ops-status
curl -s :8000/trm/policy | jq '.stats'
make rag-metrics

# 4) If green → expand canary
./scripts/canary_by_risk.sh 25 120 medium deploy

# 5) Run complete production test suite
make production-test-suite
```

## 🧪 1. Stage with Production Shape

**Goal**: Catch 80% of surprises before a single real request hits the new build.

### Production-Mirror Staging

```bash
# Run chaos testing in staging environment
make stage-chaos-test
```

**What it tests**:

- Service kills during operation (Weaviate, RAG Gateway)
- Network latency and packet loss simulation
- Disk space pressure and memory constraints
- Network partition scenarios

**Promotion gates**:

- All stage SLOs green for 24h
- `make rag-golden ≥ 80%` in stage
- Chaos tests pass without cascading failures

## 🔍 2. Shadow Traffic (Observe, Don't Influence)

**Goal**: Exercise the new stack with real production inputs, but never affect user responses.

### Shadow Traffic Mirroring

```bash
# Start shadow traffic mirroring (5% default)
make traffic-shadow-start

# Monitor shadow traffic statistics
make traffic-shadow-stats

# Stop shadow traffic
make traffic-shadow-stop
```

**What it does**:

- Duplicates real requests to shadow stack
- Drops shadow responses (no side effects)
- Compares outputs for drift detection
- Logs performance and accuracy deltas

**Shadow stack isolation**:

- Writes to separate Weaviate namespace
- Uses `dry_run` flags for tools
- Never hits production side effects

## 🚦 3. Canary by Risk, Not Just Percentage

**Goal**: Minimize blast radius and validate on real users.

### Risk-Based Canary Deployment

```bash
# Low-risk canary (internal traffic)
make canary-deploy

# Medium-risk canary (beta customers)
./scripts/canary_by_risk.sh 10 60 medium deploy

# High-risk canary (production traffic)
./scripts/canary_by_risk.sh 5 30 high deploy

# Check canary status
make canary-status

# Rollback if needed
make canary-rollback
```

**Risk segmentation**:

- **Low**: Internal team traffic only
- **Medium**: Beta customers, non-critical tenants
- **High**: Production traffic, critical workloads

**Guardrails**:

- Feature flag per request: `{"flags":{"adaptive_trm":true}}`
- Global kill-switch: `TRM_TRIGGER_THRESH=1.0`
- Hard budget: per-request token/time caps

## 📊 4. SLO-Driven Automation

### Critical SLOs

- **Availability**: ≥ 99.5% successful requests
- **Latency**: P95 end-to-end < 2s (simple), < 6s (complex)
- **Quality**: Golden score ≥ 80% (hourly)
- **Safety**: Zero high-severity policy violations

### Auto-Rollback Triggers

```bash
# SLO breach → automatic rollback
# Error rate > 1% → rollback
# P95 latency > 2s → rollback
# Golden score < 80% → rollback
# Availability < 99.5% → rollback
```

## 👥 5. Human-in-the-Loop Validation

**Goal**: Catch issues that metrics miss - LLM systems can "pass metrics" and still be wrong.

### Spot Check Validation

```bash
# Run human spot checks (50 samples)
make human-validation

# Red team adversarial testing
make red-team-test

# Policy validation
make policy-validation
```

**Validation criteria**:

- **Usefulness**: ≥ 85% of responses rated useful
- **Hallucinations**: Detect overconfidence and false claims
- **Formatting**: Appropriate response length and structure
- **Safety**: Block inappropriate or harmful content

### Red Team Testing

Tests adversarial prompts:

- Prompt injection attempts
- Tool abuse scenarios
- Data exfiltration attempts
- Policy violation attempts

## 🔄 6. Continuous Production Validation

### Day-2 Operations

```bash
# Hourly smoke tests (already automated)
make smoke-cron-setup

# Nightly RAG delta updates (already automated)
make rag-delta-setup

# Weekly chaos testing
make stage-chaos-test

# Monthly red team testing
make red-team-test
```

### Drift Detection

- Track RAG hit-rate and context waste ratio
- Monitor TRM value score: improvement / overhead
- Alert on sudden model route changes or cost spikes
- Weekly policy snapshot comparison

## 🚨 7. Failure Playbook (Pre-Wired)

### Instant Rollback Mechanisms

```bash
# Per-request rollback (no redeploy)
curl -X POST :8000/api/execute -d '{"flags":{"adaptive_trm":false}}'

# Global soft rollback (30s)
export TRM_TRIGGER_THRESH=1.0 && make stack-restart

# Hard rollback (<5 min)
make prod-rollback
```

### Escalation Triggers

- Zero-hit RAG surge
- Swap storm detection
- Weaviate OOM alerts
- Router 5xx > threshold

## 🎯 8. Stack-Specific Testing

### Router Model Routing

- Shadow + canary on `model: "auto"`
- Verify routes, latency, cost
- Test fallback behavior

### Dynamic RAG Lanes

- Ensure low/med/high queries hit intended lanes
- Alert if fast lane returns 0 hits
- Test lane escalation logic

### TRM Adaptive Policy

- A/B test static vs adaptive
- Watch `trm_value_score`, `trm_latency_overhead_ms`
- Monitor policy learning curves

### Model Pool Hot-Swap

- Simulate burst across models
- Assert no concurrent GPU residency
- Watch swap storm detector

### Weaviate Operations

- Large inserts + queries during compaction
- Ensure query latency P95 stable
- Monitor memory usage patterns

## 🔍 9. Common Failure Modes to Catch

### Silent Failures

- **Schema drift**: Weaviate class/props change → queries 0-hit
- **Embedding mismatch**: Changing encoder dims → insert OK, search wrong
- **Router fallback loops**: Model unavailable → infinite retries/cost spike

### Performance Degradation

- **Tool latency balloons**: Xcode build or shell tools → timeouts chain
- **RAG staleness**: Nightly delta fails silently → declining quality
- **Swap storms**: Model pool thrashes under mixed workloads

### Quality Issues

- **Over-retrieval**: Context waste >50% → cost + latency bloat
- **Adaptive policy over-fitting**: TRM never fires or fires on everything
- **Hallucination creep**: Confidence increases without accuracy improvement

## 📈 10. Production Readiness Checklist

- [ ] Stage environment mirrors production exactly
- [ ] Chaos testing passes without cascading failures
- [ ] Shadow traffic shows <10% drift rate
- [ ] Canary deployment with risk-based segmentation
- [ ] SLO monitoring with auto-rollback triggers
- [ ] Human validation passes (≥85% usefulness)
- [ ] Red team testing blocks ≥80% adversarial prompts
- [ ] Policy validation confirms safety measures
- [ ] Failure playbook tested and documented
- [ ] Continuous monitoring and alerting active

## 🎉 Bottom Line

**Real-world production testing = shadow → canary → ramp, guarded by SLOs, verified by humans, enforced with automated rollbacks, and chaos-tested regularly.**

Your Athena system now has battle-tested production validation that goes far beyond local "green" checks. This framework ensures your AGI system can handle real users, real data, and real failures with graceful degradation and automatic recovery.

🚀 **You're ready for production scale!**
