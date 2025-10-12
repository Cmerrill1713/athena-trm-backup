# NeuroForge Orchestrator - Operational Runbooks

**Production playbooks for incidents, rollbacks, and hot-swaps**

---

## 🚦 **GO/NO-GO GATES**

### **Pre-Launch Checklist:**
```bash
# 1. SLA Evaluation
cd orchestrator
make preflight

# Expected: ALL capabilities pass
# - Latency: ≤1500ms (p95)
# - Score: ≥0.70 (composite)

# 2. Shadow Sanity Check
# Edit policies.yaml:
# routing.summarize.shadow_percent: 1.0
make test

# Expected: Shadow fires 100% of time
# - Check trace logs for "shadow_result"
# - Shadow beats primary ≥30% on at least one capability

# 3. Error Budget
python3 scripts/load_test.py --requests 1000

# Expected: Failed requests ≤1%

# 4. DMG Realism
# Install on clean Mac → run preflight
# All SLAs pass without Xcode
```

---

## 🔐 **SECURITY POSTURE**

### **Localhost-Only Binding:**
```python
# api.py - Already configured
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)  # localhost only!
```

### **Offline Lock:**
```yaml
# policies.yaml
constraints:
  offline_only: true  # ✅ ENABLED by default
  pii_never_leave_local: true
```

### **State Hygiene:**
```bash
# Log rotation (add to cron)
find ./state -name "*.log" -mtime +7 -delete

# Optional: FileVault encryption (macOS)
diskutil apfs enableFileVault /
```

### **PII Guardrails:**
Already implemented in router - safety checks in composite scoring.

---

## 🧪 **LOAD & SOAK TESTING**

### **Concurrency Smoke:**
```bash
# Sequential (1000 requests)
python3 scripts/load_test.py --requests 1000 --mode sequential

# Parallel (25 concurrent × 200 batches = 5000 total)
python3 scripts/load_test.py --requests 5000 --concurrency 25
```

### **Soak Test:**
```bash
# 1 req/sec for 30 minutes (1800 requests)
python3 scripts/load_test.py --requests 1800 --rate 1 --duration 1800
```

### **Chaos Tiny:**
```bash
# While load test runs:
# Ctrl-C the API, restart, repeat
# Check: bandit state persists, no data loss
ls -la state/bandit.json  # Should exist and update
```

---

## 👀 **OBSERVABILITY**

### **SQLite One-Liners:**
```bash
# Count traces
sqlite3 state/telemetry.sqlite 'SELECT count(*) FROM traces;'

# Last 10 slow
sqlite3 state/telemetry.sqlite "
  SELECT capability, duration_ms, trace_id
  FROM traces
  ORDER BY duration_ms DESC
  LIMIT 10;
"

# Error rate by capability
sqlite3 state/telemetry.sqlite "
  SELECT capability,
         COUNT(*) as total,
         SUM(CASE WHEN raw_json LIKE '%timeout%' THEN 1 ELSE 0 END) as timeouts
  FROM traces
  GROUP BY capability;
"

# Shadow preference rate
sqlite3 state/telemetry.sqlite "
  SELECT COUNT(*) as shadow_preferred
  FROM traces
  WHERE raw_json LIKE '%shadow_preferred%';
"
```

### **Bandit Stats:**
```bash
# Check win rates
cat state/bandit.json | jq '.'

# Or via API
curl http://localhost:8765/stats | jq '.'
```

---

## 🧰 **PLAYBOOK 1: Hot-Swap Provider**

**Scenario:** Deploy new provider without downtime

```python
# 1. Register new provider (keep old one)
from registry import register_provider

register_provider("summarize", {
    "name": "summ_v2_improved",
    "entry": "providers.summ_v2:run",
    "caps": ["summarize"]
})

# 2. Enable shadow mode (50% traffic)
# Edit policies.yaml:
# routing.summarize.shadow_percent: 0.5

# 3. Monitor for N≥20 samples
curl http://localhost:8765/stats/summarize | jq '.providers.summ_v2_improved'

# Expected:
# {
#   "wins": X,
#   "losses": Y,
#   "samples": 20+,
#   "win_rate": >0.7,
#   "promotable": true
# }

# 4. If stable: unregister old provider
from registry import unregister_provider
unregister_provider("summarize", "summ_capability_stub")

# 5. Reset shadow to normal
# routing.summarize.shadow_percent: 0.2
```

---

## 🧰 **PLAYBOOK 2: Rollback Bandit Drift**

**Scenario:** Bandit state corrupted or poor performance

```bash
# 1. Backup current state
cp state/bandit.json state/bandit.json.bak_$(date +%s)

# 2. Reset to clean state
rm state/bandit.json

# 3. Restart API
# Bandit will reinitialize with default priors

# 4. Optional: Warm with known-good stats
cat > state/bandit.json <<EOF
{
  "summarize": {
    "agent_planner": {
      "wins": 90,
      "losses": 10,
      "samples": 100,
      "promotable": true
    }
  }
}
EOF
```

---

## 🧰 **PLAYBOOK 3: Incident Triage (<5 min)**

**Symptom:** p95 > 1.5s OR composite < 0.70

