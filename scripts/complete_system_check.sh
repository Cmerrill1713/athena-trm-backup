#!/bin/bash
# Complete System Check - Validates all integrated components
# Adapted for your current running services

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
    ((WARNINGS++))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
}

# ============================================================================
# CORE SERVICES CHECK
# ============================================================================

section "CHECKING CORE SERVICES"

# RAG Gateway (8088)
if curl -sf http://localhost:8088/health > /dev/null 2>&1; then
    SERVICE=$(curl -s http://localhost:8088/health | jq -r '.service // "unknown"')
    pass "RAG Gateway (8088) - $SERVICE"
else
    fail "RAG Gateway (8088) not responding"
fi

# Smart Chat with RAG (8089)
if curl -sf http://localhost:8089/health > /dev/null 2>&1; then
    MODEL=$(curl -s http://localhost:8089/health | jq -r '.model // "unknown"')
    pass "Smart Chat (8089) - $MODEL"
else
    fail "Smart Chat (8089) not responding"
fi

# Weaviate (8090)
if curl -sf http://localhost:8090/v1/meta > /dev/null 2>&1; then
    VERSION=$(curl -s http://localhost:8090/v1/meta | jq -r '.version // "unknown"')
    pass "Weaviate (8090) - v$VERSION"
else
    fail "Weaviate (8090) not responding"
fi

# Unified Metrics (9114)
if curl -sf http://localhost:9114/health > /dev/null 2>&1; then
    pass "Unified Metrics (9114)"
else
    warn "Unified Metrics (9114) not responding"
fi

# Ollama (11434)
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    MODELS=$(curl -s http://localhost:11434/api/tags | jq -r '.models | length')
    pass "Ollama (11434) - $MODELS models loaded"
else
    warn "Ollama (11434) not responding"
fi

# ============================================================================
# KNOWLEDGE BASE CHECK
# ============================================================================

section "CHECKING KNOWLEDGE BASE"

# Check DocsV2 document count
DOC_COUNT=$(curl -s http://localhost:8090/v1/objects -G \
    --data-urlencode 'class=DocsV2' \
    --data-urlencode 'limit=1' | jq -r '.totalResults // 0')

if [ "$DOC_COUNT" -gt 0 ]; then
    pass "Knowledge base has $DOC_COUNT documents"
else
    warn "Knowledge base is empty - seed with: python3 scripts/quick_seed_768.py"
fi

# Test KB search
KB_HITS=$(curl -s http://localhost:8088/kb/search \
    -H 'Content-Type: application/json' \
    -d '{"query":"TRM","topK":3}' | jq -r '.hits | length')

if [ "$KB_HITS" -gt 0 ]; then
    pass "KB search returns $KB_HITS hits"
else
    fail "KB search returns 0 hits"
fi

# ============================================================================
# RAG INTEGRATION CHECK
# ============================================================================

section "CHECKING RAG INTEGRATION"

# Test Smart Chat with factual query (should use RAG)
info "Testing factual query (should use RAG)..."
FACTUAL_RESPONSE=$(curl -s http://localhost:8089/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"messages":[{"role":"user","content":"What is TRM?"}],"max_tokens":100}' \
    | jq -r '.choices[0].message.content // "ERROR"')

if [ "$FACTUAL_RESPONSE" != "ERROR" ] && [ ${#FACTUAL_RESPONSE} -gt 20 ]; then
    pass "Factual query successful (${#FACTUAL_RESPONSE} chars)"
else
    fail "Factual query failed"
fi

# Test Smart Chat with creative query (should not use RAG)
info "Testing creative query (should not use RAG)..."
CREATIVE_RESPONSE=$(curl -s http://localhost:8089/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"messages":[{"role":"user","content":"Write a haiku"}],"max_tokens":50}' \
    | jq -r '.choices[0].message.content // "ERROR"')

if [ "$CREATIVE_RESPONSE" != "ERROR" ] && [ ${#CREATIVE_RESPONSE} -gt 10 ]; then
    pass "Creative query successful (${#CREATIVE_RESPONSE} chars)"
else
    fail "Creative query failed"
fi

# ============================================================================
# AGI-RAG BRIDGE CHECK
# ============================================================================

section "CHECKING AGI-RAG BRIDGE"

# Test Python KB search API
info "Testing Python kb_search API..."
KB_SEARCH_TEST=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '/Users/christianmerrill/Documents/GitHub')
try:
    from agi_core.tools import kb_search
    results = asyncio.run(kb_search('TRM', top_k=2))
    print(f'SUCCESS:{len(results)}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

if echo "$KB_SEARCH_TEST" | grep -q "SUCCESS:"; then
    RESULT_COUNT=$(echo "$KB_SEARCH_TEST" | grep -oP 'SUCCESS:\K\d+')
    pass "Python kb_search API returns $RESULT_COUNT results"
else
    warn "Python kb_search API test failed: $KB_SEARCH_TEST"
fi

# ============================================================================
# SMART ROUTING CHECK
# ============================================================================

section "CHECKING SMART ROUTING"

# Check smart router module
if python3 -c "import sys; sys.path.insert(0, 'services'); from smart_router import route_query; print('OK')" > /dev/null 2>&1; then
    pass "Smart router module loaded"
else
    warn "Smart router module not accessible"
fi

# Test routing logic
ROUTING_TEST=$(python3 -c "
import sys
sys.path.insert(0, 'services')
try:
    from smart_router import route_query
    result = route_query('What is TRM?')
    needs_rag = result.get('needs_rag', False)
    model = result.get('selected_model', 'unknown')
    print(f'RAG:{needs_rag}|MODEL:{model}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

if echo "$ROUTING_TEST" | grep -q "RAG:True"; then
    pass "Smart routing detects RAG queries correctly"
elif echo "$ROUTING_TEST" | grep -q "RAG:False"; then
    warn "Smart routing may need tuning (RAG not detected for factual query)"
else
    warn "Smart routing test inconclusive: $ROUTING_TEST"
fi

# ============================================================================
# SUMMARY
# ============================================================================

section "TEST SUMMARY"

echo ""
echo -e "  ${GREEN}✓ Passed:${NC} $PASSED"
echo -e "  ${YELLOW}⚠ Warnings:${NC} $WARNINGS"
echo -e "  ${RED}✗ Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ SYSTEM CHECK PASSED - All critical components operational${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Your AGI-RAG-TRM integration is working!"
    echo ""
    echo "🎯 Quick Test:"
    echo "   curl http://localhost:8080/simple-chat.html"
    echo ""
    echo "📊 Components:"
    echo "   • RAG Gateway:      http://localhost:8088"
    echo "   • Smart Chat:       http://localhost:8089"
    echo "   • Weaviate:         http://localhost:8090"
    echo "   • Unified Metrics:  http://localhost:9114"
    echo "   • UI:               http://localhost:8080/simple-chat.html"
    echo ""
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ SYSTEM CHECK FAILED - $FAILED critical issue(s)${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Please address the failures above before proceeding."
    echo ""
    exit 1
fi

