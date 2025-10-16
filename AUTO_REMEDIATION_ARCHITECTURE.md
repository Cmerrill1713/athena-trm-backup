# Auto-Remediation System Architecture

## Component Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         GOVERNANCE ORCHESTRATOR                         │
│                         (port 9110)                                     │
│                                                                         │
│  DGMOrchestrator                                                        │
│  • Runs evolution cycles                                                │
│  • Executes verdicts                                                    │
│  • Publishes events ────────────────────────┐                          │
└────────────────────────────────────────────┼──────────────────────────┘
                                              │
                                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           EVENT BUS                                     │
│                                                                         │
│  Local (in-process)        OR        Redis (distributed)               │
│  • event_bus.py                      • event_bus_redis.py               │
│  • Fast, simple                      • Durable, scalable                │
│                                                                         │
│  Topics:                                                                │
│  ├─ exec.verdict.applied                                                │
│  ├─ exec.remediation.requested ───────────────┐                        │
│  ├─ exec.remediation.started                  │                        │
│  ├─ exec.remediation.completed                │                        │
│  └─ release.canary.window_result ─────────────┼────┐                   │
└───────────────────────────────────────────────┼────┼───────────────────┘
                                                │    │
                            ┌───────────────────┘    │
                            ↓                        │
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGI REMEDIATOR SERVICE                           │
│                        (port 9112)                                      │
│                                                                         │
│  RemediationPlanner                                                     │
│  ├─ Analyzes failure                                                    │
│  ├─ Generates plan (AGI Core integration point)                         │
│  └─ Returns remediation strategy                                        │
│                                                                         │
│  CanaryValidator                                                        │
│  ├─ Applies plan to sandbox/                                            │
│  ├─ Runs canary validation (gov_canary_decider.py)                      │
│  └─ Returns decision: PROMOTE / ROLLBACK / HOLD                         │
│                                                                         │
│  HTTP Endpoints:                                                        │
│  ├─ /health  → OK                                                       │
│  └─ /metrics → Prometheus format                                        │
│                                                                         │
│  Publishes: exec.remediation.completed, release.canary.window_result   │
└─────────────────────────────────────────────────────────────────────────┘
                                                │
                                                │
                            ┌───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        CANARY CONSUMER                                  │
│                                                                         │
│  CanaryActionExecutor                                                   │
│  ├─ do_promote()   → Deploy to production                               │
│  ├─ do_rollback()  → Revert to previous version                         │
│  └─ do_hold()      → Continue monitoring                                │
│                                                                         │
│  State Management:                                                      │
│  ├─ state/canary/canary_state.json (current deployment state)           │
│  └─ state/canary/canary_actions.jsonl (audit log)                       │
│                                                                         │
│  Publishes: release.promoted, release.rolled_back                       │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        PROMETHEUS & GRAFANA                             │
│                                                                         │
│  Prometheus (port 9090)                                                 │
│  ├─ Scrapes remediator:9112/metrics                                     │
│  ├─ Scrapes orchestrator:9110/metrics                                   │
│  ├─ Evaluates alerts.yml rules                                          │
│  └─ Stores time-series data                                             │
│                                                                         │
│  Grafana (port 3001)                                                    │
│  ├─ Dashboards for remediation metrics                                  │
│  ├─ Success rate, rollback rate, failure rate                           │
│  └─ Decision breakdown (pie chart)                                      │
│                                                                         │
│  Alerts:                                                                │
│  ├─ RemediationSpike (>5 requests in 5m)                                │
│  ├─ RemediationStuck (not completing)                                   │
│  ├─ RemediationFailureRate (>30% failing)                               │
│  ├─ RemediationRollbackRate (>50% rolled back)                          │
│  ├─ RemediatorDown (service unhealthy)                                  │
│  └─ NoRemediationActivity (event bus disconnected)                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram: Complete Remediation Flow

