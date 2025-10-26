# 📸 Simple Visual Guide - Configure Open WebUI in 3 Steps

## ✅ The Proxy is Running and Working!

All routing is functional. You just need to point Open WebUI to it.

---

## 🎯 Step-by-Step Instructions

### Step 1: Open Open WebUI

- Go to: **http://localhost:3000**
- Log in (or create account if first time)

### Step 2: Open Settings

- Click your **user icon/avatar** in the top right corner
- Click **"Settings"** from the dropdown menu

### Step 3: Go to Connections Tab

- In the left sidebar, find and click **"Connections"**
- You'll see various connection options

### Step 4: Find Ollama Settings

- Look for section labeled **"Ollama"** or **"Ollama API"**
- You'll see a text field for **"Ollama Base URL"** or similar

### Step 5: Change the Port Number

**Current value (probably):**

```
http://localhost:11434
```

or

```
http://host.docker.internal:11434
```

**Change it to:**

```
http://host.docker.internal:11435
```

**Key Change:** `11434` → `11435` (just change last digit to 5)

### Step 6: Save

- Click **Save** button
- Or click the **refresh/reload icon** next to the URL field
- You should see your models load

### Step 7: Test It!

Go back to the chat interface and type:

```
search for machine learning
```

**Expected Result:**

```
Search results for 'search for machine learning':

• Machine learning (DuckDuckGo)
  Machine learning is a field of study...
  https://en.wikipedia.org/wiki/Machine_learning
```

---

## 🎨 What You're Looking For

### Settings Location:

```
┌─────────────────────────────────────┐
│  [👤] Username              [⚙️]    │  ← Click your avatar
├─────────────────────────────────────┤
│  ▼ Dropdown Menu                    │
│     Profile                          │
│     Settings  ← Click this          │
│     Sign Out                         │
└─────────────────────────────────────┘
```

### Connections Tab:

```
Settings
├─ General
├─ Account
├─ Connections  ← Click this
├─ Models
└─ Interface
```

### Ollama URL Field:

```
╔═══════════════════════════════════════╗
║  Connections                           ║
╠═══════════════════════════════════════╣
║                                        ║
║  Ollama API                            ║
║  ┌─────────────────────────────────┐  ║
║  │ http://host.docker.internal:    │  ║
║  │ 11435   ← Change to 11435       │  ║
║  └─────────────────────────────────┘  ║
║  [Save] or [🔄]                       ║
║                                        ║
╚═══════════════════════════════════════╝
```

---

## 🧪 Quick Tests

After changing to port 11435:

### Test 1 - Browser Search:

**Type:** `search for artificial intelligence`  
**Should get:** Real DuckDuckGo results with links

### Test 2 - Coding:

**Type:** `write a python function to add two numbers`  
**Should get:** Python code (routed to MLX)

### Test 3 - Normal Chat:

**Type:** `What is the capital of France?`  
**Should get:** Normal chat response (routed to Ollama)

---

## ❌ Common Issues

### "Can't connect to Ollama"

**Fix:** Make sure you're using `host.docker.internal:11435` not `localhost:11435`

### "Models not loading"

**Fix:** Click the refresh icon next to the URL field after changing it

### "Still getting basic responses, no search results"

**Fix 1:** Make sure port is `11435` not `11434`  
**Fix 2:** Use exact trigger words: "search for X" not just "X"  
**Fix 3:** Check proxy is running: `ps aux | grep "node server.js"`

### Proxy not running?

```bash
cd /Users/christianmerrill/Documents/GitHub/services/ollama-athena-proxy
node server.js > /tmp/athena-proxy.log 2>&1 &
```

---

## 🔍 Verify It's Working

### Method 1: Check Proxy Logs

```bash
tail -f /tmp/athena-proxy.log
```

Then type "search for AI" in Open WebUI.  
You should see: `🌐 Browser request → Athena Router (MCP Browser)`

### Method 2: Direct Test

```bash
curl -X POST http://localhost:11435/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"search for AI","stream":false}' | jq .
```

Should return search results, not regular chat.

---

## 📱 Alternative: Use Browser DevTools

1. Open Open WebUI
2. Press F12 (open developer tools)
3. Go to **Network** tab
4. Type a message in chat
5. Look for requests to see which URL it's calling
6. Should show requests to `:11435` if configured correctly

---

## 🎉 Success Looks Like:

When you type **"search for machine learning"** you get:

```
Search results for 'search for machine learning':

• Machine learning (DuckDuckGo)
  Machine learning is a field of study in artificial
  intelligence concerned with the development and study
  of statistical algorithms...
  https://en.wikipedia.org/wiki/Machine_learning

• Deep Learning (DuckDuckGo)
  Deep learning is a branch of machine learning...
  https://duckduckgo.com/Deep_learning
```

**If you see this, it's working!** ✅

---

## 💡 Remember:

- **ONE setting to change:** Port `11434` → `11435`
- **Everything else is automatic**
- **Proxy does the smart routing**
- **No other configuration needed**

---

## 🆘 Still Not Working?

Take a screenshot of:

1. Your Open WebUI Settings → Connections page
2. The response you get when typing "search for AI"
3. Proxy logs: `tail /tmp/athena-proxy.log`

And we can debug from there!
