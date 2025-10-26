# Day-2 Operations Runbook - Adaptive TRM

**Purpose**: Keep the system boring-reliable  
**Audience**: On-call engineers, SREs  
**Last Updated**: 2025-10-18

---

## 🚨 Quick Reference

### Instant Rollback (< 30 sec)

```bash
# Per-request disable
curl -X POST :8000/api/execute -d '{"flags":{"adaptive_trm":0}}'

# Global disable (restart required)
export TRM_TRIGGER_THRESH=1.0  # Never fires

# Clamp cycles (limit blast radius)
export TRM_MIN_CYCLES=4 TRM_MAX_CYCLES=12

# Stop TRM entirely
pkill -f trm_service.py
```

### Health Check One-Liner

```bash
curl -sf :8000/health && curl -sf :8420/health && curl -sf :8087/health && echo "✅ All up" || echo "❌ Service down"
```

### Policy Stats

```bash
curl -s :8000/trm/policy | jq '{decisions: .stats.total_decisions, accuracy: .stats.success_rate_with_trm, bias: .policy.bias}'
```

---

## 📅 Operational Schedules

### Hourly (Automated via Cron)

```bash
# Add to crontab
0 * * * * cd /Users/christianmerrill/Documents/GitHub && make rag-seed >> /var/log/agi/rag-seed.log 2>&1
0 * * * * cp /tmp/agi-*.log /var/log/agi/archive/$(date +\%Y\%m\%d_\%H).log
0 * * * * curl -s http://localhost:9093/metrics > /var/log/agi/metrics/$(date +\%s).txt
```

**Purpose**:

- Incremental RAG refresh (picks up new code/docs)
- Archive logs for training data
- Snapshot metrics for trend analysis

**Success Criteria**:

- Exit code 0
- New chunks indexed (check `rag_seed_state.json`)

---

### Daily (Manual or CI)

```bash
#!/bin/bash
# /usr/local/bin/agi-daily-health.sh

echo "=== Daily AGI Health Check $(date) ===" | tee -a /var/log/agi/daily.log

# 1. Golden questions (correctness)
cd /Users/christianmerrill/Documents/GitHub
make rag-golden | tee -a /var/log/agi/daily.log
# Expect: ✅ 8/10 or better

# 2. Load test (performance)
make rag-load | tee -a /var/log/agi/daily.log
# Expect: P95 < 200ms, 0 errors

# 3. Policy snapshot
curl -s http://localhost:8000/trm/policy > /var/log/agi/snapshots/policy_$(date +%s).json

# 4. Check bias drift
BIAS=$(curl -s http://localhost:8000/trm/policy | jq -r '.policy.bias')
DRIFT=$(echo "$BIAS + 0.35" | bc)
if (( $(echo "$DRIFT > 0.2 || $DRIFT < -0.2" | bc -l) )); then
  echo "⚠️ Policy bias drifted significantly: $BIAS (delta: $DRIFT)" | tee -a /var/log/agi/daily.log
fi

# 5. Alert summary
ERRORS=$(curl -s http://localhost:9090/api/v1/query --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[24h])' | jq -r '.data.result[0].value[1] // "0"')
echo "Error rate last 24h: $ERRORS" | tee -a /var/log/agi/daily.log

echo "=== Daily check complete ===" | tee -a /var/log/agi/daily.log
```

**Cron**:

```bash
0 6 * * * /usr/local/bin/agi-daily-health.sh
```

**Success Criteria**:

- Golden test ≥ 80%
- Load test P95 < 200ms
- Error rate < 0.5%
- Bias drift < ±0.2

---

### Every 6 Hours (Automatic - Already Wired)

**Policy Retrain** (`services/trm_adaptive_policy.py`)

- Triggered every 250 outcomes
- Adjusts bias based on success delta
- Only promotes if +2% accuracy or +value score

**Monitor**:

```bash
grep "policy retrained" /tmp/agi-outcomes.log | tail -5
```

---

### Weekly (Manual)

