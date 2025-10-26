# 🚀 Acceptance Testing Guide — Ship with Confidence

**Comprehensive acceptance plan for AGI+RAG+TRM integration with rollback hooks.**

---

## ⚡ TL;DR — One Command to Ship

```bash
make ship-check
```

**Exit code 0 = safe to ship. Exit code 1 = do not ship.**

---

## 📋 Full Acceptance Plan

### **Step 0: Preflight (60 seconds)**

```bash
# Start stack
make integration-up

# Health checks (automated in ship-check)
curl -sf localhost:8088/health || exit 1   # RAG Gateway
curl -sf localhost:9113/health || exit 1   # Router
curl -sf localhost:8092/snapshot || exit 1 # Unified Metrics
curl -sf localhost:3000/v1/models || exit 1 # OpenAI Adapter
curl -sf localhost:8090/v1/meta || exit 1  # Weaviate
```

**Pass if:** All services respond with 200 OK

**Fail action:** Check Docker logs, restart services

---

### **Step 1: Bridge Acceptance (AGI → /kb/search → DocsV2)**

```bash
# KB smoke: latency < 300ms, hits > 0
time curl -s localhost:8088/kb/search \
  -H 'content-type: application/json' \
  -d '{"query":"reset token policy","mode":"nearText","topK":5,"semanticEnabled":true}' \
  | jq '{hits_count:(.hits|length), latency_ms:.metrics.latency_ms, mode:.metrics.mode}'
```

**Pass if:**

- `hits_count ≥ 1`
- `latency_ms ≤ 300` (warm cache ≤150ms)

**Fail action:**

- Verify DocsV2 populated: `curl localhost:8090/v1/schema | jq '.classes[] | select(.class == "DocsV2")'`
- Check vector dimensions: `curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.objects[0].vector | length'`
- Verify `WEAVIATE_URL` in gateway env

---

### **Step 2: Router Acceptance (Policy + Relevance)**

```bash
# Factual → RAG / Hybrid
python3 scripts/router_probe.py --q "What is our refund policy?"

# Creative → LLM
python3 scripts/router_probe.py --q "Brainstorm 10 tagline options"

# Reasoning → TRM(+RAG)
python3 scripts/router_probe.py --q "Compare solutions A vs B with tradeoffs"
```

**Pass if:** Outputs show route = RAG/Hybrid, LLM, TRM(+RAG) respectively

**Fail action:**

- Too RAG-happy: `export RAG_PROBE_THRESHOLD=0.70` (raise)
- Too LLM-happy: `export RAG_PROBE_THRESHOLD=0.55` (lower)
- Retest with new threshold

---

### **Step 3: Unified Metrics Sanity (1 minute)**

```bash
curl -s localhost:8092/snapshot | jq '{
  requests: .total_requests,
  route_mix: .route_mix,
  rag: { hit@5: .rag_hit_at_5, support@3: .rag_support_at_3 },
  agi: { utility: .agi_utility_score, success: .agi_success_rate },
  latency_ms_p95: .latency_ms_p95
}'
```

**Pass if:**

- Numbers exist (not NaN/null)
- `route_mix` updates after queries

**Fail action:**

- Check metrics service: `curl localhost:8092/health`
- Restart: `make unified-metrics`

---

### **Step 4: Quality Gates (Hard Fail Rules)**

```bash
# Retrieval gates (uses your seeds)
make rag-eval

# Delta report (bm25 vs semantic)
make rag-delta
cat artifacts/delta_*.md | tail -n 20

# Integrated smoke (8 tests)
make integration-smoke
```

**Pass if:**

- `hit@5 ≥ 0.97`
- `support@3 ≥ 0.95`
- Delta doesn't regress (or within agreed margin)

**Fail action:**

- If BM25 > semantic: Check embeddings, retrain
- If semantic > BM25: Check query preprocessing, tune alpha
- Run `make rag-delta-hybrid` to test hybrid mode

---

### **Step 5: 30-Minute Canary (with Guardrails)**

```bash
# Start canary (routes 5% of traffic through new integration)
make canary-start

# Watch metrics during canary (every 10s, Ctrl+C to stop)
make canary-watch
```

**Promotion gates** (check every 10-15 min):

- p95 end-to-end ≤ +10% vs baseline
- 5xx ≤ +0.3% absolute increase
- RAG gates stay green

**Promotion ladder:**

```bash
# 5% → 25% (after 10-15 min if green)
make canary-promote

# 25% → 50% (after 10-15 min if green)
make canary-promote

# 50% → 100% (after 10-15 min if green)
make canary-promote
```

**Rollback** (one command):

```bash
make canary-rollback
```

---

### **Step 6: 2-Hour Soak (Optional but Wise)**

```bash
# 30 VUs for 2 hours
make soak-2h

# OR shorter smoke soak
make soak-30m
```

**Watch for:**

- Adapter p95 vs router p95 vs RAG p95 (stable, no runaway)
- Stream error rate < 2%
- Memory steady (no ballooning)

**Fail action:**

- Memory leak: Check for unclosed connections, restart services
- Latency drift: Check Weaviate query cache, tune `top_k`
- High stream errors: Check nginx buffering, increase timeouts

---

### **Step 7: TRM Training Loop (Smaller Slice First)**

```bash
# Generate supervised triples from KB + recent misses
make trm-train N=250

# Fine-tune and evaluate
make trm-finetune
make trm-eval-rag
```

**Pass if:**

- No regressions on AGI evals
- Grounding rate improves on factual tasks
- Router able to override to RAG if TRM uncertain

