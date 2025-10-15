#!/usr/bin/env bash
# FastVLM Crash Recovery Test
# Simulates a crash and validates auto-recovery

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          FastVLM Crash Recovery Test                           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if watchdog is running
if ! pgrep -f fastvlm_watchdog.sh > /dev/null; then
    echo -e "${YELLOW}⚠️  Watchdog not running${NC}"
    echo "   Enable with: make fastvlm-autostart"
    echo ""
    read -p "   Continue with manual test? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Pre-crash health check
echo -e "${BLUE}[1/4]${NC} Pre-crash health check..."
if bash scripts/fastvlm_health.sh > /dev/null 2>&1; then
    echo -e "      ${GREEN}✅ Server healthy before crash${NC}"
else
    echo "      ❌ Server not healthy - start with: make fastvlm-server"
    exit 1
fi

# Simulate crash
echo -e "${BLUE}[2/4]${NC} Simulating crash (killing server)..."
pkill -f fastvlm_server.py || true
sleep 2
echo "      ✓ Server killed"

# Wait for recovery
echo -e "${BLUE}[3/4]${NC} Waiting for auto-recovery (max 120s)..."
RECOVERED=false
for i in {1..24}; do
    sleep 5
    if bash scripts/fastvlm_health.sh > /dev/null 2>&1; then
        RECOVERED=true
        echo -e "      ${GREEN}✅ Server recovered in ${i}×5=${i}0 seconds${NC}"
        break
    else
        echo -n "."
    fi
done
echo ""

if [ "$RECOVERED" = false ]; then
    echo "      ❌ Server did not recover within 120 seconds"
    echo "      Check logs: make fastvlm-watchdog-logs"
    exit 1
fi

# Post-recovery validation
echo -e "${BLUE}[4/4]${NC} Post-recovery validation..."
sleep 5

if bash scripts/fastvlm_health.sh > /dev/null 2>&1; then
    echo -e "      ${GREEN}✅ Server stable after recovery${NC}"
else
    echo "      ❌ Server unhealthy after recovery"
    exit 1
fi

# Check restart counter
if [ -f /tmp/fastvlm_watchdog_restarts.count ]; then
    RESTART_COUNT=$(cat /tmp/fastvlm_watchdog_restarts.count)
    echo -e "      ${GREEN}📊 Total restarts: ${RESTART_COUNT}${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Crash Recovery Test PASSED${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Results:"
echo "   • Crash simulated successfully"
echo "   • Auto-recovery worked"
echo "   • Server stable after recovery"
echo ""
echo "📊 Check watchdog logs for details:"
echo "   make fastvlm-watchdog-logs"
echo ""

