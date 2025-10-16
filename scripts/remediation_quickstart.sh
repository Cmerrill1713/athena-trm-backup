#!/bin/bash
# Auto-Remediation Quickstart
# Demonstrates the complete verdict → remediation → canary → promote/rollback loop

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Athena Auto-Remediation System - Quick Start              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
EVENT_BUS=${EVENT_BUS:-local}  # local or redis
ORCHESTRATOR_URL=${ORCHESTRATOR_URL:-http://localhost:9110}
REMEDIATOR_URL=${REMEDIATOR_URL:-http://localhost:9112}
PROMETHEUS_URL=${PROMETHEUS_URL:-http://localhost:9090}

echo "Configuration:"
echo "  Event Bus: $EVENT_BUS"
echo "  Orchestrator: $ORCHESTRATOR_URL"
echo "  Remediator: $REMEDIATOR_URL"
echo "  Prometheus: $PROMETHEUS_URL"
echo ""

# Check if services are running
check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "${url}/health" > /dev/null 2>&1; then
        echo "✓ $name is running"
        return 0
    else
        echo "✗ $name is NOT running at $url"
        return 1
    fi
}

echo "Checking services..."
ALL_UP=true
check_service "Orchestrator" "$ORCHESTRATOR_URL" || ALL_UP=false
check_service "Remediator" "$REMEDIATOR_URL" || ALL_UP=false
check_service "Prometheus" "$PROMETHEUS_URL" || ALL_UP=false
echo ""

if [ "$ALL_UP" = false ]; then
    echo "⚠️  Some services are not running."
    echo "   Start them with: docker compose -f docker-compose.athena-governance.yml up -d"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get baseline metrics
echo "Fetching baseline metrics..."
BASELINE_REQUESTED=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=governance_remediations_requested_total" | jq -r '.data.result[0].value[1] // "0"')
BASELINE_COMPLETED=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=governance_remediations_completed_total" | jq -r '.data.result[0].value[1] // "0"')

echo "  Remediations requested: $BASELINE_REQUESTED"
echo "  Remediations completed: $BASELINE_COMPLETED"
echo ""

# Trigger a HARD_FAIL verdict
TASK_ID="demo-$(date +%s)"
echo "Triggering HARD_FAIL verdict (task=$TASK_ID)..."

VERDICT=$(cat <<EOF
{
  "task_id": "$TASK_ID",
  "verdict": "HARD_FAIL",
  "ece_estimate": 0.09,
  "actions": ["ROLLBACK"],
  "ts": "$(date -u +%FT%TZ)"
}
EOF
)

# Note: The orchestrator might not have a /verdict endpoint yet
# The event will be published internally when DGM evolution runs
echo "$VERDICT" | jq .
echo ""

if curl -sf -X POST "$ORCHESTRATOR_URL/verdict" \
    -H "Content-Type: application/json" \
    -d "$VERDICT" > /dev/null 2>&1; then
    echo "✓ Verdict sent to orchestrator"
else
    echo "⚠️  Verdict endpoint not available (this is okay if using event bus directly)"
fi
echo ""

# Wait for remediation
echo "Waiting for auto-remediation (10 seconds)..."
for i in {10..1}; do
    echo -ne "\r  $i seconds remaining...   "
    sleep 1
done
echo -e "\r  ✓ Done waiting              "
echo ""

# Check updated metrics
echo "Fetching updated metrics..."
FINAL_REQUESTED=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=governance_remediations_requested_total" | jq -r '.data.result[0].value[1] // "0"')
FINAL_COMPLETED=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=governance_remediations_completed_total" | jq -r '.data.result[0].value[1] // "0"')
FINAL_PROMOTED=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=governance_remediations_promoted_total" | jq -r '.data.result[0].value[1] // "0"')
FINAL_ROLLED_BACK=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=governance_remediations_rolled_back_total" | jq -r '.data.result[0].value[1] // "0"')

echo "  Remediations requested: $FINAL_REQUESTED (+$(echo "$FINAL_REQUESTED - $BASELINE_REQUESTED" | bc))"
echo "  Remediations completed: $FINAL_COMPLETED (+$(echo "$FINAL_COMPLETED - $BASELINE_COMPLETED" | bc))"
echo "  Promoted: $FINAL_PROMOTED"
echo "  Rolled back: $FINAL_ROLLED_BACK"
echo ""

# Check remediator metrics directly
echo "Checking remediator service..."
curl -s "$REMEDIATOR_URL/metrics" | grep governance_remediations | head -n 6
echo ""

# Check canary state
if [ -f "state/canary/canary_state.json" ]; then
    echo "Canary state:"
    cat state/canary/canary_state.json | jq .
    echo ""
fi

# Show recent action log
if [ -f "state/canary/canary_actions.jsonl" ]; then
    echo "Recent canary actions:"
    tail -n 3 state/canary/canary_actions.jsonl | jq .
    echo ""
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Quick Start Complete                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  • View Grafana dashboards: http://localhost:3001"
echo "  • Query Prometheus: http://localhost:9090"
echo "  • Run E2E tests: pytest tests/e2e/test_auto_remediation.py -v"
echo "  • Check logs: docker compose -f docker-compose.athena-governance.yml logs agi-remediator"
echo ""

