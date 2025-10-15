#!/bin/bash
set -e

echo "🛑 Stopping Real Mode Services..."
echo "=================================="
echo ""

# Configuration
UAT_PORT=${UAT_PORT:-8181}
ATHENA_PORT=8090
BRIDGE_PORT=8014

# Stop bridge
if [ -f /tmp/bridge.pid ]; then
    PID=$(cat /tmp/bridge.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 Stopping Bridge (PID: $PID)..."
        kill -9 $PID 2>/dev/null || true
    fi
    rm -f /tmp/bridge.pid
fi

# Stop by port
for PORT in $UAT_PORT $ATHENA_PORT $BRIDGE_PORT; do
    PID=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -n "$PID" ]; then
        echo "🛑 Stopping service on port $PORT (PID: $PID)..."
        kill -9 $PID 2>/dev/null || true
    fi
done

# Stop by process name
pkill -f "uvicorn uat.api" 2>/dev/null || true
pkill -f "uvicorn athena.api" 2>/dev/null || true
pkill -f "python3 bridge.py" 2>/dev/null || true

echo ""
echo "✅ All services stopped"
echo ""
echo "📋 Logs available at:"
echo "   /tmp/uat_*.log"
echo "   /tmp/athena_*.log"
echo "   /tmp/bridge_*.log"
echo ""
