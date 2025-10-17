# Athena Iteration Roadmap - Phase Ω+

**Date:** 2025-10-15  
**Status:** PLANNING  
**Integration:** Governance System + Router + Observability

---

## 🔬 Research Integration

### Key Insights to Implement:

1. **Contrastive Domain Embeddings**

   - Reduces misrouting in multi-domain settings
   - Use case: Model router selection
   - Priority: HIGH

2. **Radial/Graph-Based Routing**

   - Better generalization under drift
   - Use case: Fallback router
   - Priority: MEDIUM

3. **Guardrail Pipelines (ML Canaries)**

   - Test hard/adversarial inputs per commit
   - Use case: CI/CD integration
   - Priority: HIGH (aligns with existing canary system!)

4. **OpenTelemetry + OTLP**
   - Lightweight distributed observability
   - Use case: Cross-service tracing
   - Priority: HIGH

---

## 🛠 Implementation Plan

### 1. Swift Reflex Agent Enhancement

**Current State:**

- ✅ NeuroForgeApp Swift frontend exists
- ✅ GovernanceClient for backend integration
- ⚠️ No routing logic yet

**Delta to Apply:**

```swift
// Add to: NeuroForgeApp/Sources/Routing/RouterClient.swift (NEW)

struct RoutingChoice {
    let model: String
    let confidence: Double
    let domain: String
}

class ReflexRouter {
    let fallbackThreshold: Double = 0.7

    func route(_ request: RoutingRequest) async throws -> RoutingChoice {
        var choice = try await primaryRouter.route(request)

        if choice.confidence < fallbackThreshold {
            choice = try await fallbackRouter.route(request)
            choice.metadata["used_fallback"] = true

            // Emit metric
            Metrics.counter("athena_router_fallbacks_total",
                           labels: ["domain": request.domain])
        }

        Metrics.gauge("athena_routing_confidence",
                     value: choice.confidence,
                     labels: ["model": choice.model])

        return choice
    }
}
```

**Acceptance Check:**

- [ ] Fallback triggers when confidence < 0.7
- [ ] Metrics visible in Prometheus
- [ ] Traces show fallback path

**Files to Create:**

- `NeuroForgeApp/Sources/Routing/RouterClient.swift`
- `NeuroForgeApp/Sources/Routing/RoutingMetrics.swift`
- `NeuroForgeApp/Tests/RoutingTests.swift`

---

### 2. Model Router (Rust/Go)

**Current State:**

- ❌ No Rust/Go router exists yet
- ✅ Python orchestrator exists (could be extended)
- ⚠️ Need to decide: extend Python or new Rust service?

**Delta to Apply:**

```rust
// New file: router/src/contrastive_router.rs

struct ModelProfile {
    model_id: String,
    domain_embedding: Vec<f32>,
    quality_score: f64,
    cost: f64,
}

struct RoutingScore {
    model_id: String,
    score: f64,
    confidence: f64,
}

impl ContrastiveRouter {
    fn route(&self, query: &Query) -> RoutingScore {
        let query_emb = self.embed_domain(&query.domain);

        let mut scores: Vec<_> = self.models.iter()
            .map(|model| {
                let sim = cosine_sim(&query_emb, &model.domain_embedding);
                let score = sim * self.w_domain
                          + model.quality_score * self.w_quality
                          - model.cost * self.w_cost;
                (model.model_id.clone(), score)
            })
            .collect();

        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

        let best = scores[0].1;
        let second = scores.get(1).map(|s| s.1).unwrap_or(0.0);
        let margin = best - second;

        if margin < self.fallback_margin {
            // Use kNN fallback
            return self.knn_router.route(query);
        }

        RoutingScore {
            model_id: scores[0].0.clone(),
            score: best,
            confidence: margin / best,
        }
    }
}
```

**Acceptance Check:**

- [ ] Routing distribution shifts < 10% vs baseline
- [ ] Fallback invoked in edge cases
- [ ] Latency < 50ms (per PRD)

**Decision Needed:**

- Option A: Extend Python orchestrator with contrastive routing
- Option B: New Rust microservice (router)
- Option C: Go microservice (better for our stack?)

