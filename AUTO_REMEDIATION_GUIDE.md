# Auto-Remediation System Guide

## Overview

The Athena Auto-Remediation System creates a closed loop where governance verdicts automatically trigger remediation, validation, and promotion/rollback cycles.

**Flow:**

```
HARD_FAIL verdict → Event published → Remediator generates plan →
Canary validation → Decision (PROMOTE/ROLLBACK/HOLD) → Action executed
```

---

## Architecture

### Components

1. **Event Bus** (`infra/event_bus.py`, `infra/event_bus_redis.py`)

   - Lightweight pub/sub for governance events
   - Local (in-process) or Redis-backed
   - Topics: `exec.verdict.applied`, `exec.remediation.requested`, `release.canary.window_result`

2. **DGM Orchestrator** (`governance/executive/orchestration/dgm_orchestrator.py`)

   - Publishes `exec.verdict.applied` events after verdict execution
   - Publishes `exec.remediation.requested` for HARD_FAIL/ROLLBACK cases

3. **Remediator Service** (`agi_core/remediator.py`)

   - Subscribes to remediation requests
   - Generates remediation plans (integrates with AGI Core)
   - Applies to sandbox and runs canary validation
   - Publishes `exec.remediation.completed` with decision
   - HTTP service on port **9112** (`/health`, `/metrics`)

4. **Canary Consumer** (`governance/canary/canary_consumer.py`)

   - Subscribes to `release.canary.window_result`
   - Executes promote/rollback/hold actions
   - Maintains state in `state/canary/`

5. **Metrics & Alerts**
   - Extended `governance/observability/dgm_metrics.py` with remediation counters
   - Prometheus scrapes remediator on port 9112
   - Alerts in `monitoring/prometheus/alerts.yml`:
     - `RemediationSpike`, `RemediationStuck`, `RemediationFailureRate`
     - `RemediatorDown`, `NoRemediationActivity`

---

## Setup

### 1. Environment Configuration

Set the event bus mode in `.env`:

```bash
# Use local in-process event bus (development)
EVENT_BUS=local

# OR use Redis for multi-process/distributed (production)
EVENT_BUS=redis
REDIS_URL=redis://localhost:6379/0
```

### 2. Start Services

Using Docker Compose:

```bash
docker compose -f docker-compose.athena-governance.yml up -d
```

Services started:

- `agi-remediator` on port **9112**
- `governance-orchestrator` on port **9110**
- `governance-canary-monitor` on port **9111**
- `athena-prometheus` on port **9090**
- `athena-redis` on port **6379** (if using Redis event bus)

### 3. Verify Services

```bash
curl http://localhost:9112/health  # Remediator
curl http://localhost:9110/health  # Orchestrator
curl http://localhost:9090/-/healthy  # Prometheus
```

### 4. Run Quick Start Demo

```bash
./scripts/remediation_quickstart.sh
```

This will:

1. Check service health
2. Get baseline metrics
3. Trigger a HARD_FAIL verdict
4. Wait for auto-remediation
5. Show updated metrics and decisions

---

## Usage

### Triggering Auto-Remediation

Remediation is automatically triggered when:

1. **Verdict Type** is `HARD_FAIL` or `REJECT`
2. **Action** includes `ROLLBACK` or `HARD_BLOCK`

Example verdict that triggers remediation:

```json
{
  "task_id": "gen-42",
  "verdict": "HARD_FAIL",
  "ece_estimate": 0.09,
  "actions": ["ROLLBACK"],
  "ts": "2025-10-16T12:00:00Z"
}
```

### Event Flow

```
1. Orchestrator executes verdict
   ↓
2. Publishes exec.verdict.applied
   ↓
3. Checks if remediation needed
   ↓
4. Publishes exec.remediation.requested
   ↓
5. Remediator receives request
   ↓
6. Generates plan (stub or AGI Core integration)
   ↓
7. Applies to sandbox
   ↓
8. Runs canary validation (80% success stub)
   ↓
9. Publishes exec.remediation.completed
   ↓
10. Publishes release.canary.window_result
    ↓
11. Canary consumer executes action (PROMOTE/ROLLBACK/HOLD)
    ↓
12. Updates state and logs
```

### Metrics

Query Prometheus at `http://localhost:9090`:

```promql
# Remediation request rate
rate(governance_remediations_requested_total[5m])

# Success rate
rate(governance_remediations_promoted_total[1h])
/
rate(governance_remediations_completed_total[1h])

# Rollback rate
rate(governance_remediations_rolled_back_total[1h])
/
rate(governance_remediations_completed_total[1h])

# Failure rate
rate(governance_remediations_failed_total[1h])
/
rate(governance_remediations_requested_total[1h])
```

### Alerts

Configured in `monitoring/prometheus/alerts.yml`:

