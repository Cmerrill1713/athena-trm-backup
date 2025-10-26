#!/bin/bash
echo "🔍 Testing all 9 services from browser perspective (with CORS)..."
echo ""

services=(
    "UAI:8080:/health"
    "Router:9113:/health"
    "MCP:8412:/health"
    "Whisper:8095:/health"
    "Kokoro:8091:/health"
    "FastVLM:8088:/health"
    "Judicial:8096:/v2/health"
    "Learning:8098:/health"
    "macOS:8099:/health"
)

count=0
for service in "${services[@]}"; do
    IFS=':' read -r name port path <<< "$service"
    
    # Test with CORS headers like browser would
    response=$(curl -s -w "\n%{http_code}" -H "Origin: http://localhost:8082" \
        "http://localhost:${port}${path}" 2>&1)
    
    status_code=$(echo "$response" | tail -n 1)
    
    if [ "$status_code" = "200" ]; then
        echo "✅ $name (port $port): HEALTHY"
        ((count++))
    else
        echo "❌ $name (port $port): FAILED (status: $status_code)"
        echo "   Response: $(echo "$response" | head -n 1)"
    fi
done

echo ""
echo "📊 Total: $count/9 services responding"
