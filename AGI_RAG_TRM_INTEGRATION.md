# 🔗 AGI + RAG + TRM Integration Guide

**Complete system integration connecting three engines:**

1. **AGI Core** — 16 Expert Agents + Workflows
2. **RAG System** — 5.8GB Knowledge Base + Delta Testing
3. **TRM** — 7M Parameter Recursive Reasoning Model

---

## 🎯 Overview

This integration creates a **unified AGI stack** where:

- AGI agents can **query the knowledge base** for factual information
- The **router intelligently routes** queries to RAG, LLM, or TRM based on intent
- **TRM trains on RAG corpus** for domain-specific reasoning
- **Unified metrics** track performance across all systems

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User Query                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  RAG-Aware       │
              │  Router          │◄──── Intent Classifier
              │  (9113)          │◄──── KB Probe (BM25)
              └────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │   RAG   │  │   TRM   │  │   LLM   │
    │ Gateway │  │ Service │  │ (Ollama)│
    │ (8088)  │  │ (8089)  │  │ (11434) │
    └────┬────┘  └────┬────┘  └─────────┘
         │            │
         │            │ (trains on)
         │            │
         ▼            ▼
    ┌─────────────────────┐
    │  Weaviate DocsV2    │
    │  5.8GB Corpus       │
    └─────────────────────┘
                │
                ▼
    ┌─────────────────────┐
    │  Unified Metrics    │
    │  (8092)             │
    └─────────────────────┘
```

---

## 🚀 Quick Start

### 1. Start All Services

```bash
make integration-up
```

This starts:

- Weaviate (8090)
- RAG Gateway (8088) with `/kb/search` endpoint
- TRM Service (8089)
- Router (9113) with RAG-awareness
- Unified Metrics (8092)

### 2. Run Smoke Tests

```bash
make integration-smoke
```

Expected output:

```
✓ RAG Gateway /kb/search responding
✓ KB Search returns valid JSON with hits
✓ RAG Router module loads
✓ AGI KB Search tool loads
✓ Unified Metrics service responding
✓ All smoke tests passed!
```

### 3. Run Demo

```bash
make bridge-demo
```

This demonstrates:

- Basic KB search
- AGI agent using KB tool
- Router making intelligent routing decisions

---

## 🔧 Components

### 1. AGI-RAG Bridge

**Purpose:** Let AGI agents query the knowledge base

**Endpoint:** `POST http://localhost:8088/kb/search`

**Request:**

```json
{
  "query": "How to train recursive models?",
  "topK": 5,
  "mode": "nearText",
  "semanticEnabled": true
}
```

**Response:**

```json
{
  "hits": [
    {
      "doc_id": "doc_123",
      "title": "Training Recursive Models",
      "chunk": "Recursive models require...",
      "score": 0.92,
      "source": "path/to/doc.md",
      "url": "https://..."
    }
  ],
  "metrics": {
    "latency_ms": 123,
    "mode": "nearText",
    "total_hits": 5
  }
}
```

**Python Tool:**

```python
from agi_core.tools import kb_search

results = await kb_search("How to reset tokens?", top_k=5, mode="hybrid")
for result in results:
    print(f"{result.title}: {result.chunk[:100]}")
```

**Quality Gates:**

- Tool latency p95 ≤ 300ms
- AGI answer coverage: ≥80% use citations when factual
- Zero regressions on AGI evals

---

### 2. RAG-Aware Router

**Purpose:** Intelligently route queries to RAG, LLM, or TRM

**Routing Policy:**

```python
if probe_score >= 0.65:
    → RAG (high KB relevance)
elif intent in ["faq", "howto", "policy", "code"]:
    → Hybrid (factual + generation)
elif intent == "reasoning":
    → TRM or TRM+RAG
else:
    → LLM (creative/open-ended)
```

**Intent Classifier:**

- `faq` — "What is X?", "Define Y"
- `howto` — "How to...", "Steps to..."
- `code` — "Fix error", "Implement function"
- `policy` — "Is X allowed?", "Rules for Y"
- `reasoning` — "Compare A vs B", "Analyze X"
- `brainstorm` — "Ideas for...", "Creative solutions"