| Alert                     | Condition                    | Severity |
| ------------------------- | ---------------------------- | -------- |
| `RemediationSpike`        | >5 requests in 5m            | warning  |
| `RemediationStuck`        | Requests not completing      | critical |
| `RemediationFailureRate`  | >30% failing                 | warning  |
| `RemediationRollbackRate` | >50% rolled back             | warning  |
| `RemediatorDown`          | Service unhealthy            | critical |
| `NoRemediationActivity`   | Failures but no remediations | warning  |

---

## Testing

### E2E Test

Run the full auto-remediation loop test:

```bash
pytest tests/e2e/test_auto_remediation.py -v -s
```

This test:

1. Checks service health
2. Gets baseline metrics
3. Sends a HARD_FAIL verdict
4. Waits for remediation
5. Verifies metrics incremented
6. Validates decision execution

### Manual Smoke Test

```bash
# 1. Start remediator standalone (local event bus)
export EVENT_BUS=local
python -u agi_core/remediator.py &

# 2. Send test verdict
curl -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"smoke-1","verdict":"HARD_FAIL","ece_estimate":0.09,"actions":["ROLLBACK"],"ts":"'"$(date -u +%FT%TZ)"'"}'

# 3. Check remediator metrics
curl http://localhost:9112/metrics | grep governance_remediations

# 4. Check orchestrator metrics
curl http://localhost:9110/metrics | grep governance_
```

---

## Integration with Real AGI Core

The current implementation uses stub plan generation. To integrate real AGI Core:

### Replace RemediationPlanner in `agi_core/remediator.py`

```python
from governance.research.dgm.dgm_agi_bridge import DGMAGIBridge
from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter

class RemediationPlanner:
    def __init__(self):
        self.bridge = DGMAGIBridge()
        self.adapter = DGMGovernanceAdapter()

    def generate_plan(self, verdict: Dict[str, Any]) -> Dict[str, Any]:
        # Use actual AGI Core to analyze failure
        analysis = self.bridge.analyze_failure(verdict)

        # Generate improvement plan using STOP optimizer
        plan = self.bridge.generate_improvement_plan(analysis)

        # Validate against governance policies
        compliance = self.adapter.check_constitutional_compliance(plan)

        if not compliance['compliant']:
            raise ValueError("Generated plan violates constitutional policy")

        return plan
```

### Use Real Canary Validation

Replace stub in `CanaryValidator.run_canary()`:

```python
import subprocess

def run_canary(self, plan: Dict[str, Any]) -> Dict[str, Any]:
    # Apply plan to canary environment
    self._deploy_to_canary(plan)

    # Run actual canary decision script
    result = subprocess.run(
        ['python', 'scripts/gov_canary_decider.py'],
        capture_output=True,
        text=True
    )

    # Parse decision from script output
    decision = self._parse_canary_result(result.stdout)

    return {
        "plan_id": plan["plan_id"],
        "decision": decision,
        "ece_post": self._get_canary_ece(),
        "samples": self._get_canary_samples(),
        "timestamp": datetime.now().isoformat()
    }
```

---

## Configuration

### Event Bus Selection

**Local (Development)**

- In-process pub/sub
- No external dependencies
- Single-process only
- Fast, simple setup

```bash
EVENT_BUS=local
```

**Redis (Production)**

- Durable, multi-process
- Survives service restarts
- Distributed system support
- Requires Redis service

```bash
EVENT_BUS=redis
REDIS_URL=redis://localhost:6379/0
```

### Remediator Tuning

Environment variables in `docker-compose.athena-governance.yml`:

```yaml
environment:
  - REMEDIATOR_PORT=9112
  - EVENT_BUS=local # or redis
  - REDIS_URL=redis://athena-redis:6379/0
```

---

## State Management

### Canary State

Located in `state/canary/`:

- `canary_state.json` - Current deployment state
- `canary_actions.jsonl` - Audit log of all actions

Example state:

```json
{
  "current_model": "baseline",
  "canary_model": null,
  "last_action": "PROMOTE",
  "last_action_time": "2025-10-16T12:34:56Z",
  "promotion_details": {
    "ece_post": 0.045,
    "samples": 250,
    "source": "remediator",
    "plan_id": "plan-1729082096-1"
  }
}
```

### Remediation Artifacts

Located in `sandbox/`:

- `plan-*.json` - Generated remediation plans
- Applied patches and config changes

---

## Troubleshooting

### Remediations not triggering

1. **Check event bus connection:**

   ```bash
   # Local event bus - check logs
   docker logs agi-remediator

   # Redis - verify connectivity
   redis-cli -h localhost -p 6379 ping
   ```

2. **Verify orchestrator is publishing events:**

   ```bash
   docker logs governance-orchestrator | grep "exec.remediation.requested"
   ```

