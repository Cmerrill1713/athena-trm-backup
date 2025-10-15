# CE Precision Mode: Tuning Knobs & Extensions

## 🎛️ Primary Tuning Knobs

| Flag | Description | Default | Range | Impact |
|------|-------------|---------|-------|---------|
| `RAG_RERANKER_CE_ENABLED` | Master CE switch | `false` | `bool` | Enables precision routing |
| `RAG_RERANKER_CE_INTENTS` | Intent-based routing | `policy,incident,legal,diagnosis` | `list[str]` | Which intents trigger CE |
| `RAG_RERANKER_CE_LATENCY_BUDGET_MS` | Max CE p95 latency | `500` | `100-1000` | Performance guardrail |
| `RAG_RERANKER_CE_LENGTH_THRESHOLD` | Min query words for CE | `16` | `5-50` | Length-based routing |
| `RAG_RERANKER_CE_WEIGHT` | CE score weight in blend | `1.0` | `0-1` | How much CE influences ranking |

## 🔧 Advanced Extension Paths

### A. Confidence-Based Routing
**Problem**: CE can be overconfident on edge cases.
**Solution**: Route to CE only if top CE score > confidence threshold.

```python
# In should_use_cross_encoder()
if use_ce:
    # Quick CE inference on top candidates
    top_candidates = candidates[:3]
    ce_scores = [_cross_encoder_similarity(query_text, c.get('text', '')) for c in top_candidates]
    max_ce_score = max(ce_scores) if ce_scores else 0

    # Only use CE if confident
    ce_confidence_threshold = float(os.getenv('RAG_RERANKER_CE_CONFIDENCE_THRESHOLD', '0.6'))
    return max_ce_score > ce_confidence_threshold

return False
```

**Flag**: `RAG_RERANKER_CE_CONFIDENCE_THRESHOLD=0.6`

### B. Budget-Aware Routing
**Problem**: CE can blow latency budget during traffic spikes.
**Solution**: Monitor recent CE latency and skip if budget exceeded.

```python
# In should_use_cross_encoder()
if use_ce:
    # Check recent CE latency budget
    recent_ce_latency = get_recent_ce_p95_latency()  # From metrics
    budget = RAG_RERANKER_CE_LATENCY_BUDGET_MS

    if recent_ce_latency > budget:
        return False  # Skip CE to protect budget

return use_ce
```

**Benefit**: Adaptive routing prevents SLO violations.

### C. Progressive Intent Promotion
**Problem**: Manual intent configuration is static.
**Solution**: Auto-promote intents where CE shows significant lift.

```python
# Statistical significance test for intent promotion
def should_promote_intent(intent: str, min_samples: int = 100) -> bool:
    # Get CE vs cosine performance for this intent
    ce_scores = get_recent_judge_scores(intent, reranker='crossencoder')
    cos_scores = get_recent_judge_scores(intent, reranker='cosine')

    if len(ce_scores) < min_samples or len(cos_scores) < min_samples:
        return False

    # Z-test: CE significantly better than cosine?
    from scipy.stats import ttest_ind
    t_stat, p_value = ttest_ind(ce_scores, cos_scores, alternative='greater')

    return p_value < 0.05  # 95% confidence
```

**Result**: System learns which intents benefit most from CE.

### D. Hybrid Scoring (CE + Cosine Blend)
**Problem**: CE ignores semantic embeddings entirely.
**Solution**: Blend CE precision with cosine recall.

```python
# In rerank function for CE path
for candidate in candidates:
    ce_score = _cross_encoder_similarity(query_text, candidate.get("text", ""))
    cos_score = _cosine_similarity(query_emb, candidate["emb"])
    orig_score = candidate.get("orig", 0)

    # Weighted blend: CE precision + cosine recall + original relevance
    candidate["rerank"] = (
        RAG_RERANKER_CE_WEIGHT * ce_score +
        (1 - RAG_RERANKER_CE_WEIGHT) * 0.6 * orig_score +
        (1 - RAG_RERANKER_CE_WEIGHT) * 0.4 * cos_score
    )
```

**Flag**: `RAG_RERANKER_CE_WEIGHT=0.7` (70% CE, 30% cosine)

### E. Query Complexity Heuristics
**Problem**: Length-based routing is too simple.
**Solution**: ML-based query complexity scoring.

```python
def query_complexity_score(query: str) -> float:
    """Score query complexity 0-1."""
    words = query.split()
    features = [
        len(words) / 50,  # Normalized length
        len(set(words)) / len(words),  # Lexical diversity
        query.count('?') / 5,  # Question density
        len([w for w in words if len(w) > 6]) / len(words),  # Complex words
    ]
    return sum(features) / len(features)

# In should_use_cross_encoder()
complexity = query_complexity_score(query_text)
ce_complexity_threshold = float(os.getenv('RAG_RERANKER_CE_COMPLEXITY_THRESHOLD', '0.6'))
return use_ce or complexity > ce_complexity_threshold
```

**Flag**: `RAG_RERANKER_CE_COMPLEXITY_THRESHOLD=0.6`

## 🎯 Implementation Priority

1. **High Impact, Low Risk**: Confidence-based routing, budget-aware routing
2. **Medium Impact, Medium Risk**: Progressive intent promotion, hybrid scoring
3. **High Impact, High Risk**: Query complexity ML model

## 📊 Monitoring Extensions

Add these metrics for advanced routing:

```python
# Confidence distribution
RAG_CE_CONFIDENCE_HISTOGRAM = Histogram(
    'rag_ce_confidence_scores',
    'Distribution of CE confidence scores'
)

# Routing decisions
RAG_ROUTING_DECISIONS = Counter(
    'rag_routing_decisions_total',
    'Routing decisions by type',
    ['decision_type', 'reason']
)  # decision_type: ce/cosign, reason: intent/length/budget/confidence

# Budget monitoring
RAG_CE_BUDGET_VIOLATIONS = Counter(
    'rag_ce_budget_violations_total',
    'CE budget violations by type'
)
```

## 🚀 Quick Wins

Start with these immediate improvements:

1. **Add confidence threshold**: `RAG_RERANKER_CE_CONFIDENCE_THRESHOLD=0.65`
2. **Enable budget awareness**: Monitor and skip CE during violations
3. **Add hybrid scoring**: `RAG_RERANKER_CE_WEIGHT=0.8`

Each can be deployed independently with minimal risk.
