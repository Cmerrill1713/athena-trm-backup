#!/bin/bash
# Rollback Playbook (30 seconds)
# Reverts to previous known-good deployment

set -e

echo "🔄 Athena Rollback Playbook"
echo "==========================="
echo "Date: $(date)"
echo ""

if [ ! -f docker-compose.prev.yml ]; then
    echo "❌ No previous deployment found (docker-compose.prev.yml missing)"
    echo "Cannot rollback - no backup available"
    exit 1
fi

echo "⚠️  Rolling back to previous deployment..."
echo ""

# Stop current services
echo "🛑 Stopping current services..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
pkill -f "services/router/app.py" || true
pkill -f "agi_core/agi_service.py" || true
pkill -f "governance/canary/canary_consumer.py" || true
echo "   Services stopped"

# Start previous deployment
echo ""
echo "▶️  Starting previous deployment..."
docker compose -f docker-compose.prev.yml up -d
echo "   Services started"

# Wait for initialization
echo ""
echo "⏳ Waiting for services (10s)..."
sleep 10

# Quick health check
echo ""
echo "🏥 Quick health check..."
PORTS=(9113 9110 8000)
PORT_NAMES=("Router" "Orchestrator" "AGI-Core")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    echo -n "   $NAME ($PORT)... "
    
    if curl -fsS "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
    fi
done

echo ""
echo "================================"
echo "✅ ROLLBACK COMPLETE"
echo "================================"
echo "Reverted to previous deployment"
echo "Time: $(date)"
echo ""
echo "Next: Investigate why deployment failed"
echo "Logs: docker compose -f docker-compose.prev.yml logs"

