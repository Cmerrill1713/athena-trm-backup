# ✅ OpenAI-Compatible Adapter — READY TO USE

**Your Athena RAG backend now works with ANY OpenAI-compatible UI** (Open WebUI, ChatBot UI, LibreChat) — zero code changes needed!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd services/openai-compat
npm install
```

### Step 2: Start Your Services

**Option A: Individual Services (Development)**

```bash
# Terminal 1: RAG Gateway
cd services/rag-gateway
python3 app.py  # → Port 8090

# Terminal 2: Smart Chat
cd services/smart_chat
python3 app.py  # → Port 8088

# Terminal 3: OpenAI Adapter
cd services/openai-compat
node server.js  # → Port 3000
```

**Option B: Docker Compose (Production)**

```bash
docker-compose -f docker-compose.openai-compat.yml up -d
```

### Step 3: Test It

```bash
cd services/openai-compat
./test.sh
```

**Expected output:**

```
🧪 Testing OpenAI-Compatible Adapter
======================================

1️⃣  Health Check
{"status":"healthy","service":"openai-compat"} ✅

2️⃣  List Models
{
  "id": "athena-rag",
  "owned_by": "athena"
}
{
  "id": "athena-chat",
  "owned_by": "athena"
}
{
  "id": "athena-hybrid",
  "owned_by": "athena"
} ✅

3️⃣  Test RAG Model
"Based on the knowledge base, here's what I found:..." ✅

4️⃣  Test Chat Model
"Hello! I'm Athena, your intelligent AI assistant..." ✅

====================================
✅ Tests complete!
```

---

## 🎨 Connect to UIs

### Open WebUI

1. Open Open WebUI in browser
2. Go to **Settings → Connections**
3. Add **Custom OpenAI Connection**:
   - **Name:** Athena
   - **Base URL:** `http://localhost:3000/v1`
   - **API Key:** `dummy` (any value works)
4. Go to **Chat** and select model: `athena-rag`

**Screenshot locations in UI:**

- Settings → Connections → Add Connection
- Select "OpenAI Compatible"
- Enter base URL

### ChatBot UI (Next.js)

Create `.env.local`:

```env
OPENAI_API_HOST=http://localhost:3000/v1
OPENAI_API_KEY=dummy
DEFAULT_MODEL=athena-rag
```

Restart ChatBot UI:

```bash
npm run dev
```

### LibreChat

Edit `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: "Athena"
      apiKey: "dummy"
      baseURL: "http://localhost:3000/v1"
      models:
        default:
          - "athena-rag"
          - "athena-chat"
          - "athena-hybrid"
      titleConvo: true
      titleModel: "athena-chat"
      summarize: false
      summaryModel: "athena-chat"
```

Restart LibreChat:

```bash
docker-compose restart librechat
```

---

## 📊 Available Models

| Model             | Backend                     | Use Case               | Best For                                 |
| ----------------- | --------------------------- | ---------------------- | ---------------------------------------- |
| **athena-rag**    | RAG Gateway (semantic)      | Knowledge base queries | Fact finding, documentation lookup       |
| **athena-chat**   | Smart Chat (Ollama)         | Conversational         | General chat, personality-driven         |
| **athena-hybrid** | RAG Gateway (BM25+semantic) | Best of both worlds    | Complex queries needing exact + semantic |

**Switch models in your UI's model selector!**

---

## 🧪 Manual Testing

### Basic Chat

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [
      {"role": "user", "content": "Hello Athena!"}
    ]
  }' | jq '.choices[0].message.content'
```

### RAG Query

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-rag",
    "messages": [
      {"role": "user", "content": "What is vector search?"}
    ],
    "top_k": 5
  }' | jq '.choices[0].message.content'
```

### Streaming

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "athena-chat",
    "messages": [{"role": "user", "content": "Tell me a joke"}],
    "stream": true
  }'
