#!/bin/bash
# Start complete Athena stack including Open WebUI
# Usage: ./start-athena.sh

set -e

echo "=========================================="
echo "🚀 Starting Athena AI Stack"
echo "=========================================="
echo ""

# Start main Athena services
echo "1️⃣ Starting Athena core services..."
docker-compose up -d

echo "⏳ Waiting for services to initialize..."
sleep 5

# Start Open WebUI
echo ""
echo "2️⃣ Starting Open WebUI..."
if docker ps -a | grep -q open-webui; then
    docker start open-webui
else
    docker run -d -p 3000:8080 \
        --add-host=host.docker.internal:host-gateway \
        -v open-webui:/app/backend/data \
        --name open-webui \
        --restart unless-stopped \
        ghcr.io/open-webui/open-webui:main
fi

echo "⏳ Waiting for Open WebUI to start..."
sleep 5

# Health checks
echo ""
echo "3️⃣ Running health checks..."
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "   ✅ $name"
    else
        echo "   ⚠️  $name (may still be starting)"
    fi
}

check_service "Open WebUI       " "http://localhost:3000/health"
check_service "Athena Router    " "http://localhost:9113/health"
check_service "MCP Browser      " "http://localhost:8412/health"
check_service "Ollama           " "http://localhost:11434/api/tags"
check_service "Prometheus       " "http://localhost:9090/-/healthy"
check_service "Grafana          " "http://localhost:3001/api/health"

echo ""
echo "=========================================="
echo "✅ Athena Stack Started!"
echo "=========================================="
echo ""
echo "🌐 Open WebUI:  http://localhost:3000"
echo "🤖 Router:      http://localhost:9113"
echo "📊 Grafana:     http://localhost:3001"
echo "📈 Prometheus:  http://localhost:9090"
echo ""
echo "📖 Quick Start Guide: QUICK_START.md"
echo ""
echo "🔍 Test browser research:"
echo "   In Open WebUI, ask: 'search for machine learning'"
echo ""
echo "Opening Open WebUI in your browser..."
sleep 2
open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000"

