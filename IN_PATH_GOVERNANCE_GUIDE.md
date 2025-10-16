# In-Path Governance - Complete Deployment Guide

**End-to-end program:** Shadow → Canary → Enforce with coverage, gates, metrics, and rollback

---

## 🎯 **What This Is**

**In-Path Governance** = Every request goes through governance validation

**Three Modes:**

1. **Shadow** (0% impact) - Observe only, collect data
2. **Canary** (1-5% impact) - Enforce on small traffic slice
3. **Enforce** (100% impact) - Full governance enforcement

---

## 🚀 **Quick Start (Shadow Mode)**

```bash
# 1. Start services
make governance-up
make prom-up

# 2. Set shadow mode
make mode-shadow

# 3. Verify coverage
make gate

# 4. Monitor
make verify
```

**Shadow mode has 0% production impact** - safe to start immediately!

---

## 📦 **What Was Created**

### Infrastructure Files

```
infra/
├── ingress/nginx.conf              # Traffic mirror config
├── eventbus/nats-relay.sh          # Event bus relay
├── sdk/python/athena_client.py     # Python SDK
├── prometheus/prometheus.yml       # Metrics collection
└── prometheus/alerts-governance.yml # Alert rules
```

### Scripts

```
scripts/
├── coverage_gate.sh               # Coverage verification
└── flip_mode.sh                   # Mode switching
```

### CI/CD

```
.github/workflows/
└── governance-coverage.yml        # Continuous coverage check
```

### Makefile Targets

```
make ingress-up      # Start ingress mirror
make prom-up         # Start Prometheus
make mode-shadow     # Set shadow mode
make mode-canary     # Set canary mode
make mode-enforce    # Set enforce mode
make gate            # Check coverage
make verify          # Verify operational
```

---

## 🔌 **How It Works**

### 1. **Traffic Mirroring (Nginx)**

```
Every Request
    ↓
Nginx Ingress
    ├─→ Forward to App (normal flow)
    └─→ Mirror to Athena /receipt (async)
            ↓
        Athena Orchestrator (9110)
            ↓
        Governance Evaluation
            ↓
        Metrics Exported
            ↓
        Prometheus Scraped
```

**Key Points:**

- ✅ Mirror is async - doesn't slow down requests
- ✅ App continues working normally
- ✅ Governance sees 100% of traffic
- ✅ No code changes in app required

### 2. **Mode Controls Enforcement**

| Mode        | Mirror | Enforce | Impact |
| ----------- | ------ | ------- | ------ |
| **Shadow**  | 100%   | 0%      | None   |
| **Canary**  | 100%   | 1-5%    | Low    |
| **Enforce** | 100%   | 100%    | Full   |

**Transition:**

```bash
make mode-shadow   # Start here (day 1-2)
make mode-canary   # After verification (day 3-5)
make mode-enforce  # After canary success (day 7+)
```

---

## 📊 **Coverage Metrics**

### What Coverage Means

```
Coverage = governance_receipts_total / ingress_requests_total
```

**Target:** ≥98% coverage

**Why it matters:**

- If coverage < 98%, governance isn't seeing all traffic
- Indicates ingress mirror may be broken
- Required before moving to canary/enforce

### Check Coverage

```bash
make gate

# Manual check
curl -s "http://localhost:9090/api/v1/query?query=sum(governance_receipts_total)" | jq
curl -s "http://localhost:9090/api/v1/query?query=sum(ingress_requests_total)" | jq
```

---

## 🚦 **Rollout Ladder (Safe Progression)**

### Day 1-2: Shadow Mode ✅

```bash
# A. Start services
make governance-up
make prom-up

# B. Enable shadow mode
make mode-shadow

# C. Verify coverage reaches ~100%
watch -n 5 'make gate'

# D. Monitor for 24-48 hours
# Watch for: coverage ≥98%, no orchestrator errors, metrics flowing
```

**Success Criteria:**

- ✅ Coverage ≥98%
- ✅ Verdicts being rendered
- ✅ No orchestrator errors
- ✅ Prometheus scraping

### Day 3-5: Canary Mode ⚠️

```bash
# A. Flip to canary (1-5% enforcement)
make mode-canary

# B. Monitor closely
watch -n 10 'make verify'

# C. Check for issues
# Watch for: ECE ≤0.06, violations stable, no rollbacks
```

