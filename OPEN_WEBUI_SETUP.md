# Open WebUI Setup for Athena

## 🎉 Open WebUI is Now Running!

**Access URL:** http://localhost:3000

## 📋 Setup Steps

### 1. **Initial Setup**

1. Open your browser and go to: **http://localhost:3000**
2. Create an admin account (first user becomes admin)
3. Complete the onboarding process

### 2. **Connect to Your Local Athena Router**

#### Option A: Add OpenAI-Compatible Endpoint

1. Click your profile icon (top right) → **Settings**
2. Go to **Connections** → **OpenAI**
3. Enable OpenAI API
4. Set the following:
   - **API Base URL**: `http://host.docker.internal:9113`
   - **API Key**: `sk-athena` (any value works for local)
5. Click **Save**

#### Option B: Add as Ollama Connection (Recommended)

1. Click your profile icon → **Settings**
2. Go to **Connections** → **Ollama**
3. Set **Ollama Base URL**: `http://host.docker.internal:11434`
4. Click **Refresh** to load models
5. Models like `qwen2.5-coder:7b` should appear

### 3. **Test Browser Research Functionality**

Once connected, try asking:

- "Open a browser and look up research papers on artificial intelligence"
- "Search for machine learning papers"
- "Find information about neural networks"

The router will automatically detect browser requests and route them to the MCP browser provider!

## 🎯 Expected Behavior

When you ask for browser research:

1. **Router Detection**: Athena router detects the browser request
2. **MCP Routing**: Routes to MCP browser provider
3. **Real Search**: Searches DuckDuckGo for actual results
4. **Formatted Response**: Returns nicely formatted search results with titles, snippets, and URLs

Example response:

```
Search results for 'artificial intelligence':

• Artificial intelligence (DuckDuckGo)
  Artificial intelligence is the capability of computational systems...
  https://en.wikipedia.org/wiki/Artificial_intelligence

• Machine Learning (DuckDuckGo)
  Machine learning is a field of study in artificial intelligence...
  https://en.wikipedia.org/wiki/Machine_learning
```

## 🔧 Troubleshooting

### Can't Connect to Athena?

```bash
# Verify router is running
curl http://localhost:9113/health

# Test browser functionality directly
curl -X POST http://localhost:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"artificial intelligence","use_browser":true}' | jq .
```

### Open WebUI Not Responding?

```bash
# Check logs
docker logs open-webui

# Restart if needed
docker restart open-webui
```

## 📊 Monitoring Your Athena Stack

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **Router Metrics**: http://localhost:9113/metrics
- **Router Health**: http://localhost:9113/health

## 🚀 Advanced Configuration

### Custom Model Configuration

1. In Open WebUI, go to **Workspace** → **Models**
2. You can configure custom parameters for each model
3. Set temperature, max tokens, etc.

### Enable/Disable Browser Auto-Detection

The router automatically detects browser requests based on keywords like:

- "open a browser"
- "search for"
- "look up"
- "research papers"
- "find information"

## 💡 Tips

1. **Use Specific Queries**: Instead of "open a browser and look up research papers," try "machine learning" or "neural networks" for better results
2. **Ollama Models**: Your local Ollama instance has models available at http://localhost:11434
3. **Monitor Performance**: Use Grafana dashboards to monitor request latency and routing decisions
4. **Check Logs**: Router logs show which provider handled each request

## 📝 Quick Commands

```bash
# Stop Open WebUI
docker stop open-webui

# Start Open WebUI
docker start open-webui

# Remove Open WebUI (keeps data)
docker rm open-webui

# Remove Open WebUI and data
docker rm open-webui
docker volume rm open-webui

# Check all Athena services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

**Your Local Athena Stack is fully operational!** 🎉

Enjoy your local-first, privacy-preserving AI assistant with real browser research capabilities!
