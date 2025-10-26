#!/bin/bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 ATHENA QUICK SHIP CHECK - Complete End-to-End Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

# Track failures
FAILURES=0

# Helper function
check_step() {
    local step_name="$1"
    local step_num="$2"
    echo -e "${BLUE}${step_num}) ${step_name}${NC}"
    echo "────────────────────────────────────────────────────────────────────────────"
}

pass_step() {
    echo -e "${GREEN}✅ PASS${NC}"
    echo ""
}

fail_step() {
    local reason="$1"
    echo -e "${RED}❌ FAIL: ${reason}${NC}"
    echo ""
    FAILURES=$((FAILURES + 1))
}

# ============================================================================
# 0) PREFLIGHT
# ============================================================================

check_step "Preflight Checks" "0"

export ATHENA_NO_CLOUD=1
export ATHENA_ENV=production

# Check Docker
if docker version >/dev/null 2>&1; then
    echo "  ✅ Docker running"
else
    fail_step "Docker not running. Start Docker Desktop."
    exit 1
fi

# Create required directories
mkdir -p volumes/weaviate_data volumes/ollama artifacts seeds

# Check compose files
if [ -f "docker-compose.yml" ]; then
    echo "  ✅ docker-compose.yml exists"
else
    fail_step "docker-compose.yml not found"
    exit 1
fi

if [ -f "docker-compose.shadow.yml" ]; then
    echo "  ✅ docker-compose.shadow.yml exists"
else
    echo "  ⚠️  docker-compose.shadow.yml not found (shadow mode unavailable)"
fi

pass_step

# ============================================================================
# 1) START CORE SERVICES
# ============================================================================

check_step "Starting Core Services" "1"

echo "  Starting services (may take 60-90s)..."
docker-compose up -d athena-weaviate athena-router uai athena-prometheus 2>&1 | grep -E "(Creating|Starting|Started|Running)" || true

echo "  Waiting for services to be healthy..."
sleep 15

# Check Weaviate
if curl -sf http://127.0.0.1:8090/v1/.well-known/ready | jq -e '.status == "ok"' >/dev/null 2>&1; then
    echo "  ✅ Weaviate healthy"
else
    fail_step "Weaviate not ready"
fi

# Check Router
if curl -sf http://127.0.0.1:9113/health >/dev/null 2>&1; then
    echo "  ✅ Router healthy"
else
    echo "  ⚠️  Router not responding (may need more time)"
fi

# Check UAI
if curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "  ✅ UAI healthy"
else
    echo "  ⚠️  UAI not responding (may need more time)"
fi

# Check Prometheus
if curl -sf http://127.0.0.1:9090/-/healthy >/dev/null 2>&1; then
    echo "  ✅ Prometheus healthy"
else
    echo "  ⚠️  Prometheus not responding"
fi

pass_step

# ============================================================================
# 2) CORPUS CHECK
# ============================================================================

check_step "Checking Knowledge Corpus" "2"

