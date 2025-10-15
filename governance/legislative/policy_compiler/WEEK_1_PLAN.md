# 📅 NeuroForge v0.9.2 - Week 1 Launch Plan

**Day-by-day operational plan for first week post-launch**

**Version**: 0.9.2
**Launch Date**: [DATE]
**Status**: Active Monitoring

---

## 🎯 **WEEK 1 GOALS**

**Success Criteria:**
- ✅ 0 critical incidents
- ✅ Error rate ≤1%
- ✅ p95 latency ≤1.5s
- ✅ 5+ successful user executions
- ✅ Bandit state stable (no thrashing)
- ✅ Positive user feedback

---

## 📅 **DAY 0 (Launch Day)**

### **Morning (Pre-Launch):**
```bash
# [ ] Final preflight
cd orchestrator
make preflight

# [ ] DMG verified on clean Mac
# [ ] Checksum published
# [ ] GitHub Release created
# [ ] State snapshots saved
```

### **Launch (T+0):**
```bash
# Start monitoring
cd orchestrator

# Terminal 1: API
make api

# Terminal 2: Eval API
cd tools
python3 -m uvicorn eval_api:app --host 127.0.0.1 --port 8788
```

### **First 2 Hours (Monitor Every 15 Min):**
```bash
# Trace count (should grow)
watch -n 900 'sqlite3 state/telemetry.sqlite "SELECT count(*) FROM traces;"'

# Error rate
python3 -c "
import sqlite3
c = sqlite3.connect('orchestrator/state/telemetry.sqlite')
total = c.execute('SELECT count(*) FROM traces').fetchone()[0]
errors = c.execute('SELECT count(*) FROM traces WHERE raw_json LIKE \"%error%\" OR raw_json LIKE \"%timeout%\"').fetchone()[0]
rate = (errors/total*100) if total > 0 else 0
print(f'Errors: {errors}/{total} ({rate:.1f}%)')
if rate > 1.0:
    print('⚠️  ERROR RATE EXCEEDS 1%!')
"

# p95 latency
sqlite3 state/telemetry.sqlite "
  SELECT capability, duration_ms
  FROM traces
  ORDER BY duration_ms DESC
  LIMIT 5;
"

# Shadow performance
sqlite3 state/telemetry.sqlite "
  SELECT COUNT(*) as shadow_preferred
  FROM traces
  WHERE raw_json LIKE '%shadow_preferred%';
"
```

### **End of Day 0:**
```bash
# [ ] No critical issues in first 8 hours
# [ ] Error rate ≤1%
# [ ] At least 5 successful executions
# [ ] Bandit state updated (check state/bandit.json)
# [ ] User feedback collected
```

**If ANY red flags:** Consult `RUNBOOKS.md` - Playbook 3: Incident Triage

---

## 📅 **DAY 1**

### **Morning Check (5 min):**
```bash
# Trace count overnight
sqlite3 orchestrator/state/telemetry.sqlite 'SELECT count(*) FROM traces;'

# Error rate
python3 scripts/check_error_rate.py

# p95 latency trend
sqlite3 state/telemetry.sqlite "
  SELECT AVG(duration_ms) as avg_latency
  FROM (SELECT duration_ms FROM traces ORDER BY started_at DESC LIMIT 100);
"

# Bandit health
jq '.' state/bandit.json | head -30
```

### **Actions:**
```bash
# [ ] Review overnight traces
# [ ] Check for any timeout spikes
# [ ] Verify shadow_percent still at 0.5
# [ ] No provider thrashing (win rates stable)
```

### **If Issues:**
- **p95 creeping up** → Trim `max_tokens`, run memory cleanup
- **High error rate** → Check logs, potentially disable slow provider
- **Shadow winning** → Keep shadow at 0.5 for another day

---

## 📅 **DAY 2**

### **Morning Check (5 min):**
```bash
# Same as Day 1

# Additionally: Run eval
curl -X POST http://127.0.0.1:8788/eval/run \
  -H 'Content-Type: application/json' \
  -d '{"limit":5}' | jq '.'

# Expected: pass_rate ≥0.85
```

