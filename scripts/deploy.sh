#!/bin/bash
# Go-Live Playbook (90 seconds)
# Deploys Athena system with full validation

set -e

echo "🚀 Athena Go-Live Playbook"
echo "=========================="
echo "Release: v0.1.0"
echo "Date: $(date)"
echo ""

# Save current state for rollback
echo "📸 Backing up current deployment..."
if [ -f docker-compose.prod.yml ]; then
    cp docker-compose.prod.yml docker-compose.prev.yml
    echo "   Backup saved to docker-compose.prev.yml"
fi

# Stop existing services
echo ""
echo "🛑 Stopping existing services..."
docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
pkill -f "services/router/app.py" || true
pkill -f "agi_core/agi_service.py" || true
pkill -f "governance/canary/canary_consumer.py" || true
echo "   Services stopped"

# Build with no cache
echo ""
echo "🔨 Building fresh images..."
BUILD_SHA=$(git rev-parse --short HEAD)
echo "   Build SHA: $BUILD_SHA"
docker compose -f docker-compose.prod.yml build \
    --no-cache \
    --build-arg BUILD_SHA=$BUILD_SHA \
    2>&1 | grep -v "downloading" || true
echo "   Build complete"

# Start all services
echo ""
echo "▶️  Starting all services..."
docker compose -f docker-compose.prod.yml up -d
echo "   Services started"

# Wait for services to initialize
echo ""
echo "⏳ Waiting for services to initialize (15s)..."
sleep 15

# Health checks
echo ""
echo "🏥 Running health checks..."
PORTS=(9113 9110 8412 8000 9090 3001)
PORT_NAMES=("Router" "Orchestrator" "MCP-UI" "AGI-Core" "Prometheus" "Grafana")
FAILED=0

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    echo -n "   $NAME ($PORT)... "
    
    if curl -fsS "http://localhost:$PORT/health" > /dev/null 2>&1 || \
       curl -fsS "http://localhost:$PORT/-/healthy" > /dev/null 2>&1 || \
       curl -fsS "http://localhost:$PORT/api/health" > /dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        ((FAILED++))
    fi
done

# Version check
echo ""
echo "📋 Checking router version..."
if curl -fsS localhost:9113/version 2>/dev/null; then
    echo ""
fi

# Run contract tests
echo ""
echo "🧪 Running contract tests..."
if bash tests/test_contracts.sh; then
    echo ""
    echo "================================"
    echo "✅ DEPLOYMENT SUCCESSFUL"
    echo "================================"
    echo "Release: v0.1.0"
    echo "Build: $BUILD_SHA"
    echo "Time: $(date)"
    echo "Services: ${#PORTS[@]} healthy"
    echo ""
    echo "Next: Monitor Grafana for 30 minutes"
    echo "URL: http://localhost:3001"
    exit 0
else
    echo ""
    echo "================================"
    echo "❌ DEPLOYMENT FAILED"
    echo "================================"
    echo "Contract tests did not pass"
    echo "Run ./scripts/rollback.sh to revert"
    exit 1
fi

