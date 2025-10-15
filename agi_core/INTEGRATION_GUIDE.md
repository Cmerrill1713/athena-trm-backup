# AGI Core Integration Guide

How to integrate AGI Core with your existing systems.

## Integration with Governance System

Your existing governance orchestrator at `/orchestrator/app.py` can integrate with AGI Core:

### 1. Add AGI Core to Governance Pipeline

```python
# In your governance orchestrator
import requests

# After receiving a verdict, delegate remediation to AGI
def handle_hard_fail(verdict):
    # Existing rollback logic...
    
    # Delegate investigation to AGI expert
    response = requests.post("http://localhost:8100/experts/task/submit", json={
        "task_type": "debugging",
        "description": f"Investigate failure: {verdict.task_id}",
        "context": {
            "verdict": verdict.verdict,
            "ece": verdict.ece_estimate,
            "metrics": {
                "violation_rate_delta": verdict.violation_rate_delta,
                "latency_p95_delta": verdict.latency_p95_delta
            }
        },
        "priority": 9
    })
    
    task_id = response.json()["task_id"]
    
    # Execute task
    requests.post(f"http://localhost:8100/experts/task/{task_id}/execute")
```

### 2. Report AGI Metrics to Governance

```python
# After AGI workflow completes
def report_agi_metrics(workflow_id, result):
    response = requests.post("http://localhost:8000/verdict", json={
        "task_id": workflow_id,
        "verdict": "PASS" if result["success"] else "SOFT_FAIL",
        "ece_estimate": result.get("context_efficiency", 0.85),
        "meta": {
            "agi_workflow": True,
            "workflow_type": result["workflow_type"],
            "duration": result["duration_seconds"]
        }
    })
```

## Integration with Sentry

AGI Core already integrates with Sentry when `sentry_sdk` is installed:

### 1. Configure Sentry DSN

```bash
export SENTRY_DSN="your-sentry-dsn"
export SENTRY_ENVIRONMENT="production"
```

### 2. Initialize in Application Code

```python
# Sentry is auto-configured in agi_service.py
# All errors and performance data are automatically captured
```

### 3. Custom Sentry Instrumentation

Add custom spans for AGI operations:

```python
import sentry_sdk

def execute_agent_task(task):
    with sentry_sdk.start_span(op="agi.task", description="Execute Agent Task") as span:
        span.set_data("task_id", task.task_id)
        span.set_data("agent_type", task.agent_type)
        
        # Execute task
        result = agent.execute(task)
        
        span.set_data("success", result.success)
        span.set_data("tokens_used", result.tokens_used)
        
        return result
```

## Integration with Common Ops

AGI Core uses your existing `common/ops.py`:

```python
from common.ops import wire_tracing, attach_guardrails, add_health_endpoints

app = FastAPI()

# Wire operational concerns
wire_tracing(app, "agi-core")        # OpenTelemetry tracing
attach_guardrails(app)                # Rate limiting, timeouts
add_health_endpoints(app)             # /health, /ready, /metrics
```

## Adding Custom Experts

Register domain-specific experts:

```python
from agi_core.agent_experts import AgentExpert, ExpertDomain, ExpertRegistry

# Create custom expert
trading_expert = AgentExpert(
    expert_id="trading_expert",
    domain=ExpertDomain.OPTIMIZATION,  # or create custom domain
    name="Trading Strategy Expert",
    description="Specialist in optimizing trading strategies",
    system_prompt="""You are a trading strategy expert. Your role:
    - Analyze strategy performance
    - Identify optimization opportunities
    - Suggest parameter adjustments
    - Validate against risk constraints
    - Use focused context on relevant metrics""",
    tools=["read_file", "codebase_search", "run_terminal_cmd"],
    max_context_tokens=30000,
    capabilities=["backtesting", "optimization", "risk_analysis"]
)

# Register with registry
registry = ExpertRegistry()
registry.register_expert(trading_expert)
```

## Service Mesh Integration

### Docker Compose Setup

```yaml
services:
  agi-core:
    image: agi-core:latest
    ports:
      - "8100:8100"
    environment:
      - AGI_SERVICE_PORT=8100
      - OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
    networks:
      - governance-network

  governance-orchestrator:
    image: governance-orchestrator:latest
    ports:
      - "8000:8000"
    environment:
      - AGI_SERVICE_URL=http://agi-core:8100
    networks:
      - governance-network

networks:
  governance-network:
    driver: bridge
```

### Kubernetes Setup

```yaml
apiVersion: v1
kind: Service
metadata:
  name: agi-core
spec:
  selector:
    app: agi-core
  ports:
    - port: 8100
      targetPort: 8100
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agi-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agi-core
  template:
    metadata:
      labels:
        app: agi-core
    spec:
      containers:
      - name: agi-core
        image: agi-core:latest
        ports:
        - containerPort: 8100
        env:
        - name: AGI_SERVICE_PORT
          value: "8100"
        - name: OTLP_ENDPOINT
          value: "http://otel-collector:4318/v1/traces"
        livenessProbe:
          httpGet:
            path: /health
            port: 8100
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8100
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Event Bus Integration

Emit AGI events to your event bus:

```python
# In agi_service.py, add event emission