### **Actions:**
```bash
# [ ] Eval pass rate ≥85%
# [ ] Review shadow performance
# [ ] Check telemetry DB size (should be <50MB)
# [ ] Collect user feedback
```

---

## 📅 **DAY 3**

### **Morning Check + Shadow Ramp-Down:**

```bash
# If stable (no incidents, error rate <1%, p95 stable):
# Reduce shadow from 0.5 → 0.2

# Edit orchestrator/policies.yaml:
# routing:
#   summarize:
#     shadow_percent: 0.2  # Down from 0.5
#   plan:
#     shadow_percent: 0.2
```

```bash
# Commit change
git add orchestrator/policies.yaml
git commit -m "chore: reduce shadow to 20% after stable Day 0-2"
git push

# Restart API
killall uvicorn
cd orchestrator && make api &
```

### **Actions:**
```bash
# [ ] Shadow ramped down to 20%
# [ ] Monitor for regression after change
# [ ] Bandit has ≥20 samples per provider
# [ ] Provider win rates calculated
```

---

## 📅 **DAY 4-6**

### **Daily Check (3 min):**
```bash
# Quick health check
curl http://localhost:8765/health

# Stats
curl http://localhost:8765/stats | jq '.'

# Last 10 slow
sqlite3 state/telemetry.sqlite "
  SELECT capability, duration_ms, trace_id
  FROM traces
  ORDER BY duration_ms DESC
  LIMIT 10;
"
```

### **Actions:**
```bash
# [ ] Daily eval run (≥85% pass)
# [ ] Review any slow requests (>1500ms)
# [ ] Check bandit stability
# [ ] User feedback positive
```

---

## 📅 **DAY 7 (End of Week 1)**

### **Week 1 Retrospective:**

```bash
# ========================================
# WEEK 1 FINAL STATS
# ========================================

# Total executions
echo "Total traces:"
sqlite3 state/telemetry.sqlite 'SELECT count(*) FROM traces;'

# Error rate (week)
echo "Error rate:"
python3 -c "
import sqlite3
c = sqlite3.connect('orchestrator/state/telemetry.sqlite')
total = c.execute('SELECT count(*) FROM traces').fetchone()[0]
errors = c.execute('SELECT count(*) FROM traces WHERE raw_json LIKE \"%error%\" OR raw_json LIKE \"%timeout%\"').fetchone()[0]
print(f'{errors}/{total} ({errors/total*100 if total else 0:.2f}%)')
"

# p95 latency
echo "p95 latency:"
sqlite3 state/telemetry.sqlite "
  SELECT duration_ms
  FROM traces
  ORDER BY duration_ms DESC
  LIMIT (SELECT CAST(count(*) * 0.05 AS INTEGER) FROM traces);
" | head -1

# Shadow wins
echo "Shadow preferred count:"
sqlite3 state/telemetry.sqlite "
  SELECT COUNT(*) FROM traces WHERE raw_json LIKE '%shadow_preferred%';
"

# Provider stats
echo "Provider win rates:"
curl -s http://localhost:8765/stats | jq '.'
```

### **Snapshot & Rotate:**
```bash
# Snapshot Day 7 state
cp state/bandit.json releases/v0.9.2/bandit-day7.json
cp state/telemetry.sqlite releases/v0.9.2/telemetry-day7.sqlite

# Check DB size
du -h state/telemetry.sqlite

# If >200MB, rotate:
mv state/telemetry.sqlite state/telemetry-archive-$(date +%Y%m%d).sqlite
# Fresh DB created on next request

# Commit state snapshots
git add releases/v0.9.2/
git commit -m "chore: Day 7 state snapshot"
git push
```

### **Week 1 Checklist:**
```bash
# [ ] 0 critical incidents
# [ ] Error rate ≤1%
# [ ] p95 ≤1500ms
# [ ] 5+ user executions
# [ ] Bandit stable
# [ ] User feedback positive
# [ ] Documentation complete
# [ ] Team trained
```

### **If ALL ✅ → v0.9.2 is STABLE!**

---

## 🔄 **POST-LAUNCH IMPROVEMENTS**

### **Acceptance-Weighted Bandit:**

