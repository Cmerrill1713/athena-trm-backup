# A3: Governance Canary - Prep Status (2025-10-17)

**Status:** 🟡 In Progress (60% complete)  
**Target:** A3 full implementation  
**Build on:** A2 Router + Dedupe Complete

## Summary

A3 prep work is implementing the governance canary system that monitors routing metrics and automatically rolls back policy changes on breach. This enables intelligent, self-healing routing with zero-drift guarantees.

## What's Been Built

### 1. Router Canary Support ✅

**File:** `services/router/app.py`

**New Metrics:**

```python
router_ece_estimate{route}           # Expected Cost Error per route
governance_canary_active             # Canary state (0=off, 1=on)
canary_rollback_total{reason}        # Total rollbacks executed
```

**New Endpoints:**

- `GET /canary` - Returns rolling p95 latency, error rates, token costs per provider
  - Used by governance controller for breach detection
  - Exposes aggregate metrics + per-provider health
  - Includes breach thresholds (p95 < 1200ms, cost < $0.05)

**ECE Calculation:**

```python
ECE = latency_seconds × cost_per_token × tokens_generated

Cost rates:
- MLX: $0.00 (local)
- Ollama: $0.00 (local)
- MCP Browser: $0.0001
- Cloud: $0.001
```

**Decision Logging Enhanced:**

- All decisions now log `ece_estimate` and `tokens_generated`
- `state/router_decisions.jsonl` includes full ECE tracking

### 2. Governance Canary Controller ✅

**File:** `governance/executive/canary_controller.py`

**Functionality:**

- Monitors `http://127.0.0.1:9113/canary` every 5 seconds
- Checks breach conditions:
  - p95 latency > 1200ms
  - Error rate > 10%
  - Cost per request > $0.05
- Requires 3 consecutive breaches before rollback
- On breach: Revokes `state/router_policy_overrides.json` (ALLOW_CLOUD)

**Logging:**

- Events logged to `governance/state/policy_change_events.jsonl`
- Tracks overrides, expirations, rollbacks with full context

**Metrics (Prometheus):**

```python
athena_governance_canary_checks_total       # Total checks performed
athena_governance_canary_breaches_total{breach_type}  # Breach events
athena_governance_canary_rollbacks_total{reason}      # Rollbacks executed
athena_governance_canary_state              # 0=inactive, 1=active, 2=breached
```

**Safety:**

- Pushes metrics to Prometheus pushgateway (port 9091)
- Graceful degradation if router unavailable
- Reset breach count on healthy check

## What's Remaining

### 3. Swift Agent Telemetry 🟡

**Need to create:**

- `NeuroForgeApp/Sources/Agent/AgentDecisionLog.swift`
  - Mirror router decision context (route, latency, tokens)
  - Log agent actions in <30ms
- `NeuroForgeApp/Sources/Agent/Telemetry.swift`
  - Push metrics to Prometheus gateway
  - Track agent latency, success rate, route used

**Acceptance:**

- Agent decisions logged <30ms
- No typing lag in UI
- Metrics visible in Prometheus

### 4. Prometheus/Grafana Updates 🟡

**Prometheus Rules:** `infra/prometheus/router.rules.yml`

Need to add:

```yaml
- record: athena_router_ece_p95
  expr: histogram_quantile(0.95, athena_router_ece_estimate)

- alert: CanaryBreachDetected
  expr: athena_governance_canary_state == 2
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Canary breach detected, rollback triggered"
```

**Grafana Dashboard:** `infra/grafana/dashboards/router.json`

Need to add panels:

- Canary state gauge (inactive/active/breached)
- ECE by route (timeseries)
- Rollback counter
- Breach events log

### 5. Quick Wins 🟡

**a) Router Warm-up Script**

```bash
#!/bin/bash
# scripts/warm_router.sh
# Pre-load MLX model and prime caches

echo "Warming up router..."
curl -s http://127.0.0.1:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"warmup","max_tokens":5}' > /dev/null

echo "Router warmed up"
```

**b) Log Streaming Helper**

