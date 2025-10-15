#!/usr/bin/env bash
# NeuroForge End-to-End Smoke Test
# Validates frontend → backend integration before DMG build
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🔥 NeuroForge E2E Smoke Test"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASS++))
}

fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAIL++))
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ============================================
# PHASE 1: Backend Service Health
# ============================================
echo "🧠 Phase 1: Backend Services"
echo "----------------------------"

# Main API
if curl -sf http://localhost:8014/health > /dev/null 2>&1; then
    pass "Main API (8014)"
else
    fail "Main API (8014) - Not responding"
fi

# TTS
if curl -sf http://localhost:8888/health > /dev/null 2>&1; then
    pass "TTS Service (8888)"
else
    fail "TTS Service (8888) - Not responding"
fi

# FastVLM
if curl -sf http://localhost:8811/health > /dev/null 2>&1; then
    pass "FastVLM (8811)"
else
    warn "FastVLM (8811) - Optional service not running"
fi

# Ollama
if curl -sf http://localhost:11434/api/version > /dev/null 2>&1; then
    pass "Ollama (11434)"
else
    warn "Ollama (11434) - Optional service not running"
fi

# Weaviate
if curl -sf http://localhost:8090/v1/meta > /dev/null 2>&1; then
    pass "Weaviate (8090)"
else
    fail "Weaviate (8090) - RAG service not responding"
fi

echo ""

# ============================================
# PHASE 2: API Endpoint Validation
# ============================================
echo "⚡ Phase 2: API Endpoints"
echo "----------------------------"

# Chat endpoint
CHAT_RESPONSE=$(curl -sf -X POST http://localhost:8014/api/chat \
  -H "Content-Type: application/json" \
  -d '{"kind":"smalltalk","text":"ping"}' 2>/dev/null || echo "")

if [[ -n "$CHAT_RESPONSE" ]]; then
    pass "Chat endpoint (/api/chat)"
else
    fail "Chat endpoint - Not responding"
fi

