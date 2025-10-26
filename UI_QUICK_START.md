# 🖥️ UI Quick Start — Access Your AGI-RAG System

**You have 3 UI options ready to use!**

---

## ⚡ Option 1: Local HTML Chat UI (100% Offline)

**Location:** `ui/athena-chat.html`

**Start it:**

```bash
# Serve the UI
python3 -m http.server 8080 --directory ui

# Open in browser
open http://localhost:8080/athena-chat.html
```

**Features:**

- ✅ 100% local (no internet required)
- ✅ PWA-ready (installable on iPhone)
- ✅ Streaming support
- ✅ Multiple models (athena-rag, athena-chat, athena-hybrid)
- ✅ Clean modern design
- ✅ Markdown rendering
- ✅ Citation display

**How to use:**

1. Open `http://localhost:8080/athena-chat.html` in your browser
2. Select model (athena-rag recommended for KB queries)
3. Ask questions like:
   - "What is TRM?"
   - "Explain recursive reasoning"
   - "How does AGI Core work?"
4. Get answers with citations from your knowledge base!

---

## 📱 Option 2: Install as iPhone PWA

**Steps:**

1. Open `https://your-domain.com/athena-chat.html` on iPhone (needs HTTPS)
2. Tap Share → Add to Home Screen
3. App icon appears on home screen
4. Launch like native app!

**For local dev with HTTPS:**

```bash
# Install mkcert
brew install mkcert
mkcert -install

# Generate cert
mkcert localhost 127.0.0.1

# Update nginx.conf or use HTTPS proxy
# Then access via https://localhost/athena-chat.html
```

---

## 🌐 Option 3: Open WebUI (Optional - Needs Manual Setup)

Open WebUI was disabled due to internet dependency.

**To use it (if desired):**

```bash
# 1. Pull image on a machine with internet
docker pull ghcr.io/open-webui/open-webui:main

# 2. Save image
docker save ghcr.io/open-webui/open-webui:main > open-webui.tar

# 3. Transfer to your machine and load
docker load < open-webui.tar

# 4. Start it
docker run -d \
  -p 8081:8080 \
  -e OPENAI_API_BASE_URL=http://host.docker.internal:3000/v1 \
  -e OPENAI_API_KEY=not-needed \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main

# 5. Open
open http://localhost:8081
```

---

## 🎯 Recommended: Use Local HTML UI

**Why:**

- ✅ Already built and working
- ✅ 100% offline
- ✅ No docker image pulls
- ✅ PWA-ready for iPhone
- ✅ Direct integration with your adapter

**Start now:**

```bash
# 1. Start UI server
python3 -m http.server 8080 --directory ui &

# 2. Open UI
open http://localhost:8080/athena-chat.html

# 3. Test it!
# Ask: "What is TRM recursive reasoning?"
# Should get: Answer with citations from DocsV2
```

---

## 🧪 Test the UI

### **Test 1: Basic Chat**

1. Open `http://localhost:8080/athena-chat.html`
2. Select model: `athena-rag`
3. Ask: "What is TRM?"
4. Should return answer citing "TRM Recursive Models"

### **Test 2: Streaming**

1. Same UI
2. Enable streaming (default)
3. Ask longer question
4. Watch tokens stream in real-time

### **Test 3: Model Switching**

1. Try `athena-chat` (no RAG, pure LLM)
2. Try `athena-hybrid` (RAG + LLM combined)
3. Compare responses

---

## 📊 UI Features

| Feature     | Local HTML | Open WebUI                  |
| ----------- | ---------- | --------------------------- |
| Offline     | ✅ YES     | ❌ Needs internet for image |
| PWA         | ✅ YES     | ✅ YES                      |
| Streaming   | ✅ YES     | ✅ YES                      |
| Citations   | ✅ YES     | ⚠️ Limited                  |
| Setup Time  | ⚡ Instant | 🐌 10-15 min                |
| iPhone      | ✅ PWA     | ✅ PWA                      |
| Local-First | ✅ 100%    | ⚠️ Partial                  |

---

## 🚀 Quick Commands

```bash
# Start UI server
python3 -m http.server 8080 --directory ui &

# Open UI
open http://localhost:8080/athena-chat.html

# Test in terminal
curl http://localhost:3000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"athena-rag","messages":[{"role":"user","content":"What is TRM?"}]}' \
  | jq -r '.choices[0].message.content'

# Stop UI server
pkill -f "http.server 8080"
```

---

## 🎨 UI Customization

The local HTML UI is in `ui/athena-chat.html` - you can customize:

- Colors/theme
- Model list
- Default settings
- Citation format
- Streaming behavior

It's just one HTML file - easy to modify!

---

## ✅ Current Status

```
✅ Local HTML UI ready (ui/athena-chat.html)
✅ PWA manifest configured (ui/manifest.json)
✅ Service worker ready (ui/sw.js)
✅ OpenAI Adapter serving on :3000
✅ RAG Gateway serving on :8088
```

**Your UI is ready to use RIGHT NOW!**

---

## 🔥 Start Using It

```bash
# One command:
python3 -m http.server 8080 --directory ui &
open http://localhost:8080/athena-chat.html

# Then ask your AGI system questions!
```

**That's it!** Your AGI-RAG system now has a beautiful UI! 🎨
