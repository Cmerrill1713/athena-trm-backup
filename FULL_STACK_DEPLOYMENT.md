# 🚀 Full Stack Deployment — Local RAG with Open WebUI

**Complete local-first RAG system with OpenAI-compatible API and beautiful UI.**

---

## 🎯 What You Get

```
┌────────────────────────────────────────┐
│  Open WebUI (Port 80 or 8080)         │
│  Beautiful chat interface              │
└──────────────┬─────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  OpenAI Adapter      │
    │  Port 3000           │
    └─────┬──────────┬─────┘
          │          │
    ┌─────┘          └─────┐
    │                      │
    ▼                      ▼
┌─────────┐          ┌──────────┐
│RAG:8090 │          │Chat:8088 │
└────┬────┘          └────┬─────┘
     │                    │
     ▼                    ▼
 Weaviate             Ollama
 (5.8GB)             (qwen2.5)
```

---

## 🚀 Quick Start

### 1. Start Full Stack

```bash
# Start everything
docker-compose -f docker-compose.full-stack.yml up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.full-stack.yml ps
```

### 2. Access Open WebUI

Open browser: **http://localhost:8080**

**First time setup:**

1. Create admin account (if signup enabled)
2. Go to Settings → Connections
3. Verify connection to `http://openai-compat:3000/v1`
4. Select model: **athena-rag**, **athena-chat**, or **athena-hybrid**

### 3. Start Chatting!

Try these queries:

- **"What is retrieval augmented generation?"** (tests RAG)
- **"Hello Athena, introduce yourself"** (tests Chat)
- **"Explain vector embeddings"** (tests knowledge base)

---

## 🧪 Smoke Tests

### Before UI Access

```bash
cd services/openai-compat
./smoke-test.sh
```

**Expected output:**

```
🧪 OpenAI Adapter Smoke Tests
======================================

1️⃣  Health Check
✅ Health check passed

2️⃣  List Models
✅ Models endpoint working
   Available models:
   - athena-rag
   - athena-chat
   - athena-hybrid

3️⃣  Non-Streaming Chat Completion
✅ Non-streaming completion works

4️⃣  Streaming Chat Completion
✅ Streaming works

5️⃣  Hybrid Model Test
✅ Hybrid model routing works

6️⃣  Backend Routing Verification
   - athena-rag: rag_gateway (nearText)
   - athena-chat: smart_chat
   - athena-hybrid: rag_gateway (hybrid)
✅ All models route correctly

======================================
✅ All smoke tests passed!
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```env
# Backend Configuration
RAG_API_TOKEN=                      # Optional bearer token
WEAVIATE_URL=http://weaviate:8080
OLLAMA_URL=http://ollama:11434

# Adapter Tuning
TIMEOUT_MS=30000                    # 30 second timeout
ENABLE_STREAMING=true               # Enable SSE streaming
DEFAULT_MODE=nearText               # bm25, nearText, hybrid
DEFAULT_TOP_K=5                     # Number of results
CORS_ORIGIN=*                       # CORS policy

# Open WebUI
WEBUI_NAME=Athena RAG              # UI title
ENABLE_SIGNUP=false                 # Disable public signup
DEFAULT_MODELS=athena-rag,athena-chat,athena-hybrid
```

### Model Selection in UI

| Model             | Use For                | Expected Behavior                         |
| ----------------- | ---------------------- | ----------------------------------------- |
| **athena-rag**    | Knowledge base queries | Returns docs from Weaviate with citations |
| **athena-chat**   | General conversation   | Conversational with Athena personality    |
| **athena-hybrid** | Complex queries        | BM25 + semantic for best recall           |

---

## 📊 Service Ports

| Service          | Port            | Purpose                 |
| ---------------- | --------------- | ----------------------- |
| Open WebUI       | 8080            | Main chat interface     |
| OpenAI Adapter   | 3000            | API compatibility layer |
| RAG Gateway      | 8090            | Vector search backend   |
| Smart Chat       | 8088            | Conversational backend  |
| Weaviate         | 8080 (internal) | Vector database         |
| Ollama           | 11434           | Local LLM inference     |
| Nginx (optional) | 80              | Reverse proxy           |

---

## 🐳 Advanced: With Nginx Proxy

### Start with Nginx

```bash
docker-compose -f docker-compose.full-stack.yml --profile with-nginx up -d
```

**Benefits:**

- Single entry point (port 80)
- Proper streaming support
- CORS handling
- SSL termination (add certs)

**Access:**

- UI: http://localhost/
- API: http://localhost/v1/

---

## 🔍 Troubleshooting

### Services Not Starting

**Check logs:**

```bash
docker-compose -f docker-compose.full-stack.yml logs -f openai-compat
docker-compose -f docker-compose.full-stack.yml logs -f rag-gateway
```

**Check health:**

```bash
curl http://localhost:3000/healthz | jq .
```

### Open WebUI Can't Connect

**Problem:** "Failed to connect to OpenAI API"

**Fix:**

1. Verify adapter is healthy: `curl http://localhost:3000/health`
2. Check Open WebUI settings:
   - Base URL: `http://openai-compat:3000/v1` (not localhost!)
   - API Key: any non-empty value