**Recommendation:** Option A (Python) for speed, move to Rust later if needed

---

### 3. Governance / CI Hooks

**Current State:**

- ✅ Governance orchestrator exists (port 9110)
- ✅ Canary monitor exists (port 9111)
- ✅ Prometheus metrics exist
- ⚠️ Need canary test suite in CI

**Delta to Apply:**

```python
# Add to: governance/ci/canary_test_suite.py

class CanaryTestSuite:
    """Run edge-case queries to detect regressions"""

    def __init__(self):
        self.edge_cases = self.load_edge_cases()  # 50 hard queries
        self.quality_threshold = 0.85
        self.safety_assertions = self.load_assertions()

    def run(self) -> TestResult:
        results = []
        for query in self.edge_cases:
            response = self.call_router(query)

            # Quality check
            quality = self.evaluate_quality(response)
            if quality < self.quality_threshold:
                results.append(Failure(query, quality))

            # Safety check
            for assertion in self.safety_assertions:
                if not assertion.check(response):
                    results.append(SafetyViolation(query, assertion))

        return TestResult(
            total=len(self.edge_cases),
            failures=len(results),
            details=results
        )

# Add to: .github/workflows/canary-ci.yml

jobs:
  canary_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Canary Test Suite
        run: python governance/ci/canary_test_suite.py
      - name: Fail if regressions
        run: |
          if [ $(cat canary_results.json | jq '.failures') -gt 0 ]; then
            echo "❌ Canary tests failed - quality regression detected"
            exit 1
          fi
```

**Acceptance Check:**

- [ ] PRs with regressions in 50 test cases must fail
- [ ] No false negatives
- [ ] CI runs in < 5 minutes

**Files to Create:**

- `governance/ci/canary_test_suite.py`
- `governance/ci/edge_cases.json`
- `governance/ci/safety_assertions.json`
- `.github/workflows/canary-ci.yml`

---

### 4. Prometheus / Grafana Observability

**Current State:**

- ✅ Prometheus running (port 9090)
- ✅ Grafana dashboards exist
- ✅ Scraping governance services
- ⚠️ Need routing-specific metrics

**Delta to Apply:**

**New Metrics:**

```python
# Add to: governance/observability/routing_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Routing metrics
ROUTER_REQUESTS = Counter(
    'athena_router_requests_total',
    'Total routing requests',
    ['model', 'domain']
)

ROUTER_LATENCY = Histogram(
    'athena_router_latency_ms',
    'Router latency in milliseconds',
    ['model']
)

ROUTER_FALLBACKS = Counter(
    'athena_fallbacks_total',
    'Total fallback invocations',
    ['reason']
)

REFLEX_AGENT_ERRORS = Counter(
    'reflex_agent_errors',
    'Reflex agent errors',
    ['agent', 'error_type']
)

ROUTING_CONFIDENCE = Gauge(
    'athena_routing_confidence',
    'Current routing confidence',
    ['model', 'domain']
)
```

**New Dashboards:**

```json
// dashboards/routing_dashboard.json

{
  "title": "Athena Routing Dashboard",
  "panels": [
    {
      "title": "Routing Distribution Over Time",
      "targets": [
        {
          "expr": "rate(athena_router_requests_total[5m])"
        }
      ]
    },
    {
      "title": "Latency Heatmap",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, athena_router_latency_ms)"
        }
      ]
    },
    {
      "title": "Fallback Rate",
      "targets": [
        {
          "expr": "rate(athena_fallbacks_total[5m])"
        }
      ]
    },
    {
      "title": "Routing Confidence",
      "targets": [
        {
          "expr": "athena_routing_confidence"
        }
      ]
    }
  ]
}
```

**Acceptance Check:**

- [ ] Dashboards show real data post-deploy
- [ ] Alerts fire on anomalies
- [ ] Latency p95 < 50ms

**Files to Create:**

- `governance/observability/routing_metrics.py`
- `dashboards/routing_dashboard.json`
- `monitoring/prometheus/routing_alerts.yml`

---

## 🚧 Open Blockers & Solutions

### 1. Cold Start for Domain Embeddings

**Blocker:** New models lack domain profiles

**Solution:**