```bash
# Step 1: Check if shadow is winning
curl http://localhost:8765/traces?limit=20 | jq '.traces[] | select(.raw_json | contains("shadow_preferred"))'

# If shadow wins consistently → promote it (see Playbook 1)

# Step 2: Check context bloat
sqlite3 state/telemetry.sqlite "
  SELECT AVG(LENGTH(raw_json)) as avg_trace_size
  FROM traces
  WHERE capability='summarize';
"

# If >10KB avg → reduce context or TTL

# Step 3: Reduce max_tokens temporarily
# Edit policies.yaml:
# routing.summarize.max_tokens: 256  # down from 512

# Step 4: Unregister slow provider
from registry import unregister_provider
unregister_provider("summarize", "slow_provider_name")

# Restart API
```

---

## 🧰 **PLAYBOOK 4: Memory Hygiene**

**Scenario:** Memory growing too large

```python
# Configure TTLs
from memory.vector_store import configure_namespace

# Documents: 7 day TTL, max 1000 items
configure_namespace("docs", ttl_secs=7*24*3600, max_items=1000)

# Memory: 30 day TTL, max 2000 items
configure_namespace("mem", ttl_secs=30*24*3600, max_items=2000)

# Pin important items
from memory.hygiene import pin

def is_golden(text):
    return "golden" in text.lower() or "high-quality" in text.lower()

pin("docs", is_golden)
```

---

## 🧰 **PLAYBOOK 5: Quality Lever Tuning**

**Scenario:** Adjust scoring priorities

```yaml
# policies.yaml - Prioritize structure over latency
scorecard_weights:
  correctness: 0.45
  structure:   0.30  # ↑ increased from 0.15
  safety:      0.15
  latency:     0.05  # ↓ decreased from 0.15
  acceptance:  0.05  # ↓ decreased from 0.10
```

---

## 🧰 **PLAYBOOK 6: User Acceptance Loop**

**Future Enhancement:** Track user feedback

```python
# Add to trace events
log_event(trace, "user_feedback", {
    "action": "accept|edit|revert",
    "timestamp": time.time()
})

# Adjust reward in scorer.py
def reward_with_feedback(capability, provider, score, feedback):
    if feedback == "accept":
        score += 0.2
    elif feedback == "revert":
        score -= 0.2

    reward(capability, provider, score)
```

---

## 📦 **RELEASE RITUAL**

### **Step-by-Step:**
```bash
# 1. Bump policy version
# Edit policies.yaml:
# policy_version: "v2"

# 2. Update changelog
echo "## v2.0.0 - $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "- New provider: XYZ" >> CHANGELOG.md
echo "- Improved latency: 15%" >> CHANGELOG.md

# 3. Merge to main
git checkout main
git merge --no-ff v0.9.2-dev
git tag v2.0.0
git push && git push --tags

# 4. Build DMG from main
cd ../NeuroForgeApp
make -f Makefile.dmg dmg

# 5. Generate checksum
shasum -a 256 build/NeuroForge.dmg > build/NeuroForge.dmg.sha256

# 6. Create GitHub Release
# - Attach DMG + checksum
# - Paste changelog

# 7. Snapshot state
cp orchestrator/state/bandit.json releases/v2.0.0-bandit.json
cp orchestrator/state/telemetry.sqlite releases/v2.0.0-telemetry.sqlite

# 8. Ramp shadow to 20%
# Edit policies.yaml:
# routing.*.shadow_percent: 0.2

# Monitor for 24h
```

---

## ✅ **SHIP-IT CHECKLIST**

**One-Page Verification:**

```bash
# [ ] Preflight SLA green on DMG install
cd NeuroForgeApp && make -f Makefile.dmg dmg
# Install on clean Mac, run: orchestrator/preflight.sh

# [ ] Shadow ramped to 20% without regressions
# Check: no increase in timeout rate, scores stable

# [ ] Bandit state persists across restart
killall uvicorn; make api &
cat state/bandit.json  # Should contain previous stats

# [ ] Offline lock ON
grep "offline_only: true" policies.yaml

# [ ] No egress in traces
sqlite3 state/telemetry.sqlite "
  SELECT * FROM traces
  WHERE raw_json LIKE '%external%' OR raw_json LIKE '%network%';
"
# Should be empty

# [ ] Eval pass ≥80%
python3 scripts/eval.py
# Expected: ≥80% pass rate

# [ ] Robustness pass 100%
python3 scripts/robustness_test.py
# Expected: 0 policy violations

# [ ] Runbooks printed
ls -la RUNBOOKS.md

# [ ] Release note + checksum
ls -la build/NeuroForge.dmg.sha256
```

---

## 🆘 **EMERGENCY CONTACTS**

**Critical Issues:**
- Check: `state/telemetry.sqlite` for traces
- Check: `state/bandit.json` for stats
- Rollback: Restore `.bak` files
- Kill switch: `rm state/bandit.json && restart`

**Performance Degradation:**
1. Enable shadow 100% → find winner
2. Reduce max_tokens
3. Clear memory namespaces
4. Unregister slow providers

**Data Loss:**
- State files in `state/` directory
- Backups in `releases/` directory
- Git tags preserve policy versions

---

**RUNBOOKS COMPLETE** ✅
**Print this file and keep near your desk!** 📋