```

---

## 🔧 Configuration

### Environment Variables

Create `services/openai-compat/.env`:

```env
RAG_API_BASE_URL=http://127.0.0.1:8090
CHAT_API_BASE_URL=http://127.0.0.1:8088
PORT=3000
NODE_ENV=production
```

### Advanced Options

Pass RAG-specific params in the request:

```json
{
  "model": "athena-rag",
  "messages": [...],
  "top_k": 10,          // Return more results
  "mode": "hybrid"      // Override to hybrid search
}
```

---

## 🐳 Docker Deployment

### Start Full Stack

```bash
docker-compose -f docker-compose.openai-compat.yml up -d
```

**Services started:**

- Weaviate (port 8080)
- RAG Gateway (port 8090)
- Smart Chat (port 8088)
- OpenAI Adapter (port 3000) ← **Point your UI here**

### Check Status

```bash
docker-compose -f docker-compose.openai-compat.yml ps
```

### View Logs

```bash
docker-compose -f docker-compose.openai-compat.yml logs -f openai-compat
```

---

## 🛠️ Troubleshooting

### "Connection refused" on port 3000

**Problem:** Adapter not running.

**Fix:**

```bash
cd services/openai-compat
npm install
node server.js
```

### "RAG API error: 500"

**Problem:** RAG Gateway not running or can't reach Weaviate.

**Fix:**

```bash
# Check RAG Gateway
curl http://127.0.0.1:8090/health

# Check Weaviate
curl http://127.0.0.1:8080/v1/.well-known/ready
```

### UI shows "Invalid API key"

**Problem:** Some UIs require an API key field.

**Fix:** Enter `dummy` or `sk-athena` — it's not validated.

### Empty responses from RAG

**Problem:** Weaviate has no data.

**Fix:** Import your 5.8GB corpus from external drive:

```bash
# Stop Weaviate
docker-compose down weaviate

# Restore data from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  ./volumes/weaviate_data/

# Restart
docker-compose up -d weaviate
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────┐
│  Chat UI (Open WebUI, ChatBot UI, etc)     │
│  http://localhost:3000/v1                   │
└──────────────────┬──────────────────────────┘
                   │
                   │ OpenAI-compatible API
                   ▼
    ┌──────────────────────────┐
    │  OpenAI-Compat Adapter   │
    │  Port 3000               │
    │  (Node.js/Express)       │
    └──────┬───────────┬───────┘
           │           │
    ┌──────┘           └──────┐
    │                          │
    ▼                          ▼
┌──────────────┐       ┌──────────────┐
│ RAG Gateway  │       │ Smart Chat   │
│ Port 8090    │       │ Port 8088    │
│ (Python)     │       │ (Python)     │
└──────┬───────┘       └──────┬───────┘
       │                      │
       ▼                      ▼
   Weaviate              Ollama/Router
   (5.8GB corpus)        (qwen2.5:7b)
```

---

## 🎯 What You Get

✅ **100% Local-First** — No cloud APIs, all data stays local  
✅ **Zero UI Changes** — Works with stock Open WebUI, ChatBot UI  
✅ **Multi-Model** — Switch between RAG, Chat, Hybrid in UI  
✅ **Streaming Support** — Real-time token streaming  
✅ **Production Ready** — Docker deployment, health checks  
✅ **Compatible** — OpenAI API format (drop-in replacement)

---

## 🎓 Next Steps

### 1. Import Your Corpus

You have 5.8GB of embedded documents on your external drive. Restore them:

```bash
# Copy from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data \
  ./volumes/

# Or mount directly in docker-compose:
# volumes:
#   - /Volumes/Untitled/docker-data/volumes/weaviate_data:/var/lib/weaviate
```

### 2. Customize Responses

Edit `services/openai-compat/server.js`:

- Modify `callRAG()` function to format responses differently
- Add custom system prompts
- Implement conversation memory

### 3. Add Authentication

Add real auth if exposing publicly:

```javascript
// server.js
app.use((req, res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (token !== process.env.VALID_API_KEY) {
    return res.status(401).json({ error: "Invalid API key" });
  }
  next();
});
```

### 4. Monitor Usage

Add Prometheus metrics:

```javascript
import client from "prom-client";
const requestCounter = new client.Counter({
  name: "openai_compat_requests_total",
  help: "Total requests",
  labelNames: ["model", "status"],
});
```

---

## 📚 Related Docs

- [Services README](services/openai-compat/README.md)
- [RAG Gateway](services/rag-gateway/README.md)
- [Smart Chat](services/smart_chat/README.md)
- [RAG Evaluation](RAG_EVALUATION_README.md)
- [RAG Delta Reports](docs/RAG_DELTA_REPORTS.md)

---

## 🎉 Success!

**You now have a fully local, OpenAI-compatible RAG system!**

Use with:

- Open WebUI
- ChatBot UI
- LibreChat
- Continue.dev
- Any OpenAI-compatible client

**No cloud. No leaks. Just your infrastructure.** ✅

---

**Questions?** Check `services/openai-compat/README.md` or test with `./test.sh`
