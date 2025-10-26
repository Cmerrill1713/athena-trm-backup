# 🚨 Quick Fixes — When Gates Fail

**Fast fixes for common ship-check failures.**

---

## 🔴 KB hits = 0 / slow search

**Symptom:** `ship-check` fails with "KB search returned 0 hits" or latency > 300ms

**Diagnosis:**

```bash
# Check DocsV2 exists
curl localhost:8090/v1/schema | jq '.classes[] | select(.class == "DocsV2")'

# Check vector dimensions (should be 384)
curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.objects[0].vector | length'

# Check object count
curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.totalResults'
```

**Fix:**

```bash
# If corpus missing or wrong dimensions:
make seed-corpus

# If corpus exists but cold cache:
for i in {1..5}; do
  curl -s localhost:8088/kb/search \
    -H 'content-type: application/json' \
    -d '{"query":"test query","topK":5,"mode":"nearText"}' > /dev/null
  echo "Warming cache: $i/5"
done

# Retest
make bridge-smoke
```

**Tune for better performance:**

```bash
# Reduce top_k if latency high
export RAG_DEFAULT_TOPK=5  # Default is 8

# Increase HNSW ef for better recall
# In Weaviate config:
#   QUERY_DEFAULTS_LIMIT: 10
#   HNSW_EF: 128
```

---

## 🔴 Router misroutes

**Symptom:** `ship-check` fails with "Factual query routed to LLM" or similar

**Diagnosis:**

```bash
# Test routing manually
python3 scripts/router_probe.py --q "What is our refund policy?"
# Expected: RAG or Hybrid

python3 scripts/router_probe.py --q "Brainstorm creative ideas"
# Expected: LLM

python3 scripts/router_probe.py --q "Compare solution A vs B"
# Expected: TRM or TRM+RAG
```

**Fix:**

```bash
# If too RAG-happy (everything goes to RAG):
export RAG_PROBE_THRESHOLD=0.70  # Raise from 0.65

# If too LLM-happy (everything goes to LLM):
export RAG_PROBE_THRESHOLD=0.55  # Lower from 0.65

# Test with new threshold
make router-test

# If good, persist in docker-compose.full-stack.yml:
services:
  router:
    environment:
      - RAG_PROBE_THRESHOLD=0.60
```

**Understand probe scores:**

```bash
# Get detailed routing info
python3 -c "
import asyncio
from services.router.rag_router import route_query

async def test():
    result = await route_query('What is X?')
    print(f'Route: {result.route.value}')
    print(f'Probe score: {result.probe_score}')
    print(f'Threshold: 0.65')
    print(f'Intent: {result.intent.category}')

asyncio.run(test())
"
```

---

## 🔴 Delta regression

**Symptom:** `ship-check` fails with "Delta report shows regression"

**Diagnosis:**

```bash
# Check delta report
cat artifacts/delta_report.md

# Look for negative deltas
jq '.delta' artifacts/delta_report.json
```

**Fix:**

```bash
# If semantic < BM25:
#   → Embeddings quality issue

# 1. Check embedding service
curl http://localhost:8087/health

# 2. Bump HNSW ef in Weaviate
# In docker-compose:
services:
  weaviate:
    environment:
      - HNSW_EF_CONSTRUCTION: 256
      - HNSW_EF: 128

# 3. Re-run eval
make rag-eval
make rag-delta

# If hybrid < both modes:
#   → Tune hybrid alpha

# In rag-gateway:
export RAG_HYBRID_ALPHA=0.75  # Default 0.7 (higher = more semantic)

# Retest
make rag-delta-hybrid
```

**Acceptable regressions:**

- Delta within ±2% = acceptable variance
- If BM25 improved but semantic regressed: check if queries changed
- If all modes regressed: corpus quality issue (re-seed)

---

## 🔴 Metrics not collecting

**Symptom:** `ship-check` fails with "Unified metrics not available"

**Diagnosis:**

```bash
# Check unified metrics service
curl -sf http://localhost:8092/health

# Check upstream services
curl -sf http://localhost:8088/metrics  # RAG
curl -sf http://localhost:9113/metrics  # Router
curl -sf http://localhost:8089/metrics  # TRM (if running)
```

**Fix:**

```bash
# Restart unified metrics
pkill -f unified_metrics
cd services && python3 unified_metrics.py &

# Wait a few seconds
sleep 5

# Test
curl http://localhost:8092/snapshot | jq '.'

# If still failing, check dependencies
pip install httpx fastapi uvicorn pydantic prometheus-client

# Retest
make metrics-snapshot
```

