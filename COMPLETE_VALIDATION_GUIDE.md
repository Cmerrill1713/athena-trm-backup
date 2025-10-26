# 🧪 **COMPLETE VALIDATION GUIDE**

**End-to-end confidence pass for Athena - no backtracking, no rewrites**

---

## 🎯 **Quick Start:**

```bash
# One-button validation:
./QUICK_SHIP_CHECK.sh
```

**Expect:** ✅ banner if everything is green.

---

## 📋 **Manual Validation Steps:**

### **0️⃣ Preflight (10s)**

```bash
# Set environment
export ATHENA_NO_CLOUD=1
export ATHENA_ENV=production

# Check Docker
docker version && echo "✅ Docker OK"

# Create directories
mkdir -p volumes/weaviate_data volumes/ollama artifacts seeds

# Check compose files
ls -1 docker-compose.yml docker-compose.shadow.yml

# Check ports are free
lsof -i :8080,:8090,:9113,:8081,:9115,:9090 2>/dev/null
```

**If port busy:** `docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Ports}}'`

---

### **1️⃣ Start Core Services (60-90s)**

```bash
docker-compose up -d athena-weaviate athena-router uai athena-prometheus
```

**Health Probes:**
```bash
# Weaviate
curl -s http://127.0.0.1:8090/v1/.well-known/ready | jq .status

# Router
curl -s http://127.0.0.1:9113/health | jq .

# UAI
curl -s http://127.0.0.1:8080/health | jq .

# Prometheus
curl -s http://127.0.0.1:9090/-/healthy
```

**Fixes:**
- Weaviate not ready → `docker restart athena-weaviate && sleep 15`
- Router 500 → `docker logs athena-router --tail 100`
- UAI not responding → `docker-compose restart uai`

---

### **2️⃣ Corpus Check**

```bash
# Check DocsV2 count
curl -s http://127.0.0.1:8090/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ Aggregate { DocsV2 { meta { count } } } }"}' | jq '.data.Aggregate.DocsV2[0].meta.count'
```

**Expect:** Number > 0

**If 0:**
```bash
# Restore corpus
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* volumes/weaviate_data/
docker restart athena-weaviate
sleep 15
# Re-check count
```

---

### **3️⃣ RAG Smoke Test**

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"athena-chat",
    "messages":[{"role":"user","content":"What is TRM?"}],
    "stream": false
  }' | jq '.choices[0].message.content'
```

**Expect:** Coherent answer about "Tiny Recursive Model"

**If empty:** Check UAI logs: `docker logs athena-uai --tail 50`

---

### **4️⃣ OpenAI-Compat End-to-End**

```bash
# List models
curl -s http://127.0.0.1:8080/v1/models | jq '.data[].id'

# Chat completion
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"athena-chat",
    "messages":[{"role":"user","content":"Summarize REP protocol in one sentence"}],
    "stream": false
  }' | jq '.choices[0].message.content'
```

**Expect:** List of models + coherent answer

**If 500:** `docker logs athena-uai --tail 100`

---

### **5️⃣ Governance Gate**

```bash
curl -s http://127.0.0.1:9110/authorize \
  -H "Content-Type: application/json" \
  -d '{
    "type":"routing",
    "decision":{"route":"rag","model":"athena-rag"},
    "context":{"source":"smoke"}
  }' | jq .
```

**Expect:** `{"allowed": true}` or clear deny reason

**If down:** `docker-compose up -d governance-orchestrator`

---

### **6️⃣ Ship Check Gates**

```bash
make -f Makefile.production ship-check
```

**Expect:** All gates PASS

**If fails:** Script prints first red gate with fix

---

### **7️⃣ Dev Daemon (Copilot)**

```bash
# Start daemon
make -f Makefile.production athena-up

# Health check
curl -s http://127.0.0.1:8765/healthz | jq .

# Test context gathering
curl -s http://127.0.0.1:8765/ctx/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "repoRoot":"'"$(pwd)"'",
    "file":"services/router/app.py",
    "query":"routing logic",
    "intent":"explain"
  }' | jq '.snippets | length'
```

**Expect:** Health = healthy, snippets > 0

**If blocked by governance:** Check policy caps for `dev.assist`

---

### **8️⃣ Observability Spine**

```bash
# OTEL metrics
curl -s http://127.0.0.1:8889/metrics | grep -E 'athena_' | head -5

# Prometheus targets
curl -s 'http://127.0.0.1:9090/api/v1/targets' | jq '.data.activeTargets | length'
```

**Expect:** athena_* metrics visible, targets > 0

**If no metrics:** Check `docker logs athena-otel-collector`

---

### **9️⃣ Go Shadow Stack**

```bash
# Start Go services
docker-compose -f docker-compose.yml -f docker-compose.shadow.yml up -d go-router go-gateway

sleep 10

# Check health
docker ps | grep "athena-go"

# Run parity test
python3 scripts/shadow_compare.py
```

**Expect:** Parity ≥ 99%, p95 improvement ≥ 20%

**If parity low:** Keep shadowing, don't promote

---

### **🔟 Local UI**

```bash
# Start UI server (if not already running)
python3 -m http.server 8082 -d ui &

# Open browser
open http://localhost:8082/athena-chat.html
```

**Test:**
- Type "Hi Athena"
- Check 9/9 services ready
- Verify response is brief and natural

---

## 🛠️ **Quick Fixes:**

### **Weaviate 0 docs:**
```bash
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* volumes/weaviate_data/
docker restart athena-weaviate && sleep 15
```

### **OTEL logging error:**
```bash
# Remove file exporters from config
docker restart athena-otel-collector
```

### **Prometheus no targets:**
```bash
# Check scrape config
docker exec athena-prometheus cat /etc/prometheus/prometheus.yml | grep -A5 athena
```

### **SSE hangs:**
```bash
# Ensure write deadlines in adapter
# Disable proxy buffering if using Nginx
```

### **Router 5xx:**
```bash
# Check governance latency
docker logs athena-router --tail 50
# Set gRPC deadlines to 2-5s
```

### **Copilot floods:**
```bash
# Enable rate limiting in devd middleware
# Returns 429 on violation
```

---

## 📊 **Exit Criteria:**

All checks must pass:
- ✅ Docker running
- ✅ Weaviate healthy (DocsV2 > 0)
- ✅ Router healthy
- ✅ UAI healthy
- ✅ RAG search works (response > 0)
- ✅ Governance gate responds
- ✅ Dev daemon healthy (if running)
- ✅ OTEL + Prometheus collecting
- ✅ Go shadow parity ≥ 99% (if testing)

---

## 🚀 **After All Green:**

```bash
# Production deployment:
make -f Makefile.production canary-start

# Copilot usage:
athena-assist "your question"

# Go migration:
make -f Makefile.production go-promote-5
```

---

## 💙 **Bottom Line:**

**One script validates everything:**
```bash
./QUICK_SHIP_CHECK.sh
```

**If green → Ship it! 🎉**

**If red → Fix shown, re-run, ship! 🚀**

---

**Complete. Validated. Production-Ready. 💙**

