# Hybrid LLM-Based REP - Quick Start Guide

Get started with intelligent multi-agent coordination in 5 minutes.

---

## Prerequisites

1. **Redis** running locally
2. **Ollama** with qwen2.5-coder:7b model
3. **Project Iceberg** (Phase 1) installed

---

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Ensure services are running
docker-compose up -d athena-redis
docker ps | grep athena-redis

# 2. Start router with hybrid mode (already configured)
docker-compose up -d athena-router

# 3. Check it's working
curl http://localhost:9113/rep/stats

# Expected response:
{
  "enabled": true,
  "calculator_mode": "hybrid",
  "peer_count": 0,
  ...
}
```

### Option 2: Local Development

```bash
# 1. Set environment variables
export ATHENA_REP_ENABLED=true
export ATHENA_REP_CALCULATOR_MODE=hybrid
export ATHENA_REP_REDIS_URL=redis://127.0.0.1:6379
export ATHENA_NO_CLOUD=1

# 2. Start router
python -c "
from governance.routing.rep_router import REPEnhancedRouter
from governance.routing.basic_router import RoutingRequest
from pathlib import Path

router = REPEnhancedRouter(
    profiles_path=Path('governance/routing/model_profiles.json'),
    agent_id='test_router',
    calculator_mode='hybrid'
)

# Test routing
request = RoutingRequest(query='implement fibonacci', domain='code')
choice = router.route(request)
print(f'Routed to: {choice.model}')

# Check stats
stats = router.get_rep_stats()
print(f'Calculator mode: {stats[\"calculator_mode\"]}')
print(f'Calculator stats: {stats.get(\"calculator_stats\")}')
"
```

---

## Test Scenarios

### Test 1: Simple Scenario (Rule-Based)

```python
# Create simple conditions
# - Few peers
# - Good budget
# - Low queues

router.system_state.accumulated_cost = 30.0
router.system_state.cost_budget = 100.0
router.system_state.queue_depths = {"qwen2.5-coder:7b": 2}

# Route - should use rules (fast)
choice = router.route(request)

# Check which calculator was used
assert choice.metadata.get('calculator') == 'rules'
print(f"Latency: {choice.latency_ms}ms")  # Should be <10ms
```

### Test 2: Complex Scenario (LLM Reasoning)

```python
# Create complex conditions
# - Many peers
# - Moderate budget pressure
# - High queues

# Simulate 10 peers (you'd normally have real agents)
for i in range(10):
    router.rep_coordinator.peer_messages.append(
        create_fake_peer_message(agent_id=f"peer_{i}")
    )

router.system_state.accumulated_cost = 75.0
router.system_state.cost_budget = 100.0
router.system_state.queue_depths = {"qwen2.5-coder:7b": 12}

# Route - should use LLM (smart)
choice = router.route(request)

# Check which calculator was used
assert choice.metadata.get('calculator') == 'llm'
print(f"Latency: {choice.latency_ms}ms")  # Should be 50-200ms
print(f"Complexity: {choice.metadata.get('complexity')}")  # 'complex'
```

### Test 3: Critical Scenario (Dual Validation)

```python
# Create critical conditions
# - Budget exhaustion
# - Model failures

router.system_state.accumulated_cost = 92.0
router.system_state.cost_budget = 100.0
router.system_state.unavailable_models = ["qwen2.5-coder:7b"]

# Route - should use both calculators
choice = router.route(request)

# Check which calculator was used
assert choice.metadata.get('calculator') == 'critical_hybrid'
print(f"Validated by: {choice.metadata.get('validated_by')}")
```

---

## Verify Mode

### Check Calculator Mode

```bash
# Via API
curl http://localhost:9113/rep/stats | jq '.calculator_mode'
# Output: "hybrid"

# Via metrics
curl http://localhost:9113/metrics | grep rep_policy_mode
# Output: athena_rep_policy_mode{agent_id="router_primary"} 2
# (0=rules, 1=llm, 2=hybrid)
```

### Check Calculator Stats

```bash
curl http://localhost:9113/rep/stats | jq '.calculator_stats'
```

Expected output:

```json
{
  "total_calculations": 100,
  "simple_count": 95,
  "complex_count": 4,
  "critical_count": 1,
  "llm_failures": 0,
  "llm_fallbacks": 0,
  "percentages": {
    "simple": 95.0,
    "complex": 4.0,
    "critical": 1.0
  }
}
```

---

## Monitor Metrics

### Key Metrics

```bash
# Scenario complexity distribution
curl -s http://localhost:9113/metrics | grep rep_scenario_complexity_total

# LLM success rate
curl -s http://localhost:9113/metrics | grep rep_llm_calculations_total