**Success Criteria:**

- ✅ No ECE regression (≤0.06)
- ✅ No violation increase
- ✅ No emergency rollbacks
- ✅ Actions being taken on canary traffic

**Auto-Rollback Triggers:**

- ❌ ECE > 0.08 → immediate rollback
- ❌ Violations +0.5% → rollback + freeze 30m
- ❌ Entropy ≥0.25 → rollback

### Day 7+: Enforce Mode 🛡️

```bash
# A. Review canary results (3-5 days of data)
# Ensure: stable metrics, no regressions, team confident

# B. Flip to full enforcement
make mode-enforce

# C. Monitor intensively for first 24h
watch -n 5 'make verify'

# D. Have rollback ready
# If any issues: make mode-shadow
```

**Success Criteria:**

- ✅ All SLOs maintained
- ✅ ECE stable
- ✅ No violation spikes
- ✅ Team confidence high

---

## 🔧 **SDK Integration (Optional)**

For jobs, CLIs, or services that don't go through nginx:

```python
from infra.sdk.python.athena_client import governed_task, emit_receipt

# Decorator approach
@governed_task("batch_processing")
def process_batch(items):
    # Your code here
    return results

# Manual approach
emit_receipt("manual_task", {"step": 1}, "start")
try:
    do_work()
    emit_receipt("manual_task", {"result": "ok"}, "end")
except Exception as e:
    emit_receipt("manual_task", {"error": str(e)}, "error")
    raise
```

**Why use it:**

- Extends governance coverage to background jobs
- Consistent tracing across system
- No ingress dependency

---

## 📈 **Metrics to Watch**

### Critical SLOs

```prometheus
# Coverage
sum(governance_receipts_total) / sum(ingress_requests_total) >= 0.98

# Safety
governance_ece_post < 0.06
governance_entropy_drift < 0.25
governance_violation_rate_delta < 0.005

# Availability
governance_orchestrator_up == 1
increase(governance_verdicts_total[5m]) > 0
```

### Performance

```prometheus
# Latency
governance_latency_p95_delta < 0.50

# Throughput
rate(governance_verdicts_total[1m]) > 0
```

### Remediation (Experimental)

```prometheus
# Phase 1
governance_shadow_would_promote_total / governance_shadow_experiments_total >= 0.70

# Phase 2
rate(governance_remediations_completed_total{decision="PROMOTE"}[1h])
```

---

## 🚨 **Alert Rules**

### Critical (Immediate Action)

- **GovernanceCoverageDrop** - Coverage <98%
- **ECECritical** - ECE >0.08 → auto-rollback
- **EntropyDriftCritical** - Entropy ≥0.25 → rollback
- **ViolationRateSpike** - Violations +0.5%
- **GovernanceOrchestratorDown** - Service down

### Warning (Monitor Closely)

- **NoVerdictsProduced** - Receipts flowing but no verdicts
- **GovernanceLatencyHigh** - Latency p95 +50%
- **EdgeCaseScoreLow** - Edge case score <0.8
- **RemediationFailureRate** - >50% remediations fail

---

## 🛡️ **Safety Rails**

### Automatic Rollback Triggers

```bash
# Hard gates (immediate rollback)
ECE > 0.08                    → make mode-shadow + freeze 30m
Entropy drift ≥ 0.25          → make mode-shadow + freeze 30m
Violations +0.5%              → make mode-shadow + freeze 30m

# Freeze after incidents
HARD_FAIL verdict             → freeze promotions 10-15m
```

### Hysteresis

- No flip-flop decisions per route <10m
- Minimum cool-down: 15m after rollback
- Mode changes require manual approval

### Fail-Safe

- Missing metrics → HOLD (not PROMOTE)
- Orchestrator down → fall back to app-only
- Prometheus down → freeze decisions

---

## 🧪 **Experimental Integration**

Once in-path governance is stable (shadow mode running):

```bash
# Run shadow remediation experiments
make exp-shadow

# View results
ls -lh artifacts/remediation_shadow/

# Analyze
jq '.would_promote' artifacts/remediation_shadow/*.json | grep true | wc -l
```

**Success:** ≥70% would promote → ready for Phase 2 (auto-remediation)

