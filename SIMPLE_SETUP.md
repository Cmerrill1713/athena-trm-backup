# 🚀 Simple 3-Minute Setup

## What You Need to Do (Just 3 Steps!)

### Step 1: Open Open WebUI

Go to: **http://localhost:3000**

### Step 2: Create Account (First Time Only)

- Fill in any email/password
- Click "Sign Up"
- You're in!

### Step 3: Connect to Ollama

1. Click your **profile icon** (top right)
2. Click **Settings**
3. Find **"Connections"** or **"Ollama"** section
4. In the **Ollama Base URL** field, enter exactly this:
   ```
   http://host.docker.internal:11434
   ```
5. Click **Save** or the **refresh icon**

## ✅ That's It!

You don't need to configure anything else. The browser research functionality is **already wired up internally** in your Athena stack.

## 🔍 Test It Right Now!

In the chat, just type:

- **"search for machine learning"**
- **"look up artificial intelligence"**
- **"find information about neural networks"**

The router will **automatically detect** these are browser requests and search DuckDuckGo for you!

## 🤔 Why Don't I Need to Add URLs?

Because the Athena Router is **already configured** to:

1. Detect browser request patterns (like "search", "look up", etc.)
2. Route to the MCP Browser Provider automatically
3. The MCP Browser searches DuckDuckGo
4. Results come back to you

**It's all internal routing - no external URLs needed!**

## 📊 Behind the Scenes (You Don't Need to Touch This)

Your stack internally routes like this:

```
Open WebUI
    ↓
Ollama (localhost:11434) ← You configure this in UI
    ↓
Athena Router (localhost:9113) ← Auto-configured
    ↓
MCP Browser (localhost:8412) ← Auto-configured
    ↓
DuckDuckGo Search ← Automatic
    ↓
Results back to you!
```

**Everything except the Ollama URL is pre-wired!**

## ⚠️ Common Confusion

**❌ WRONG**: "Do I need to add the router URL in Open WebUI?"  
**✅ CORRECT**: No! Just add Ollama URL. The router is internal.

**❌ WRONG**: "Do I need to add the MCP Browser URL?"  
**✅ CORRECT**: No! The router handles that automatically.

**❌ WRONG**: "Do I need API keys for DuckDuckGo?"  
**✅ CORRECT**: No! It's free and automatic.

## 🎯 The ONLY URL You Configure:

```
http://host.docker.internal:11434
```

That's it! This tells Open WebUI where to find your local Ollama models.

Everything else (router, browser, search) is **already connected internally**.

## 🧪 Quick Test

After connecting to Ollama, try this exact message:

```
search for machine learning
```

You should get results like:

```
Search results for 'machine learning':

• Machine learning (DuckDuckGo)
  Machine learning is a field of study...
  https://en.wikipedia.org/wiki/Machine_learning

• Deep Learning (DuckDuckGo)
  Deep learning is a branch of ML...
```

If you see this, **it's working!** 🎉

## 🐛 Troubleshooting

**Not getting search results?**

1. Make sure Ollama URL is set correctly
2. Try simpler queries: just "machine learning" instead of "search for machine learning"
3. Check router is running: `curl http://localhost:9113/health`

**Can't connect to Ollama?**

- Make sure you used `host.docker.internal:11434` not `localhost:11434`
- Docker containers need the special hostname

---

**That's all you need to know!** 🚀

No external APIs. No extra configuration. Just connect to Ollama and start chatting!