**Usage:**

```python
from services.router.rag_router import route_query

result = await route_query("What is recursive reasoning?")
print(f"Route to: {result.route.value}")  # → "rag"
print(f"Confidence: {result.confidence}")  # → 0.87
print(f"Reasoning: {result.reasoning}")    # → "High KB relevance (score=0.87)"
```

**Makefile Targets:**

```bash
make router-test    # Test routing decisions
make router-eval    # A/B test vs control
make router-report  # Performance metrics
```

**Quality Gates:**

- Cost ↓ ≥ 20% (fewer pure-LLM turns)
- Hit@5 not worse than baseline
- User-visible latency not worse by >10%

---

### 3. Unified Metrics

**Purpose:** Single dashboard for AGI + RAG + TRM performance

**Endpoint:** `GET http://localhost:8092/snapshot`

**Metrics Collected:**

| System          | Metrics                                                    |
| --------------- | ---------------------------------------------------------- |
| **AGI Core**    | requests, utility_score, success_rate, avg_latency_ms      |
| **RAG Gateway** | requests, hit@5, support@3, avg_latency_ms, p95_latency_ms |
| **TRM Service** | requests, avg_cycles, reasoning_quality, avg_latency_ms    |
| **Router**      | requests, rag_pct, llm_pct, hybrid_pct, trm_pct            |
| **Adapter**     | requests, stream_rate, errors                              |

**Quality Gates:**

```bash
make metrics-gates
```

Checks:

- `rag_hit_at_5 >= 0.97`
- `rag_support_at_3 >= 0.95`
- `agi_utility_score >= 0.80`
- `agi_success_rate >= 0.90`

**Usage:**

```python
import httpx

# Get snapshot
response = httpx.get("http://localhost:8092/snapshot")
snapshot = response.json()

print(f"Total requests: {snapshot['total_requests']}")
print(f"RAG hit@5: {snapshot['rag_hit_at_5']:.2%}")
print(f"AGI utility: {snapshot['agi_utility_score']:.2f}")

# Check gates
gates = {
    "rag_hit_at_5": 0.97,
    "rag_support_at_3": 0.95,
    "agi_utility_score": 0.80
}

response = httpx.post("http://localhost:8092/gates", json=gates)
result = response.json()

if result["passed"]:
    print("✓ All gates passed!")
else:
    print("✗ Failed gates:")
    for failure in result["failures"]:
        print(f"  - {failure}")
```

---

### 4. TRM Training Loop

**Purpose:** Fine-tune TRM on RAG corpus for domain-specific reasoning

**Pipeline Steps:**

1. Sample documents from DocsV2 (5.8GB corpus)
2. Mine hard negatives from RAG eval failures
3. Generate synthetic queries from documents
4. Create training triples: `(<query>, <context>, <ideal_response>)`
5. Export to JSONL for fine-tuning
6. Fine-tune TRM
7. Evaluate improvements

**Usage:**

```bash
# Generate training data
make trm-train

# Output: data/trm_training/trm_training_data.jsonl
# 1000 training examples from RAG corpus

# Fine-tune TRM
make trm-finetune

# Evaluate TRM with RAG grounding
make trm-eval-rag
```

**Training Example Format:**

```json
{
  "input": "Query: How to train recursive models?\n\nContext:\n[1] Recursive models require...\n[2] Training involves...",
  "output": "To train recursive models, you need to [Document 1] configure the recursion depth and [Document 2] use a specialized training loop...",
  "metadata": {
    "generated_at": "2025-10-18T12:00:00",
    "model": "qwen2.5-coder:7b",
    "has_ground_truth": false
  }
}
```

**Quality Gates:**

- ARC/AGI evals don't regress
- Grounding rate improves (more answers with correct citations)
- Latency unchanged (or documented trade-off)

---

## 📊 Nightly CI Pipeline

**Command:**

```bash
make nightly
```

**Steps:**

1. RAG Evaluation (hit@k, support@k, latency)
2. RAG Delta Report (BM25 vs semantic vs hybrid)
3. Router Evaluation (A/B vs control)
4. Quality Gates Check (unified metrics)

