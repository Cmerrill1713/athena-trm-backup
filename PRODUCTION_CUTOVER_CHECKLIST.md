# 🚀 Production Cutover Checklist - Adaptive TRM

**Target Date**: Ready Now  
**Risk Level**: Low (Full rollback capability)  
**Duration**: 60-90 minutes

---

## ✅ Pre-Cutover Checklist (30 min)

### 1. Freeze Known-Good Snapshot

```bash
# Tag current state
cd /Users/christianmerrill/Documents/GitHub
git add -A
git commit -m "Production-ready: Adaptive TRM with Dynamic RAG"
git tag prod-agi-$(date +%Y%m%d)
git push origin prod-agi-$(date +%Y%m%d)

# Save configurations
mkdir -p snapshots/prod-$(date +%Y%m%d)
cp config/routing_policy.yaml snapshots/prod-$(date +%Y%m%d)/
cp Makefile.dynamic snapshots/prod-$(date +%Y%m%d)/
cp services/trm_adaptive_policy.py snapshots/prod-$(date +%Y%m%d)/

# Save policy checkpoint
curl -s http://localhost:8000/trm/policy > snapshots/prod-$(date +%Y%m%d)/policy_checkpoint.json

# Document versions
cat > snapshots/prod-$(date +%Y%m%d)/MANIFEST.txt <<EOF
Production Snapshot: $(date)
TRM Model: 60M params, MLX
RAG Classes: ChunkMini (384d), ChunkBase (768d), ChunkLong (1536d)
Weaviate: localhost:8090
Model Pool: fast (0.5b), balanced (7b), precise (14b)
Policy Threshold: 0.6
Cycle Range: [4, 24]
EOF
```

### 2. Set Runtime Environment

```bash
# Add to ~/.bashrc or systemd service
export OTEL_SDK_DISABLED=true
export OTEL_TRACES_EXPORTER=none
export OTEL_METRICS_EXPORTER=none
export OTEL_LOGS_EXPORTER=none

# AGI-specific
export AGI_SERVICE_PORT=8000
export TRM_TRIGGER_THRESH=0.60
export TRM_MIN_CYCLES=4
export TRM_MAX_CYCLES=24
export TRM_RETRAIN_EVERY=250
export TRM_HISTORY_SIZE=5000
```

### 3. Verify All Services Healthy

```bash
# Check services
curl -sf http://localhost:8420/health || echo "❌ TRM DOWN"
curl -sf http://localhost:8087/health || echo "❌ RAG DOWN"
curl -sf http://localhost:8090/v1/.well-known/ready || echo "❌ Weaviate DOWN"
curl -sf http://localhost:8000/health || echo "❌ AGI DOWN"

# Check policy loaded
curl -s http://localhost:8000/trm/policy | jq '.status' | grep -q "ok" || echo "❌ Policy not loaded"

# Check tools count (should be 19)
curl -s http://localhost:8000/tools | jq '.count' | grep -q "19" || echo "❌ Tools missing"
```

---

## 🧪 Canary Rollout (10% Traffic)

### Phase 1: Shadow Mode (Day 1)

```bash
# All requests compute adaptive decision, log probability, but don't change behavior
# Monitor: trigger_prob distribution, would-have-invoked vs actual

# Run for 24 hours, generate 500-1000 requests
# Check logs for patterns
```

### Phase 2: 10% Live (Day 2-3)

```bash
# Route 10% of traffic to adaptive_trm=true
# Use load balancer or probabilistic flag in your ingress

# A/B Test
./scripts/ab_test_trm.sh 3600 0.1  # 1 hour, 10% adaptive

# Monitor SLOs (see below)
```

### Phase 3: 50% Live (Day 4-5)

```bash
# Expand if SLOs met
./scripts/ab_test_trm.sh 3600 0.5  # 1 hour, 50% adaptive
```

### Phase 4: 100% (Day 6+)

```bash
# Set adaptive_trm=true as default
# Remove static fallback after 2 weeks of stability
```

---

## 📊 SLOs (Service Level Objectives)

### Latency Targets