---

## 📋 **Sanity Checks**

### Before Going to Canary

```bash
# 1. Coverage check
make gate
# Expect: ✅ Coverage OK (>= 0.98)

# 2. Metrics flowing
make verify
# Expect: governance_* metrics visible

# 3. Verdicts rendering
curl -s "http://localhost:9090/api/v1/query?query=increase(governance_verdicts_total[5m])" | jq
# Expect: Non-zero verdicts

# 4. No errors
docker logs governance-orchestrator --tail 100 | grep ERROR
# Expect: No critical errors

# 5. Prometheus healthy
curl http://localhost:9090/-/healthy
# Expect: Prometheus Server is Healthy.
```

### After Each Mode Change

```bash
# Wait 5 minutes, then check
sleep 300

# Verify metrics stable
make verify

# Check for alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
# Expect: No critical alerts

# Check ECE
curl -s "http://localhost:9090/api/v1/query?query=governance_ece_post" | jq '.data.result[0].value[1]'
# Expect: <0.06
```

---

## 🔄 **Rollback Procedure**

### Manual Rollback

```bash
# Immediate rollback to shadow
make mode-shadow

# Stop ingress mirror (if needed)
docker stop ingress

# Freeze promotions
curl -X POST http://localhost:9110/freeze \
  -H 'Content-Type: application/json' \
  -d '{"duration_minutes":30,"reason":"manual_rollback"}'
```

### Automated Rollback

The orchestrator will auto-rollback if:

- ECE >0.08
- Entropy ≥0.25
- Violations +0.5%

Monitor in Prometheus:

```bash
watch -n 5 'curl -s http://localhost:9090/api/v1/alerts | jq ".data.alerts[] | select(.labels.action==\"rollback\")"'
```

---

## 📚 **Configuration Reference**

### Environment Variables

```bash
# Required
export ATHENA_MODE=shadow                    # shadow | canary | enforce
export ATHENA_POLICY_VERSION=abc123def456    # Policy bundle hash

# Optional
export ATHENA_URL=http://localhost:9110      # Orchestrator URL
export PROM_URL=http://localhost:9090        # Prometheus URL
export MIN_COVERAGE=0.98                     # Coverage threshold
```

### Policy Bundle

```bash
# Generate policy version hash
shasum -a 256 governance/legislative/self_modification_policy.yaml | cut -c1-12
```

This hash is sent with every receipt to track policy compliance.

---

## 🎯 **SLOs (Service Level Objectives)**

| Metric                  | Target          | Rollback At |
| ----------------------- | --------------- | ----------- |
| **Coverage**            | ≥98%            | <95%        |
| **ECE**                 | ≤0.06           | >0.08       |
| **Entropy Drift**       | <0.25           | ≥0.25       |
| **Violations**          | Stable          | +0.5%       |
| **Verdict Latency p95** | <150ms (canary) | >500ms      |
| **Verdict Latency p95** | <50ms (enforce) | >200ms      |

---

## 🔍 **Debugging**

### Coverage Is Low (<98%)

```bash
# Check ingress is mirroring
docker logs ingress | grep athena_mirror

# Check orchestrator /receipt endpoint
curl -X POST http://localhost:9110/receipt \
  -H 'Content-Type: application/json' \
  -d '{"trace_id":"test","method":"GET","path":"/test"}'

# Check Prometheus scraping
curl http://localhost:9090/api/v1/targets | jq
```

### No Verdicts Rendered

```bash
# Check orchestrator health
curl http://localhost:9110/health | jq

# Check metrics
curl http://localhost:9110/metrics | grep governance_receipts

# Check logs
docker logs governance-orchestrator --tail 50
```

### Metrics Not in Prometheus

```bash
# Verify Prometheus targets
make prom-verify

# Check scrape config
docker exec athena-prometheus cat /etc/prometheus/prometheus.yml

# Reload config
curl -X POST http://localhost:9090/-/reload
```

---

## 📚 **Related Documentation**

- **EXPERIMENTS.md** - 7-phase remediation plan
- **WIRING_DEFINITION.md** - Integration architecture
- **PROMETHEUS_SCRAPING_COMPLETE.md** - Metrics setup
- **CURSOR_SETUP_GUIDE.md** - IDE configuration

---