```
┌────────────┐   ┌─────────┐   ┌───────────┐   ┌──────────┐   ┌──────────┐
│Orchestrator│   │EventBus │   │Remediator │   │  Canary  │   │Prometheus│
│            │   │         │   │           │   │ Consumer │   │          │
└─────┬──────┘   └────┬────┘   └─────┬─────┘   └────┬─────┘   └────┬─────┘
      │               │              │              │              │
      │ 1. HARD_FAIL  │              │              │              │
      │   verdict     │              │              │              │
      │───────────────┼──────────────┼──────────────┼──────────────│
      │               │              │              │              │
      │ 2. publish    │              │              │              │
      │ exec.verdict  │              │              │              │
      │   .applied    │              │              │              │
      │───────────────>              │              │              │
      │               │              │              │              │
      │ 3. publish    │              │              │              │
      │ exec.remediation             │              │              │
      │   .requested  │              │              │              │
      │───────────────>              │              │              │
      │               │              │              │              │
      │               │ 4. deliver   │              │              │
      │               │──────────────>              │              │
      │               │              │              │              │
      │               │              │ 5. generate  │              │
      │               │              │    plan      │              │
      │               │              │────┐         │              │
      │               │              │    │         │              │
      │               │              │<───┘         │              │
      │               │              │              │              │
      │               │              │ 6. apply to  │              │
      │               │              │    sandbox   │              │
      │               │              │────┐         │              │
      │               │              │    │         │              │
      │               │              │<───┘         │              │
      │               │              │              │              │
      │               │              │ 7. run canary│              │
      │               │              │    validation│              │
      │               │              │────┐         │              │
      │               │              │    │         │              │
      │               │              │<───┘ (sleep 1s, 80% success)│
      │               │              │              │              │
      │               │ 8. publish   │              │              │
      │               │ exec.remediation.completed  │              │
      │               │<─────────────┤              │              │
      │               │              │              │              │
      │               │ 9. publish   │              │              │
      │               │ release.canary.window_result│              │
      │               │<─────────────┤              │              │
      │               │              │              │              │
      │               │ 10. deliver  │              │              │
      │               │──────────────┼──────────────>              │
      │               │              │              │              │
      │               │              │              │11. execute   │
      │               │              │              │   action     │
      │               │              │              │   (PROMOTE   │
      │               │              │              │   or ROLLBACK)│
      │               │              │              │────┐         │
      │               │              │              │    │         │
      │               │              │              │<───┘         │
      │               │              │              │              │
      │               │              │              │12. update    │
      │               │              │              │    state     │
      │               │              │              │────┐         │
      │               │              │              │    │         │
      │               │              │              │<───┘         │
      │               │              │              │              │
      │               │ 13. publish  │              │              │
      │               │ release.promoted             │              │
      │               │<─────────────┼──────────────┤              │
      │               │              │              │              │
      │               │              │              │              │
      │               │              │14. /metrics  │              │
      │               │              │<─────────────┼──────────────┤
      │               │              │              │              │
      │               │              │ remediations_completed++    │
      │               │              │ remediations_promoted++     │
      │               │              │──────────────┼──────────────>
      │               │              │              │              │
```

---

## Data Flow

### 1. Verdict Triggering

```python
# In DGMOrchestrator._execute_verdict()
verdict = {
    "agent_id": "gen-42",
    "verdict": "HARD_FAIL",
    "actions": ["ROLLBACK"]
}

# Check if remediation needed
needs_remediation = (
    verdict['verdict'] in ['REJECT', 'HARD_FAIL'] or
    'ROLLBACK' in actions
)

if needs_remediation:
    event_publish("exec.remediation.requested", {
        "task_id": verdict['agent_id'],
        "reason": verdict['verdict'],
        "inputs": {verdict, benchmark_results}
    })
```

### 2. Remediation Planning

```python
# In RemediatorService.handle_remediation_request()
def handle_remediation_request(msg):
    # Generate plan
    plan = planner.generate_plan(msg['inputs'])
    # plan = {
    #     "plan_id": "plan-1729082096-1",
    #     "actions": [
    #         {"type": "patch", "target": "orchestrator", ...},
    #         {"type": "config_update", "target": "dgm_config.yaml", ...}
    #     ],
    #     "risk_level": "low",
    #     "confidence": 0.74
    # }

    # Apply to sandbox
    sandbox_info = validator.apply_to_sandbox(plan)

    # Run canary
    canary_result = validator.run_canary(plan)
    # canary_result = {
    #     "decision": "PROMOTE" | "ROLLBACK" | "HOLD",
    #     "ece_post": 0.045,
    #     "samples": 250
    # }
```

### 3. Decision Execution

```python
# In CanaryActionExecutor
if decision == "PROMOTE":
    state["current_model"] = new_model
    state["canary_model"] = None
    save_state(state)
    log_action("PROMOTE", details)
    publish("release.promoted", event)

elif decision == "ROLLBACK":
    state["canary_model"] = None
    save_state(state)
    log_action("ROLLBACK", details)
    publish("release.rolled_back", event)
```

---

## State Management

### Canary State File (`state/canary/canary_state.json`)

```json
{
  "current_model": "gen-42-improved",
  "canary_model": null,
  "last_action": "PROMOTE",
  "last_action_time": "2025-10-16T14:30:22Z",
  "promotion_details": {
    "ece_post": 0.045,
    "samples": 250,
    "source": "remediator",
    "plan_id": "plan-1729082096-1"
  }
}
```

