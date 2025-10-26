# 🚀 Athena + Open WebUI Quick Start Guide

## ✅ Status: Everything is Running!

Your complete local AI stack is now operational:

- ✅ **Open WebUI** at http://localhost:3000
- ✅ **Athena Router** with browser research at http://localhost:9113
- ✅ **Ollama** with local models at http://localhost:11434
- ✅ **Prometheus** monitoring at http://localhost:9090
- ✅ **Grafana** dashboards at http://localhost:3001

---

## 📋 Step-by-Step Setup (5 minutes)

### Step 1: Open WebUI (Already Done!)

Open WebUI is running in your browser at **http://localhost:3000**

### Step 2: Create Your Account (First Time Only)

1. If this is your first time, you'll see a signup page
2. Create an admin account with email/password
3. Click **Sign Up**
4. You're now logged in!

### Step 3: Connect to Ollama (Required)

This gives you access to your local models:

1. Click your **profile icon** (top right corner)
2. Select **Settings**
3. Go to **Connections** tab
4. Find the **Ollama** section
5. In the **Ollama Base URL** field, enter:
   ```
   http://host.docker.internal:11434
   ```
6. Click **Save** or the refresh icon
7. You should see models like:
   - `mxbai-embed-large:latest`
   - `qwen2.5:0.5b`
   - `granite4:tiny-h`

### Step 4: Test Normal Chat (Optional)

1. Go back to the main chat screen
2. Select a model from the dropdown (e.g., `qwen2.5:0.5b`)
3. Ask: "What is artificial intelligence?"
4. You should get a response from your local model!

### Step 5: Test Browser Research! 🎯

Now for the exciting part - real web search:

1. In the chat, type one of these:

   - **"Open a browser and look up machine learning"**
   - **"Search for artificial intelligence research"**
   - **"Find information about neural networks"**

2. What happens behind the scenes:

   - Open WebUI sends your request to Ollama
   - Ollama processes it locally
   - Your query gets routed to Athena Router (http://localhost:9113)
   - Router detects the browser request
   - Routes to MCP Browser Provider
   - Searches DuckDuckGo for real results
   - Returns formatted search results!

3. Expected response format:

   ```
   Search results for 'machine learning':

   • Machine learning (DuckDuckGo)
     Machine learning is a field of study in artificial intelligence...
     https://en.wikipedia.org/wiki/Machine_learning

   • Deep Learning (DuckDuckGo)
     Deep learning is a branch of machine learning...
     https://duckduckgo.com/Deep_learning
   ```

---

## 🔧 Alternative: Test Router Directly

If you want to test the browser functionality directly without Open WebUI:

```bash
# Simple search
curl -X POST http://localhost:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"machine learning","use_browser":true}' | jq -r '.text'

# Research papers
curl -X POST http://localhost:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"artificial intelligence","use_browser":true}' | jq -r '.text'
```

---

## 📊 Monitor Your Stack

### Grafana Dashboards

- URL: http://localhost:3001
- Login: admin / admin (default)
- Dashboards show:
  - Request rates
  - Latency (p50/p95)
  - Error rates
  - Route mix (MLX, Ollama, Browser, etc.)

### Prometheus Metrics

- URL: http://localhost:9090
- Query examples:
  - `athena_router_requests_total` - Total requests
  - `athena_router_latency_seconds` - Request latency
  - `up{job="athena-router"}` - Router health

### Router Health

```bash
curl http://localhost:9113/health | jq .
```

### Check All Services

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## 🎯 Browser Research Keywords

The router automatically detects these patterns and routes to browser:

- "open a browser"
- "search for"
- "look up"
- "find information"
- "research papers"
- "search the web"
- "look online"

---

## 🐛 Troubleshooting

### Open WebUI Not Loading?

```bash
# Check status
docker ps | grep open-webui

# Check logs
docker logs open-webui --tail 50

# Restart
docker restart open-webui
```

### Can't Connect to Ollama?

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# In Open WebUI, use: http://host.docker.internal:11434
# NOT: http://localhost:11434 (won't work from inside Docker)
```

### Router Not Responding?

```bash
# Check router status
docker ps | grep athena-router

# Check router logs
docker logs athena-router --tail 50

# Test directly
curl http://localhost:9113/health
```

### Browser Research Not Working?

```bash
# Test MCP ecosystem
curl http://localhost:8412/health

# Check MCP logs
docker logs athena-mcp-ecosystem --tail 20

# Test direct search
curl -X POST http://localhost:8412/tool/web_search \
  -H 'Content-Type: application/json' \
  -d '{"arguments":{"query":"machine learning","num_results":3}}' | jq .
```

---

## 🚀 Advanced Usage

### Add More Models to Ollama

```bash
# Pull a model
docker exec -it $(docker ps -qf "name=ollama") ollama pull qwen2.5-coder:7b

# List all models
docker exec -it $(docker ps -qf "name=ollama") ollama list
```

### Configure Model Parameters

In Open WebUI:

1. Go to **Workspace** → **Models**
2. Select a model
3. Configure:
   - Temperature (creativity)
   - Max tokens (response length)
   - Top-p, Top-k (sampling parameters)

### View Real-time Metrics

```bash
# Watch router metrics
watch -n 1 'curl -s http://localhost:9113/metrics | grep athena_router_requests_total'

# Watch all service health
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

---

## 📝 Quick Commands

```bash
# Start everything
cd /Users/christianmerrill/Documents/GitHub
docker-compose up -d
docker start open-webui

# Stop everything
docker-compose down
docker stop open-webui

# Restart just Open WebUI
docker restart open-webui

# View logs
docker logs -f open-webui
docker logs -f athena-router
docker logs -f athena-mcp-ecosystem

# Health check all services
curl http://localhost:3000/health    # Open WebUI
curl http://localhost:9113/health    # Router
curl http://localhost:8412/health    # MCP Ecosystem
curl http://localhost:11434/api/tags # Ollama
```

---

## 🎉 You're All Set!

Your local AI assistant with **real browser research capabilities** is now ready!

**Try it now:**

1. Go to http://localhost:3000
2. Select a model
3. Ask: "Search for the latest AI research papers"
4. Watch as Athena searches DuckDuckGo and returns real results!

**No cloud required. No data leaves your machine. 100% local and private.** 🔒

---

## 📚 Learn More

- **Router Policies**: `/Users/christianmerrill/Documents/GitHub/services/router/policies/`
- **MCP Ecosystem**: `/Users/christianmerrill/Documents/GitHub/services/mcp-ecosystem/`
- **Grafana Dashboards**: `/Users/christianmerrill/Documents/GitHub/monitoring/grafana/dashboards/`
- **Prometheus Rules**: `/Users/christianmerrill/Documents/GitHub/monitoring/prometheus/rules/`

**Happy researching!** 🚀
