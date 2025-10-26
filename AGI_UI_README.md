# Athena AGI Demo UI

## 🎯 Quick Start

1. **Ensure services are running:**
   ```bash
   docker compose ps | grep -E "agi-core|uai|mcp"
   ```

2. **Open the demo:**
   ```bash
   open ui/agi_demo.html
   # Or navigate to: file:///Users/christianmerrill/Documents/GitHub/ui/agi_demo.html
   ```

3. **Click any button to test AGI capabilities!**

## 🌐 Architecture

```
┌──────────────┐
│   Browser    │
│  (Demo UI)   │
└──────┬───────┘
       │
       │ HTTP POST /api/execute
       │
       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   AGI Core   │─────▶│     UAI      │─────▶│   Ollama     │
│  :8000       │      │   :8080      │      │   :11434     │
└──────────────┘      └──────────────┘      └──────────────┘
       │
       │ (Optional)
       ▼
┌──────────────┐
│ MCP Ecosystem│
│   :8412      │
└──────────────┘
```

## ✨ Features

### 1. **Service Health Monitoring**
- Real-time health checks for AGI Core, UAI, and MCP
- Visual status indicators (green = healthy, red = offline)
- Auto-refresh every 30 seconds

### 2. **Pre-Built Demo Tasks**
**Simple Planning:**
- Code readability improvement plan
- Incident response workflow
- API latency reduction strategy

**Complex Analysis:**
- System health monitoring strategy
- Zero-downtime deployment pipeline
- Multi-region failover architecture

### 3. **Execution Visualization**
- Task execution progress
- Step-by-step trace of AGI agents
- Tool usage tracking
- Performance metrics (execution time)

## 🔍 What's Happening

When you click a button:

1. **UI** sends POST request to AGI Core `/api/execute`
2. **Scout Agent** analyzes the objective and determines complexity
3. **Planner Agent** (if complex) breaks down into subtasks
4. **Expert Agents** execute the plan using available tools
5. **Result** streams back with full trace

### Example Trace:
```
Step 1: scout → analyze_objective
  "Analyzing: Create a 3-step plan to improve code readability"

Step 2: planner → decompose_task
  "Breaking into subtasks"

Step 3: code_quality_expert → execution_complete
  "Status: completed"
```

## 🛠️ Customization

Edit `ui/agi_demo.html` to:
- Add new demo tasks
- Change AGI endpoints
- Customize styling
- Add more visualizations

## 🐛 Troubleshooting

**Services show offline:**
```bash
# Restart services
docker compose restart agi-core uai athena-mcp-ecosystem

# Check logs
docker compose logs agi-core --tail=50
```

**CORS errors:**
AGI Core includes CORS headers by default. If you see CORS errors:
1. Check browser console
2. Verify AGI Core is running: `curl http://localhost:8000/health`

**No execution trace:**
- Simple tasks may not trigger full Scout-Plan-Build (by design)
- Try a complex task from the "Complex Analysis" section

## 📊 Metrics

Access raw metrics:
- AGI Core: http://localhost:8000/metrics
- UAI: http://localhost:8080/metrics
- Router: http://localhost:9113/metrics

## 🚀 Next Steps

- [ ] Add WebSocket for real-time streaming
- [ ] Visualize agent coordination graph
- [ ] Show Prometheus metrics in UI
- [ ] Add custom task input field
- [ ] Integrate with NeuroForge desktop app