---

## 🔴 Stream errors

**Symptom:** Adapter reports high stream error rate or timeouts

**Diagnosis:**

```bash
# Check nginx config
grep proxy_buffering nginx.conf
grep proxy_read_timeout nginx.conf

# Test streaming
curl -N http://localhost:3000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"athena-rag","messages":[{"role":"user","content":"test"}],"stream":true}'
```

**Fix:**

```bash
# Update nginx.conf
proxy_buffering off;
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
proxy_http_version 1.1;
proxy_set_header Connection "";

# Restart nginx
docker-compose restart nginx

# Or if using docker:
docker restart nginx
```

---

## 🔴 Canary fails gates

**Symptom:** `make canary-promote` fails automatic gate checks

**Diagnosis:**

```bash
# Check current canary status
make canary-status

# Get detailed metrics
curl http://localhost:8092/snapshot | jq '{
  p95: .rag_avg_latency_ms,
  errors: .total_errors,
  hit_5: .rag_hit_at_5
}'
```

**Fix:**

```bash
# 1. ROLLBACK immediately
make canary-rollback

# 2. Check logs
docker logs rag-gateway | tail -50
docker logs router | tail -50
docker logs openai-compat | tail -50

# 3. Fix issue locally
make ship-check  # Should pass before trying canary again

# 4. If latency issue:
#    → Check Weaviate cache
#    → Reduce top_k
#    → Check for slow queries in logs

# 5. If error rate issue:
#    → Check for timeout errors
#    → Check for malformed requests
#    → Verify all services healthy

# 6. Retry canary
make canary-start
```

---

## 🔴 DocsV2 not populated

**Symptom:** `ship-check` fails with "DocsV2 empty or missing"

**Diagnosis:**

```bash
# Check if class exists
curl localhost:8090/v1/schema | jq '.classes[].class'

# Check object count
curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.totalResults'
```

**Fix:**

```bash
# Option 1: Restore from backup
cp -r /path/to/backup/weaviate_data volumes/
docker-compose restart weaviate

# Option 2: Re-seed corpus
make seed-corpus

# Option 3: Import from external drive
rsync -av /Volumes/ExternalDrive/weaviate_data/ volumes/weaviate_data/
docker-compose restart weaviate

# Verify
curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '{
  class: .objects[0].class,
  vector_length: (.objects[0].vector | length),
  total: .totalResults
}'

# Should show:
# - class: "DocsV2"
# - vector_length: 384
# - total: > 0
```

---

## 🔴 Services not responding

**Symptom:** `ship-check` fails preflight checks

**Diagnosis:**

```bash
# Check which service is down
curl -sf http://localhost:8088/health || echo "RAG Gateway down"
curl -sf http://localhost:9113/health || echo "Router down"
curl -sf http://localhost:8090/v1/meta || echo "Weaviate down"
curl -sf http://localhost:11434/api/tags || echo "Ollama down"

# Check Docker containers
docker ps | grep -E "(weaviate|ollama|rag-gateway|router)"
```

**Fix:**

```bash
# Restart all services
docker-compose -f docker-compose.full-stack.yml restart

# Wait for health
sleep 10

# Check logs for errors
docker-compose logs --tail=50

# If specific service failing:
docker-compose restart <service-name>

# If persistent failures:
docker-compose down
docker-compose -f docker-compose.full-stack.yml up -d
```

---

## 📊 Debugging Workflow

For any gate failure:

1. **Read the error** from `ship-check` output
2. **Run the diagnostic** commands above
3. **Apply the fix**
4. **Retest locally:** `make ship-check`
5. **Only try canary after** local tests pass

---

## 🔧 Prevention

**Before every deployment:**

```bash
# 1. Run full validation
make nightly

# 2. Check baselines
make metrics-snapshot

# 3. Review artifacts
ls -lh artifacts/

# 4. Test in staging first
make ship-check  # On staging environment

# 5. Only then production
make canary-start
```

---

## 🚨 Emergency Rollback

**If production is broken:**

```bash
# Immediate rollback
make canary-rollback

# Check what happened
make day2-check

# Review recent changes
git log --oneline -10

# Revert if needed
git revert <bad-commit>

# Retest
make ship-check

# Only redeploy after passing
```

---

**🔥 Keep this handy during deployments!**
