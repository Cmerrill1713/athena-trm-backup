#!/bin/bash
# Simplified Ship Check - Works with current services
# Validates core AGI-RAG integration is functional

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() { echo -e "${GREEN}✓ PASS${NC} $1"; ((PASSED++)) || true; }
fail() { echo -e "${RED}✗ FAIL${NC} $1"; ((FAILED++)) || true; }
info() { echo -e "${YELLOW}ℹ${NC} $1"; }

echo "═══════════════════════════════════════════════════════════════════════"
echo "  SIMPLIFIED SHIP CHECK (Core Services)"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# 1. RAG Gateway
info "Checking RAG Gateway..."
if curl -sf http://localhost:8088/health > /dev/null 2>&1; then
    pass "RAG Gateway (8088) responding"
else
    fail "RAG Gateway (8088) not responding"
fi

# 2. Weaviate
info "Checking Weaviate..."
if curl -sf http://localhost:8090/v1/meta > /dev/null 2>&1; then
    pass "Weaviate (8090) responding"
else
    fail "Weaviate (8090) not responding"
fi

# 3. Embedding Service
info "Checking Embedding Service..."
if curl -sf http://localhost:8086/health > /dev/null 2>&1; then
    pass "Embedding Service (8086) responding"
else
    fail "Embedding Service (8086) not responding"
fi

# 4. OpenAI Adapter
info "Checking OpenAI Adapter..."
if curl -sf http://localhost:3000/v1/models > /dev/null 2>&1; then
    pass "OpenAI Adapter (3000) responding"
else
    fail "OpenAI Adapter (3000) not responding"
fi

# 5. KB Search functional
info "Testing KB search..."
RESPONSE=$(curl -s http://localhost:8088/kb/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test search","topK":3,"mode":"nearText"}')

HITS=$(echo "$RESPONSE" | jq -r '.hits | length' 2>/dev/null || echo "0")
LATENCY=$(echo "$RESPONSE" | jq -r '.metrics.latency_ms' 2>/dev/null || echo "999")

if [ "$HITS" -ge 1 ]; then
    pass "KB search returns hits ($HITS found)"
else
    fail "KB search returns 0 hits (corpus empty?)"
fi

if [ "$LATENCY" != "null" ] && [ "$LATENCY" -le 300 ]; then
    pass "KB search latency ${LATENCY}ms ≤ 300ms"
else
    info "KB search latency: ${LATENCY}ms"
fi

# 6. DocsV2 populated
info "Checking DocsV2 corpus..."
DOC_COUNT=$(curl -s 'http://localhost:8090/v1/objects?class=DocsV2&limit=1' | jq -r '.totalResults // 0')

if [ "$DOC_COUNT" -gt 0 ]; then
    pass "DocsV2 has $DOC_COUNT documents"
else
    fail "DocsV2 is empty (0 documents)"
fi

# 7. Embeddings working
info "Testing embeddings..."
EMBED_RESPONSE=$(curl -s http://localhost:8086/embed \
    -H 'Content-Type: application/json' \
    -d '{"texts":["test"],"tier":"base"}')

EMBED_DIMS=$(echo "$EMBED_RESPONSE" | jq -r '.dimension // 0')

if [ "$EMBED_DIMS" -eq 768 ]; then
    pass "Embeddings generating 768-dim vectors"
else
    fail "Embeddings not working (dims: $EMBED_DIMS)"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  RESULTS"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "═══════════════════════════════════════════════════════════════════════"
    echo -e "  ${GREEN}✓ SHIP IT!${NC} Core AGI-RAG integration is working."
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Your AGI agents can query the knowledge base!"
    echo ""
    echo "Next steps:"
    echo "  - Add more docs: python3 scripts/embed_docs_v2.py --input <dir>"
    echo "  - Run full tests: make rag-eval"
    echo "  - Scale up corpus: migrate your research papers"
    echo ""
    exit 0
else
    echo "═══════════════════════════════════════════════════════════════════════"
    echo -e "  ${RED}✗ NOT READY${NC} - $FAILED check(s) failed"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Fix the issues above before shipping."
    echo ""
    exit 1
fi

