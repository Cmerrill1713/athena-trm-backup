# 🔒 Athena — 100% Offline Local RAG System

**Your complete local-first knowledge base with zero internet dependency.**

---

## ⚡ **60-Second Quick Start**

```bash
# 1. Restore your 5.8GB knowledge base
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* volumes/weaviate_data/

# 2. Start services (no internet required)
docker-compose -f docker-compose.full-stack.yml up -d weaviate ollama rag-gateway smart-chat openai-compat

# 3. Start UI
cd ui && python3 -m http.server 8080 &

# 4. Open browser
open http://localhost:8080/athena-chat.html

# 5. Select model: athena-rag
# 6. Start chatting! 🎉
```

---

## 🎯 What You Have

### Your Knowledge Base

- **5.8GB** of embedded documents
- Research papers, language files, documentation
- Indexed with BGE embeddings (384-dim)
- **Location:** `/Volumes/Untitled/docker-data/volumes/weaviate_data/`

### Three AI Models

| Model             | Best For              | Backend                    |
| ----------------- | --------------------- | -------------------------- |
| **athena-rag**    | Knowledge base search | Weaviate (Semantic)        |
| **athena-chat**   | Conversational AI     | Ollama (qwen2.5:7b)        |
| **athena-hybrid** | Complex queries       | Weaviate (BM25 + Semantic) |

### Local Infrastructure

- Weaviate (vector database)
- Ollama (local LLM)
- RAG Gateway (search backend)
- Smart Chat (conversational backend)
- OpenAI Adapter (API compatibility)
- Local HTML UI (chat interface)

**100% local. 100% offline. 100% yours.** ✅

---

## 📋 Validation Commands

### Offline Validation

```bash
make offline
```

**Checks:**

- ✅ Weaviate data present
- ✅ No external API calls
- ✅ All services healthy
- ✅ Streaming works
- ✅ Models route correctly

### Full E2E Test

```bash
make e2e-full
```

**10 quality gates** including model routing, streaming, contract validation

### Go-Live Drill

```bash
make go-live-full
```

**14 production-readiness gates** including performance baseline

---

## 🧪 Test in Browser Console

Open http://localhost:8080/athena-chat.html  
Open DevTools (Cmd+Option+I)  
Run:

```javascript
// Non-streaming test
sendOnce("What is RAG?").then(console.log);

// Streaming test
let output = "";
sendStream("Explain embeddings", "athena-rag", (chunk) => {
  output += chunk;
  console.log(chunk);
});

// Different models
sendOnce("Hello!", "athena-chat").then(console.log);
sendOnce("vector search", "athena-hybrid").then(console.log);
```

**Check Network tab:** Should only see `localhost:3000` (no external calls)

---

## 🔧 Configuration

### Environment Variables

```env
# services/openai-compat/.env

# API Settings
API_KEY=your-secret-key               # Optional auth
CORS_ORIGIN=http://localhost:8080     # UI origin
PORT=3000

# Performance
TIMEOUT_MS=30000
DEFAULT_MODE=nearText
DEFAULT_TOP_K=5
ENABLE_STREAMING=true

# Safety (100% Local)
ATHENA_NO_CLOUD=1                     # Block cloud APIs
ATHENA_FAIL_CLOSED=1                  # Fail if no local models
```

### Docker Volumes

```yaml
volumes:
  - ./volumes/weaviate_data:/var/lib/weaviate # 5.8GB corpus
  - ./volumes/ollama:/root/.ollama # Ollama models
```

**All data in `./volumes/` for easy backup!**

---

## 📊 Monitoring

### Metrics

```bash
# Prometheus metrics
curl http://localhost:3000/metrics

# Health + config
curl http://localhost:3000/healthz | jq .
```

### Grafana Dashboard

```bash
# Import grafana-dashboard.json
# View at: http://localhost:3001
```

**9 panels:**

- Request rate
- Error rate
- Latency (p50, p95, p99)
- Model usage
- Backend latency
- Active requests
- Stream status
- Memory usage

---

## 🚨 Alerts

**10 Prometheus alert rules:**

**Critical:**

- High error rate (>0.5%)
- No requests (service down)
- RAG Gateway down
- Weaviate connection errors

**Warning:**

- High latency (>1.5s)
- Stream errors (>2%)
- Empty responses (>5%)
- Backend latency spike
- High memory (>1.5GB)
- High CPU (>80%)

**Configure:** `prometheus-alerts.yml`

---

## 🎓 Usage Examples

### Knowledge Base Search

```
You: What is retrieval augmented generation?

Athena: Based on the knowledge base, here's what I found:

1. RAG (Retrieval-Augmented Generation) combines...
   (Relevance: 95.3%)

2. The technique involves retrieving relevant documents...
   (Relevance: 92.1%)

Would you like me to elaborate on any of these points?
```

### Conversational

```
You: Hello Athena!

Athena: Hello! I'm Athena, your intelligent AI assistant.
I'm powered by local models and have access to a comprehensive
knowledge base. How can I help you today?
```

### A/B Testing

```bash
# Compare retrieval strategies
make rag-delta

# Output:
## RAG Delta Report (bm25 → nearText)

| Metric    | Baseline | Treatment | Δ      |
|-----------|----------|-----------|--------|
| hit@k     | 90.0%    | 97.0%     | +7.0%  ✅ |
| support@k | 85.0%    | 95.0%     | +10.0% ✅ |
```

---

## 🛠️ Troubleshooting

### Services Won't Start

```bash
# Check Docker
docker ps

# View logs
docker logs openai-compat
docker logs rag-gateway

# Restart
docker-compose -f docker-compose.full-stack.yml restart
```

### UI Can't Connect

```bash
# Check adapter
curl http://localhost:3000/health

# Check CORS
# Ensure UI served from http://localhost:8080
# Not file://
```

### No Knowledge Base Results

```bash
# Verify Weaviate data
ls -lh volumes/weaviate_data/

# If empty, restore from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  volumes/weaviate_data/

# Restart Weaviate
docker-compose -f docker-compose.full-stack.yml restart weaviate
```

---

## 📞 Quick Reference

| Task             | Command                                      |
| ---------------- | -------------------------------------------- |
| Validate offline | `make offline`                               |
| Start UI         | `make offline-ui`                            |
| Run E2E tests    | `make e2e`                                   |
| Go-live drill    | `make go-live-full`                          |
| Load test        | `k6 run k6-rag.js`                           |
| View metrics     | `curl http://localhost:3000/metrics`         |
| Check health     | `curl http://localhost:3000/healthz \| jq .` |

---

## 🎉 **YOU'RE READY!**

**Complete offline RAG system with:**

- ✅ 5.8GB knowledge base
- ✅ 3 AI models (RAG, Chat, Hybrid)
- ✅ Beautiful local UI
- ✅ Production monitoring
- ✅ Quality gates
- ✅ Zero internet dependency

**Commands:**

```bash
make offline      # Validate
make offline-ui   # Start UI
```

**Then open http://localhost:8080/athena-chat.html and chat!** 🚀

---

**No cloud. No tracking. Just your knowledge.** ✅
