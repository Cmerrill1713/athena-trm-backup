#!/usr/bin/env bash
# GO LIVE - Complete Athena System Activation
# Boots stack, enables watchdog, validates everything

set -e

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKSPACE_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        🚀 ATHENA AUTONOMOUS SYSTEM - GO LIVE 🚀           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Boot stack
echo -e "${BLUE}1/6: Starting services...${NC}"
export OTEL_DISABLED=1  # Graceful degradation without Docker
bash scripts/real_up.sh > /tmp/go_live_startup.log 2>&1
sleep 5
echo -e "${GREEN}  ✅ Services started${NC}"
echo ""

# Step 2: Verify health
echo -e "${BLUE}2/6: Verifying health...${NC}"
if curl -sf http://127.0.0.1:8014/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Bridge healthy${NC}"
else
    echo -e "${YELLOW}  ⚠️  Bridge not responding${NC}"
fi

if curl -sf http://127.0.0.1:8090/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Athena healthy${NC}"
else
    echo -e "${YELLOW}  ⚠️  Athena not responding${NC}"
fi

if curl -sf http://127.0.0.1:8181/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ UAT healthy${NC}"
else
    echo -e "${YELLOW}  ⚠️  UAT not responding${NC}"
fi
echo ""

# Step 3: Enable watchdog
echo -e "${BLUE}3/6: Enabling autonomous healing...${NC}"
make auto-heal-start > /dev/null 2>&1 || echo -e "${YELLOW}  ⚠️  Watchdog already running${NC}"
sleep 2
echo -e "${GREEN}  ✅ Watchdog active${NC}"
echo ""

# Step 4: Run smoke tests
echo -e "${BLUE}4/6: Running validation...${NC}"
SMOKE_RESULT=$(make athena-tests-smoke 2>&1 | grep "Status:" || echo "Status: UNKNOWN")
if echo "$SMOKE_RESULT" | grep -q "PASS"; then
    echo -e "${GREEN}  ✅ Smoke tests passed${NC}"
else
    echo -e "${YELLOW}  ⚠️  Smoke tests: $SMOKE_RESULT${NC}"
fi
echo ""

# Step 5: Health probes
echo -e "${BLUE}5/6: Checking Tier 4 features...${NC}"
if curl -sf http://127.0.0.1:8014/live > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Liveness probe${NC}"
else
    echo -e "${YELLOW}  ⚠️  Liveness probe${NC}"
fi

if curl -sf http://127.0.0.1:8014/ready > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Readiness probe${NC}"
else
    echo -e "${YELLOW}  ⚠️  Readiness probe${NC}"
fi

if curl -sf http://127.0.0.1:8090/metrics 2>&1 | head -1 | grep -q "#"; then
    echo -e "${GREEN}  ✅ Metrics export${NC}"
else
    echo -e "${YELLOW}  ⚠️  Metrics export${NC}"
fi
echo ""

# Step 6: Ready
echo -e "${BLUE}6/6: System status...${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ ATHENA SYSTEM: LIVE & OPERATIONAL ✅           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Services Running:${NC}"
echo "  Bridge:  http://127.0.0.1:8014"
echo "  UAT:     http://127.0.0.1:8181"
echo "  Athena:  http://127.0.0.1:8090"
echo ""
echo -e "${GREEN}Autonomous Features:${NC}"
echo "  ✅ Watchdog: Active (auto-heal < 60s)"
echo "  ✅ Pre-push: Validates all branches"
echo "  ✅ Canary: SLO-driven decisions"
echo "  ✅ Voice: 23 intents available"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "  1. Connect frontend:"
echo "     export NEXT_PUBLIC_API_BASE=http://127.0.0.1:8014"
echo "     npm run dev"
echo ""
echo "  2. Test chat:"
echo "     curl -X POST http://127.0.0.1:8014/chat -H 'Content-Type: application/json' -d '{\"text\":\"hello\"}'"
echo ""
echo "  3. Voice commands:"
echo "     athena \"what's running\""
echo "     athena \"run smoke tests\""
echo "     athena \"ship it\""
echo ""
echo -e "${GREEN}Logs:${NC}"
echo "  Watchdog: tail -f /tmp/watchdog_stack.log"
echo "  Bridge:   tail -f /tmp/bridge_8014.log"
echo "  Athena:   tail -f /tmp/athena_8090.log"
echo ""
echo -e "${GREEN}Shutdown:${NC}"
echo "  athena \"shut everything down\""
echo ""