# Health with routing
HEALTH=$(curl -sf http://localhost:8014/health 2>/dev/null || echo "")
if [[ -n "$HEALTH" ]]; then
    pass "Health endpoint (/health)"
else
    fail "Health endpoint - Not responding"
fi

# Provider health endpoints
for provider in fastvlm ollama trm; do
    RESP=$(curl -sf http://localhost:8014/provider/$provider/health 2>/dev/null || echo "")
    if [[ -n "$RESP" ]]; then
        pass "Provider health (/provider/$provider/health)"
    else
        warn "Provider $provider - Endpoint not available (optional)"
    fi
done

echo ""

# ============================================
# PHASE 3: Swift Build Validation
# ============================================
echo "🔨 Phase 3: Swift Build"
echo "----------------------------"

# Clean build
if swift build -c debug > /dev/null 2>&1; then
    pass "SwiftPM debug build"
else
    fail "SwiftPM debug build - Compilation errors"
fi

# Check binary exists
if [[ -f .build/debug/NeuroForgeApp ]]; then
    pass "Binary exists (.build/debug/NeuroForgeApp)"
else
    fail "Binary not found after build"
fi

echo ""

# ============================================
# PHASE 4: Xcode Project Validation
# ============================================
echo "🔧 Phase 4: Xcode Project"
echo "----------------------------"

# Check project exists
if [[ -f NeuroForgeApp.xcodeproj/project.pbxproj ]]; then
    pass "Xcode project exists"
else
    fail "Xcode project missing"
fi

# Validate project can be opened
if xcodebuild -project NeuroForgeApp.xcodeproj -list > /dev/null 2>&1; then
    pass "Xcode project valid"
else
    fail "Xcode project corrupted or invalid"
fi

# Check UI test target exists
if xcodebuild -project NeuroForgeApp.xcodeproj -list 2>/dev/null | grep -q "NeuroForgeAppUITests"; then
    pass "UI test target exists"
else
    fail "UI test target missing"
fi

echo ""

# ============================================
# PHASE 5: DMG Build Prerequisites
# ============================================
echo "📦 Phase 5: DMG Prerequisites"
echo "----------------------------"

# Entitlements
if [[ -f entitlements.plist ]]; then
    pass "entitlements.plist exists"
    if xmllint --noout entitlements.plist 2>/dev/null; then
        pass "entitlements.plist valid XML"
    else
        fail "entitlements.plist invalid XML"
    fi
else
    fail "entitlements.plist missing"
fi

# Makefile.dmg
if [[ -f Makefile.dmg ]]; then
    pass "Makefile.dmg exists"
else
    fail "Makefile.dmg missing"
fi

# env.template
if [[ -f env.template ]]; then
    pass "env.template exists"
else
    fail "env.template missing"
fi

# Check for signing identity (won't validate creds, just check if command works)
if security find-identity -p codesigning > /dev/null 2>&1; then
    pass "Keychain access working"
    IDENTITY_COUNT=$(security find-identity -p codesigning | grep -c "Developer ID Application" || echo "0")
    if [[ $IDENTITY_COUNT -gt 0 ]]; then
        pass "Developer ID certificate(s) found ($IDENTITY_COUNT)"
    else
        warn "No Developer ID Application certificate found (needed for DMG)"
    fi
else
    fail "Cannot access keychain"
fi

echo ""

# ============================================
# PHASE 6: Configuration Files
# ============================================
echo "⚙️  Phase 6: Configuration"
echo "----------------------------"

# Info.plist
if [[ -f Info.plist ]]; then
    pass "Info.plist exists"
else
    fail "Info.plist missing"
fi

# project.yml (XcodeGen)
if [[ -f project.yml ]]; then
    pass "project.yml exists"
else
    warn "project.yml missing (optional if not using XcodeGen)"
fi

# Scripts
for script in run_frontend.sh warmup_services.sh nightly_qa.sh; do
    if [[ -f "scripts/$script" ]]; then
        pass "Script exists: $script"
        if [[ -x "scripts/$script" ]]; then
            pass "Script executable: $script"
        else
            warn "Script not executable: $script (run: chmod +x scripts/$script)"
        fi
    else
        fail "Script missing: $script"
    fi
done

echo ""

# ============================================
# PHASE 7: Environment Integration
# ============================================
echo "🌐 Phase 7: Environment"
echo "----------------------------"

# Check if .env exists (for DMG builds)
if [[ -f .env ]]; then
    pass ".env exists (configured for DMG build)"
    # Check required vars
    if grep -q "TEAM_ID=" .env && grep -q "SIGN_IDENTITY=" .env; then
        pass ".env contains required variables"
    else
        warn ".env missing TEAM_ID or SIGN_IDENTITY"
    fi
else
    warn ".env not configured (needed for DMG build - copy from env.template)"
fi

# Check backend URL can be resolved
if [[ -n "${API_BASE:-}" ]]; then
    pass "API_BASE environment variable set: $API_BASE"
else
    warn "API_BASE not set (defaults to http://localhost:8014)"
fi

echo ""

# ============================================
# SUMMARY
# ============================================
echo "===================================="
echo "📊 Smoke Test Summary"
echo "===================================="
echo -e "${GREEN}✅ Passed: $PASS${NC}"
echo -e "${RED}❌ Failed: $FAIL${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS GO!${NC}"
    echo ""
    echo "✅ Ready for:"
    echo "   1. UI test run (make xctest)"
    echo "   2. Frontend launch (bash scripts/run_frontend.sh)"
    echo "   3. DMG build (make -f Makefile.dmg dmg)"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  FAILURES DETECTED${NC}"
    echo ""
    echo "Fix failures above before proceeding."
    echo ""
    echo "Common fixes:"
    echo "  - Backend: make green"
    echo "  - Build: swift build"
    echo "  - Xcode: xcodegen generate"
    echo "  - DMG: cp env.template .env && edit .env"
    echo ""
    exit 1
fi