---

### **Step 8: CI "Ship or Block"**

Add to `.github/workflows/`:

```yaml
name: Ship Gate
on: [pull_request, push]

jobs:
  ship-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: make integration-up
      - name: Run ship check
        run: make ship-check
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ship-check-artifacts
          path: artifacts/
```

**Fail the build** if any gate trips.

---

## 🚨 Top 6 Things Most Likely to Bite (and Fast Fix)

### **1. Wrong class or dims (DocsV2 not 384)**

```bash
# Check schema
curl localhost:8090/v1/schema | jq '.classes[] | select(.class == "DocsV2")'

# Check vector length
curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.objects[0].vector | length'

# Fix: Re-seed with correct dimensions
make seed-corpus
```

### **2. Router threshold bad**

```bash
# Tune threshold
export RAG_PROBE_THRESHOLD=0.60  # Default 0.65

# Retest
make router-test
```

### **3. Adapter CORS (from PWA/iPhone)**

```bash
# Set exact origin in docker-compose
CORS_ORIGIN: "https://your-domain.com"

# Restart adapter
docker-compose restart openai-compat
```

### **4. SSE buffering**

```nginx
# In nginx.conf
proxy_buffering off;
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
```

### **5. Seed/ID mismatch in eval**

```bash
# Verify doc_id in seeds matches Weaviate
jq -r '.doc_id' seeds/rag_eval_seeds.jsonl | head -5

# Check Weaviate IDs
curl 'localhost:8090/v1/objects?class=DocsV2&limit=5' | jq '.objects[].properties.doc_id'
```

### **6. TRM drift**

```bash
# Keep nightly eval
make trm-eval-rag

# Route override stays enabled (router can force RAG if TRM uncertain)
```

---

## 📅 Day-2 Runbook (What You Actually Check Daily)

```bash
make day2-check
```

**Checks:**

1. **Route mix trend** — Did router silently drift?
2. **p95 by route** — rag/llm/hybrid/trm
3. **RAG gates** — hit@5/support@3
4. **Error budget** — 5xx, stream errors
5. **Recent papers ingest** — Only approved sources; eval slice

---

## 🎯 Quick Reference

| Command                | Purpose                               | Duration   |
| ---------------------- | ------------------------------------- | ---------- |
| `make ship-check`      | Full acceptance (steps 0-4)           | 2-3 min    |
| `make ship-preflight`  | Preflight checks only                 | 30s        |
| `make ship-quick`      | Fast smoke (health + bridge + router) | 1 min      |
| `make canary-start`    | Start canary at 5%                    | instant    |
| `make canary-promote`  | Promote to next level                 | instant    |
| `make canary-rollback` | Rollback to baseline                  | instant    |
| `make canary-watch`    | Watch canary metrics (live)           | continuous |
| `make soak-2h`         | 2-hour load test                      | 2 hours    |
| `make day2-check`      | Daily operational checks              | 1 min      |

---

## 🚀 Ship Workflow (Recommended)

### **Pre-Ship (Developer)**

```bash
# 1. Run local ship check
make ship-check

# If PASS:
#   Commit + push
# If FAIL:
#   Fix issues, retest
```

### **CI/CD (Automated)**

```yaml
# In GitHub Actions
- run: make integration-up
- run: make ship-check # Fails build if gates violated
- run: make rag-delta # Generate delta report
- uses: actions/upload-artifact@v3
  with:
    name: ship-artifacts
    path: artifacts/
```

### **Production Deployment**

```bash
# 1. Deploy to canary
make canary-start

# 2. Watch for 10-15 minutes
make canary-watch

# 3. Promote if green
make canary-promote  # 5% → 25%
# Wait 10-15 min, watch metrics

make canary-promote  # 25% → 50%
# Wait 10-15 min, watch metrics

make canary-promote  # 50% → 100%
# Done!

# OR rollback if issues
make canary-rollback
```

---

## 📊 Success Criteria

### **Ship Check Pass**

- ✅ All services healthy
- ✅ KB search < 300ms with hits
- ✅ Router routes correctly (factual→RAG, creative→LLM, reasoning→TRM)
- ✅ Metrics collecting valid data
- ✅ RAG gates passing (hit@5 ≥ 0.97, support@3 ≥ 0.95)
- ✅ Smoke tests passing

### **Canary Promotion**

- ✅ p95 latency ≤ baseline + 10%
- ✅ Error rate < 1%
- ✅ RAG gates still green
- ✅ No memory leaks
- ✅ Stream error rate < 2%

### **Soak Test Pass**

- ✅ Latency stable over 2 hours
- ✅ Memory steady (no growth)
- ✅ Error rate < 0.5%
- ✅ No service restarts

---

## 🔥 One-Command Ship Path

```bash
# Full acceptance (steps 0-4)
make ship-check

# If PASS:
make canary-start
make canary-watch  # Watch for 30 min

# If green:
make canary-promote  # 3x with monitoring between

# If issues:
make canary-rollback
```

---

## 📚 Related Documentation

- **[ship_check.sh](scripts/ship_check.sh)** — Main acceptance test script
- **[canary_deploy.sh](scripts/canary_deploy.sh)** — Canary deployment with rollback
- **[day2_runbook.sh](scripts/day2_runbook.sh)** — Daily operational checks
- **[router_probe.py](scripts/router_probe.py)** — Router decision testing

---

**🚀 With this acceptance plan, you can ship with confidence knowing every critical path is validated.**