3. Check docker network: `docker network inspect github_athena`

### No Streaming in UI

**Problem:** Responses appear all at once, not token-by-token

**Fix:**

1. Check `ENABLE_STREAMING=true` in `.env`
2. Verify adapter logs show `Content-Type: text/event-stream`
3. If using Nginx, ensure `proxy_buffering off`

### Empty RAG Responses

**Problem:** "I couldn't find relevant information"

**Fix:** Restore your 5.8GB Weaviate corpus:

```bash
# Stop services
docker-compose -f docker-compose.full-stack.yml down

# Restore from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  ./volumes/weaviate_data/

# Restart
docker-compose -f docker-compose.full-stack.yml up -d weaviate
```

### Ollama Models Not Loaded

**Download qwen2.5:7b:**

```bash
docker-compose -f docker-compose.full-stack.yml exec ollama \
  ollama pull qwen2.5:7b
```

---

## 🎯 Production Checklist

### Security

- [ ] Disable `ENABLE_SIGNUP=false` in Open WebUI
- [ ] Add authentication to adapter (implement `RAG_API_TOKEN` check)
- [ ] Use Nginx with SSL/TLS certificates
- [ ] Restrict CORS to specific origins
- [ ] Run services as non-root users
- [ ] Enable Docker security features (AppArmor, seccomp)

### Performance

- [ ] Tune `TIMEOUT_MS` based on your queries
- [ ] Adjust `DEFAULT_TOP_K` for accuracy vs speed
- [ ] Monitor resource usage: `docker stats`
- [ ] Add Redis caching for frequent queries
- [ ] Use GPU for Ollama (uncomment GPU config in compose)

### Monitoring

- [ ] Add Prometheus metrics endpoint to adapter
- [ ] Set up Grafana dashboards
- [ ] Configure alerting on service health
- [ ] Log aggregation (ELK, Loki)
- [ ] Track response times and error rates

### Backup

- [ ] Backup Weaviate data: `./volumes/weaviate_data/`
- [ ] Backup Open WebUI data: `./data/open-webui/`
- [ ] Backup Ollama models: `./volumes/ollama_data/`
- [ ] Document restore procedures

---

## 📈 Scaling

### Vertical Scaling

Increase resources in `docker-compose.full-stack.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "4.0"
      memory: 8G
    reservations:
      cpus: "2.0"
      memory: 4G
```

### Horizontal Scaling

**Multiple adapter instances:**

```yaml
openai-compat:
  deploy:
    replicas: 3
```

**Load balance with Nginx:**

```nginx
upstream openai_backend {
    server openai-compat1:3000;
    server openai-compat2:3000;
    server openai-compat3:3000;
}
```

---

## 🎓 Usage Examples

### In Open WebUI

**Knowledge Base Query:**

```
User: What are the best practices for RAG evaluation?

Athena: Based on the knowledge base, here's what I found:

1. Use hit@k metric to measure retrieval accuracy...
   (Relevance: 95.3%)

2. Implement semantic search with BM25 fallback...
   (Relevance: 92.1%)

Would you like me to elaborate on any of these points?
```

**Conversational:**

```
User: Hello Athena!

Athena: Hello! I'm Athena, your intelligent AI assistant.
I'm powered by local models and have access to a comprehensive
knowledge base. How can I help you today?
```

### Direct API Access

```bash
# RAG query
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-rag",
    "messages": [{"role":"user","content":"vector embeddings"}],
    "top_k": 5
  }' | jq '.choices[0].message.content'

# Chat query
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [{"role":"user","content":"explain RAG simply"}]
  }' | jq '.choices[0].message.content'
```

---

## 🎉 Success!

You now have:

✅ **Complete local RAG system** (Weaviate + Ollama)  
✅ **OpenAI-compatible API** (works with any client)  
✅ **Beautiful UI** (Open WebUI)  
✅ **3 models** (RAG, Chat, Hybrid)  
✅ **Streaming support** (real-time responses)  
✅ **Production-ready** (Docker, health checks, Nginx)

**No cloud. No data leaks. Just your infrastructure.** 🚀

---

## 📚 Next Steps

1. **Restore your 5.8GB corpus** from external drive
2. **Customize Athena's personality** in `smart-chat/app.py`
3. **Add authentication** for production use
4. **Set up monitoring** with Prometheus/Grafana
5. **Try other UIs** (ChatBot UI, LibreChat, Continue.dev)

---

**Questions?** Check the troubleshooting section or run `./smoke-test.sh` to diagnose issues.
