# 🖥️ Local UI Options — No Internet Required

**Your OpenAI-compatible adapter works with these 100% local UIs.**

---

## 🚫 Problem: Open WebUI Requires Internet

Open WebUI is great, but it requires pulling from `ghcr.io` (violates `ATHENA_NO_CLOUD=1`).

---

## ✅ Solution: Local-First UI Options

### Option 1: Simple HTML Chat Interface (Included)

**Use the included HTML/JS chat UI:**

```bash
# Serve the UI
cd ui
python3 -m http.server 8080

# Open browser
open http://localhost:8080/chat.html
```

**Features:**

- ✅ 100% local (HTML + vanilla JS)
- ✅ No build required
- ✅ Connects to adapter at http://localhost:3000/v1
- ✅ Model selector (athena-rag, athena-chat, athena-hybrid)
- ✅ Streaming support
- ✅ Conversation history

Let me create this now...

### Option 2: Continue.dev (VS Code Extension)

**Perfect for code documentation search!**

```json
// ~/.continue/config.json
{
  "models": [
    {
      "title": "Athena RAG",
      "provider": "openai",
      "model": "athena-rag",
      "apiBase": "http://localhost:3000/v1",
      "apiKey": "dummy"
    }
  ]
}
```

**Install:**

1. Install Continue.dev extension in VS Code
2. Add config above
3. Use Cmd+L to chat with your knowledge base!

### Option 3: ChatGPT-like Web UI (Static HTML)

**Pre-built, no npm required:**

```bash
# Clone a static ChatGPT UI
git clone https://github.com/cogentapps/chat-with-gpt
cd chat-with-gpt

# Edit config.js
# Change API_BASE to: http://localhost:3000/v1

# Serve
python3 -m http.server 8080
open http://localhost:8080
```

### Option 4: Terminal UI (0 dependencies)

**Quick curl wrapper:**

```bash
# Save as ~/bin/athena-chat
#!/bin/bash
while true; do
  echo -n "You: "
  read -r query
  [ -z "$query" ] && break

  echo "Athena: "
  curl -s http://localhost:3000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"athena-rag\",\"messages\":[{\"role\":\"user\",\"content\":\"$query\"}]}" \
    | jq -r '.choices[0].message.content'
  echo ""
done

# Usage:
chmod +x ~/bin/athena-chat
athena-chat
```

---

## 🎯 Recommended: Simple HTML UI

Let me create a beautiful, local-first HTML chat interface for you...

**Features:**

- ✅ Works offline (no external deps)
- ✅ Model selector
- ✅ Streaming support
- ✅ Conversation history
- ✅ Markdown rendering
- ✅ Dark/light theme

---

## 🔧 If You Really Want Open WebUI

**Pre-download on a machine with internet:**

```bash
# On internet-connected machine
docker pull ghcr.io/open-webui/open-webui:main
docker save ghcr.io/open-webui/open-webui:main | gzip > open-webui.tar.gz

# Transfer to your machine (USB, etc)

# Load on your machine
docker load < open-webui.tar.gz

# Now uncomment the open-webui service in docker-compose.full-stack.yml
```

---

**Let me create the simple HTML UI for you now...**
