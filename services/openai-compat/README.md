# OpenAI-Compatible Adapter for Athena

**Drop-in OpenAI API adapter** that makes your Athena RAG backend compatible with off-the-shelf UIs like Open WebUI, ChatBot UI, and LibreChat—without modifying any UI code.

---

## 🎯 What It Does

Wraps your existing services:

- `RAG Gateway` (port 8090) → `/query` endpoint
- `Smart Chat` (port 8088) → `/chat` endpoint

And exposes them as OpenAI-compatible endpoints:

- `/v1/chat/completions` (OpenAI format)
- `/v1/models` (lists available models)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd services/openai-compat
npm install
```

### 2. Start Your Backend Services

```bash
# Terminal 1: RAG Gateway
cd services/rag-gateway
python3 app.py  # Port 8090

# Terminal 2: Smart Chat
cd services/smart_chat
python3 app.py  # Port 8088
```

### 3. Start the Adapter

```bash
# Terminal 3: OpenAI Adapter
cd services/openai-compat
RAG_API_BASE_URL=http://127.0.0.1:8090 \
CHAT_API_BASE_URL=http://127.0.0.1:8088 \
node server.js
```

**Output:**

```
🚀 OpenAI-Compatible Adapter running on http://localhost:3000
📡 RAG API: http://127.0.0.1:8090
💬 Chat API: http://127.0.0.1:8088
```

### 4. Test It

```bash
curl http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-rag",
    "messages": [
      {"role": "user", "content": "What is RAG?"}
    ]
  }'
```

---

## 🎨 Connect to UIs

### Open WebUI

1. Open Open WebUI settings
2. Set **OpenAI Base URL**: `http://localhost:3000/v1`
3. Set **API Key**: `dummy` (not checked)
4. Select model: **athena-rag** or **athena-chat**

### ChatBot UI (Next.js)

```env
# .env.local
OPENAI_API_HOST=http://localhost:3000/v1
OPENAI_API_KEY=dummy
DEFAULT_MODEL=athena-rag
```

### LibreChat

```yaml
# librechat.yaml
endpoints:
  custom:
    - name: "Athena"
      apiKey: "dummy"
      baseURL: "http://localhost:3000/v1"
      models:
        default: ["athena-rag", "athena-chat", "athena-hybrid"]
```

---

## 📊 Available Models

| Model ID        | Backend                | Description                     |
| --------------- | ---------------------- | ------------------------------- |
| `athena-rag`    | RAG Gateway (nearText) | Semantic search via Weaviate    |
| `athena-chat`   | Smart Chat             | Conversational with personality |
| `athena-hybrid` | RAG Gateway (hybrid)   | BM25 + Semantic combined        |

**Switch modes by changing the model name in your UI!**

---

## 🔧 Configuration

### Environment Variables

| Variable            | Default                 | Description           |
| ------------------- | ----------------------- | --------------------- |
| `RAG_API_BASE_URL`  | `http://127.0.0.1:8090` | RAG Gateway endpoint  |
| `CHAT_API_BASE_URL` | `http://127.0.0.1:8088` | Smart Chat endpoint   |
| `RAG_API_TOKEN`     | (empty)                 | Optional bearer token |
| `PORT`              | `3000`                  | Adapter port          |

### Advanced Options

Pass extra parameters via the `model` field:

```json
{
  "model": "athena-rag",
  "messages": [...],
  "top_k": 10,
  "mode": "hybrid"
}
```

---

## 🐳 Docker Deployment

### docker-compose.yml

```yaml
version: "3.8"
services:
  rag-gateway:
    build: ../rag-gateway
    ports: ["8090:8090"]
    environment:
      WEAVIATE_URL: "http://weaviate:8080"

  smart-chat:
    build: ../smart_chat
    ports: ["8088:8088"]
    environment:
      OLLAMA_URL: "http://ollama:11434"

  openai-compat:
    build: .
    ports: ["3000:3000"]
    environment:
      RAG_API_BASE_URL: "http://rag-gateway:8090"
      CHAT_API_BASE_URL: "http://smart-chat:8088"
    depends_on:
      - rag-gateway
      - smart-chat
```

### Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY server.js ./

EXPOSE 3000
CMD ["node", "server.js"]
```

---

## 🎯 Features

### ✅ OpenAI Compatibility

- `/v1/chat/completions` endpoint
- `/v1/models` listing
- Streaming support (`stream: true`)
- Standard error responses

### ✅ Multi-Backend Routing

- `athena-rag` → RAG Gateway (semantic search)
- `athena-chat` → Smart Chat (conversational)
- `athena-hybrid` → RAG Gateway (BM25 + semantic)

### ✅ Zero UI Changes

- Works with Open WebUI, ChatBot UI, LibreChat out-of-the-box
- Just point UI's "OpenAI Base URL" to adapter

### ✅ Local-First

- No external API calls
- All data stays on your infrastructure
- Adheres to `ATHENA_NO_CLOUD=1` policy

---

## 🔍 Testing

### Manual Test

```bash
# Test RAG model
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-rag",
    "messages": [{"role": "user", "content": "explain embeddings"}]
  }' | jq .

# Test Chat model
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [{"role": "user", "content": "hello athena"}]
  }' | jq .

# Test streaming
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [{"role": "user", "content": "count to 5"}],
    "stream": true
  }'
```

### List Models

```bash
curl http://localhost:3000/v1/models | jq .
```

---

## 🛠️ Troubleshooting

### "Connection refused" errors

**Problem:** Adapter can't reach backend services.

**Fix:** Verify backends are running:

```bash
curl http://127.0.0.1:8090/health  # RAG Gateway
curl http://127.0.0.1:8088/health  # Smart Chat
```

### UI shows "Invalid API key"

**Problem:** Some UIs require an API key field.

**Fix:** Enter any dummy value (e.g., `sk-athena`) — adapter doesn't validate it.

### Slow responses

**Problem:** RAG queries taking too long.

**Fix:** Reduce `top_k`:

```json
{ "model": "athena-rag", "top_k": 3 }
```

---

## 📚 Related Documentation

- [RAG Gateway](../rag-gateway/README.md)
- [Smart Chat](../smart_chat/README.md)
- [RAG Evaluation System](../../docs/RAG_EVALUATION_README.md)
- [RAG Delta Reports](../../docs/RAG_DELTA_REPORTS.md)

---

## 🎉 Success!

You now have a **100% local-first** chat system that works with any OpenAI-compatible UI!

**No cloud APIs. No data leaks. Just your infrastructure.** ✅
