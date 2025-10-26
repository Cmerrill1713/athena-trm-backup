#!/bin/bash
# Open WebUI Setup Script for Athena
# This script configures Open WebUI to work with your local Athena router

set -e

BASE_URL="http://localhost:3000"
ROUTER_URL="http://host.docker.internal:9113"
OLLAMA_URL="http://host.docker.internal:11434"

echo "=========================================="
echo "🚀 Setting up Open WebUI for Athena"
echo "=========================================="
echo ""

# Check if Open WebUI is running
echo "📋 Checking Open WebUI status..."
if ! curl -sf "${BASE_URL}/health" > /dev/null; then
    echo "❌ Open WebUI is not running!"
    echo "Starting Open WebUI..."
    docker start open-webui 2>/dev/null || {
        docker run -d -p 3000:8080 \
            --add-host=host.docker.internal:host-gateway \
            -v open-webui:/app/backend/data \
            --name open-webui \
            --restart unless-stopped \
            ghcr.io/open-webui/open-webui:main
    }
    echo "⏳ Waiting for Open WebUI to start..."
    sleep 10
fi

echo "✅ Open WebUI is running at ${BASE_URL}"
echo ""

# Check if Athena router is accessible
echo "📋 Checking Athena Router..."
if curl -sf "http://localhost:9113/health" > /dev/null; then
    echo "✅ Athena Router is accessible"
else
    echo "⚠️  Athena Router may not be accessible from Docker"
    echo "   Make sure it's running: docker ps | grep athena-router"
fi
echo ""

# Check Ollama
echo "📋 Checking Ollama..."
if curl -sf "http://localhost:11434/api/tags" > /dev/null; then
    echo "✅ Ollama is accessible"
    MODELS=$(curl -s "http://localhost:11434/api/tags" | jq -r '.models[].name' | head -3)
    echo "   Available models:"
    echo "$MODELS" | sed 's/^/   - /'
else
    echo "⚠️  Ollama may not be running"
fi
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🌐 Open WebUI: ${BASE_URL}"
echo "🤖 Athena Router: http://localhost:9113"
echo "🦙 Ollama: http://localhost:11434"
echo ""
echo "📋 Next Steps:"
echo "1. Open your browser to: ${BASE_URL}"
echo "2. Create your admin account (if first time)"
echo "3. Go to Settings → Connections → Ollama"
echo "4. Set Ollama URL to: ${OLLAMA_URL}"
echo "5. Click 'Refresh' to load models"
echo ""
echo "🔍 Test Browser Research:"
echo "   Ask: 'open a browser and look up machine learning'"
echo ""
echo "📊 Monitor your stack:"
echo "   - Grafana: http://localhost:3001"
echo "   - Prometheus: http://localhost:9090"
echo ""
echo "Opening Open WebUI in your browser..."
sleep 2
open "${BASE_URL}" 2>/dev/null || {
    echo ""
    echo "Please open ${BASE_URL} in your browser"
}