import asyncio
from nats.aio.client import Client as NATS

nc = NATS()

async def emit_agi_event(event_type: str, payload: dict):
    """Emit AGI event to NATS"""
    await nc.connect("nats://localhost:4222")
    await nc.publish(f"agi.{event_type}", json.dumps(payload).encode())

# Emit on key operations
@app.post("/workflow/execute")
async def execute_workflow(request: WorkflowExecuteRequest):
    result = workflow_orchestrator.execute_workflow(workflow_id)
    
    # Emit event
    await emit_agi_event("workflow.completed", {
        "workflow_id": workflow_id,
        "type": request.workflow_type,
        "duration": result["duration_seconds"],
        "success": True
    })
    
    return result
```

## Monitoring & Alerting

### Prometheus Rules

```yaml
groups:
  - name: agi_core
    interval: 30s
    rules:
      # Context efficiency below threshold
      - alert: AGILowContextEfficiency
        expr: agi_context_efficiency < 0.7
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AGI context efficiency low"
          description: "Context efficiency is {{ $value }} (< 70%)"
      
      # Workflow failures
      - alert: AGIWorkflowFailures
        expr: rate(agi_workflow_executions_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High AGI workflow failure rate"
          description: "{{ $value }} workflow failures/sec"
      
      # High delegation latency
      - alert: AGIDelegationLatency
        expr: histogram_quantile(0.95, agi_workflow_duration_seconds) > 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "AGI delegation latency high"
          description: "P95 latency is {{ $value }}s (> 300s)"
```

### Grafana Dashboard

Import the provided dashboard JSON:

```bash
# See grafana-dashboards/agi-core.json
```

Key panels:
- Context efficiency over time
- Active agents count
- Workflow execution rate
- Token usage histogram
- Delegation strategy breakdown

## Testing Integration

```python
import pytest
import requests

@pytest.fixture
def agi_service():
    """Start AGI service for testing"""
    # Use test configuration
    os.environ["AGI_STATE_DIR"] = "/tmp/agi_test"
    # Start service...
    yield "http://localhost:8100"

def test_governance_integration(agi_service):
    """Test governance integration"""
    # Submit expert task
    response = requests.post(f"{agi_service}/experts/task/submit", json={
        "task_type": "debugging",
        "description": "Test task",
        "context": {},
        "priority": 5
    })
    
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    
    # Execute task
    response = requests.post(f"{agi_service}/experts/task/{task_id}/execute")
    assert response.status_code == 200

def test_workflow_execution(agi_service):
    """Test workflow execution"""
    response = requests.post(f"{agi_service}/workflow/execute", json={
        "workflow_type": "background",
        "task_description": "Test workflow",
        "context": {}
    })
    
    assert response.status_code == 200
    assert "workflow_id" in response.json()
```

## Production Deployment Checklist

- [ ] Configure Sentry DSN
- [ ] Set up OpenTelemetry collector
- [ ] Configure Prometheus scraping
- [ ] Set up Grafana dashboards
- [ ] Configure rate limits in `attach_guardrails()`
- [ ] Set up persistent storage for state directory
- [ ] Configure backup strategy for context bundles
- [ ] Set up monitoring alerts
- [ ] Enable authentication/authorization
- [ ] Configure network policies
- [ ] Set resource limits (CPU, memory)
- [ ] Enable HTTPS/TLS
- [ ] Set up log aggregation
- [ ] Configure auto-scaling policies
- [ ] Document runbooks for common issues
- [ ] Set up on-call rotation

## Troubleshooting

### High Context Usage

```python
# Check context status
response = requests.get("http://localhost:8100/context/agent_123/status")
status = response.json()

if status["utilization_percent"] > 75:
    # Apply REDUCE strategy
    requests.post("http://localhost:8100/context/reduce", json={
        "agent_id": "agent_123",
        "strategy": "auto"
    })
```

### Agent Stuck/Not Responding

```python
# Check active agents
response = requests.get("http://localhost:8100/delegation/agents/active")
active_agents = response.json()

# Check specific agent status
for agent in active_agents:
    status = requests.get(f"http://localhost:8100/delegation/agent/{agent['agent_id']}/status")
    print(status.json())
```

### Workflow Not Completing

```bash
# Check workflow status
curl http://localhost:8100/workflow/wf_123/status

# Check service logs
docker logs agi-core

# Check Prometheus metrics
curl http://localhost:8100/metrics | grep agi_workflow
```

## Support

For issues specific to AGI Core:
- Check logs: `docker logs agi-core`
- Check metrics: `http://localhost:8100/metrics`
- Check health: `http://localhost:8100/health`
- Check stats: `http://localhost:8100/stats`

For integration issues:
- Verify network connectivity between services
- Check environment variables
- Verify API endpoints are accessible
- Check Sentry for error traces
- Check OpenTelemetry traces for request flow