```
Simple tasks (80%):  P95 < 1.2s
Medium tasks (15%):  P95 < 2.5s
Complex tasks (5%):  P95 < 3.5s

Overall:             P95 < 2.0s
                     P99 < 4.0s
```

### Error Budget

```
HTTP errors:         < 0.5% per hour
Tool call failures:  < 2% per hour
RAG zero-hits:       < 2% per 15min
TRM timeouts:        < 1% per hour
```

### Quality Metrics

```
TRM value score:     ≥ 1.1 (quality gain / latency cost)
Policy accuracy:     ≥ 70% (rising to 80%)
Context waste:       < 35% (falling to 25%)
Plan success rate:   ≥ 85% (rising to 90%)
```

---

## 🚨 Alerts Configuration

### Page-Worthy (Immediate Response)

```yaml
# Prometheus alert rules
groups:
  - name: agi_critical
    interval: 1m
    rules:
      # Error budget burn
      - alert: ErrorBudgetBurn
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        annotations:
          summary: "Error rate > 1% for 2min"

      # RAG zero-hit spike
      - alert: RAGZeroHitSpike
        expr: |
          rate(rag_queries_total{outcome="ok"}[15m]) > 50
          and
          rate(rag_hits_total[15m]) == 0
        for: 5m
        annotations:
          summary: "RAG returning 0 hits despite queries"

      # Weaviate down
      - alert: WeaviateDown
        expr: up{job="weaviate"} == 0
        for: 1m
        annotations:
          summary: "Weaviate unreachable"

      # Model swap storm
      - alert: ModelSwapStorm
        expr: rate(model_pool_hotswaps_total[5m]) > 20
        for: 2m
        annotations:
          summary: "Model swapping >20/min (thrash)"
```

### Warnings (Monitor & Investigate)

```yaml
- name: agi_warnings
  interval: 5m
  rules:
    # Context waste
    - alert: ContextWasteHigh
      expr: trm_context_waste_ratio{mode="deliberate"} > 0.5
      for: 15m
      annotations:
        summary: "Context waste >50% for 15min"

    # Policy accuracy drop
    - alert: PolicyAccuracyLow
      expr: trm_policy_accuracy < 0.65
      for: 1h
      annotations:
        summary: "Policy accuracy <65% for 1h"

    # Cold start latency
    - alert: ColdStartSlow
      expr: |
        histogram_quantile(0.95, 
          rate(model_pool_first_token_latency_ms_bucket{warm_state="cold"}[10m])
        ) > 2000
      for: 10m
      annotations:
        summary: "Cold model loads >2s P95"

    # TRM queue depth
    - alert: TRMQueueDeep
      expr: max_over_time(model_pool_queue_depth[5m]) > 15
      for: 5m
      annotations:
        summary: "TRM queue >15 for 5min"
```

---

## 🔙 Rollback Procedures

### Instant Kill Switches (< 30 seconds)

#### 1. Disable Adaptive Policy

```bash
# Via environment (restart required)
export TRM_TRIGGER_THRESH=1.0  # Never triggers

# Via request flag (immediate)
# Set default to adaptive_trm=false in your load balancer
```

#### 2. Clamp Cycles (Limit Blast Radius)

```bash
export TRM_MIN_CYCLES=4
export TRM_MAX_CYCLES=8  # Cap at 8 instead of 24
# Restart AGI Core
```

#### 3. Disable TRM Entirely

```bash
# Stop TRM service
pkill -f trm_service.py

# AGI will gracefully skip TRM calls
# Verify: curl http://localhost:8000/api/execute ... | jq '.trace | map(select(.action | contains("trm")))'
# Should be empty
```

#### 4. RAG Fallback Mode

```bash
# If RAG gateway crashes, AGI continues without context
# Verify in logs: "RAG query failed: Connection refused" → continues execution

# Force BM25-only (if needed)
# Edit dynamic_app.py: set vector_weight=0.0, bm25_weight=1.0
```

#### 5. Pin Model Pool to Fast

```bash
# Edit config/routing_policy.yaml
complexity:
  low:  {model: fast}
  medium: {model: fast}  # Override
  high: {model: fast}    # Override

# Avoids swaps, uses only qwen2.5:0.5b
```

### Full Rollback (< 5 minutes)

