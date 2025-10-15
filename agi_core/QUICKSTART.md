# AGI Core - Quick Start Guide

Get up and running with AGI Core in 5 minutes.

## 🚀 Installation

```bash
cd /Users/christianmerrill/Documents/GitHub/agi_core

# Install dependencies
pip install -r requirements.txt

# Create state directories
mkdir -p state/agi/{context,bundles,experts,workflows,delegation}
```

## 🎯 Start the Service

```bash
# Start AGI Core service
python -m agi_core.agi_service

# Service running at: http://localhost:8100
```

## 📝 Run Examples

### Example 1: Context Engineering (R&D Framework)

```bash
python examples/example_context_engineering.py
```

This demonstrates:
- Creating context windows
- **REDUCE** strategy (minimize context)
- **DELEGATE** strategy (offload to specialists)
- Context priming
- Context bundles for replay

### Example 2: Scout-Plan-Build Workflow

```bash
python examples/example_scout_plan_build.py
```

This demonstrates:
- **Scout** phase: Explore codebase
- **Plan** phase: Create strategy
- **Build** phase: Execute plan

### Example 3: Multi-Agent Delegation

```bash
python examples/example_multi_agent.py
```

This demonstrates:
- Background agents (out-of-loop)
- Parallel execution
- Agent coordination
- Result aggregation

## 🧪 Test the API

### 1. Create a Context Window

```bash
curl -X POST http://localhost:8100/context/create \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_001",
    "session_id": "session_123",
    "max_tokens": 200000
  }'
```

### 2. Submit Task to Expert

```bash
curl -X POST http://localhost:8100/experts/task/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "debugging",
    "description": "Fix authentication bug",
    "context": {"files": ["auth.py"]},
    "priority": 8
  }'
```

### 3. Execute Scout-Plan-Build Workflow

```bash
curl -X POST http://localhost:8100/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "scout_plan_build",
    "task_description": "Add rate limiting to API",
    "codebase_path": "/path/to/repo",
    "context": {}
  }'
```

### 4. Delegate Task to Background Agent

```bash
curl -X POST "http://localhost:8100/delegation/task?agent_type=refactor&description=Refactor%20payment%20service&strategy=background&priority=7" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 5. Check Service Statistics

```bash
curl http://localhost:8100/stats
```

## 📊 View Metrics

```bash
# Prometheus metrics
curl http://localhost:8100/metrics

# Key metrics:
# - agi_context_operations_total
# - agi_context_tokens
# - agi_context_efficiency
# - agi_workflow_executions_total
# - agi_delegation_tasks_total
```

## 🐳 Docker Deployment

```bash
# Build and start services
docker-compose up -d

# Services:
# - AGI Core: http://localhost:8100
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
```

## 🔗 Integration with Your Systems

### Integrate with Governance Orchestrator

```python
import requests

# After governance verdict, delegate to AGI
response = requests.post("http://localhost:8100/experts/task/submit", json={
    "task_type": "debugging",
    "description": "Investigate service failure",
    "context": {"verdict": "HARD_FAIL"},
    "priority": 9
})
```

### Report AGI Metrics to Governance

```python
# After AGI operation, report to governance
requests.post("http://localhost:8000/verdict", json={
    "task_id": "agi_task_123",
    "verdict": "PASS",
    "ece_estimate": 0.92,
    "meta": {"agi_workflow": True}
})
```

## 📚 Key Concepts

### R&D Framework

There are only **two ways** to manage context:

1. **REDUCE** - Minimize unnecessary context
   - Remove unused MCP tools
   - Trim memory files
   - Archive old prompts

2. **DELEGATE** - Distribute work to specialized agents
   - Background agents
   - Parallel execution
   - Specialist routing

### Agent Experts

**6 Built-in Experts:**
- `debug_expert` - Bug fixing
- `scout_expert` - Code exploration
- `plan_expert` - Task breakdown
- `build_expert` - Implementation
- `security_expert` - Security auditing
- `performance_expert` - Optimization

### Scout-Plan-Build Pattern

The most powerful workflow:

```
Scout → Plan → Build
  ↓       ↓       ↓
Explore  Strategy  Execute
```

### Context Bundles

Execution trails for agent replay:
- Records operations (read, write, tools)
- Enables ~70% context recovery
- Perfect for long-running work

## 🎓 Next Steps

1. **Read the full README**: `README.md`
2. **Check integration guide**: `INTEGRATION_GUIDE.md`
3. **Explore examples**: `examples/`
4. **Add custom experts**: See `agent_experts.py`
5. **Deploy to production**: See `docker-compose.yml`

## 💡 Pro Tips

1. **Always use R&D**: Reduce first, then delegate
2. **Prefer specialists**: Use expert agents over general agents
3. **Prime for focus**: Load task-specific context
4. **Use bundles**: For work that might exceed context
5. **Go background**: Delegate independent work out-of-loop

## 🆘 Troubleshooting

### Service won't start

```bash
# Check if port is in use
lsof -i :8100

# Check logs
python -m agi_core.agi_service 2>&1 | tee agi_core.log
```

### High context usage

```bash
# Check context status
curl http://localhost:8100/context/agent_id/status

# Apply REDUCE strategy
curl -X POST http://localhost:8100/context/reduce \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_id", "strategy": "auto"}'
```

### Agent not completing

```bash
# Check active agents
curl http://localhost:8100/delegation/agents/active

# Check specific agent
curl http://localhost:8100/delegation/agent/AGENT_ID/status
```

## 📞 Support

- **Documentation**: See `README.md` and `INTEGRATION_GUIDE.md`
- **Examples**: Check `examples/` directory
- **Health**: `http://localhost:8100/health`
- **Metrics**: `http://localhost:8100/metrics`
- **Stats**: `http://localhost:8100/stats`

---

**Ready to build AGI systems!** 🚀

> "A focused agent is a performant agent" - IndyDevDan

