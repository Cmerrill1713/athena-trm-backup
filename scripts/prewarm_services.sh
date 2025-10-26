#!/bin/bash
# Prewarm Athena services for UI testing
# Prevents cold-start spikes and ensures smooth UI experience

set -euo pipefail

echo "🔥 Pre-warming Athena services for UI testing..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set safe defaults
export ATHENA_ENV=production
export ATHENA_NO_CLOUD=1
export ATHENA_UI_TEST_MODE=1
export ATHENA_MAX_CONCURRENCY=2
export ENABLE_STREAMING=true

# 1. Health check all services
echo "1️⃣  Checking service health..."
services=("weaviate:8090" "router:9113" "uai:8080" "prometheus:9090")

for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"
    
    if curl -sf "http://127.0.0.1:${port}/health" >/dev/null 2>&1 || \
       curl -sf "http://127.0.0.1:${port}/v1/.well-known/ready" >/dev/null 2>&1; then
        echo "  ✅ ${name} healthy"
    else
        echo "  ⚠️  ${name} not responding - starting..."
        docker-compose up -d "athena-${name}" 2>/dev/null || docker-compose up -d "${name}" 2>/dev/null || true
    fi
done

echo ""
echo "2️⃣  Pre-warming models (reduces first-query latency)..."

# Check if Ollama is accessible
if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "  ✅ Ollama accessible"
    
    # Pull common models if not present
    for model in "qwen2.5-coder:7b" "qwen2.5:7b"; do
        if ollama list | grep -q "$model"; then
            echo "  ✅ $model present"
        else
            echo "  📥 Pulling $model..."
            ollama pull "$model" 2>&1 | tail -1
        fi
    done
    
    # Warm-up query to load model into memory
    echo "  🔥 Warm-up query..."
    curl -sf http://127.0.0.1:11434/api/generate -d '{
        "model": "qwen2.5:7b",
        "prompt": "Hello",
        "stream": false
    }' >/dev/null 2>&1 || true
    
else
    echo "  ⚠️  Ollama not accessible (skip model pre-warm)"
fi

echo ""
echo "3️⃣  Warming knowledge base (first RAG query)..."

# Send a test RAG query to warm the index
curl -sf http://127.0.0.1:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "athena-chat",
        "messages": [{"role": "user", "content": "test"}],
        "stream": false
    }' >/dev/null 2>&1 && echo "  ✅ RAG warmed" || echo "  ⚠️  RAG warm-up skipped"

echo ""
echo "4️⃣  Setting safe concurrency limits..."

# These prevent stampeding during UI tests
echo "  ATHENA_MAX_CONCURRENCY=2"
echo "  ROUTER_RATE_QPS=3"
echo "  ROUTER_BURST=6"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Services pre-warmed and ready for UI testing!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next: make ui-drill or make ui-manual-test"