```python
# Add to router.py after primary execution:
def apply_user_feedback(trace_id: str, action: str):
    """
    Apply user feedback to bandit learning

    Args:
        trace_id: Trace ID
        action: "accept", "edit", or "revert"
    """
    # Retrieve trace
    trace = query_single_trace(trace_id)
    provider = trace.get("provider")
    capability = trace.get("capability")
    base_score = trace.get("score", 0.7)

    # Adjust score based on feedback
    if action == "accept":
        adjusted_score = min(1.0, base_score + 0.2)
    elif action == "revert":
        adjusted_score = max(0.0, base_score - 0.2)
    else:  # edit
        adjusted_score = base_score  # Neutral

    # Re-reward with adjusted score
    reward(capability, provider, adjusted_score)
```

**Wire into SwiftUI:**
```swift
// Add feedback buttons to chat results
HStack {
    Button("✅ Accept") { applyFeedback(traceId, "accept") }
    Button("✏️ Edit") { applyFeedback(traceId, "edit") }
    Button("❌ Revert") { applyFeedback(traceId, "revert") }
}
```

### **Memory Hygiene Cron:**

```bash
# Add to crontab -e:
0 2 * * * cd ~/orchestrator && python3 -c "
from memory.vector_store import configure_namespace, get_namespace_stats
from memory.hygiene import dedupe, pin

# Configure TTLs
configure_namespace('docs', ttl_secs=7*24*3600, max_items=1000)
configure_namespace('mem', ttl_secs=30*24*3600, max_items=2000)

# Before
before = get_namespace_stats('docs')

# Clean
dedupe('docs')
pin('docs', lambda t: 'golden' in t.lower())

# After
after = get_namespace_stats('docs')

print(f'Cleaned: {before[\"count\"]} → {after[\"count\"]} docs')
" >> logs/hygiene-$(date +\%Y\%m\%d).log
```

### **"Why This Choice?" in UI:**

Already implemented in `TracePanel.swift`!
- Shows subscores with progress bars
- Displays provider selection
- Lists policy constraints met
- Export button (⌘⇧E)

---

## 🎯 **SUCCESS METRICS**

**Week 1 Targets:**

| **Metric** | **Target** | **Status** |
|------------|------------|------------|
| Uptime | >99% | [ ] |
| Error rate | <1% | [ ] |
| p95 latency | <1500ms | [ ] |
| User executions | 5+ | [ ] |
| Eval pass rate | ≥85% | [ ] |
| Incidents | 0 critical | [ ] |
| User satisfaction | Positive | [ ] |

**If ALL targets met → v0.9.2 STABLE** ✅

---

## 🆘 **ESCALATION PATHS**

### **Minor Issue (p95 1.5s - 2.5s):**
1. Check memory bloat
2. Trim max_tokens
3. Monitor for 1 hour
4. If persists → disable slow provider

### **Major Issue (error rate >5%):**
1. Check logs immediately
2. Identify failing provider
3. Unregister provider
4. Monitor for 30 min
5. If persists → execute rollback

### **Critical Issue (crashes, data loss):**
1. **IMMEDIATE**: Execute binary rollback (Playbook option A)
2. Notify team
3. Root cause analysis
4. Hotfix on v0.9.2-hotfix branch
5. Re-verify with full checklist
6. Re-release as v0.9.2.1

---

## 📋 **DAILY CHECKLIST**

**Every morning (5 min):**
```bash
# [ ] Check trace count
# [ ] Verify error rate <1%
# [ ] Review p95 latency
# [ ] Check bandit stability
# [ ] Run eval (/eval/run)
# [ ] Review user feedback
# [ ] Check DB size
```

**If all ✅ → Continue monitoring**
**If any ❌ → Consult runbooks**

---

## 🎓 **LESSONS LEARNED (Update Weekly)**

**What worked well:**
- [Add after Day 7]

**What could improve:**
- [Add after Day 7]

**Metrics to track for v0.9.3:**
- [Add after Day 7]

---

**WEEK 1 PLAN COMPLETE** ✅
**Execute day-by-day**
**Update metrics daily**
**Ship with confidence!** 🚀