# Agreement rate
curl -s http://localhost:9113/metrics | grep rep_rule_vs_llm_agreement_total

# Latency
curl -s http://localhost:9113/metrics | grep rep_llm_calculation_latency
```

### Grafana Dashboard

```promql
# Complexity Distribution Pie Chart
sum by (complexity) (rate(rep_scenario_complexity_total[5m]))

# LLM Success Rate Gauge
rate(rep_llm_calculations_total{status="success"}[5m]) /
rate(rep_llm_calculations_total[5m]) * 100

# Average LLM Latency Graph
histogram_quantile(0.95,
  rate(rep_llm_calculation_latency_seconds_bucket[5m]))

# Agreement Rate Over Time
rate(rep_rule_vs_llm_agreement_total{agreement="agree"}[5m]) /
rate(rep_rule_vs_llm_agreement_total[5m]) * 100
```

---

## Switch Modes

### Change to Rule-Based Only

```bash
# Docker
docker-compose stop athena-router
# Edit docker-compose.yml: ATHENA_REP_CALCULATOR_MODE=rule_based
docker-compose up -d athena-router

# Or restart with env var
docker-compose up -d -e ATHENA_REP_CALCULATOR_MODE=rule_based athena-router
```

### Change to LLM Only

```bash
# Only for testing! Not recommended for production
export ATHENA_REP_CALCULATOR_MODE=llm_based
docker-compose up -d athena-router
```

### Back to Hybrid (Recommended)

```bash
export ATHENA_REP_CALCULATOR_MODE=hybrid
docker-compose up -d athena-router
```

---

## Tune Complexity Thresholds

Edit `governance/legislative/rep_coordination_policy.yaml`:

```yaml
hybrid:
  # Make more scenarios "simple" (faster)
  simple_scenario:
    max_peers: 10 # Increase from 5
    max_queue_depth: 20 # Increase from 10

  # Make fewer scenarios "critical" (more LLM usage)
  critical_scenario:
    min_budget_remaining: 0.05 # Lower from 0.1
```

Then reload policy (if hot reload supported) or restart router.

---

## Troubleshooting

### LLM Not Being Called

**Symptoms**: All requests use rules, never LLM

**Check**:

```bash
# Verify mode
curl http://localhost:9113/rep/stats | jq '.calculator_mode'

# Check if scenarios are too simple
curl http://localhost:9113/rep/stats | jq '.calculator_stats'
# If simple_count is 100%, scenarios aren't complex enough
```

**Fix**: Create more complex conditions or lower thresholds

### High LLM Failure Rate

**Symptoms**: Many `llm_fallbacks` in stats

**Check**:

```bash
# Check LLM metrics
curl http://localhost:9113/metrics | grep rep_llm_calculations_total

# Check logs
docker logs athena-router | grep "LLM"
```

**Fix**:

- Ensure Ollama is running
- Check model is loaded: `ollama list`
- Increase timeout: Edit policy `llm_based.timeout_seconds`

### Low Agreement Rate

**Symptoms**: Rule and LLM disagree often

**Check**:

```bash
curl http://localhost:9113/metrics | grep rep_rule_vs_llm_agreement
```

**Fix**:

- Review disagreement logs
- Tune rule thresholds to match LLM reasoning
- Or adjust LLM prompt for more conservative outputs

---

## Performance Tips

### Optimize for Speed (95%+ simple)

```yaml
# In rep_coordination_policy.yaml
hybrid:
  simple_scenario:
    max_peers: 15 # Higher threshold
    max_queue_depth: 25
    max_latency_p95_ms: 3000
```

### Optimize for Intelligence (More LLM)

```yaml
# In rep_coordination_policy.yaml
hybrid:
  simple_scenario:
    max_peers: 3 # Lower threshold
    max_queue_depth: 5
```

### Optimize for Cost

```yaml
llm_based:
  # Use smaller, faster model
  model: "phi-2:latest" # Smaller than qwen2.5-coder
  temperature: 0.1 # More deterministic = faster
  max_tokens: 300 # Fewer tokens
```

---

## Next Steps

1. **Run load test** with 10+ agents
2. **Monitor metrics** for 24 hours
3. **Tune thresholds** based on complexity distribution
4. **Enable canary testing** for policy experimentation

---

## Reference

- Main docs: `PROJECT_ICEBERG_LLM_ENHANCEMENTS.md`
- Policy file: `governance/legislative/rep_coordination_policy.yaml`
- Code: `governance/routing/rep_hybrid_calculator.py`
- Tests: `governance/routing/tests/test_rep_integration.py`

---

**Ready to coordinate 20+ agents intelligently!** 🧊🧠🚀
