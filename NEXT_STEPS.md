# Next Steps - Athena Platform

**Current Status:** 96% Wired, Shadow Mode Active  
**Target:** 100% Wired, Production Ready

---

## 🎯 **Phase A: Quick Wins (15 min → 100%)**

### **1. Fix Orchestrator Health Check**
```bash
# Check orchestrator status
curl -s http://localhost:9110/health

# If not running, start it:
cd governance/executive/orchestration
python3 orchestrator_service.py &

# Or via Docker:
docker compose -f docker-compose.athena-governance.yml restart orchestrator
```

**Expected:** Orchestrator health returns 200 OK

### **2. Fix Grafana Health Check**
```bash
# Grafana is running on 3001, but health check expects 3000
# Update wiring matrix or check actual port:
curl -s http://localhost:3001/api/health

# Option A: Update config to use 3001
# Option B: Restart Grafana on port 3000
```

**Expected:** Grafana health returns 200 OK

### **3. Validate 100%**
```bash
make wire-validate
# Expected: 100% (59/59) ✅
```

---

## 🔬 **Phase B: Prove Auto-Remediation Works (1-2 hours)**

### **Experiment 1: Shadow Analysis**
```bash
# Generate 10 shadow remediation plans
for i in {1..10}; do
  make exp-shadow
  sleep 30
done

# Analyze results
python3 << 'PY'
import json, glob
results = [json.load(open(f)) for f in glob.glob("artifacts/remediation_shadow/*.json")]
promote_rate = sum(1 for r in results if r["would_promote"]) / len(results)
print(f"Shadow Promote Rate: {promote_rate:.1%}")
print(f"Avg ECE: {sum(r['canary_simulation']['ece_post'] for r in results) / len(results):.4f}")
PY
```

**Success Criteria:** 
- ≥30% would promote
- Avg ECE < 0.06

### **Experiment 2: Deploy Canary (1% Traffic)**
```bash
# Start canary mode
./scripts/flip_mode.sh canary

# Monitor for 30 minutes
watch -n 10 'curl -s http://localhost:9110/metrics | grep governance_'

# Check KPIs
make gate
```

**Success Criteria:**
- No ECE spikes > 0.08
- No entropy drift > 0.25
- Coverage ≥ 98%

### **Experiment 3: Manual Verdict Test**
```bash
# Send test verdicts
curl -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "manual-test-001",
    "verdict": "HARD_FAIL",
    "ece_post": 0.09,
    "entropy": 0.3,
    "actions": ["ROLLBACK"],
    "ts": "'$(date -u +%FT%TZ)'"
  }'

# Verify rollback happened
curl -s http://localhost:9110/state | jq
```

**Expected:** State shows rollback applied

---

## 📊 **Phase C: Observability Setup (30 min)**

### **1. Import Grafana Dashboards**
```bash
# Governance dashboard
curl -X POST http://localhost:3001/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer admin:admin' \
  -d @monitoring/grafana/dashboards/governance-dashboard.json

# DGM Evolution dashboard
curl -X POST http://localhost:3001/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer admin:admin' \
  -d @monitoring/grafana/dashboards/dgm-evolution.json

# Unified Athena dashboard
curl -X POST http://localhost:3001/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer admin:admin' \
  -d @monitoring/grafana/dashboards/athena-unified.json
```

**Access:** http://localhost:3001 (admin/admin)

### **2. Verify Prometheus Alerts**
```bash
# Check alert rules loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[].name'

# Should see:
# - GovernanceCoverageDrop
# - NoVerdictsProduced
# - ECEHigh
# - EntropyDriftHigh
```

### **3. Set Up Alert Routing (Optional)**
```bash
# Configure Slack webhook (if you have one)
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

# Test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname": "TestAlert", "severity": "info"},
    "annotations": {"summary": "Athena test alert"}
  }]'
```

---

## 🧪 **Phase D: Run Full Experimental Suite (2-3 hours)**

### **Phase 1: Shadow (Already Done ✅)**
```bash
make exp-shadow
```

