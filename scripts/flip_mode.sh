#!/usr/bin/env bash
#
# Flip Athena Governance Mode
# Transitions between: shadow → canary → enforce
#

set -euo pipefail

MODE="${1:-}"

if [ -z "$MODE" ]; then
    echo "Usage: $0 <shadow|canary|enforce>"
    echo ""
    echo "Modes:"
    echo "  shadow  - Observe only, no enforcement (0% impact)"
    echo "  canary  - Enforce on 1-5% of traffic"
    echo "  enforce - Full enforcement (100% of traffic)"
    exit 1
fi

if [[ ! "$MODE" =~ ^(shadow|canary|enforce)$ ]]; then
    echo "❌ Invalid mode: $MODE"
    echo "   Must be: shadow | canary | enforce"
    exit 1
fi

echo "🔄 Flipping Athena governance mode..."
echo ""
echo "   Current mode: ${ATHENA_MODE:-unknown}"
echo "   Target mode:  $MODE"
echo ""

# Export for subsequent processes
export ATHENA_MODE="$MODE"

# Persist to env file if it exists
if [ -f .env ]; then
    if grep -q "^ATHENA_MODE=" .env; then
        sed -i.bak "s/^ATHENA_MODE=.*/ATHENA_MODE=$MODE/" .env
    else
        echo "ATHENA_MODE=$MODE" >> .env
    fi
    echo "✅ Updated .env"
fi

# Reload nginx ingress (if running)
if docker ps --format '{{.Names}}' | grep -q ingress; then
    echo "🔄 Reloading nginx ingress..."
    docker exec ingress nginx -s reload || echo "⚠️  Nginx reload failed (may not be running)"
fi

# Notify orchestrator
echo "📡 Notifying orchestrator..."
curl -sS -X POST http://localhost:9110/mode \
    -H 'Content-Type: application/json' \
    -d "{\"mode\":\"$MODE\",\"timestamp\":\"$(date -u +%FT%TZ)\"}" \
    | jq -r '.status // "ok"' || echo "⚠️  Orchestrator mode endpoint not available"

echo ""
echo "✅ Mode flip complete: $MODE"
echo ""

# Show what this means
case "$MODE" in
    shadow)
        echo "🔍 Shadow Mode Active"
        echo "   • Governance observes all traffic"
        echo "   • No enforcement actions taken"
        echo "   • Metrics collected for analysis"
        echo "   • 0% production impact"
        ;;
    canary)
        echo "🐤 Canary Mode Active"
        echo "   • Governance enforces on 1-5% of traffic"
        echo "   • Remainder in shadow mode"
        echo "   • Monitor metrics closely"
        echo "   • Low production impact"
        ;;
    enforce)
        echo "🛡️ Enforce Mode Active"
        echo "   • Governance enforces on 100% of traffic"
        echo "   • All requests governed"
        echo "   • Full policy enforcement"
        echo "   • Production protected"
        ;;
esac

echo ""
echo "📊 Monitor with:"
echo "   curl http://localhost:9110/metrics | grep governance_"
echo "   make gate  # Check coverage"