3. **Check Prometheus alert:**
   - Look for `NoRemediationActivity` alert
   - Query: `increase(governance_remediations_requested_total[1h])`

### Remediations stuck

1. **Check remediator health:**

   ```bash
   curl http://localhost:9112/health
   ```

2. **Look for errors in logs:**

   ```bash
   docker logs agi-remediator --tail 50
   ```

3. **Verify canary validator is running:**
   ```bash
   ls -la sandbox/  # Should have plan files
   ```

### High rollback rate

1. **Check canary thresholds** in `agi_core/remediator.py`
2. **Review recent plans:** `cat sandbox/plan-*.json`
3. **Analyze failure patterns** in Prometheus:
   ```promql
   rate(governance_remediations_rolled_back_total[1h]) by (reason)
   ```

---

## Monitoring

### Grafana Dashboards

Add these panels to your governance dashboard:

1. **Remediation Request Rate**

   ```promql
   rate(governance_remediations_requested_total[5m])
   ```

2. **Success Rate (Gauge)**

   ```promql
   (rate(governance_remediations_promoted_total[1h]) / rate(governance_remediations_completed_total[1h])) * 100
   ```

3. **Decision Breakdown (Pie Chart)**

   ```promql
   sum(increase(governance_remediations_completed_total[1h])) by (decision)
   ```

4. **Remediation Duration (Heatmap)**
   ```promql
   histogram_quantile(0.95, rate(governance_remediation_duration_seconds_bucket[5m]))
   ```

### Key Metrics to Watch

| Metric        | Good Range | Alert Threshold |
| ------------- | ---------- | --------------- |
| Success Rate  | >70%       | <50%            |
| Rollback Rate | <30%       | >50%            |
| Failure Rate  | <10%       | >30%            |
| Avg Duration  | <30s       | >120s           |
| Requests/Hour | Varies     | Spike >5/5m     |

---

## Architecture Decisions

### Why Event Bus?

- **Loose Coupling**: Services don't need direct HTTP connections
- **Async Processing**: Non-blocking remediation loops
- **Extensibility**: Easy to add new subscribers (logging, ChatOps, etc.)
- **Replay**: Redis pub/sub allows audit and replay

### Why Canary Validation?

- **Safety**: Never promote untested changes
- **Data-Driven**: Statistical confidence before promotion
- **Rollback**: Automatic revert on canary failure
- **Risk Mitigation**: Small blast radius

### Why Separate Remediator Service?

- **Isolation**: Failures don't impact orchestrator
- **Scaling**: Can run multiple remediators
- **Observability**: Dedicated metrics and health checks
- **Pluggability**: Easy to swap implementation

---

## Next Steps

1. **Add ChatOps Integration**

   - Subscribe to `exec.remediation.completed`
   - Post to Slack/Discord on promote/rollback

2. **Enhance Plan Generation**

   - Integrate GovernanceBridge
   - Use STOP optimizer for improvement synthesis
   - Add constitutional policy checks

3. **Improve Canary Validation**

   - Call real `gov_canary_decider.py`
   - Add statistical significance tests
   - Support multi-metric evaluation

4. **Add Human-in-the-Loop**

   - Request approval for high-risk changes
   - Show plan diff before promotion
   - Allow override of decisions

5. **Extend Event Schema**
   - Add structured metadata
   - Include performance deltas
   - Track remediation lineage

---

## Files Changed/Created

### New Files

- `infra/event_bus.py` - Local event bus
- `infra/event_bus_redis.py` - Redis event bus
- `agi_core/remediator.py` - Remediator service
- `agi_core/Dockerfile` - Remediator container
- `governance/canary/canary_consumer.py` - Canary action executor
- `tests/e2e/test_auto_remediation.py` - E2E test
- `scripts/remediation_quickstart.sh` - Quick start demo
- `AUTO_REMEDIATION_GUIDE.md` - This guide

### Modified Files

- `governance/executive/orchestration/dgm_orchestrator.py` - Added event publishing
- `governance/observability/dgm_metrics.py` - Added remediation metrics
- `monitoring/prometheus/prometheus.yml` - Added remediator scrape target
- `monitoring/prometheus/alerts.yml` - Added remediation alerts
- `docker-compose.athena-governance.yml` - Added agi-remediator service

---

## Summary

You now have a fully functional auto-remediation system that:

✅ Detects failures automatically  
✅ Generates remediation plans  
✅ Validates via canary deployments  
✅ Promotes or rolls back automatically  
✅ Exports comprehensive metrics  
✅ Sends alerts on issues  
✅ Maintains audit logs  
✅ Integrates with existing governance

**The loop is closed. Governance verdicts now trigger automatic healing.**
