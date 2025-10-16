#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting Athena Platform..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local port=$2
    local endpoint=${3:-/health}
    
    if curl -s --max-time 2 "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${name} (port ${port})${NC}"
        return 0
    else
        echo -e "${RED}❌ ${name} (port ${port})${NC}"
        return 1
    fi
}

echo "📡 Starting Docker services..."
docker compose -f docker-compose.athena-governance.yml up -d 2>/dev/null || true
sleep 3

echo ""
echo "🔍 Checking service health..."
echo ""

# Check each service
check_service "Prometheus" 9090 "/-/ready" || echo "  → Starting Prometheus..."
check_service "Grafana" 3001 "/api/health" || echo "  → Grafana may need manual start"
check_service "Metrics Exporter" 9109 "/metrics" || echo "  → Check governance/observability/"
check_service "Canary Monitor" 9111 "/health" || echo "  → Check release/canary service"

echo ""
echo "🎯 Starting core services..."
echo ""

# Start Orchestrator (port 9110)
if ! check_service "Orchestrator" 9110 "/health" 2>/dev/null; then
    echo "  → Starting Orchestrator on port 9110..."
    cd governance/executive/orchestration
    python3 orchestrator_service.py > ../../../artifacts/orchestrator.log 2>&1 &
    echo $! > ../../../.orchestrator.pid
    cd ../../..
    sleep 2
    check_service "Orchestrator" 9110 "/health" || echo "    ⚠️  May need more time to start"
fi

# Start Master API (port 8000)
if ! check_service "Master API" 8000 "/health" 2>/dev/null; then
    echo "  → Starting Master API on port 8000..."
    python3 athena_api.py > artifacts/athena_api.log 2>&1 &
    echo $! > .athena_api.pid
    sleep 2
    check_service "Master API" 8000 "/health" || echo "    ⚠️  May need more time to start"
fi

echo ""
echo "🎊 Athena startup complete!"
echo ""
echo "📊 Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_service "Orchestrator" 9110 "/health" || true
check_service "Metrics Exporter" 9109 "/metrics" || true
check_service "Canary Monitor" 9111 "/health" || true
check_service "Prometheus" 9090 "/-/ready" || true
check_service "Grafana" 3001 "/api/health" || true
check_service "Master API" 8000 "/health" || true
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check current mode
MODE=$(curl -s http://localhost:9110/state 2>/dev/null | jq -r '.mode // "unknown"' || echo "unknown")
echo "🔍 Current Mode: ${MODE}"
echo ""

# Quick metrics check
echo "📈 Quick Metrics Check:"
VERDICTS=$(curl -s http://localhost:9110/metrics 2>/dev/null | grep "governance_verdicts_total" | tail -1 || echo "Not available")
echo "   Verdicts: ${VERDICTS}"
echo ""

echo "🌐 Access Points:"
echo "   • Orchestrator:    http://localhost:9110"
echo "   • Master API:      http://localhost:8000"
echo "   • Prometheus:      http://localhost:9090"
echo "   • Grafana:         http://localhost:3001 (admin/admin)"
echo "   • Metrics:         http://localhost:9109/metrics"
echo ""

echo "📚 Next Steps:"
echo "   make wire-validate    # Verify 100% wiring"
echo "   make exp-shadow       # Run experiment"
echo "   open http://localhost:3001  # View dashboards"
echo ""