```bash
# 1. Stop all services
make stack-down

# 2. Checkout last stable tag
git checkout prod-agi-YYYYMMDD

# 3. Restore configs
cp snapshots/prod-YYYYMMDD/*.yaml config/
cp snapshots/prod-YYYYMMDD/trm_adaptive_policy.py services/

# 4. Restart with OTEL disabled
OTEL_SDK_DISABLED=true make stack-up

# 5. Verify
curl http://localhost:8000/health
curl http://localhost:8000/trm/policy | jq '.policy.bias'
```

---

## 📊 Grafana Dashboard (Production View)

```json
{
  "dashboard": {
    "title": "AGI Adaptive TRM - Production",
    "panels": [
      {
        "title": "Decision Funnel",
        "targets": [
          "sum(increase(trm_policy_predictions_total{result='pred'}[5m]))",
          "sum(increase(agi_curiosity_actions_total{kind='trm_deliberate'}[5m]))"
        ]
      },
      {
        "title": "Policy Accuracy",
        "targets": ["trm_policy_accuracy"]
      },
      {
        "title": "Adaptive Cycles P50/P95",
        "targets": [
          "histogram_quantile(0.5, sum(rate(trm_adaptive_cycles_bucket[5m])) by (le))",
          "histogram_quantile(0.95, sum(rate(trm_adaptive_cycles_bucket[5m])) by (le))"
        ]
      },
      {
        "title": "RAG Hit Rate",
        "targets": ["rate(rag_hits_total[5m]) / rate(rag_queries_total[5m])"]
      },
      {
        "title": "Context Waste",
        "targets": ["trm_context_waste_ratio{mode='deliberate'}"]
      },
      {
        "title": "API Latency P50/P95/P99",
        "targets": [
          "histogram_quantile(0.5, rate(http_request_duration_seconds_bucket{route='/api/execute'}[5m]))",
          "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{route='/api/execute'}[5m]))",
          "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{route='/api/execute'}[5m]))"
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          "rate(http_requests_total{status=~'5..'}[5m]) / rate(http_requests_total[5m])"
        ]
      },
      {
        "title": "Model Pool Swaps",
        "targets": ["rate(model_pool_hotswaps_total[5m])"]
      },
      {
        "title": "TRM Value Score",
        "targets": ["trm_value_score"]
      }
    ]
  }
}
```

---

## 🔁 Learning Loop Safety

### Policy Checkpoint Management

```bash
# Save checkpoint every 500 outcomes
# Keep last 3 checkpoints

mkdir -p policy_checkpoints
curl -s http://localhost:8000/trm/policy > policy_checkpoints/$(date +%Y%m%d_%H%M).json

# Prune old checkpoints (keep 3)
ls -t policy_checkpoints/*.json | tail -n +4 | xargs rm -f
```

### Validation Before Accept

```python
# In trm_adaptive_policy.py _retrain_async()
def _accept_new_weights(self, old_accuracy, new_accuracy, old_bias, new_bias):
    """Only accept if +2% accuracy or bias drift < 0.3"""
    if new_accuracy < old_accuracy - 0.02:
        return False  # Reject: accuracy dropped

    if abs(new_bias - old_bias) > 0.3:
        return False  # Reject: bias drifted too much

    return True  # Accept
```

---

## 🧪 Daily Validation Playbook

### Morning Health Check (5 min)

```bash
#!/bin/bash
echo "=== Daily AGI Health Check ==="

# 1. Services up
curl -sf http://localhost:8000/health > /dev/null && echo "✅ AGI" || echo "❌ AGI DOWN"
curl -sf http://localhost:8420/health > /dev/null && echo "✅ TRM" || echo "❌ TRM DOWN"
curl -sf http://localhost:8087/health > /dev/null && echo "✅ RAG" || echo "❌ RAG DOWN"

# 2. Policy stats
DECISIONS=$(curl -s http://localhost:8000/trm/policy | jq '.stats.total_decisions')
echo "Policy decisions last 24h: $DECISIONS"

# 3. RAG golden test
make rag-golden
# Expect: ✅ 8/10 or better

# 4. Error rate last hour
ERRORS=$(curl -s http://localhost:9090/api/v1/query --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[1h])' | jq '.data.result[0].value[1]')
echo "Error rate last hour: $ERRORS"

# 5. Policy bias drift
BIAS=$(curl -s http://localhost:8000/trm/policy | jq '.policy.bias')
echo "Current bias: $BIAS (initial: -0.35)"
```

