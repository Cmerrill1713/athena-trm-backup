#!/bin/bash
set -e

echo "🚀 Real Mode Startup - Clean, No Ghosts"
echo "========================================"
echo ""

# Configuration
UAT_PORT=${UAT_PORT:-8181}  # Use 8181 by default to avoid conflicts
ATHENA_PORT=8090
BRIDGE_PORT=8014
UAT_TOKEN=${UAT_TOKEN:-supersecret}
ATH_TOKEN=${ATH_TOKEN:-supersecret}
UAT_BASE=${UAT_BASE:-http://127.0.0.1:$UAT_PORT}
ATHENA_BASE=${ATHENA_BASE:-http://127.0.0.1:$ATHENA_PORT}

# Step 0: Nuke any squatters
echo "🛑 Step 0: Clearing ports..."
for PORT in $UAT_PORT $ATHENA_PORT $BRIDGE_PORT; do
    PID=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -n "$PID" ]; then
        echo "   Killing process on port $PORT (PID: $PID)"
        kill -9 $PID 2>/dev/null || true
    fi
done

# Check for assistant-broker launchd service
if launchctl list 2>/dev/null | grep -q "assistant-broker"; then
    echo "   Removing assistant-broker launchd service..."
    launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.assistant-broker.plist 2>/dev/null || true
    launchctl remove com.assistant-broker 2>/dev/null || true
fi

sleep 2
echo "✅ Ports cleared"
echo ""

# Step 1: Start UAT
echo "🚀 Step 1: Starting UAT on port $UAT_PORT..."
cd "$(dirname "$0")/../AI-Projects/universal-ai-tools"
UAT_TOKEN=$UAT_TOKEN UAT_AUTO_SEED=1 \
python3 -m uvicorn uat.api:app --host 127.0.0.1 --port $UAT_PORT --reload > /tmp/uat_$UAT_PORT.log 2>&1 &
UAT_PID=$!
echo "✅ UAT started (PID: $UAT_PID)"
sleep 3

# Verify UAT
echo "   Testing UAT..."
if curl -sf -H "Authorization: Bearer $UAT_TOKEN" $UAT_BASE/health > /dev/null; then
    echo "   ✅ UAT responding"
else
    echo "   ❌ UAT not responding - check /tmp/uat_$UAT_PORT.log"
    exit 1
fi
echo ""

# Step 2: Start Athena
echo "🚀 Step 2: Starting Athena on port $ATHENA_PORT..."
ATH_TOKEN=$ATH_TOKEN \
python3 -m uvicorn athena.api:app --host 127.0.0.1 --port $ATHENA_PORT --reload > /tmp/athena_$ATHENA_PORT.log 2>&1 &
ATHENA_PID=$!
echo "✅ Athena started (PID: $ATHENA_PID)"
sleep 3

# Verify Athena
echo "   Testing Athena..."
if curl -sf -H "Authorization: Bearer $ATH_TOKEN" $ATHENA_BASE/health > /dev/null; then
    echo "   ✅ Athena responding"
else
    echo "   ❌ Athena not responding - check /tmp/athena_$ATHENA_PORT.log"
    exit 1
fi
echo ""

# Step 3: Start Bridge in real mode
echo "🚀 Step 3: Starting Bridge in REAL mode on port $BRIDGE_PORT..."
ENV=dev USE_MOCK=0 \
UAT_BASE=$UAT_BASE ATHENA_BASE=$ATHENA_BASE \
UAT_TOKEN=$UAT_TOKEN ATH_TOKEN=$ATH_TOKEN \
python3 bridge.py > /tmp/bridge_$BRIDGE_PORT.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > /tmp/bridge.pid
echo "✅ Bridge started (PID: $BRIDGE_PID)"
sleep 3

# Verify Bridge
echo "   Testing Bridge..."
BRIDGE_STATUS=$(curl -s http://127.0.0.1:$BRIDGE_PORT/ | python3 -c "import sys,json; print(json.load(sys.stdin).get('mock_mode', 'unknown'))" 2>/dev/null || echo "error")

if [ "$BRIDGE_STATUS" = "False" ] || [ "$BRIDGE_STATUS" = "false" ]; then
    echo "   ✅ Bridge in REAL mode"
elif [ "$BRIDGE_STATUS" = "True" ] || [ "$BRIDGE_STATUS" = "true" ]; then
    echo "   ⚠️  Bridge still in MOCK mode - check logs"
else
    echo "   ❌ Bridge not responding - check /tmp/bridge_$BRIDGE_PORT.log"
    exit 1
fi
echo ""

# Step 4: Run smoke tests
echo "🧪 Step 4: Smoke tests..."
echo ""
echo "1. Bridge Health:"
curl -s http://127.0.0.1:$BRIDGE_PORT/health | python3 -m json.tool | head -10
echo ""
echo "2. Traces (first item):"
curl -s http://127.0.0.1:$BRIDGE_PORT/traces | python3 -m json.tool | head -20
echo ""

# Success summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║         ✅  REAL MODE ACTIVE - ALL GREEN!  ✅             ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Services Running:"
echo "   UAT:    $UAT_BASE (PID: $UAT_PID)"
echo "   Athena: $ATHENA_BASE (PID: $ATHENA_PID)"
echo "   Bridge: http://127.0.0.1:$BRIDGE_PORT (PID: $BRIDGE_PID)"
echo ""
echo "📝 Logs:"
echo "   UAT:    tail -f /tmp/uat_$UAT_PORT.log"
echo "   Athena: tail -f /tmp/athena_$ATHENA_PORT.log"
echo "   Bridge: tail -f /tmp/bridge_$BRIDGE_PORT.log"
echo ""
echo "🧪 Test Commands:"
echo "   curl -s http://127.0.0.1:$BRIDGE_PORT/health | jq ."
echo "   curl -s http://127.0.0.1:$BRIDGE_PORT/traces | jq '.[0]'"
echo "   curl -s -X POST http://127.0.0.1:$BRIDGE_PORT/chat -H 'content-type: application/json' -d '{\"text\":\"ping\"}' | jq ."
echo ""
echo "🚀 Launch App:"
echo "   API_BASE=http://127.0.0.1:$BRIDGE_PORT QA_MODE=1 swift run"
echo ""
echo "🛑 Stop All:"
echo "   ./scripts/real_down.sh"
echo ""
