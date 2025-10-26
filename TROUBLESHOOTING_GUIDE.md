# 🔧 Open WebUI Troubleshooting Guide

## ✅ All Services Are Running:

- ✅ Open WebUI (port 3000)
- ✅ Ollama (port 11434)
- ✅ Proxy (port 11435)
- ✅ Router (port 9113)

## 🎯 The Issue: Open WebUI Configuration

The proxy is working perfectly (I tested it), but Open WebUI needs the right configuration.

## 📝 Step-by-Step Fix:

### Option 1: Manual Configuration (Recommended)

1. **Go to:** http://localhost:3000
2. **Click:** Your user icon (top right)
3. **Click:** Settings
4. **Click:** External Tools (left sidebar)
5. **Find:** Ollama section
6. **Change:** `http://host.docker.internal:11434`
   **To:** `http://host.docker.internal:11435`
7. **Click:** Save/Apply

### Option 2: JSON Configuration (If Manual Fails)

If the UI doesn't work, you can configure via JSON:

1. **Open:** http://localhost:3000/settings
2. **Look for:** "Import Settings" or "Configuration"
3. **Use this JSON:**

```json
{
  "ollama": {
    "base_url": "http://host.docker.internal:11435"
  }
}
```

### Option 3: Environment Variable

If you're running Open WebUI via Docker, you can set:

```bash
docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11435 ...
```

## 🧪 Test After Configuration:

Type these in Open WebUI chat:

1. **Browser Search:** `search for machine learning`

   - **Expected:** Real DuckDuckGo results with URLs

2. **Coding:** `write a python function to add numbers`

   - **Expected:** Python code generation

3. **Normal Chat:** `What is 2+2?`
   - **Expected:** Normal chat response

## 🔍 Debug Steps:

### Check Proxy Logs:

```bash
tail -f /tmp/athena-proxy.log
```

When you type in Open WebUI, you should see:

- `🌐 Browser request → Athena Router (MCP Browser)`
- `💻 Coding task → Athena Router (MLX)`
- `💬 Normal chat → Ollama`

### Test Direct API:

```bash
curl -X POST http://localhost:11435/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"search for AI","stream":false}'
```

Should return search results.

### Check Open WebUI Network:

1. Open Open WebUI
2. Press F12 (Developer Tools)
3. Go to Network tab
4. Type a message
5. Look for requests to `:11435` (not `:11434`)

## ❌ Common Issues:

### "Connection Failed"

- **Fix:** Use `host.docker.internal:11435` not `localhost:11435`

### "Models Not Loading"

- **Fix:** Click refresh icon after changing URL

### "Still Getting Basic Responses"

- **Fix 1:** Verify port is `11435` not `11434`
- **Fix 2:** Use exact trigger words: "search for X"
- **Fix 3:** Check proxy logs show routing

### "JSON Configuration Not Working"

- **Fix:** Try manual UI configuration instead

## 🎯 What "Failed" Means:

Can you tell me:

1. **What exactly failed?** (Error message?)
2. **What did you see in Open WebUI?** (Still basic chat?)
3. **What URL did you set?** (Should be `:11435`)

## 🚀 Alternative: Use Direct API

If Open WebUI keeps failing, you can use the proxy directly:

```bash
# Browser search
curl -X POST http://localhost:11435/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"search for AI","stream":false}'

# Chat
curl -X POST http://localhost:11435/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"What is 2+2?","stream":false}'
```

This bypasses Open WebUI entirely and uses the proxy directly.

---

## 📞 Need Help?

Tell me:

1. **Exact error message** you're seeing
2. **What URL** you set in Open WebUI
3. **What response** you get when typing "search for AI"

And I'll fix it immediately!