**GitHub Actions:**

```yaml
name: Nightly Integration Validation
on:
  schedule:
    - cron: "0 2 * * *" # 2 AM daily
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: make integration-up
      - name: Run nightly validation
        run: make nightly
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: nightly-reports
          path: artifacts/
```

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/integration/ -v
```

### Smoke Tests

```bash
make integration-smoke
# or
bash scripts/integration_smoke_tests.sh
```

### E2E Tests

```bash
make integration-e2e
```

Validates:

- User query → Router → RAG → Response
- AGI agent → KB search → Citation
- TRM → RAG context → Reasoning
- Metrics collection → Dashboard

### Demo

```bash
make demo-all
```

Shows:

1. AGI agent queries KB
2. Router makes intelligent decisions
3. TRM uses RAG context for reasoning

---

## 📈 Performance Baselines

| Metric                           | Target  | Current |
| -------------------------------- | ------- | ------- |
| **KB Search Latency (p95)**      | ≤ 300ms | TBD     |
| **Router Decision Time**         | ≤ 50ms  | TBD     |
| **Cost Reduction (vs pure LLM)** | ≥ 20%   | TBD     |
| **Hit@5**                        | ≥ 0.97  | TBD     |
| **Support@3**                    | ≥ 0.95  | TBD     |
| **AGI Utility Score**            | ≥ 0.80  | TBD     |

Run `make metrics-snapshot` to get current values.

---

## 🎯 Next Steps

1. **Baseline Measurement** — Run `make nightly` to establish baselines
2. **Router Tuning** — Adjust `PROBE_THRESHOLD` based on cost vs accuracy trade-offs
3. **TRM Fine-Tuning** — Run `make trm-train && make trm-finetune` on your corpus
4. **Dashboard Setup** — Import Grafana dashboard for real-time monitoring
5. **Production Deployment** — Add to `docker-compose.full-stack.yml`

---

## 🔍 Troubleshooting

### KB Search returns empty results

```bash
# Check Weaviate data
curl http://localhost:8090/v1/schema | jq '.classes[] | select(.class == "DocsV2")'

# Verify embeddings
curl http://localhost:8087/health
```

### Router not routing to RAG

```bash
# Check probe threshold
export RAG_PROBE_THRESHOLD=0.50  # Lower threshold

# Test manually
python3 -c "import asyncio; from services.router.rag_router import route_query; \
    result = asyncio.run(route_query('What is X?')); \
    print(result.reasoning)"
```

### Unified metrics not collecting

```bash
# Check service endpoints
curl http://localhost:8088/metrics  # RAG
curl http://localhost:8089/metrics  # TRM
curl http://localhost:9113/metrics  # Router

# Restart unified metrics
make unified-metrics
```

---

## 📚 Related Documentation

- **[RAG Delta Reports](docs/RAG_DELTA_REPORTS.md)** — A/B testing RAG strategies
- **[OpenAI Adapter](OPENAI_COMPAT_QUICK_START.md)** — Universal API compatibility
- **[Production Hardening](PRODUCTION_HARDENING_COMPLETE.md)** — Security, monitoring, alerts
- **[E2E Testing](E2E_TESTING_COMPLETE.md)** — Full stack validation
- **[AGI Core Metrics](agi_core/METRICS_GUIDE.md)** — Agent performance tracking
- **[TRM Training](TinyRecursiveModels/README.md)** — Recursive model training

---

## 🎉 Success Criteria

✅ **Bridge Integration**

- AGI agents can search KB in <300ms
- ≥80% of factual answers include citations
- Zero regressions on AGI evals

✅ **Intelligent Routing**

- ≥20% cost reduction vs pure LLM
- Hit@5 maintained or improved
- Latency not worse by >10%

✅ **Unified Telemetry**

- All systems reporting to single dashboard
- Quality gates enforced in CI
- Alerts firing on regressions

✅ **TRM Training**

- 1000+ training examples from corpus
- ARC/AGI evals maintained
- Improved grounding rate

---

**🚀 You now have a production-grade, local-first AGI stack with unified intelligence!**
