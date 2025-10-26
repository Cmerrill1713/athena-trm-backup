# 🚀 AGI + RAG + TRM Integration — Quick Reference

**Everything you need on one page.**

---

## ⚡ Quick Start

```bash
# 1. Start all services
make integration-up

# 2. Verify it's working
make integration-smoke

# 3. See it in action
make bridge-demo

# 4. Check performance
make metrics-snapshot
```

---

## 🔧 Key Components

| Component           | Port | Purpose             | Test It                                                               |
| ------------------- | ---- | ------------------- | --------------------------------------------------------------------- |
| **RAG Gateway**     | 8088 | KB search endpoint  | `curl http://localhost:8088/kb/search -d '{"query":"test","topK":3}'` |
| **TRM Service**     | 8089 | Recursive reasoning | `curl http://localhost:8089/health`                                   |
| **Router**          | 9113 | Intelligent routing | `make router-test`                                                    |
| **Unified Metrics** | 8092 | Combined dashboard  | `curl http://localhost:8092/snapshot`                                 |
| **Weaviate**        | 8090 | Vector database     | `curl http://localhost:8090/v1/meta`                                  |

---

## 🎯 Common Commands

### **AGI-RAG Bridge**

```bash
make bridge-smoke        # Test /kb/search
make bridge-test         # Test AGI tool
make bridge-demo         # Full demo
```

### **RAG-Aware Router**

```bash
make router-test         # Test routing decisions
make router-eval         # A/B vs control
make router-report       # Performance metrics
```

### **Unified Metrics**

```bash
make unified-metrics     # Start service
make metrics-snapshot    # Current state
make metrics-gates       # Check quality gates
```

### **TRM Training**

```bash
make trm-train          # Generate training data
make trm-finetune       # Fine-tune TRM
make trm-eval-rag       # Evaluate TRM+RAG
```

### **Integration Tests**

```bash
make integration-smoke   # Quick validation (30s)
make integration-test    # Full unit tests (2min)
make integration-e2e     # End-to-end (10min)
make nightly             # Full validation (30min)
```

---

## 💻 Python API

### **KB Search (AGI Agents)**

```python
from agi_core.tools import kb_search

# Simple search
results = await kb_search("How to train models?", top_k=5)

# With tool instance
tool = KBSearchTool()
results = await tool.search(query, mode="hybrid")
formatted = tool.format_results_for_agent(results)
```

### **RAG-Aware Router**

```python
from services.router.rag_router import route_query

result = await route_query("What is X?")
print(f"Route: {result.route.value}")        # rag|llm|trm|hybrid
print(f"Confidence: {result.confidence}")    # 0.0-1.0
print(f"Reasoning: {result.reasoning}")      # Why this route?
```

### **Unified Metrics**

```python
import httpx

# Get snapshot
response = httpx.get("http://localhost:8092/snapshot")
metrics = response.json()

# Check gates
gates = {"rag_hit_at_5": 0.97, "agi_utility_score": 0.80}
response = httpx.post("http://localhost:8092/gates", json=gates)
result = response.json()

if result["passed"]:
    print("✓ All gates passed!")
```

---

## 🔌 REST API

### **KB Search**

```bash
curl -X POST http://localhost:8088/kb/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to train models?",
    "topK": 5,
    "mode": "hybrid"
  }'

# Response:
{
  "hits": [
    {"doc_id": "...", "title": "...", "chunk": "...", "score": 0.92}
  ],
  "metrics": {"latency_ms": 123, "mode": "hybrid"}
}
```

### **Metrics Snapshot**

```bash
curl http://localhost:8092/snapshot | jq '{
  total_requests,
  rag_hit_at_5,
  agi_utility_score,
  trm_reasoning_quality
}'
```

---

## 🎓 Training Workflow

```bash
# 1. Generate training data from RAG corpus
make trm-train
# → data/trm_training/trm_training_data.jsonl (1000 examples)

# 2. Fine-tune TRM
make trm-finetune
# → models/trm-rag-v1

# 3. Evaluate improvements
make trm-eval-rag
# → artifacts/trm_rag_eval.json

# 4. Deploy
export TRM_MODEL_PATH=models/trm-rag-v1
make integration-up
```