### **Phase 2: Canary Auto-Remediation**
```bash
# Deploy to 1% canary traffic
make exp-remediate

# Monitor for 1 hour
# Check metrics every 5 minutes
```

**Success Criteria:**
- ≥30% reduction in rollback rate
- No violation increase
- ECE stays < 0.06

### **Phase 3: A/B Policy Testing**
```bash
make exp-ab

# Compare LLM free-form vs rule-templated plans
# Run for 24 hours or 100 incidents
```

### **Phase 4: Devil's Advocate Gates**
```bash
make exp-devils-adv

# Add adversarial probes to gates
# Measure post-promotion incident rate
```

### **Phase 5: Cost-Aware Remediation**
```bash
make exp-cost

# Track token usage, build time, infra cost
# Optimize for cheap + safe
```

### **Phase 6: Human-in-the-Loop Fast-Track**
```bash
# Set up Slack integration
export SLACK_WEBHOOK_URL='...'

make exp-fasttrack

# Expert can approve via Slack to skip long windows
```

### **Phase 7: Long-Run Adaptive Learning**
```bash
make exp-longrun

# Run weekly adaptive threshold tuning
# Compare learned vs static thresholds
```

---

## 🚀 **Phase E: Production Deployment (1 day)**

### **Day 1 Morning: Shadow Validation**
```bash
# Confirm shadow mode stable for 24h
curl -s http://localhost:9110/metrics | grep governance_

# Check coverage
make gate
# Expected: ≥98%
```

### **Day 1 Afternoon: Canary Promotion**
```bash
# Deploy to 5% canary
./scripts/flip_mode.sh canary

# Monitor closely for 4 hours
# Check dashboards every 15 minutes
# Alert on any ECE > 0.08 or entropy > 0.25
```

### **Day 1 Evening: Decision Point**
```bash
# If all green after 4 hours:
# Option A: Increase to 10% canary
# Option B: Hold at 5% for 24h
# Option C: Full enforce (if very confident)

# If any issues:
./scripts/flip_mode.sh shadow  # Rollback
```

### **Day 2: Full Enforcement**
```bash
# After 24h stable canary:
./scripts/flip_mode.sh enforce

# Monitor for first 2 hours continuously
# Then hourly checks for 24 hours
```

---

## 🎯 **Phase F: Advanced Features (Week 2)**

### **1. DGM Self-Improvement Experiments**
```bash
# Update DGM to use local Ollama
export OLLAMA_HOST='http://localhost:11434'
export REMEDIATION_MODEL='qwen3-coder:30b'

# Run DGM experiment
./scripts/dgm_quickstart.sh

# Monitor evolution
curl -s http://localhost:8000/dgm/status | jq
```

### **2. AGI Core Integration**
```bash
# Test full research → governance → deployment workflow
python3 workflows/end_to_end_integration.py \
  --mode research_to_production \
  --task "Optimize ECE calculation for sparse data"

# Check results in artifacts/
```

### **3. Swift UI Integration**
```bash
# Open in Xcode
cd NeuroForgeApp
open NeuroForgeApp.xcodeproj

# Run app (⌘R)
# Should see:
# - Live governance KPIs
# - Mode switcher (Shadow/Canary/Enforce)
# - Verdict submission form
# - Recent receipts list
# - Active alerts
```

### **4. Policy Self-Modification**
```bash
# Enable DGM policy learning
python3 governance/executive/orchestration/dgm_orchestrator.py \
  --enable-self-modification \
  --constitutional-guard

# Monitor changes
tail -f governance/legislative/self_modification_policy.yaml
```

---

## 🎓 **Phase G: Optimization & Tuning (Week 3-4)**

### **1. Threshold Tuning**
```bash
# Analyze historical data
python3 << 'PY'
import pandas as pd
import json

# Load verdict history
verdicts = pd.read_json("exec_action_ledger.jsonl", lines=True)

# Calculate optimal thresholds
ece_p95 = verdicts["ece_post"].quantile(0.95)
entropy_p95 = verdicts["entropy"].quantile(0.95)

print(f"Suggested ECE threshold: {ece_p95:.4f}")
print(f"Suggested Entropy threshold: {entropy_p95:.4f}")
PY

# Update policy file with learned thresholds
```