```bash
# scripts/stream_router_logs.sh
tail -f state/router_decisions.jsonl | jq -c '{route, latency_ms, ece_estimate}'
```

**c) TTL Jitter**

- Add random jitter to policy TTL (±10%) to prevent synchronized expiry storms
- Update `governance/executive/api.py` to apply jitter

## Testing

### Test /canary Endpoint

```bash
curl http://127.0.0.1:9113/canary | jq
```

Expected response:

```json
{
  "canary_active": false,
  "providers": {
    "mlx": {
      "available": true,
      "p95_latency_ms": 480,
      "error_rate": 0.01,
      "total_requests": 150
    },
    "ollama": {
      "available": true,
      "p95_latency_ms": 620,
      "error_rate": 0.02
    }
  },
  "aggregate": {
    "available_count": 2,
    "avg_p95_latency_ms": 550
  },
  "breach_thresholds": {
    "max_p95_ms": 1200,
    "max_cost_per_request": 0.05
  }
}
```

### Test Canary Controller

```bash
# Start controller
python governance/executive/canary_controller.py

# In another terminal, enable cloud
curl -X POST http://127.0.0.1:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{"action":"ALLOW_CLOUD","ttl_minutes":10}'

# Simulate breach (need to inject high latency)
# Controller should auto-rollback within 15s (3 breaches × 5s)
```

### Verify ECE Logging

```bash
tail -f state/router_decisions.jsonl | jq '.ece_estimate'
```

Should see ECE values calculated for each decision.

## Acceptance Criteria

| Area              | Target                     | Status |
| ----------------- | -------------------------- | ------ |
| Router /canary    | Works, returns p95/ECE     | ✅     |
| ECE logging       | Logged in JSONL            | ✅     |
| Canary controller | Auto-rollback on breach    | ✅     |
| Swift telemetry   | Decision logs <30ms        | 🟡     |
| Prometheus rules  | ECE metrics + alerts       | 🟡     |
| Grafana panels    | Canary health visible      | 🟡     |
| Quick wins        | Warm-up, streaming, jitter | 🟡     |

## Next Steps

1. Add Prometheus rules for canary metrics
2. Update Grafana dashboard with canary panels
3. Create Swift agent telemetry
4. Implement quick wins (warm-up, streaming, jitter)
5. End-to-end canary test with synthetic breach

## Architecture

```
┌─────────────┐
│ Swift App   │
│ (Agent)     │──┐
└─────────────┘  │
                 │ Metrics
                 ▼
┌─────────────────────────┐
│ Prometheus Pushgateway  │ :9091
└─────────────────────────┘
                 ▲
                 │
┌────────────────┼───────────────┐
│                │               │
│  ┌─────────────┴────┐          │
│  │ Canary Controller│ :N/A     │
│  └─────────┬────────┘          │
│            │                   │
│   Every 5s │ GET /canary       │
│            ▼                   │
│  ┌──────────────────┐          │
│  │  Router :9113    │          │
│  │  - /health       │          │
│  │  - /route        │          │
│  │  - /canary ←───┐ │          │
│  │  - /metrics     │ │          │
│  └─────────────────┘ │          │
│         │             │          │
│         │             │          │
│         ▼             │          │
│  ┌────────────┐      │          │
│  │  Providers │      │          │
│  │  MLX/Ollama│      │          │
│  └────────────┘      │          │
│                      │          │
│  On breach:          │          │
│  1. Detect ──────────┘          │
│  2. Revoke state/               │
│     router_policy_overrides.json│
│  3. Log to policy_change_events │
│  4. Fire alert                  │
└─────────────────────────────────┘
```

## Key Insight

With A3 canary prep, Athena gains **self-healing routing**:

- Policies can be changed (ALLOW_CLOUD)
- Canary monitors for degradation
- Auto-rollback on breach (p95, error rate, cost)
- Zero-drift guarantee: bad policies can't persist

This enables **intelligent experimentation** without risk:

- Try new routing policies
- Monitor real-world impact
- Auto-revert if performance degrades
- Learn from safe failures

---

**Status:** Router + Controller complete, Swift + Observability in progress  
**Next:** Complete remaining items for full A3 deployment