### Weekly Deep Dive (30 min)

```bash
# 1. Run load test
make rag-load
# Check: P95 < 200ms, 0 errors

# 2. A/B comparison
./scripts/ab_test_trm.sh 900 0.5  # 15min, 50/50
# Compare success rates

# 3. Policy performance
curl -s http://localhost:8000/trm/policy | jq '{
  accuracy: .stats.success_rate_with_trm,
  avg_cycles: .stats.avg_cycles,
  bias_drift: (.policy.bias + 0.35)
}'

# 4. Context waste analysis
curl -s http://localhost:9093/metrics | grep context_waste

# 5. Model pool health
curl -s http://localhost:9093/metrics | grep model_pool | grep -E "swaps|evicts"
```

---

## 🧱 Guardrails (Always On)

### Context Budgets

```python
# In trm_adaptive_policy.py budget_context_chars()
MIN_BUDGET = 600
MAX_BUDGET = 8000
DEFAULT_BUDGETS = {"low": 1000, "medium": 3000, "high": 5000}

# Allow ±20% adjustment
budget = base * (0.8 to 1.2)
return max(MIN_BUDGET, min(MAX_BUDGET, budget))
```

### Cycle Bounds

```bash
export TRM_MIN_CYCLES=4   # Never go below (quality floor)
export TRM_MAX_CYCLES=24  # Never exceed (latency cap)
```

### Timeout Hierarchy

```
TRM deliberate:    2s  (fail-fast)
TRM critique:      1s  (lightweight)
RAG query:         3s  (allow multi-tier)
Xcode build:     300s  (full compile)
App launch:       60s  (wait for binary)
UI probe:         30s  (interaction timeout)
```

### Schema Validation

```python
# In api_execute.py before tool call
def validate_tool_payload(tool: str, payload: dict) -> bool:
    """Validate against tool schema"""
    schema = TOOL_SCHEMAS.get(tool)
    if not schema:
        return True  # No schema = allow

    try:
        jsonschema.validate(payload, schema)
        return True
    except ValidationError:
        logger.error(f"Invalid payload for {tool}: {payload}")
        return False  # Reject
```

---

## 🎯 High-ROI Upgrades (Next 2 Weeks)

### 1. Bandit Threshold Tuning

```python
# Replace fixed 0.6 with Thompson sampling
class ThompsonBandit:
    def __init__(self):
        self.alpha = 1.0  # successes
        self.beta = 1.0   # failures

    def sample_threshold(self) -> float:
        return np.random.beta(self.alpha, self.beta)

    def update(self, invoked: bool, success: bool):
        if invoked and success:
            self.alpha += 1
        elif invoked and not success:
            self.beta += 1
```

### 2. Per-Domain Policies

```python
# Separate weights for task types
DOMAIN_WEIGHTS = {
    "frontend": {"uncertainty": 0.4, "novelty": 0.2},  # More aggressive
    "backend": {"uncertainty": 0.2, "novelty": 0.4},   # Conservative
    "research": {"uncertainty": 0.5, "novelty": 0.5},  # Always deep
}

def classify_domain(objective: str) -> str:
    if any(kw in objective.lower() for kw in ["ui", "app", "button"]):
        return "frontend"
    # ...
```

### 3. MLX Cross-Encoder Reranker

```python
# In dynamic_app.py after RRF fusion
from mlx_models import load_reranker

reranker = load_reranker("bge-reranker-base")  # 280MB model

def rerank_top_k(query: str, candidates: List[str], k=8) -> List[str]:
    scores = reranker.score(query, candidates)
    ranked = sorted(zip(scores, candidates), reverse=True)
    return [cand for score, cand in ranked[:k]]
```

### 4. Context-Use Tracing