### **2. Canary Window Optimization**
```bash
# Analyze window effectiveness
python3 << 'PY'
import json
results = json.load(open("artifacts/canary_results.json"))

# Find optimal sample size
for min_samples in [100, 200, 300, 500]:
    subset = [r for r in results if r["samples"] >= min_samples]
    accuracy = sum(1 for r in subset if r["correct_decision"]) / len(subset)
    print(f"Samples≥{min_samples}: {accuracy:.1%} accuracy")
PY
```

### **3. Performance Optimization**
```bash
# Profile verdict latency
curl -s http://localhost:9110/metrics | grep verdict_duration

# If p95 > 150ms, optimize:
# - Add verdict caching
# - Parallelize policy checks
# - Use faster embedding model
```

---

## 📊 **Success Metrics (Track Weekly)**

### **Governance KPIs**
- ECE: < 0.06 (target), < 0.08 (red line)
- Entropy: < 0.20 (target), < 0.25 (red line)
- Coverage: ≥ 98%
- Verdict latency p95: < 150ms
- Action success rate: ≥ 95%

### **Auto-Remediation KPIs**
- Rollback reduction: ≥ 30%
- Time to mitigation: ≤ 10 minutes
- False positive rate: < 5%
- Cost per remediation: < $0.50

### **System KPIs**
- Uptime: ≥ 99.9%
- Prometheus scrape success: 100%
- Alert firing rate: < 5/day (steady state)
- Canary pass rate: ≥ 70%

---

## 🛡️ **Safety Checks (Run Daily)**

```bash
# Daily health check
make wire-validate        # Should be 100%
make gate                 # Should be ≥98%

# Weekly full test
make pre-ship-safe        # All tests pass

# Monthly chaos drill
make chaos-full           # System recovers gracefully
```

---

## 📞 **When to Escalate**

**Stop and rollback if:**
- ECE > 0.10 for 5+ minutes
- Entropy > 0.30 for 2+ minutes
- Violation rate increases > 1%
- Any HARD_FAIL in enforce mode causes production issue
- Coverage drops below 95%

**Command:**
```bash
./scripts/flip_mode.sh shadow
# Then investigate artifacts/ and Grafana
```

---

## 🎯 **1-Month Roadmap Summary**

| Week | Focus | Goal |
|------|-------|------|
| 1 | Get to 100%, run experiments | Shadow → Canary validated |
| 2 | Canary deployment | 5% → 10% → 50% canary |
| 3 | Full enforcement | 100% governed traffic |
| 4 | Optimization & DGM | Self-improving, cost-optimized |

---

## 🏆 **End State (1 Month)**

**You'll have:**
- ✅ 100% governance coverage
- ✅ Auto-remediation reducing incidents by 30%+
- ✅ Self-improving AI agents (DGM)
- ✅ Adaptive thresholds learning from data
- ✅ Real-time dashboards and alerts
- ✅ Full constitutional compliance
- ✅ Cost-optimized operations
- ✅ Swift UI for live control

**Commands you'll run daily:**
```bash
make wire-validate  # Quick health check
make gate          # Coverage verification
open http://localhost:3001  # Check dashboards
```

**You'll be able to say:**
"Our AI governance system autonomously maintains ECE < 0.06, auto-remediates incidents in < 10 minutes, and self-improves weekly while staying constitutionally compliant."

---

## 📚 **References**

- **Status:** `STATUS.md`
- **Architecture:** `SYSTEM_ARCHITECTURE.md`
- **Experiments:** `governance/experimental/EXPERIMENTS.md`
- **Runbooks:** `RUNBOOKS/DGM_OPERATOR_RUNBOOK.md`
- **Wiring:** `WIRING_DEFINITION.md`

