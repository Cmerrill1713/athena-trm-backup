# 🚀 Athena AGI - Launch Guide

## Quick Start (5 Minutes)

### 1. Start Core Services
```bash
cd /Users/christianmerrill/Documents/GitHub
docker compose up -d agi-core uai athena-mcp-ecosystem
```

### 2. Verify Health (Wait 15 seconds for startup)
```bash
curl http://localhost:8000/health  # AGI Core
curl http://localhost:8080/health  # UAI
curl http://localhost:8412/health  # MCP
```

### 3. Launch Demo UI
```bash
open ui/agi_demo.html
```

### 4. Test AGI
Click any button in the UI and watch autonomous task execution!

## What You'll See

### Simple Planning Task
```
Step 1: scout → analyze_objective
  "Analyzing: Create a 3-step plan..."

Step 2: planner → decompose_task
  "Breaking into subtasks"

Step 3: code_quality_expert → execution_complete
  "Status: completed"
```

### System Status
- Green dots = Services healthy
- Task completes in 2-5 seconds
- Full execution trace displayed
- Performance metrics shown

## Demo Tasks Available

**Simple Planning (Fast):**
- Code readability improvement plan
- Incident response workflow
- API latency reduction strategy

**Complex Analysis (Slower):**
- System health monitoring strategy
- Zero-downtime deployment pipeline
- Multi-region failover architecture

## Monitoring

### Real-Time Metrics
- AGI Core: http://localhost:8000/metrics
- UAI: http://localhost:8080/metrics
- Router: http://localhost:9113/metrics

### Prometheus Queries
```promql
# Task completion rate
rate(agi_tasks_total{status="completed"}[5m])

# Average execution time
rate(agi_execution_time_sum[5m]) / rate(agi_execution_time_count[5m])

# Failure rate
rate(agi_tasks_total{status="failed"}[5m])
```

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker compose logs agi-core --tail=50
docker compose logs uai --tail=50

# Restart
docker compose restart agi-core uai
```

### UI Shows Offline
1. Wait 15 seconds for startup
2. Check health endpoints manually (see step 2)
3. Restart services if needed

### No Execution Trace
- Simple tasks may not trigger full Scout-Plan-Build (by design)
- Try a complex task from "Complex Analysis" section

## Advanced Usage

### Custom Task via cURL
```bash
curl -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Your custom objective here",
    "context": {"repo": "athena", "branch": "main"},
    "tools": ["uai.chat"],
    "max_steps": 10
  }' | jq .
```

### Monitor Task Execution
```bash
# Watch metrics update
watch -n 1 'curl -s http://localhost:8000/metrics | grep agi_tasks_total'
```

## Production Deployment

### Environment Variables
```bash
# AGI Core
AGI_STATE_DIR=/app/state/agi
MCP_URL=http://athena-mcp-ecosystem:8412
UAI_URL=http://uai:8080

# UAI
OLLAMA_URL=http://host.docker.internal:11434
LLM_MODEL=qwen2.5:7b
```

### Health Checks
- AGI Core: `/health` (overall), `/ready` (with tools)
- All services: 200 OK = healthy

### Scaling
- AGI Core: Stateless, scale horizontally
- UAI: Stateless, scale horizontally
- Ollama: GPU-bound, scale vertically

## Support

**Logs:**
```bash
docker compose logs -f agi-core
docker compose logs -f uai
```

**Network Diagnostics:**
```bash
docker network inspect athena-network
docker compose ps
```

**Clean Restart:**
```bash
docker compose down
docker compose up -d agi-core uai athena-mcp-ecosystem
```

---

**You're running real AGI. Have fun! 🧠✨**