## ✅ **Pre-Flight Checklist**

Before deploying to production:

### Shadow Mode (Day 1)

- [ ] All governance services running (9109, 9110, 9111)
- [ ] Prometheus scraping targets
- [ ] Nginx ingress mirror configured
- [ ] Coverage gate passing (≥98%)
- [ ] Metrics flowing to Grafana
- [ ] Alerts configured
- [ ] Runbook reviewed

### Canary Mode (Day 3)

- [ ] Shadow ran for 24-48h successfully
- [ ] No critical alerts
- [ ] Coverage stable at ≥98%
- [ ] Team reviewed shadow data
- [ ] Rollback procedure tested
- [ ] On-call engineer available

### Enforce Mode (Day 7)

- [ ] Canary ran for 3-5 days successfully
- [ ] All SLOs maintained
- [ ] No regressions detected
- [ ] Team has high confidence
- [ ] Rollback tested and fast (<2min)
- [ ] Incident response plan ready

---

## 🎊 **Success Criteria**

### Shadow Mode

- ✅ Coverage ≥98%
- ✅ Verdicts rendering
- ✅ Metrics in Prometheus
- ✅ No orchestrator errors
- ✅ Run for 24-48h

### Canary Mode

- ✅ ECE ≤0.06
- ✅ No violation increase
- ✅ No rollbacks
- ✅ Latency p95 <150ms
- ✅ Run for 3-5 days

### Enforce Mode

- ✅ All SLOs maintained
- ✅ ECE stable
- ✅ No regressions
- ✅ Rollback <2min if needed
- ✅ 100% coverage

---

## 🚀 **Commands Reference**

### Setup

```bash
make governance-up     # Start governance stack
make prom-up           # Start Prometheus
make ingress-up        # Start ingress mirror
```

### Mode Switching

```bash
make mode-shadow       # Observe only (0% impact)
make mode-canary       # Enforce on 1-5%
make mode-enforce      # Full enforcement (100%)
```

### Verification

```bash
make gate              # Check coverage ≥98%
make verify            # Check services operational
make wire-check        # Full integration check
make prom-verify       # Check Prometheus targets
```

### Monitoring

```bash
make prom-query        # Query governance metrics
curl http://localhost:9110/metrics | grep governance_
curl http://localhost:9090/api/v1/alerts
```

### Experiments

```bash
make exp-shadow        # Phase 1 (shadow remediation)
```

---

## 🏆 **Complete System Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                   USER TRAFFIC                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   NGINX INGRESS       │
         │   (Mirror Enabled)    │
         └─────┬────────────┬────┘
               │            │
         ┌─────▼────┐   ┌───▼──────────────┐
         │   APP    │   │ Athena /receipt  │ (async)
         │  (Normal)│   │   (9110)         │
         └──────────┘   └────────┬─────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Governance Orchestrator│
                    │  • Evaluate request    │
                    │  • Render verdict      │
                    │  • Execute actions     │
                    └───────┬────────────────┘
                            │
                    ┌───────┼────────┐
                    │       │        │
                    ▼       ▼        ▼
              ┌─────────┐ ┌──────┐ ┌────────┐
              │ Metrics │ │ State│ │ Ledger │
              │ (Prom)  │ │ (JSON│ │ (JSONL)│
              └─────────┘ └──────┘ └────────┘
                    │
                    ▼
              ┌─────────────┐
              │  Grafana    │
              │ (Dashboards)│
              └─────────────┘
```

---

## 🎯 **Next Steps**

1. **Deploy to Shadow** (NOW - no risk)

   ```bash
   make mode-shadow
   make gate
   ```

2. **Run Experiments** (while in shadow)

   ```bash
   make exp-shadow
   ```

3. **Monitor for 24-48h**

   - Check coverage stays ≥98%
   - Verify metrics flowing
   - Review shadow experiment results

4. **Graduate to Canary** (when ready)

   ```bash
   make mode-canary
   ```

5. **Monitor canary closely**

   - Watch for 3-5 days
   - Check ECE, violations, rollbacks

6. **Full Enforce** (after canary success)
   ```bash
   make mode-enforce
   ```

---

**Start now with zero risk:**

```bash
make mode-shadow
make gate
```

🎉 **You now have complete in-path governance ready to deploy!**