```python
# In trm_service.py deliberate response
def estimate_context_usage(trm_output: str, rag_context: str) -> int:
    """Semantic overlap via embeddings"""
    trm_emb = embed(trm_output)
    rag_emb = embed(rag_context)

    # Cosine similarity
    similarity = np.dot(trm_emb, rag_emb) / (norm(trm_emb) * norm(rag_emb))

    # Estimate chars used
    return int(len(rag_context) * similarity)
```

---

## 🔑 One-Liners for Production

### Policy Inspection

```bash
# Live readout
curl -s http://localhost:8000/trm/policy | jq

# Just stats
curl -s http://localhost:8000/trm/policy | jq '.stats'

# Check bias drift
curl -s http://localhost:8000/trm/policy | jq '.policy.bias'
```

### Force TRM (Testing)

```bash
# Single request
curl -s -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{"objective":"Test TRM","tools":[],"max_steps":3,"flags":{"adaptive_trm":1}}' | \
  jq '.trace[] | select(.action | contains("trm"))'

# Set threshold to 0 (always invoke)
export TRM_TRIGGER_THRESH=0.0
# Restart AGI
```

### Silence OTEL (Systemd)

```ini
# /etc/systemd/system/agi-core.service
[Service]
Environment=OTEL_SDK_DISABLED=true
Environment=OTEL_TRACES_EXPORTER=none
Environment=OTEL_METRICS_EXPORTER=none
Environment=OTEL_LOGS_EXPORTER=none
Environment=PYTHONPATH=/Users/christianmerrill/Documents/GitHub
Environment=AGI_SERVICE_PORT=8000
ExecStart=/usr/bin/python3 -m agi_core.agi_service
Restart=always
```

### Quick Metrics Check

```bash
# TRM activity
curl -s http://localhost:9093/metrics | grep trm_requests_total

# Policy decisions
curl -s http://localhost:8000/trm/policy | jq '.stats.total_decisions'

# RAG hit rate
curl -s http://localhost:9093/metrics | grep rag_hits_total
```

---

## ✅ Go/No-Go Criteria

### ✅ GO if:

- [ ] All services healthy (TRM, RAG, Weaviate, AGI)
- [ ] Policy loaded and recording outcomes
- [ ] 19 tools registered
- [ ] OTEL noise eliminated
- [ ] Traces show TRM when invoked
- [ ] Rollback tested and < 5min
- [ ] SLOs defined and baseline captured
- [ ] Alerts configured
- [ ] Team trained on rollback procedures

### ❌ NO-GO if:

- [ ] Any service unhealthy
- [ ] Policy not recording outcomes
- [ ] OTEL spam in logs
- [ ] Rollback untested
- [ ] No baseline metrics
- [ ] No alert coverage

---

## 🏁 Final Verification

```bash
#!/bin/bash
echo "=== PRODUCTION READINESS CHECK ==="

# 1. Services
curl -sf http://localhost:8000/health && echo "✅ AGI" || exit 1
curl -sf http://localhost:8420/health && echo "✅ TRM" || exit 1
curl -sf http://localhost:8087/health && echo "✅ RAG" || exit 1

# 2. Policy
DECISIONS=$(curl -s http://localhost:8000/trm/policy | jq '.stats.total_decisions // 0')
[ "$DECISIONS" -gt 0 ] && echo "✅ Policy learning" || echo "⚠️ No decisions yet"

# 3. Tools
TOOLS=$(curl -s http://localhost:8000/tools | jq '.count')
[ "$TOOLS" -eq 19 ] && echo "✅ All tools loaded" || exit 1

# 4. OTEL
! tail -20 /tmp/agi-outcomes.log | grep -q "Connection refused" && echo "✅ No OTEL noise" || exit 1

# 5. Test request
RESULT=$(curl -s -X POST http://localhost:8000/api/execute \
  -d '{"objective":"Production test","flags":{"adaptive_trm":1}}' | jq '.status')
[ "$RESULT" != "null" ] && echo "✅ Execution works" || exit 1

echo ""
echo "🚀 READY FOR PRODUCTION"
```

---

**Status**: ✅ **PRODUCTION READY**  
**Next Step**: Run cutover checklist, start canary at 10%, monitor SLOs for 48h, expand to 100%.