```bash
#!/bin/bash
# /usr/local/bin/agi-weekly-maintenance.sh

echo "=== Weekly AGI Maintenance $(date) ==="

# 1. Weaviate compaction
echo "Compacting Weaviate..."
# Compact each class
for CLASS in ChunkMini ChunkBase ChunkLong Docs; do
  curl -X POST "http://localhost:8090/v1/schema/$CLASS/shards/_compact"
done

# 2. BM25 index rebuild (if using hybrid)
echo "Rebuilding BM25 indexes..."
# Force reindex by toggling invertedIndexConfig
# (Weaviate-specific, adjust as needed)

# 3. Model pool analysis
echo "Analyzing model swap patterns..."
SWAP_DATA=$(curl -s http://localhost:9093/metrics | grep model_pool_hotswaps_total)
echo "$SWAP_DATA" | tee -a /var/log/agi/weekly.log
# Identify: most swapped pairs → consider keep_alive tuning

# 4. Policy checkpoint rotation (keep last 30)
cd /var/log/agi/snapshots
ls -t policy_*.json | tail -n +31 | xargs rm -f

# 5. Log rotation (keep last 90 days)
find /var/log/agi/archive -name "*.log" -mtime +90 -delete

echo "=== Weekly maintenance complete ==="
```

**Cron**:

```bash
0 3 * * 0 /usr/local/bin/agi-weekly-maintenance.sh
```

---

## 📊 What to Watch (Grafana Panels)

### End-to-End Health

**Panel**: "API Latency P50/P95/P99"  
**Targets**:

- Simple (80%): P95 < 1.2s
- Complex (5%): P95 < 3.5s
- Overall: P95 < 2.0s

**Alert**: P95 > 2.5s for 5min

---

### RAG Quality

**Panels**:

1. "RAG Hit Rate": `rate(rag_hits_total) / rate(rag_queries_total)`

   - Target: > 90%
   - Alert: < 80% for 15min

2. "Zero-Hit Rate": `rate(rag_queries_total{outcome="ok"}) - rate(rag_hits_total) / rate(rag_queries_total)`

   - Target: < 2%
   - Alert: > 5% for 10min

3. "Context Waste": `trm_context_waste_ratio{mode="deliberate"}`
   - Target: 25-35%
   - Alert: > 50% for 15min

---

### TRM Policy

**Panels**:

1. "Decision Funnel":

   - Predictions vs Invocations vs Success
   - Watch for: predictions >> invocations (good filtering)

2. "Policy Accuracy": `trm_policy_accuracy`

   - Target: ≥ 75%
   - Alert: < 65% for 1h

3. "Cycles P50/P95": `histogram_quantile(..., trm_adaptive_cycles_bucket)`

   - Watch for: clustering around efficient ranges (6-12)
   - Alert: P95 > 20 (hitting max)

4. "Value Score": `trm_value_score`
   - Target: ≥ 1.1 (ROI positive)
   - Alert: < 0.9 for 1h

---

### Model Pool

**Panels**:

1. "Swap Rate": `rate(model_pool_hotswaps_total[5m])`

   - Normal: < 10/min
   - Alert: > 20/min for 2min (thrash)

2. "Evictions by Reason": `rate(model_pool_evicts_total) by (reason)`

   - Watch: `reason=pressure` → need more VRAM

3. "Hot vs Warm Latency":
   - `model_pool_first_token_latency_ms{warm_state="hot"}` vs `{warm_state="warm"}`
   - Target: hot < 50ms, warm < 500ms

---

## 🚨 Common Pitfalls & Fixes

### OTEL Spam Returning

**Symptom**: Logs fill with "Connection refused :4318"

**Fix**:

```bash
# Verify env vars set
env | grep OTEL

# Should show:
# OTEL_SDK_DISABLED=true
# OTEL_TRACES_EXPORTER=none
# OTEL_METRICS_EXPORTER=none
# OTEL_LOGS_EXPORTER=none

# Add to systemd service permanently
cat >> /etc/systemd/system/agi-core.service <<EOF
Environment=OTEL_SDK_DISABLED=true
Environment=OTEL_TRACES_EXPORTER=none
Environment=OTEL_METRICS_EXPORTER=none
Environment=OTEL_LOGS_EXPORTER=none
EOF

systemctl daemon-reload
systemctl restart agi-core
```

---

### Python Path Drift

**Symptom**: `ImportError: No module named 'services.trm_adaptive_policy'`

**Fix**:

```bash
# Always set PYTHONPATH explicitly
export PYTHONPATH=/Users/christianmerrill/Documents/GitHub:$PYTHONPATH

# Verify
python3 -c "from services.trm_adaptive_policy import policy; print('OK')"

# Add to service wrapper
echo 'export PYTHONPATH=/Users/christianmerrill/Documents/GitHub' >> ~/.bashrc
```

---

### Port Conflicts (8087/8088)

**Symptom**: RAG Gateway on wrong port, FastVLM conflict

**Fix**:

```bash
# Create single source of truth
cat > /Users/christianmerrill/Documents/GitHub/.env <<EOF
RAG_GATEWAY_PORT=8087
TRM_SERVICE_PORT=8420
AGI_CORE_PORT=8000
WEAVIATE_PORT=8090
FASTVLM_PORT=8088
EOF

# Source in all start scripts
source .env
PORT=$RAG_GATEWAY_PORT python3 services/rag-gateway/dynamic_app.py
```

---

### Policy Stats Flatline

**Symptom**: `total_decisions` stops incrementing

**Root Cause**: Exception in outcome recording, variable scope issue

**Fix** (Already Applied):

```python
# In api_execute.py
# Initialize variables at top level
use_trm = False
use_adaptive = False
cycles_delib = 0

# Record outcome in both success and error paths
try:
    # ... execution ...
    if TRM_ADAPTIVE_AVAILABLE and trm_policy:
        trm_policy.record_outcome(...)
except Exception as e:
    # ... error handling ...
    if TRM_ADAPTIVE_AVAILABLE and trm_policy:
        trm_policy.record_outcome(..., success=False)
```

**Verify**:

```bash
# Generate traffic
for i in {1..5}; do curl -s -X POST :8000/api/execute -d '{"objective":"Test"}' > /dev/null; done

# Check incremented
curl -s :8000/trm/policy | jq '.stats.total_decisions'
# Should be > 0 and incrementing
```

---

## 🎯 Low-Risk Improvements (Easy Wins)

### 1. Thompson Sampling for Trigger Threshold

**Current**: Fixed threshold (0.6)  
**Upgrade**: Adaptive threshold via Thompson Sampling

```python
# In services/trm_adaptive_policy.py
class ThompsonBanditThreshold:
    def __init__(self):
        self.alpha = 1.0  # successes (TRM helped)
        self.beta = 1.0   # failures (TRM didn't help)

    def sample_threshold(self) -> float:
        """Sample threshold from Beta distribution"""
        return np.random.beta(self.alpha, self.beta)

    def update(self, invoked: bool, success: bool, baseline_success: float):
        """Update based on outcome"""
        if invoked:
            helped = success > baseline_success
            if helped:
                self.alpha += 1.0
            else:
                self.beta += 1.0

# Use in should_invoke()
threshold = self.bandit.sample_threshold()
return (p >= threshold, p)
```

**Expected Impact**: +5% trigger accuracy, -10% unnecessary invocations

---

### 2. MLX Reranker for Top-8

**Current**: RRF fusion only  
**Upgrade**: Add cross-encoder rerank

```python
# In services/rag-gateway/dynamic_app.py
import mlx.core as mx

class MLXReranker:
    def __init__(self):
        self.model = load_mlx_model("bge-reranker-base")  # 280MB

    def rerank(self, query: str, candidates: List[str], k=8) -> List[str]:
        scores = self.model.score(query, candidates)
        ranked = sorted(zip(scores, candidates), reverse=True)
        return [cand for _, cand in ranked[:k]]

# After RRF fusion
candidates = rrf_fuse(pools, k=50)
reranked = reranker.rerank(query, candidates, k=8)
```

**Expected Impact**: +10-15% golden test accuracy

---

### 3. Per-Domain Sub-Policies

**Current**: Single policy for all tasks  
**Upgrade**: Separate weights per domain

```python
# In services/trm_adaptive_policy.py
DOMAIN_POLICIES = {
    "frontend": {
        "weights": {"uncertainty": 0.35, "novelty": 0.15},  # Aggressive
        "threshold": 0.55,
        "default_cycles": 14
    },
    "backend": {
        "weights": {"uncertainty": 0.20, "novelty": 0.40},  # Conservative
        "threshold": 0.65,
        "default_cycles": 10
    },
    "research": {
        "weights": {"uncertainty": 0.50, "novelty": 0.50},  # Always deep
        "threshold": 0.40,
        "default_cycles": 18
    }
}

def classify_domain(objective: str) -> str:
    if any(kw in objective.lower() for kw in ["ui", "button", "view", "frontend"]):
        return "frontend"
    elif any(kw in objective.lower() for kw in ["api", "database", "cache", "backend"]):
        return "backend"
    else:
        return "research"

def should_invoke(self, objective: str, signals: Dict) -> Tuple[bool, float]:
    domain = classify_domain(objective)
    policy_config = DOMAIN_POLICIES.get(domain, self.default_config)
    # Use domain-specific weights & threshold
```