---

## 📊 Quality Gates

```bash
make metrics-gates
```

Enforces:

- `rag_hit_at_5 >= 0.97`
- `rag_support_at_3 >= 0.95`
- `agi_utility_score >= 0.80`
- `agi_success_rate >= 0.90`

---

## 🧪 Testing

### **Smoke Test (30s)**

```bash
make integration-smoke
# ✓ RAG Gateway /kb/search responding
# ✓ KB Search returns valid JSON
# ✓ RAG Router module loads
# ✓ AGI KB Search tool loads
# ✓ All smoke tests passed!
```

### **Demo (2min)**

```bash
make bridge-demo
# Shows:
# 1. Basic KB search
# 2. AGI agent using KB tool
# 3. Router making intelligent decisions
```

### **Nightly (30min)**

```bash
make nightly
# 1/4 RAG Evaluation
# 2/4 RAG Delta Report
# 3/4 Router Evaluation
# 4/4 Quality Gates
# ✓ Nightly validation complete
```

---

## 🔍 Troubleshooting

### **KB Search returns no results**

```bash
# Check Weaviate
curl http://localhost:8090/v1/schema | jq '.classes'

# Check DocsV2 count
curl 'http://localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.totalResults'
```

### **Router not routing to RAG**

```bash
# Lower threshold
export RAG_PROBE_THRESHOLD=0.50

# Test manually
python3 -c "import asyncio; from services.router.rag_router import route_query; \
    print(asyncio.run(route_query('What is X?')))"
```

### **Metrics service down**

```bash
pip install httpx fastapi uvicorn pydantic prometheus-client
cd services && python3 unified_metrics.py &
```

---

## 📁 File Locations

| File                                   | Purpose                       |
| -------------------------------------- | ----------------------------- |
| `services/rag-gateway/app.py`          | RAG Gateway with `/kb/search` |
| `agi_core/tools/kb_search_tool.py`     | KB search tool for agents     |
| `services/router/rag_router.py`        | RAG-aware router              |
| `services/unified_metrics.py`          | Unified metrics service       |
| `scripts/trm_rag_training_pipeline.py` | TRM training pipeline         |
| `Makefile.integration`                 | All integration targets       |
| `scripts/demo_agi_rag_bridge.py`       | Demo script                   |
| `scripts/integration_smoke_tests.sh`   | Smoke tests                   |

---

## 🎯 Routing Policy

```python
if probe_score >= 0.65:
    → RAG                    # High KB relevance

elif intent == "reasoning":
    if probe_score >= 0.50:
        → TRM + RAG          # Reasoning with context
    else:
        → TRM                # Pure reasoning

elif intent in ["faq", "howto", "policy", "code"]:
    → Hybrid                 # Factual + generation

elif intent == "brainstorm":
    → LLM                    # Creative/open-ended

else:
    → Hybrid                 # Safe fallback
```

---

## 📈 Performance Targets

| Metric                  | Target  |
| ----------------------- | ------- |
| KB Search Latency (p95) | ≤ 300ms |
| Router Decision Time    | ≤ 50ms  |
| Cost Reduction          | ≥ 20%   |
| Hit@5                   | ≥ 0.97  |
| Support@3               | ≥ 0.95  |
| AGI Utility Score       | ≥ 0.80  |

---

## 🚀 One-Liner Cheat Sheet

```bash
# Start everything
make integration-up

# Quick validation
make integration-smoke

# See demo
make bridge-demo

# Check metrics
make metrics-snapshot

# Run nightly
make nightly

# Train TRM
make trm-train && make trm-finetune

# Stop everything
make integration-down
```

---

**📚 Full docs:** [AGI_RAG_TRM_INTEGRATION.md](AGI_RAG_TRM_INTEGRATION.md)

**🎉 Integration complete:** [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)
