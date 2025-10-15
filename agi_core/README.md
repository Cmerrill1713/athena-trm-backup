# AGI Core - Advanced Agent Intelligence Framework

**Based on IndyDevDan's R&D Framework and Context Engineering Patterns**

A production-ready framework for building scalable, efficient AI agent systems using proven patterns from agentic coding workflows.

## 🎯 Core Principles

> **"A focused agent is a performant agent"** - IndyDevDan

This framework implements battle-tested patterns for building AGI systems:

1. **R&D Framework** - Only two ways to manage context:
   - **Reduce**: Minimize unnecessary context
   - **Delegate**: Distribute work to specialized agents

2. **Agent Experts** - Specialized agents > General-purpose agents

3. **Scout-Plan-Build** - The most powerful workflow pattern:
   - Scout: Explore and gather information
   - Plan: Break down and strategize
   - Build: Execute precisely

4. **Context Bundles** - Execution trails for agent replay (~70% context recovery)

5. **Multi-Agent Delegation** - Out-of-loop execution for maximum efficiency

## 📦 Components

### 1. Context Engineering (`context_engineering.py`)

Manages agent context windows using the R&D Framework:

```python
from agi_core import ContextManager, ContextBundle

# Create context manager
cm = ContextManager()

# Create agent context
context = cm.create_context(
    agent_id="agent_123",
    session_id="session_456",
    max_tokens=200000
)

# REDUCE context when needed
result = cm.reduce_context(agent_id="agent_123")
# Freed: 23,000 tokens

# DELEGATE to specialized agent
delegation = cm.delegate_to_agent(
    source_agent_id="agent_123",
    task={"type": "debugging", "description": "Fix auth bug"},
    specialist_type="debug_expert"
)
```

**Key Features:**
- Context window monitoring and optimization
- Token efficiency tracking
- Context priming for task-specific focus
- Context bundles for execution replay

### 2. Agent Experts (`agent_experts.py`)

Registry of specialized expert agents:

```python
from agi_core import ExpertRegistry, ExpertOrchestrator

# Initialize expert system
registry = ExpertRegistry()
orchestrator = ExpertOrchestrator(registry)

# Built-in experts:
# - Debug Expert: Bug fixing and troubleshooting
# - Scout Expert: Code exploration
# - Plan Expert: Task breakdown
# - Build Expert: Implementation
# - Security Expert: Security auditing
# - Performance Expert: Optimization

# Submit task to appropriate expert
task_id = orchestrator.submit_task(
    task_type="debugging",
    description="Investigate memory leak in user service",
    context={"service": "user-api", "files": ["api.py"]},
    priority=8
)

# Execute with expert
result = orchestrator.execute_task(task_id)
```

**Key Features:**
- Domain-specific expertise
- Focused system prompts (minimal context)
- Automatic task routing
- Custom expert registration

### 3. Workflows (`workflows.py`)

Agentic workflow patterns:

```python
from agi_core import ScoutPlanBuild, BackgroundWorkflow

# Scout-Plan-Build Pattern
workflow = ScoutPlanBuild(
    workflow_id="feature_123",
    task_description="Implement user authentication",
    codebase_path=Path("./src"),
    constraints={"test_coverage": 0.85}
)

result = workflow.execute()

# Phases executed:
# 1. Scout: Explored codebase, identified key files
# 2. Plan: Created 4-step implementation plan
# 3. Build: Executed plan, added tests
```

**Key Features:**
- Scout-Plan-Build pattern
- Background workflows (out-of-loop)
- Parallel workflows
- Workflow orchestration

### 4. Multi-Agent Delegation (`delegation.py`)

Delegate work to specialized agents:

```python
from agi_core import AgentDelegator, MultiAgentCoordinator

delegator = AgentDelegator(max_parallel_agents=5)
coordinator = MultiAgentCoordinator(delegator)

# Delegate single task
agent_id = delegator.delegate_task(
    agent_type="refactor",
    description="Refactor payment service",
    context={"files": ["payment.py"]},
    strategy=DelegationStrategy.BACKGROUND
)

# Coordinate multi-agent workflow
workflow = coordinator.coordinate_workflow(
    workflow_id="migrate_db",
    tasks=[
        {"agent_type": "scout", "description": "Map database schema"},
        {"agent_type": "plan", "description": "Create migration strategy"},
        {"agent_type": "build", "description": "Implement migrations"}
    ],
    strategy=DelegationStrategy.SEQUENTIAL
)
```

**Key Features:**
- Background execution (fire-and-forget)
- Parallel execution
- Sequential execution with dependencies
- Result aggregation

### 5. AGI Service API (`agi_service.py`)

Production-ready FastAPI service integrating all components:

```bash
# Start the service
python -m agi_core.agi_service
# Service runs on http://localhost:8100
```

**Endpoints:**

**Context Management:**
- `POST /context/create` - Create agent context
- `POST /context/reduce` - Reduce context (R in R&D)
- `POST /context/delegate` - Delegate work (D in R&D)
- `POST /context/prime` - Prime context for task
- `GET /context/{agent_id}/status` - Get context status

**Context Bundles:**
- `POST /bundle/start` - Start execution trail
- `POST /bundle/{bundle_id}/record` - Record operation
- `POST /bundle/{bundle_id}/finalize` - Save bundle
- `POST /bundle/{bundle_id}/replay` - Replay to new agent

**Expert Agents:**
- `GET /experts/list` - List all experts
- `POST /experts/task/submit` - Submit task to expert
- `POST /experts/task/{task_id}/execute` - Execute task
- `GET /experts/task/{task_id}/status` - Task status

**Workflows:**
- `POST /workflow/execute` - Execute workflow
- `GET /workflow/{workflow_id}/status` - Workflow status

**Multi-Agent Delegation:**
- `POST /delegation/task` - Delegate task
- `GET /delegation/agent/{agent_id}/status` - Agent status
- `GET /delegation/task/{task_id}/result` - Task result

**Monitoring:**
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /metrics` - Prometheus metrics
- `GET /stats` - Service statistics

## 🚀 Quick Start

### Installation

```bash
cd agi_core
pip install -r requirements.txt
```

### Start the Service

```bash
# Set environment variables (optional)
export AGI_STATE_DIR=./state/agi
export AGI_SERVICE_PORT=8100
export OTLP_ENDPOINT=http://localhost:4318/v1/traces

# Start service
python -m agi_core.agi_service
```

### Example: Scout-Plan-Build Workflow

```bash
# Execute a Scout-Plan-Build workflow
curl -X POST http://localhost:8100/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "scout_plan_build",
    "task_description": "Add rate limiting to API",
    "codebase_path": "/path/to/repo",
    "context": {"test_coverage": 0.85}
  }'
```

### Example: Delegate to Expert

```bash
# Submit task to expert agent
curl -X POST http://localhost:8100/experts/task/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "security_audit",
    "description": "Audit authentication flow",
    "context": {"files": ["auth.py", "middleware.py"]},
    "priority": 9
  }'
```

### Example: Multi-Agent Coordination

```bash
# Coordinate multiple agents
curl -X POST http://localhost:8100/coordination/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "refactor_v2",
    "tasks": [
      {
        "agent_type": "scout",
        "description": "Identify code smells",
        "context": {"directory": "src/"}
      },
      {
        "agent_type": "refactor",
        "description": "Refactor identified issues",
        "context": {}
      }
    ],
    "strategy": "sequential"
  }'
