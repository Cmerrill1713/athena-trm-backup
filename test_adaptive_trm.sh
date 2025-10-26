#!/bin/bash
# Test Adaptive TRM Policy Integration

set -e

echo "══════════════════════════════════════════════════════════"
echo "  🧠 ADAPTIVE TRM POLICY - INTEGRATION TEST"
echo "══════════════════════════════════════════════════════════"
echo ""

# 1. Check policy is loaded
echo "1️⃣  Policy Configuration:"
cd /Users/christianmerrill/Documents/GitHub && /usr/bin/python3 -c "
from services.trm_adaptive_policy import policy
print(f'  Trigger threshold: {policy.cfg.trigger_threshold}')
print(f'  Cycle range: [{policy.cfg.min_cycles}, {policy.cfg.max_cycles}]')
print(f'  History size: {len(policy.history)}')
print(f'  Current bias: {policy.bias:.3f}')
"
echo ""

# 2. Test adaptive trigger (high probability)
echo "2️⃣  Test High-Probability Trigger:"
RESULT=$(curl -s http://localhost:8000/api/execute -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "objective":"How do I implement a complex distributed consensus algorithm with Byzantine fault tolerance?",
    "tools":[],
    "max_steps":3,
    "flags":{"adaptive_trm":true}
  }')

TRIGGER_PROB=$(echo "$RESULT" | jq -r '.trace[] | select(.action=="trm_deliberated") | .details.trigger_prob // "not_triggered"')
ADAPTIVE=$(echo "$RESULT" | jq -r '.trace[] | select(.action=="trm_deliberated") | .details.adaptive // false')

if [ "$TRIGGER_PROB" != "not_triggered" ]; then
  echo "  ✅ TRM Invoked (adaptive=$ADAPTIVE, prob=$TRIGGER_PROB)"
else
  echo "  ⚠️  TRM Not Invoked (might be below threshold)"
fi
echo ""

# 3. Test low-probability skip
echo "3️⃣  Test Low-Probability Skip:"
RESULT2=$(curl -s http://localhost:8000/api/execute -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "objective":"Hello",
    "tools":["mcp.shell"],
    "max_steps":2,
    "flags":{"adaptive_trm":true}
  }')

TRM_TRACE=$(echo "$RESULT2" | jq '.trace[] | select(.action | contains("trm"))')
if [ -z "$TRM_TRACE" ]; then
  echo "  ✅ TRM Skipped (low probability, simple task)"
else
  echo "  ℹ️  TRM Invoked (policy learning phase)"
fi
echo ""

# 4. Show policy stats
echo "4️⃣  Policy Statistics:"
cd /Users/christianmerrill/Documents/GitHub && /usr/bin/python3 -c "
from services.trm_adaptive_policy import policy
import json
stats = policy.get_stats()
if stats.get('status') == 'no_data':
    print('  No outcomes recorded yet')
else:
    print(f'  Total decisions: {stats[\"total_decisions\"]}')
    print(f'  Recent invocations: {stats[\"recent_invocations\"]}')
    print(f'  Recent skips: {stats[\"recent_skips\"]}')
    if stats.get('success_rate_with_trm', 0) > 0:
        print(f'  Success with TRM: {stats[\"success_rate_with_trm\"]:.1%}')
        print(f'  Success without TRM: {stats[\"success_rate_without_trm\"]:.1%}')
"
echo ""

# 5. Compare adaptive vs static
echo "5️⃣  Adaptive vs Static Comparison:"
echo "  Adaptive request:"
ADAPTIVE_RESULT=$(curl -s http://localhost:8000/api/execute -X POST \
  -H 'Content-Type: application/json' \
  -d '{"objective":"Design a microservices architecture","tools":[],"max_steps":3,"flags":{"adaptive_trm":true}}')
ADAPTIVE_TIME=$(echo "$ADAPTIVE_RESULT" | jq -r '.execution_time_s')
ADAPTIVE_TRM=$(echo "$ADAPTIVE_RESULT" | jq -r '.trace[] | select(.action=="trm_deliberated") | .details.cycles_allocated // "skipped"')

echo "    Time: ${ADAPTIVE_TIME}s, Cycles allocated: $ADAPTIVE_TRM"

echo "  Static request:"
STATIC_RESULT=$(curl -s http://localhost:8000/api/execute -X POST \
  -H 'Content-Type: application/json' \
  -d '{"objective":"Design a microservices architecture","tools":[],"max_steps":3,"flags":{"adaptive_trm":false}}')
STATIC_TIME=$(echo "$STATIC_RESULT" | jq -r '.execution_time_s')
STATIC_TRM=$(echo "$STATIC_RESULT" | jq -r '.trace[] | select(.action=="trm_deliberated") | .details.cycles_allocated // "skipped"')

echo "    Time: ${STATIC_TIME}s, Cycles allocated: $STATIC_TRM"
echo ""

echo "══════════════════════════════════════════════════════════"
echo "  ✅ ADAPTIVE TRM POLICY TEST COMPLETE"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "📊 Next Steps:"
echo "  1. Run A/B test: make trm-ab"
echo "  2. Monitor metrics: make trm-policy-metrics"
echo "  3. Check stats after 100+ tasks: make trm-policy-stats"
echo "  4. Adjust thresholds via env vars if needed"

