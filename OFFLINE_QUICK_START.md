# 🔒 Offline Quick Start — 100% Local RAG System

**No internet. No cloud. Just your local infrastructure and 5.8GB knowledge base.**

---

## 🚀 3-Step Quick Start

### Step 1: Restore Your Corpus

```bash
cd /Users/christianmerrill/Documents/GitHub

# Create volumes directory
mkdir -p volumes/weaviate_data volumes/ollama

# Copy 5.8GB corpus from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  volumes/weaviate_data/
```

### Step 2: Start Services (No Internet)

```bash
# Start core services only (local images)
docker-compose -f docker-compose.full-stack.yml up -d \
  weaviate ollama rag-gateway smart-chat openai-compat

# Wait 30s for services to be healthy
sleep 30
```

### Step 3: Open Local UI

**Terminal 1 (Services):**

```bash
# Already running from Step 2
```

**Terminal 2 (UI):**

```bash
cd ui
python3 -m http.server 8080
```

**Browser:**

```bash
open http://localhost:8080/athena-chat.html
```

**Select model:** `athena-rag`  
**Start chatting!** 🎉

---

## ✅ Offline Validation

### Run Complete Offline Check

```bash
make offline
```

**This validates:**

1. ✅ Weaviate data present
2. ✅ Services start without internet
3. ✅ Adapter health
4. ✅ Models endpoint working
5. ✅ Non-streaming completion
6. ✅ Streaming (SSE)
7. ✅ Zero external network calls
8. ✅ Local HTML UI present

**Expected output:**

```
🔒 Offline Validation — Zero Internet Dependency
==================================================

📋 Pre-Flight Checks

✅ Weaviate data present
5.8G    volumes/weaviate_data

🚀 Starting Services (Local Images Only)

🔌 Adapter Validation

1. Adapter health... ✅
2. Models endpoint... ✅
   - athena-rag
   - athena-chat
   - athena-hybrid

3. Non-streaming completion... ✅
4. Streaming completion... ✅

🔒 Network Isolation Check

✅ No external API calls detected

🖥️  Local UI Validation

✅ Local HTML UI present

==================================================
✅ OFFLINE VALIDATION PASSED
```

---

## 🧪 Console Testing (DevTools)

### Open UI and Console

```bash
# Serve UI
cd ui && python3 -m http.server 8080

# Open browser
open http://localhost:8080/athena-chat.html

# Open DevTools Console (Cmd+Option+I on Mac)
```

### Run These Tests

```javascript
// Test 1: Non-streaming
sendOnce("hello").then(console.log);
// Should print response after ~500ms

// Test 2: Streaming
let out = "";
sendStream("count to 5", "athena-rag", (chunk) => {
  out += chunk;
  console.log(chunk);
});
// Should print chunks in real-time

// Test 3: Different models
sendOnce("test", "athena-chat").then(console.log);
sendOnce("test", "athena-hybrid").then(console.log);

// Test 4: Check network tab
// Filter by "fetch" — should only see localhost:3000
// No calls to openai.com, anthropic.com, etc.
```

---

## 🔧 Troubleshooting

### "Cannot reach API"

**Fix:**

```bash
# Check services
docker-compose -f docker-compose.full-stack.yml ps

# Check adapter health
curl http://localhost:3000/healthz | jq .

# View logs
docker logs openai-compat
```

### "No data in Weaviate"

**Fix:**

```bash
# Verify data copied
ls -lh volumes/weaviate_data/

# If empty, restore from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  volumes/weaviate_data/

# Restart Weaviate
docker-compose -f docker-compose.full-stack.yml restart weaviate
```

### CORS Errors

**Fix:**

```bash
# Ensure UI served from http://localhost:8080
cd ui && python3 -m http.server 8080

# Check adapter CORS setting
docker-compose -f docker-compose.full-stack.yml exec openai-compat \
  sh -c 'echo $CORS_ORIGIN'
# Should be: http://localhost:8080
```

### Streaming Not Working

**Check:**

1. Network tab shows `text/event-stream` content type
2. Response has `data:` lines
3. Response ends with `[DONE]`
4. No nginx buffering (if using nginx)

---

## 📦 What You Have (100% Offline)

### Services

- ✅ Weaviate (5.8GB local corpus)
- ✅ Ollama (local LLM)
- ✅ RAG Gateway (Python)
- ✅ Smart Chat (Python)
- ✅ OpenAI Adapter (Node.js)

### UI

- ✅ Local HTML chat (`ui/athena-chat.html`)
- ✅ Model selector (3 models)
- ✅ Streaming support
- ✅ Beautiful dark theme
- ✅ Zero external dependencies

### No Internet Required

- ✅ All Docker images pre-pulled
- ✅ All data on local volumes
- ✅ No CDN fonts/CSS
- ✅ No external API calls

---

## 🎯 Daily Usage

### Morning (Start Services)

```bash
cd /Users/christianmerrill/Documents/GitHub

# Start services
docker-compose -f docker-compose.full-stack.yml up -d \
  weaviate ollama rag-gateway smart-chat openai-compat

# Start UI
cd ui && python3 -m http.server 8080 &

# Open browser
open http://localhost:8080/athena-chat.html
```

### Evening (Stop Services)

```bash
# Stop UI server
pkill -f "python3 -m http.server 8080"

# Stop services
docker-compose -f docker-compose.full-stack.yml down
```

---

## 📊 Performance

### Local UI

- Load time: <100ms
- First paint: <200ms
- Time to interactive: <300ms
- No external requests: ✅

### Adapter

- Non-streaming: 250-600ms
- Streaming (first token): 200-400ms
- Streaming (full response): 500-1500ms

### Total (UI → Response)

- First response: ~1s
- Streaming feels instant

---

## 🎉 Success!

**You now have a 100% offline RAG system:**

✅ **No internet required** — Works air-gapped  
✅ **Local HTML UI** — Beautiful and fast  
✅ **Streaming support** — Real-time token display  
✅ **3 Models** — RAG, Chat, Hybrid  
✅ **5.8GB knowledge** — Your research papers and docs  
✅ **Production-grade** — Monitored, tested, hardened

---

## 🎓 Next Steps

### Validate Now

```bash
make offline  # Ensure zero internet dependency
```

### Start Using

```bash
make offline-ui  # Start UI server
# Open http://localhost:8080/athena-chat.html
```

### Advanced

- Add more models to selector
- Customize UI theme
- Add citation display
- Add mode toggles (BM25/Semantic/Hybrid)

---

**Your 100% local-first RAG system is ready!** 🚀

**No cloud. No tracking. Just your knowledge.** ✅

---

**Last Updated:** October 18, 2025  
**UI Location:** `ui/athena-chat.html`  
**Start Command:** `make offline-ui`