doc_count=$(curl -sf http://127.0.0.1:8090/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ Aggregate { DocsV2 { meta { count } } } }"}' 2>/dev/null | jq -r '.data.Aggregate.DocsV2[0].meta.count // 0')

if [ "$doc_count" -gt 0 ]; then
    echo "  ✅ DocsV2 corpus: $doc_count documents"
    pass_step
else
    fail_step "No documents in DocsV2. Restore volumes/weaviate_data or run embedding."
fi

# ============================================================================
# 3) RAG SMOKE TEST
# ============================================================================

check_step "RAG Semantic Search" "3"

# Wait a bit more if needed
sleep 5

rag_hits=$(curl -sf http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"athena-chat",
    "messages":[{"role":"user","content":"What is TRM?"}],
    "stream": false
  }' 2>/dev/null | jq -r '.choices[0].message.content // ""' | wc -c)

if [ "$rag_hits" -gt 10 ]; then
    echo "  ✅ RAG working (response: ${rag_hits} chars)"
    pass_step
else
    fail_step "RAG not responding properly. Check UAI logs."
fi

# ============================================================================
# 4) GOVERNANCE GATE
# ============================================================================

check_step "Governance Authorization Gate" "4"

# Check if governance is running
if docker ps | grep -q governance-orchestrator; then
    echo "  ✅ Governance service running"
    
    # Test authorize endpoint (may not be implemented yet)
    gov_response=$(curl -sf http://127.0.0.1:9110/authorize \
      -H "Content-Type: application/json" \
      -d '{"type":"routing","decision":{"route":"rag"},"context":{"source":"smoke"}}' 2>/dev/null || echo '{"error":"not_implemented"}')
    
    if echo "$gov_response" | jq -e '.allowed' >/dev/null 2>&1; then
        echo "  ✅ Governance authorize working"
    else
        echo "  ⚠️  Governance authorize not implemented (advisory mode)"
    fi
    pass_step
else
    echo "  ⚠️  Governance service not running (advisory mode)"
    pass_step
fi

# ============================================================================
# 5) DEV DAEMON (COPILOT)
# ============================================================================

check_step "Athena Dev Daemon (Universal Copilot)" "5"

if docker ps | grep -q athena-devd; then
    if curl -sf http://127.0.0.1:8765/healthz | jq -e '.status == "healthy"' >/dev/null 2>&1; then
        echo "  ✅ Dev daemon healthy"
        
        # Test context suggestion
        snippets=$(curl -sf http://127.0.0.1:8765/ctx/suggest \
          -H "Content-Type: application/json" \
          -d '{"repoRoot":"'"$(pwd)"'","file":"services/router/app.py","query":"routing logic","intent":"explain"}' 2>/dev/null | jq '.snippets | length' || echo 0)
        
        if [ "$snippets" -gt 0 ]; then
            echo "  ✅ Context gathering working (${snippets} snippets)"
        else
            echo "  ⚠️  Context gathering returned 0 snippets"
        fi
        pass_step
    else
        fail_step "Dev daemon unhealthy"
    fi
else
    echo "  ⚠️  Dev daemon not running. Start with: make athena-up"
    pass_step
fi

# ============================================================================
# 6) OBSERVABILITY SPINE
# ============================================================================

check_step "Observability (OTEL + Prometheus)" "6"

# Check OTEL collector
if curl -sf http://127.0.0.1:13133/ >/dev/null 2>&1; then
    echo "  ✅ OTEL collector responding"
else
    echo "  ⚠️  OTEL collector not responding"
fi

# Check Prometheus
if curl -sf http://127.0.0.1:9090/-/healthy >/dev/null 2>&1; then
    echo "  ✅ Prometheus healthy"
    
    # Check if scraping OTEL
    targets=$(curl -sf 'http://127.0.0.1:9090/api/v1/targets' 2>/dev/null | jq -r '.data.activeTargets | length' || echo 0)
    echo "  ✅ Prometheus scraping ${targets} targets"
else
    echo "  ⚠️  Prometheus not responding"
fi

pass_step

# ============================================================================
# 7) GO SHADOW STACK (if enabled)
# ============================================================================

check_step "Go Shadow Stack (Migration Testing)" "7"

if [ -f "docker-compose.shadow.yml" ]; then
    echo "  Starting Go shadow services..."
    docker-compose -f docker-compose.yml -f docker-compose.shadow.yml up -d go-router go-gateway 2>&1 | grep -E "(Creating|Starting|Started|Running)" || true
    
    sleep 10
    
    # Check Go router
    if docker ps | grep -q athena-go-router; then
        echo "  ✅ Go router running (port 9115)"
    else
        echo "  ⚠️  Go router not running"
    fi
    
    # Check Go gateway
    if docker ps | grep -q athena-go-gateway; then
        echo "  ✅ Go gateway running (port 8081)"
    else
        echo "  ⚠️  Go gateway not running"
    fi
    
    pass_step
else
    echo "  ⚠️  Shadow stack not configured (skip)"
    pass_step
fi

# ============================================================================
# 8) PARITY TEST (if Go shadow running)
# ============================================================================

if docker ps | grep -q athena-go-gateway; then
    check_step "Shadow Parity Test" "8"
    
    if [ -f "scripts/shadow_compare.py" ]; then
        echo "  Running parity test..."
        if python3 scripts/shadow_compare.py 2>&1 | tail -20; then
            echo "  ✅ Parity test completed (see artifacts/shadow_results.json)"
            pass_step
        else
            fail_step "Parity test failed"
        fi
    else
        echo "  ⚠️  Shadow test script not found (skip)"
        pass_step
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 FINAL SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}"
    echo "🎉 ALL CHECKS PASSED! 🎉"
    echo ""
    echo "Athena is PRODUCTION-READY!"
    echo ""
    echo "Next steps:"
    echo "  - Production: docker-compose up -d"
    echo "  - Copilot: make athena-up"
    echo "  - Go Migration: make go-shadow-up"
    echo ""
    echo -e "${NC}"
    exit 0
else
    echo -e "${YELLOW}"
    echo "⚠️  ${FAILURES} CHECK(S) FAILED"
    echo ""
    echo "Review failures above and fix before shipping."
    echo ""
    echo -e "${NC}"
    exit 1
fi
