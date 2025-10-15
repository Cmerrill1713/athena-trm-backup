#!/bin/bash
# Athena Tool: Show status of all services
cd "$(dirname "$0")/.."

echo "📊 Service Status:"
echo ""

make stack-status-full 2>/dev/null || {
    echo "=== Port Status ==="
    lsof -i :8014,8015,8016,8020,8090,8181,8811 2>/dev/null | grep LISTEN || echo "No services listening"
    
    echo ""
    echo "=== Process Status ==="
    ps aux | grep -E "bridge|athena|uat|kokoro|rag_service|vision" | grep -v grep | awk '{print $2, $11}'
}