```python
# governance/routing/embedding_bootstrap.py

def bootstrap_embedding(model_name: str, model_description: str) -> np.ndarray:
    """Generate approximate domain embedding from model description"""
    # Use sentence-transformers or similar
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = embedder.encode(model_description)

    # Mark as approximate
    return {
        "embedding": embedding.tolist(),
        "is_approximate": True,
        "confidence": 0.6
    }
```

**Accept Check:**

- [ ] New models get embeddings within 1 second
- [ ] Approximate embeddings marked clearly
- [ ] Updated with real embeddings within 24 hours

---

### 2. Latency Overhead

**Blocker:** Embedding similarity + fallback adds latency

**Solution:**

- Cache embeddings in memory
- Pre-compute similarity matrix
- Async fallback (don't block on it)
- Use approximate nearest neighbors (FAISS/Annoy)

```python
# Optimization
class CachedRouter:
    def __init__(self):
        self.embedding_cache = {}
        self.similarity_cache = LRUCache(maxsize=10000)

    async def route_fast(self, query):
        # Use cached embeddings
        if query.domain in self.embedding_cache:
            emb = self.embedding_cache[query.domain]
        else:
            emb = await self.compute_embedding(query.domain)
            self.embedding_cache[query.domain] = emb

        # Check similarity cache
        cache_key = (query.domain, tuple(self.model_ids))
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        # Compute and cache
        result = self.compute_routing(emb)
        self.similarity_cache[cache_key] = result
        return result
```

**Target:** < 10ms added latency

---

### 3. CI Noise Tuning

**Blocker:** Too strict = false positives, too lax = misses regressions

**Solution:**

```python
# Adaptive threshold based on historical data
class AdaptiveCanaryThreshold:
    def __init__(self):
        self.baseline_stats = self.load_baseline()
        self.tolerance_stddev = 2.0  # 2 std deviations

    def should_fail(self, metric_value: float, metric_name: str) -> bool:
        baseline = self.baseline_stats[metric_name]
        threshold = baseline.mean - (self.tolerance_stddev * baseline.stddev)

        # Fail only if significantly worse
        return metric_value < threshold
```

**Accept Check:**

- [ ] False positive rate < 5%
- [ ] No missed real regressions in last 10 PRs

---

### 4. Trace Context Propagation

**Blocker:** Swift ↔ Rust ↔ Go trace context can break

**Solution:**

```swift
// Use OpenTelemetry context propagation

import OpenTelemetryApi
import OpenTelemetrySwift

class TracedRequest {
    func makeRequest(to service: String) async throws -> Response {
        let span = tracer.spanBuilder(spanName: "request_\(service)")
            .startSpan()

        defer { span.end() }

        var request = URLRequest(url: serviceURL)

        // Inject trace context into headers
        let carrier = HTTPHeadersCarrier(headers: &request.allHTTPHeaderFields)
        OpenTelemetry.instance.propagators.textMapPropagator
            .inject(spanContext: span.context, carrier: carrier)

        return try await URLSession.shared.data(for: request)
    }
}
```

**Accept Check:**

- [ ] End-to-end traces visible in Jaeger/Tempo
- [ ] No broken trace contexts in 99% of requests

---

## ⚡ Quick Wins (Immediate Actions)

### 1. Shadow Mode Deployment ✅

**Already have this!** Our canary system supports shadow mode.

```python
# governance/canary/shadow_mode.py
# Already exists - just enable for routing changes

SHADOW_MODE = True  # Log-only, don't affect traffic

if SHADOW_MODE:
    new_result = new_router.route(request)
    metrics.record("shadow_routing", new_result)
    return old_router.route(request)  # Use old result
else:
    return new_router.route(request)
```

**Action:** Enable shadow mode flag in config

---

### 2. Seed Domain Embeddings ✅

**Quick implementation:**

```python
# Run this once
python scripts/seed_embeddings.py \
  --models models.json \
  --output model_profiles.json
```

**Action:** Create seed script

---

### 3. Minimal Fallback Stub ✅

**Already have this pattern in auto-remediation!**

```python
# Governance pattern: always have a fallback
def route_with_fallback(query):
    try:
        return primary_router.route(query)
    except Exception as e:
        log_error(e)
        return fallback_router.route(query)  # Simple round-robin
```

**Action:** Apply this pattern to router

---

### 4. Skeleton Grafana Panel ✅

**We already have Grafana running!**

**Action:** Add one routing metric to existing dashboard

```bash
# Quick addition to existing dashboard
cat >> dashboards/governance_dashboard.json << 'EOF'
{
  "title": "Router Requests",
  "targets": [{
    "expr": "rate(athena_router_requests_total[5m])"
  }]
}
EOF
```

---

## 🎯 Integration with Existing Systems

### What We Already Have:

| Component      | Status     | Port | Integration Point               |
| -------------- | ---------- | ---- | ------------------------------- |
| Orchestrator   | ✅ Running | 9110 | Add routing logic here          |
| Canary Monitor | ✅ Running | 9111 | Use for routing validation      |
| Remediator     | ✅ Running | 9112 | Can trigger on routing failures |
| Prometheus     | ✅ Running | 9090 | Add routing metrics             |
| Grafana        | ✅ Running | 3000 | Add routing dashboards          |
| Swift UI       | ✅ Built   | N/A  | Add routing client              |

### What We Need to Build:

1. **Router Service** (new or extend orchestrator)
2. **Domain Embedding Service** (Python or Rust)
3. **Canary Test Suite** (CI integration)
4. **Routing Metrics** (extend existing)
5. **Swift Routing Client** (new)

---

## 📋 Execution Plan (Prioritized)

### Sprint 1: Foundation (Week 1)

**Goal:** Get routing infrastructure in place

- [ ] Create `model_profiles.json` schema
- [ ] Implement embedding bootstrap script
- [ ] Add routing metrics to Prometheus
- [ ] Create skeleton routing dashboard
- [ ] Extend orchestrator with basic routing

**Deliverables:**

- Routing metrics flowing to Prometheus
- Basic dashboard showing routing distribution
- Mock router endpoint responding

---

### Sprint 2: Contrastive Routing (Week 2)

**Goal:** Implement domain-aware routing

- [ ] Add contrastive domain embedding logic
- [ ] Implement margin-based fallback
- [ ] Create kNN fallback router
- [ ] Add confidence metrics
- [ ] Deploy in shadow mode

**Deliverables:**

- Contrastive router functional
- Shadow mode logging routing decisions
- Confidence metrics tracked

---

### Sprint 3: CI Integration (Week 3)

**Goal:** Add canary test suite to CI

- [ ] Create 50-query edge case suite
- [ ] Implement quality evaluation
- [ ] Add safety assertions
- [ ] Create CI workflow
- [ ] Tune thresholds

**Deliverables:**

- CI fails on regressions
- Canary tests run < 5min
- False positive rate < 5%

---

### Sprint 4: Swift Client (Week 4)

**Goal:** Integrate routing into Swift UI

- [ ] Create RouterClient in Swift
- [ ] Add fallback logic
- [ ] Implement metrics emission
- [ ] Add trace context propagation
- [ ] E2E testing

**Deliverables:**

- Swift app can route requests
- Fallback works
- Traces visible end-to-end

---

## 🎓 Success Criteria

### Technical Metrics:

- ✅ Routing latency p95 < 50ms
- ✅ Fallback rate < 10%
- ✅ Routing confidence > 0.7 for 95% of requests
- ✅ CI canary tests run < 5 minutes
- ✅ False positive rate < 5%
- ✅ Trace context propagation > 99%

### Governance Metrics:

- ✅ All routing changes go through canary
- ✅ Metrics dashboards show real-time data
- ✅ Alerts fire on anomalies
- ✅ Auto-remediation triggers on routing failures

---

## 🚀 Next Actions

1. **Review this roadmap** - Approve/adjust priorities
2. **Choose router implementation** - Extend Python orchestrator vs new Rust service
3. **Create Sprint 1 tasks** - Break down into concrete todos
4. **Kickoff Sprint 1** - Start with metrics and embedding bootstrap

---

**Generated:** 2025-10-15 23:28 UTC  
**Status:** READY FOR REVIEW  
**Owner:** Development Team  
**Integration:** Governance Phase Ω+
