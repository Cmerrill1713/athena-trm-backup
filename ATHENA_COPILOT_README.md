# 🤖 Athena Universal Copilot

**Editor-agnostic coding assistant that automatically gathers the right context**

---

## 🎯 **What This Is**

Athena is now a **universal coding copilot** that works with:
- ✅ VS Code / Cursor
- ✅ Neovim / Vim
- ✅ JetBrains (IntelliJ, PyCharm, etc.)
- ✅ Xcode
- ✅ Terminal / CLI

**No more hand-curating prompts!** Athena automatically:
- Watches your repo for changes
- Gathers relevant code context
- Uses ripgrep, ctags, and semantic search
- Returns answers with file citations

---

## 🚀 **Quick Start**

### **1. Start Athena Daemon**
```bash
make athena-up
```

### **2. Use from Your Editor**

**Terminal (works everywhere):**
```bash
athena-assist "why is the router failing?"
```

**VS Code/Cursor:**
1. Select code
2. Press `Cmd+K` then `Cmd+A`
3. Athena answers with citations

**Neovim:**
1. Select code
2. Press `<leader>aa`
3. Answer opens in split

---

## 📋 **How It Works**

### **The Daemon (athena-devd):**
- Runs on `http://localhost:8765`
- Watches your repo for file changes
- Maintains a code context graph
- Provides `/assist` and `/ctx/suggest` APIs

### **The Adapters:**
- Ultra-thin (30-100 lines each)
- Forward context to daemon
- Display answers with citations
- **No per-editor prompt engineering!**

### **Context Gathering:**
1. **Ripgrep** - Exact text matches
2. **Ctags** - Symbol definitions & references
3. **Semantic** - Similar code via embeddings
4. **Git** - Recently changed files
5. **Diagnostics** - Files with errors

**Result:** 6-8 perfect code snippets automatically!

---

## 🛠️ **Installation**

### **Terminal (works immediately):**
```bash
make athena-up
athena-assist "your question"
```

### **VS Code/Cursor:**
```bash
# Install adapter
cd .athena/adapters
npm init -y
npm install node-fetch @types/vscode
tsc vscode-cursor.ts

# Add to VS Code
# Copy to: ~/.vscode/extensions/athena-copilot/
# Or use the compiled .js directly
```

### **Neovim:**
```bash
# Copy adapter
cp .athena/adapters/neovim.lua ~/.config/nvim/lua/athena.lua

# Add to init.lua:
require('athena').setup()

# Use: <leader>aa
```

### **JetBrains:**
```bash
# Create HTTP Request action
# POST to http://localhost:8765/assist
# Display in tool window
```

---

## 📖 **API Reference**

### **POST /assist**

**Request:**
```json
{
  "repoRoot": "/path/to/repo",
  "file": "services/router/app.py",
  "cursor": {"line": 132, "col": 8},
  "selection": {"start": 100, "end": 150},
  "diagnostics": [
    {"file": "app.py", "line": 88, "msg": "NameError: func not defined"}
  ],
  "intent": "explain-and-fix",
  "query": "why is this failing?"
}
```

**Response:**
```json
{
  "snippets": [
    {
      "path": "services/router/app.py",
      "start": 80,
      "end": 120,
      "text": "...",
      "why": "definition of failing function",
      "score": 0.95
    }
  ],
  "summary": "The function fails because...",
  "citations": ["services/router/app.py:80-120"],
  "nextActions": []
}
```

### **POST /ctx/suggest**

Returns only snippets (no LLM call) for editors that do their own prompts.

### **GET /healthz**

Health check for adapters to detect daemon.

---

## ⚙️ **Configuration**

**File:** `.athena/config.yml`

```yaml
context:
  max_snippets: 8           # How many code snippets to return
  max_lines_per_snippet: 300
  recent_days: 90           # Freshness window

athena:
  api_url: "http://localhost:8080/v1/chat/completions"
  temperature: 0.3          # Lower for code (less creative)
```

**File:** `.athena/ignore`

Like `.gitignore` but for code context:
```
archive/**
node_modules/**
*.png
*.pdf
volumes/**
```

---

## 🎯 **Use Cases**

### **1. Fix Errors**
```bash
# See error in VS Code
# Select error line
# Cmd+K Cmd+A
# Athena: "Import missing. Add: from x import y"
```

### **2. Understand Code**
```bash
athena-assist "how does the router choose models?"
# Returns: Citations to router logic + explanation
```

### **3. Test Failures**
```bash
# Paste test output
athena-assist "why is test_rag_route failing?"
# Returns: Root cause + suggested fix
```

### **4. Refactoring**
```bash
# Select function
# Cmd+K Cmd+A with query: "optimize this"
# Athena: Suggests improvements with context
```

---

## 🔧 **Maintenance**

### **Rebuild Index:**
```bash
make athena-index
```

### **Check Status:**
```bash
curl http://localhost:8765/healthz
```

### **Logs:**
```bash
docker logs athena-devd --tail 50
```

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────┐
│         Editors (Any)                       │
│  VS Code │ Neovim │ Terminal │ Xcode       │
└────────────────┬────────────────────────────┘
                 │ HTTP/Unix Socket
┌────────────────┴────────────────────────────┐
│         Athena Dev Daemon (8765)            │
│  ┌──────────┬──────────┬─────────────────┐ │
│  │ Watcher  │ Indexer  │ Context Ranker  │ │
│  │ (Files)  │(ripgrep) │ (Smart merge)   │ │
│  └──────────┴──────────┴─────────────────┘ │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┴────────────────────────────┐
│         Athena AI (8080)                    │
│  Chat + RAG + Learning + Safety             │
└─────────────────────────────────────────────┘
```

**Flow:**
1. You select code or get error
2. Adapter sends context to daemon
3. Daemon gathers snippets (ripgrep + ctags + semantic)
4. Daemon calls Athena AI with enriched context
5. Answer returns with file citations
6. Adapter displays with clickable links

**Zero manual context curation!**

---

## 💙 **Bottom Line**

**Before:** Copy/paste code into chat, lose context, repeat

**After:** Select code → Athena auto-gathers context → Perfect answer with citations

**Works in:** VS Code, Cursor, Neovim, Terminal, JetBrains, Xcode

**Zero friction. Universal. Automatic. 🚀**

---

## 📚 **Learn More**

- Configuration: `.athena/config.yml`
- Ignore patterns: `.athena/ignore`
- Adapters: `.athena/adapters/`
- API docs: `http://localhost:8765/docs`

**Athena is now your universal coding companion! 💙**

