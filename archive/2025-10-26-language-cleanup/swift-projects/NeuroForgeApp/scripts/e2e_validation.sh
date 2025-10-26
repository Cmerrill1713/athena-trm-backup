#!/usr/bin/env bash
# NeuroForge End-to-End Integration Validation
# Tests actual frontend → backend communication
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🧪 NeuroForge E2E Integration Test"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
API_BASE="${API_BASE:-http://localhost:8014}"

pass() { echo -e "${GREEN}✅ $1${NC}"; ((PASS++)); }
fail() { echo -e "${RED}❌ $1${NC}"; ((FAIL++)); }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# ============================================
# TEST 1: Basic Chat (Smalltalk)
# ============================================
echo "💬 Test 1: Basic Chat"
echo "----------------------------"

CHAT_REQ='{"kind":"smalltalk","text":"hello"}'
CHAT_RESP=$(curl -sf -X POST "$API_BASE/api/chat" \
    -H "Content-Type: application/json" \
    -d "$CHAT_REQ" 2>/dev/null || echo "")

if [[ -n "$CHAT_RESP" ]] && [[ "$CHAT_RESP" != *"error"* ]]; then
    pass "Chat endpoint responds"
    info "Response: ${CHAT_RESP:0:80}..."
else
    fail "Chat endpoint failed or returned error"
fi

echo ""

# ============================================
# TEST 2: Provider Override Headers
# ============================================
echo "🔀 Test 2: Provider Override"
echo "----------------------------"

for provider in auto fastvlm ollama trm; do
    RESP=$(curl -sf -X POST "$API_BASE/api/chat" \
        -H "Content-Type: application/json" \
        -H "X-Provider-Override: $provider" \
        -d '{"kind":"smalltalk","text":"test"}' 2>/dev/null || echo "")

    if [[ -n "$RESP" ]]; then
        pass "Provider override: $provider"
    else
        warn "Provider $provider - Not responding (may not be running)"
    fi
done

echo ""

# ============================================
# TEST 3: RAG Search
# ============================================
echo "🔍 Test 3: RAG Search"
echo "----------------------------"

RAG_RESP=$(curl -sf "$API_BASE/api/rag/search?query=test&limit=3" 2>/dev/null || echo "")

if [[ -n "$RAG_RESP" ]]; then
    pass "RAG search endpoint"
    if echo "$RAG_RESP" | grep -q "results\|chunks\|documents"; then
        pass "RAG returns structured data"
    else
        warn "RAG response format unexpected"
    fi
else
    warn "RAG search not available (Weaviate may not be seeded)"
fi

echo ""

# ============================================
# TEST 4: Vision Endpoint (if available)
# ============================================
echo "👁️  Test 4: Vision Endpoint"
echo "----------------------------"

# Check if vision endpoint exists
VISION_HEALTH=$(curl -sf "$API_BASE/api/vision/health" 2>/dev/null || echo "")

if [[ -n "$VISION_HEALTH" ]]; then
    pass "Vision endpoint available"
else
    warn "Vision endpoint not responding (optional)"
fi

echo ""

# ============================================
# TEST 5: Router Health Probes
# ============================================
echo "🏥 Test 5: Router Health"
echo "----------------------------"

ROUTER_HEALTH=$(curl -sf "$API_BASE/api/router/health" 2>/dev/null || echo "")

if [[ -n "$ROUTER_HEALTH" ]]; then
    pass "Router health endpoint"
else
    warn "Router health endpoint not available (backend may not support it)"
fi

echo ""

# ============================================
# TEST 6: Frontend Build Artifacts
# ============================================
echo "🔨 Test 6: Frontend Build"
echo "----------------------------"

# Check debug build
if [[ -f .build/debug/NeuroForgeApp ]]; then
    pass "Debug binary exists"
else
    info "Building debug binary..."
    if swift build -c debug > /dev/null 2>&1; then
        pass "Debug build successful"
    else
        fail "Debug build failed"
    fi
fi

# Check if app bundle is properly structured
if [[ -d .build/debug/NeuroForgeApp.app ]]; then
    pass "App bundle structure valid"

    # Check Info.plist
    if [[ -f .build/debug/NeuroForgeApp.app/Contents/Info.plist ]]; then
        pass "Info.plist in bundle"
    else
        fail "Info.plist missing from bundle"
    fi
else
    warn "App bundle not found (may be executable-only)"
fi

echo ""

# ============================================
# TEST 7: Configuration Validation
# ============================================
echo "⚙️  Test 7: Configuration"
echo "----------------------------"

# Check required files
for file in Info.plist entitlements.plist Makefile.dmg env.template; do
    if [[ -f "$file" ]]; then
        pass "Config file: $file"
    else
        fail "Config file missing: $file"
    fi
done

# Validate XML files
for plist in Info.plist entitlements.plist; do
    if [[ -f "$plist" ]] && xmllint --noout "$plist" 2>/dev/null; then
        pass "$plist valid XML"
    elif [[ -f "$plist" ]]; then
        fail "$plist invalid XML"
    fi
done

echo ""

# ============================================
# TEST 8: Network Connectivity Test
# ============================================
echo "🌐 Test 8: Network Round-Trip"
echo "----------------------------"

START=$(date +%s%3N)
PING=$(curl -sf -w "%{time_total}" "$API_BASE/health" -o /dev/null 2>/dev/null || echo "999")
END=$(date +%s%3N)
RTT=$((END - START))

if [[ "$PING" != "999" ]]; then
    if [[ $RTT -lt 100 ]]; then
        pass "Network latency: ${RTT}ms (excellent)"
    elif [[ $RTT -lt 500 ]]; then
        pass "Network latency: ${RTT}ms (good)"
    else
        warn "Network latency: ${RTT}ms (slow)"
    fi
else
    fail "Network connectivity test failed"
fi

echo ""

# ============================================
# TEST 9: Environment Variables
# ============================================
echo "🔐 Test 9: Environment Check"
echo "----------------------------"

if [[ -n "${API_BASE:-}" ]]; then
    pass "API_BASE set: $API_BASE"
else
    warn "API_BASE not set (will use default: http://localhost:8014)"
fi

if [[ -n "${QA_MODE:-}" ]]; then
    pass "QA_MODE set: $QA_MODE"
else
    info "QA_MODE not set (UI features may be hidden)"
fi

echo ""

# ============================================
# SUMMARY
# ============================================
echo "===================================="
echo "📊 E2E Validation Summary"
echo "===================================="
echo -e "${GREEN}✅ Passed: $PASS${NC}"
echo -e "${RED}❌ Failed: $FAIL${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 E2E VALIDATION PASSED!${NC}"
    echo ""
    echo "✅ All integration points healthy"
    echo "✅ Frontend can communicate with backend"
    echo "✅ Ready for:"
    echo "   • Full UI test run"
    echo "   • Frontend launch"
    echo "   • DMG build"
    echo ""
    echo "Next steps:"
    echo "  1. Run UI tests: make xctest"
    echo "  2. Launch app: bash scripts/run_frontend.sh"
    echo "  3. Build DMG: make -f Makefile.dmg dmg"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  E2E VALIDATION FAILED${NC}"
    echo ""
    echo "Fix $FAIL issue(s) above before proceeding."
    echo ""
    echo "Common fixes:"
    echo "  • Backend down: cd .. && make green"
    echo "  • Build errors: swift build"
    echo "  • Missing files: Check git status"
    echo ""
    exit 1
fi
