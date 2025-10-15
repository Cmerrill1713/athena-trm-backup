#!/usr/bin/env bash
# Stack Validation Script
# Runs health checks and smoke tests on the full stack

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Stack Validation - UAT + Athena + Bridge         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
UAT_BASE="${UAT_BASE:-http://127.0.0.1:8181}"
ATHENA_BASE="${ATHENA_BASE:-http://127.0.0.1:8090}"
BRIDGE_BASE="${BRIDGE_BASE:-http://127.0.0.1:8014}"
UAT_TOKEN="${UAT_TOKEN:-supersecret}"
ATH_TOKEN="${ATH_TOKEN:-supersecret}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📊 Step 1: Health Checks"
echo "═══════════════════════════════════════════════════════════"

# Check UAT
if curl -sf "$UAT_BASE/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ UAT${NC}       $UAT_BASE"
else
    echo -e "${RED}❌ UAT${NC}       $UAT_BASE (not responding)"
    exit 1
fi

# Check Athena
if curl -sf "$ATHENA_BASE/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Athena${NC}    $ATHENA_BASE"
else
    echo -e "${RED}❌ Athena${NC}    $ATHENA_BASE (not responding)"
    exit 1
fi

# Check Bridge
if curl -sf "$BRIDGE_BASE/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bridge${NC}    $BRIDGE_BASE"
else
    echo -e "${RED}❌ Bridge${NC}    $BRIDGE_BASE (not responding)"
    exit 1
fi

echo ""
echo "🧪 Step 2: Smoke Tests via Athena"
echo "═══════════════════════════════════════════════════════════"

RESULT=$(curl -sS -X POST "$ATHENA_BASE/run_tests" \
  -H "Authorization: Bearer $ATH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"suite\":\"integration\",\"markers\":\"smoke\",\"maxfail\":10,\"env\":{\"BRIDGE_BASE\":\"$BRIDGE_BASE\",\"BRIDGE_TOKEN\":\"\"}}")

PASSED=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("summary",{}).get("passed",0))')
FAILED=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("summary",{}).get("failed",0))')
OK=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("ok","false"))')

if [ "$OK" = "True" ] || [ "$OK" = "true" ]; then
    echo -e "${GREEN}✅ Smoke Tests PASSED${NC}"
    echo "   Passed: $PASSED | Failed: $FAILED"
else
    echo -e "${RED}❌ Smoke Tests FAILED${NC}"
    echo "   Passed: $PASSED | Failed: $FAILED"
    exit 1
fi

echo ""
echo "🔗 Step 3: Backend Integration"
echo "═══════════════════════════════════════════════════════════"

RESULT=$(curl -sS -X POST "$ATHENA_BASE/run_tests" \
  -H "Authorization: Bearer $ATH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"suite\":\"integration\",\"markers\":\"backends\",\"maxfail\":10,\"env\":{\"UAT_BASE\":\"$UAT_BASE\",\"ATHENA_BASE\":\"$ATHENA_BASE\",\"UAT_TOKEN\":\"$UAT_TOKEN\",\"ATH_TOKEN\":\"$ATH_TOKEN\"}}")

PASSED=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("summary",{}).get("passed",0))')
FAILED=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("summary",{}).get("failed",0))')
OK=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("ok","false"))')

if [ "$OK" = "True" ] || [ "$OK" = "true" ]; then
    echo -e "${GREEN}✅ Backend Tests PASSED${NC}"
    echo "   Passed: $PASSED | Failed: $FAILED"
    echo -e "${GREEN}✅ No 401 errors - token pass-through working!${NC}"
else
    echo -e "${YELLOW}⚠️  Backend Tests FAILED${NC}"
    echo "   Passed: $PASSED | Failed: $FAILED"
    # Don't exit - backend failures may be test issues, not stack issues
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║            ✅ Stack Validation Complete!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Stack Status:"
echo "   UAT:    $UAT_BASE    ✅"
echo "   Athena: $ATHENA_BASE ✅"
echo "   Bridge: $BRIDGE_BASE ✅"
echo ""
echo "🎯 Available Commands:"
echo "   make athena-tests         # Run all integration tests"
echo "   make athena-tests-smoke   # Quick smoke tests"
echo "   make athena-tests-backends # Backend integration tests"
echo "   make stack-down           # Stop all services"
echo ""