**Expected Impact**: +8-12% overall success rate via specialization

---

### 4. Semantic Context Usage Tracking

**Current**: Estimate context usage via length  
**Upgrade**: Track semantic overlap

```python
# In services/trm_service.py
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def estimate_context_usage(trm_output: str, rag_context: str) -> int:
    """Semantic overlap via embedding similarity"""
    if not rag_context or not trm_output:
        return 0

    # Embed both
    trm_emb = embedder.encode(trm_output, convert_to_numpy=True)
    rag_emb = embedder.encode(rag_context, convert_to_numpy=True)

    # Cosine similarity
    similarity = np.dot(trm_emb, rag_emb) / (np.linalg.norm(trm_emb) * np.linalg.norm(rag_emb))

    # Estimate chars actually referenced
    return int(len(rag_context) * max(0, similarity))

# Return in deliberate response
return {
    "answer": outline,
    "context_used_chars": estimate_context_usage(outline, context)
}
```

**Expected Impact**: -20% context waste via accurate usage tracking

---

## 🔧 Emergency Procedures

### System Unresponsive

1. Check services:

```bash
curl -sf :8000/health || echo "AGI down"
curl -sf :8420/health || echo "TRM down"
curl -sf :8087/health || echo "RAG down"
```

2. Check ports:

```bash
lsof -i :8000 -i :8420 -i :8087
```

3. Restart stack:

```bash
make stack-down
sleep 5
make stack-up
```

---

### RAG Returning Zero Hits

1. Check Weaviate:

```bash
curl -sf http://localhost:8090/v1/.well-known/ready || echo "Weaviate not ready"
```

2. Check data:

```bash
curl -s http://localhost:8090/v1/schema | jq '.classes[].class'
# Should show: ChunkMini, ChunkBase, ChunkLong, Docs
```

3. Force re-seed:

```bash
make rag-seed-full
```

---

### Policy Acting Erratically

1. Check bias drift:

```bash
curl -s :8000/trm/policy | jq '.policy.bias'
# Should be near -0.35 (±0.3 is OK)
```

2. Rollback to last checkpoint:

```bash
# Find last good checkpoint
ls -t /var/log/agi/snapshots/policy_*.json | head -1

# Restore (requires restart with loaded checkpoint)
# Or just reset threshold to disable
export TRM_TRIGGER_THRESH=1.0
```

3. Reset history:

```python
# In Python REPL
from services.trm_adaptive_policy import policy
policy.history.clear()
policy.bias = -0.35
```

---

## 📋 Cutover Automation

See `make prod-cutover` below for one-shot automation.

---

## 📖 Useful Commands

```bash
# Policy stats
curl -s :8000/trm/policy | jq

# Force TRM on
export TRM_TRIGGER_THRESH=0.0

# Clamp cycles
export TRM_MIN_CYCLES=6 TRM_MAX_CYCLES=12

# Check metrics
curl -s http://localhost:9093/metrics | grep trm_

# View logs
tail -f /tmp/agi-outcomes.log | grep -E "TRM|adaptive|policy"

# Health check all
for PORT in 8000 8420 8087 8090; do
  curl -sf http://localhost:$PORT/health > /dev/null && echo "✅ $PORT" || echo "❌ $PORT"
done
```

---

## 🎓 Key Principles

1. **Boring is Good**: If you're not getting paged, it's working
2. **Monitor Trends**: Daily stats matter more than minute-to-minute
3. **Fail Safe**: System degrades gracefully (TRM skip, RAG fallback, model pinning)
4. **Document Changes**: Every manual intervention goes in the runbook
5. **Test Rollbacks**: Monthly drill to ensure <5min recovery

---

**This runbook keeps the system reliable, observable, and easy to operate.** 🎯
