#!/usr/bin/env bash
#
# Governance Coverage Gate
# Ensures governance is seeing sufficient traffic before deploying
#

set -euo pipefail

PROM_URL="${PROM_URL:-http://localhost:9090}"
MIN_COVERAGE="${MIN_COVERAGE:-0.98}"

echo "🔍 Checking governance coverage..."
echo "   Prometheus: $PROM_URL"
echo "   Min required: $MIN_COVERAGE"
echo ""

# Query Prometheus
query() {
    local q="$1"
    curl -sS "$PROM_URL/api/v1/query" \
        --get \
        --data-urlencode "query=$q" \
        | jq -r '.data.result[0].value[1] // "0"'
}

# Get metrics
ingress=$(query 'sum(ingress_requests_total) or vector(0)')
receipts=$(query 'sum(governance_receipts_total) or vector(0)')
verdicts=$(query 'sum(governance_verdicts_total) or vector(0)')
actions=$(query 'sum(governance_actions_total) or vector(0)')

echo "📊 Metrics:"
echo "   Ingress requests: $ingress"
echo "   Governance receipts: $receipts"
echo "   Verdicts rendered: $verdicts"
echo "   Actions taken: $actions"
echo ""

# Calculate coverage
coverage=$(python3 - <<EOF
import sys
ing = float("$ingress") or 1.0
rec = float("$receipts")
cov = rec / ing
print(f"{cov:.4f}")
EOF
)

echo "📈 Coverage: $coverage"
echo ""

# Check threshold
if awk -v c="$coverage" -v m="$MIN_COVERAGE" 'BEGIN{ exit !(c+0 >= m+0) }'; then
    echo "✅ Coverage OK (>= $MIN_COVERAGE)"
    echo ""
    echo "🟢 GATE PASSED - Governance is seeing sufficient traffic"
    exit 0
else
    echo "❌ Coverage below threshold"
    echo "   Current: $coverage"
    echo "   Required: $MIN_COVERAGE"
    echo "   Gap: $(awk -v c="$coverage" -v m="$MIN_COVERAGE" 'BEGIN{printf "%.2f%%", (m-c)*100}')"
    echo ""
    echo "🔴 GATE FAILED - Check ingress mirror configuration"
    echo ""
    echo "Debug:"
    echo "  • Is nginx mirroring enabled?"
    echo "  • Is orchestrator /receipt endpoint working?"
    echo "  • Check: curl http://localhost:9110/health"
    exit 1
fi