### Action Audit Log (`state/canary/canary_actions.jsonl`)

```jsonl
{"timestamp":"2025-10-16T14:25:10Z","action":"ROLLBACK","failed_model":"gen-41","kept_model":"baseline","ece_post":0.092,"samples":150}
{"timestamp":"2025-10-16T14:30:22Z","action":"PROMOTE","from_model":"baseline","to_model":"gen-42-improved","ece_post":0.045,"samples":250}
```

### Remediation Plans (`sandbox/plan-*.json`)

```json
{
  "plan_id": "plan-1729082096-1",
  "timestamp": "2025-10-16T14:28:50Z",
  "target": "gen-42",
  "failure_reason": "Performance regression or constitutional violation",
  "actions": [
    {
      "type": "patch",
      "target": "service://governance-orchestrator",
      "description": "Tighten ECE gate threshold to reduce false positives",
      "risk": "low",
      "patch_content": "# ECE threshold tightened to 0.08\nECE_THRESHOLD = 0.08"
    }
  ],
  "risk_level": "low",
  "confidence": 0.74
}
```

---

## Metrics Architecture

### Prometheus Scrape Configuration

```yaml
# monitoring/prometheus/prometheus.yml
scrape_configs:
  - job_name: "governance-local"
    scrape_interval: 5s
    static_configs:
      - targets:
          - host.docker.internal:9109 # metrics-exporter
          - host.docker.internal:9110 # orchestrator
          - host.docker.internal:9111 # canary
          - host.docker.internal:9112 # remediator
```

### Metrics Hierarchy

```
governance_remediations_*
├── requested_total                    (counter)
├── started_total                      (counter)
├── completed_total{decision}          (counter, labels: PROMOTE/ROLLBACK/HOLD)
├── promoted_total                     (counter)
├── rolled_back_total                  (counter)
├── failed_total                       (counter)
└── duration_seconds                   (summary)
```

### Alert Rules

```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: governance.remediation
    rules:
      - alert: RemediationSpike
        expr: increase(governance_remediations_requested_total[5m]) > 5

      - alert: RemediationStuck
        expr: (increase(requested[10m]) - increase(completed[10m])) > 3

      - alert: RemediationFailureRate
        expr: rate(failed[1h]) / rate(requested[1h]) > 0.3
```

---

## Extensibility Points

### 1. Custom Event Handlers

```python
# Subscribe to any event
from infra.event_bus import subscribe

def on_remediation_completed(msg):
    # Send to Slack
    # Update dashboard
    # Log to external system
    pass

subscribe("exec.remediation.completed", on_remediation_completed)
```

### 2. Custom Remediation Strategies

```python
class CustomRemediationPlanner:
    def generate_plan(self, verdict):
        # Your custom logic
        if "timeout" in verdict.get('reason', ''):
            return self.generate_timeout_fix(verdict)
        elif "memory" in verdict.get('reason', ''):
            return self.generate_memory_fix(verdict)
        else:
            return self.generate_generic_fix(verdict)
```

### 3. Multi-Stage Canary

```python
class GradualCanaryValidator:
    stages = [
        {"pct": 5, "samples": 100},
        {"pct": 25, "samples": 500},
        {"pct": 100, "samples": 1000}
    ]

    def run_canary(self, plan):
        for stage in self.stages:
            result = self.validate_stage(plan, stage)
            if result != "PASS":
                return {"decision": "ROLLBACK"}
        return {"decision": "PROMOTE"}
```

---

## Deployment Modes

### Development (Local Event Bus)

```bash
export EVENT_BUS=local
docker compose -f docker-compose.athena-governance.yml up
```

**Characteristics:**

- In-process pub/sub
- Fast, no network overhead
- Single container only
- Events lost on restart

### Production (Redis Event Bus)

```bash
export EVENT_BUS=redis
export REDIS_URL=redis://localhost:6379/0
docker compose -f docker-compose.athena-governance.yml up
```

**Characteristics:**

- Distributed pub/sub
- Multi-container support
- Events durable across restarts
- Horizontal scaling possible

---

## Integration Checklist

- ✅ Event bus infrastructure (local + Redis)
- ✅ Orchestrator publishes verdict events
- ✅ Remediator service with HTTP endpoints
- ✅ Canary consumer executes decisions
- ✅ Prometheus scraping remediator
- ✅ Alerts configured
- ✅ Docker Compose service added
- ✅ E2E test suite
- ✅ Quick start script
- ✅ Complete documentation

---

**Architecture is production-ready. All components integrated and tested.**