```

## 📊 Monitoring & Observability

### Prometheus Metrics

- `agi_context_operations_total` - Context operations by strategy
- `agi_context_tokens` - Token usage histogram
- `agi_context_efficiency` - Context efficiency score (0-1)
- `agi_workflow_executions_total` - Workflow executions
- `agi_workflow_duration_seconds` - Workflow duration
- `agi_delegation_tasks_total` - Delegated tasks

### Sentry Integration

The service integrates with Sentry for error tracking and performance monitoring (when `sentry_sdk` is installed).

### OpenTelemetry Tracing

Distributed tracing support via OTLP export (configure `OTLP_ENDPOINT`).

## 🏗️ Architecture

```
AGI Core
├── Context Engineering (R&D Framework)
│   ├── ContextManager - Reduce & Delegate strategies
│   ├── ContextBundle - Execution trails
│   └── ContextMetrics - Efficiency tracking
│
├── Agent Experts (Specialized Agents)
│   ├── ExpertRegistry - Expert pool management
│   ├── ExpertOrchestrator - Task routing
│   └── Built-in Experts (Debug, Scout, Plan, Build, etc.)
│
├── Workflows (Agentic Patterns)
│   ├── ScoutPlanBuild - Primary workflow pattern
│   ├── BackgroundWorkflow - Out-of-loop execution
│   ├── ParallelWorkflow - Concurrent execution
│   └── WorkflowOrchestrator - Lifecycle management
│
└── Multi-Agent Delegation
    ├── AgentDelegator - Task delegation
    ├── BackgroundAgent - Background execution
    └── MultiAgentCoordinator - Workflow coordination
```

## 🔗 Integration with Existing Systems

### Governance Integration

The AGI service integrates with your existing governance orchestrator:

```python
# Report metrics to governance
POST /governance/report
{
  "agent_id": "agent_123",
  "metrics": {
    "context_efficiency": 0.92,
    "tokens_used": 12500,
    "duration_seconds": 45.2
  },
  "verdict": "PASS"
}
```

### Common Ops Integration

Uses your existing `common/ops.py` utilities:
- `wire_tracing()` - OpenTelemetry tracing
- `attach_guardrails()` - Rate limiting & timeouts
- `add_health_endpoints()` - Health checks

## 🎓 Patterns & Best Practices

### 1. Always Use R&D Framework

When context is growing:
- **First try REDUCE** - Remove unused tools, trim memory
- **Then DELEGATE** - Offload to specialized agent

### 2. Prefer Specialists Over Generalists

Instead of one agent doing everything:
- Use Scout Expert for exploration
- Use Plan Expert for strategy
- Use Build Expert for execution

### 3. Use Context Bundles for Long-Running Work

For tasks that might exceed context limits:
- Start bundle at beginning
- Record all operations
- Can replay to new agent with ~70% context

### 4. Leverage Background Agents

For independent work:
- Delegate to background agent
- Agent reports when done
- No need to stay in-loop

### 5. Scout Before Building

Always follow Scout-Plan-Build:
1. Scout to understand landscape
2. Plan the approach
3. Build the solution

## 📈 Performance Characteristics

Based on IndyDevDan's findings:

- **Context Efficiency**: 85-95% with proper R&D management
- **Token Savings**: 20,000-40,000 tokens per delegation
- **Workflow Speed**: 3-5x faster with parallel execution
- **Context Recovery**: ~70% with context bundles

## 🔐 Security

- Rate limiting on all endpoints
- Request size limits (5MB default)
- Request timeouts (30s default)
- Secrets management via environment variables
- Audit logging for all operations

## 📝 License

See project root LICENSE file.

## 🙏 Credits

Based on patterns and principles from **IndyDevDan** ([YouTube](https://www.youtube.com/@indydevdan)):
- R&D Framework (Reduce & Delegate)
- Context Engineering techniques
- Scout-Plan-Build workflow
- Agent Expert patterns
- Multi-agent delegation strategies

## 🚧 Roadmap

- [ ] Real agent execution (currently simulated)
- [ ] MCP server integration
- [ ] WebSocket support for real-time updates
- [ ] Advanced workflow DAGs
- [ ] Agent learning/improvement loops
- [ ] Cloud deployment configs (K8s, Docker Compose)

