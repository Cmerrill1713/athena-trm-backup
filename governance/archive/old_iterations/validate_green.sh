#!/usr/bin/env bash
# Validate Green - Complete system validation before tagging

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Validate Green - Pre-Tag Checklist                    ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

check() {
    local name="$1"
    local cmd="$2"

    echo -ne "${BLUE}[CHECK]${NC} $name... "

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌${NC}"
        ((FAILED++))
        return 1
    fi
}

# Gate 1: Fast health
echo -e "${BLUE}Gate 1: Fast Health${NC}"
make green > /tmp/validate_green_health.log 2>&1
if grep -q "✅" /tmp/validate_green_health.log; then
    HEALTH_COUNT=$(grep -c "✅" /tmp/validate_green_health.log)
    echo -e "  ${GREEN}✅ $HEALTH_COUNT/6 services healthy${NC}"
    ((PASSED++))
else
    echo -e "  ${RED}❌ Health check failed${NC}"
    cat /tmp/validate_green_health.log
    ((FAILED++))
fi

# Gate 2: E2E sweep
echo -e "\n${BLUE}Gate 2: E2E Sweep${NC}"
if python3 scripts/e2e_full_sweep.py > /tmp/validate_green_e2e.log 2>&1; then
    SWEEP_PASSED=$(grep -c "PASS" /tmp/validate_green_e2e.log || echo 0)
    echo -e "  ${GREEN}✅ E2E sweep: $SWEEP_PASSED tests passed${NC}"
    ((PASSED++))
else
    echo -e "  ${YELLOW}⚠️  E2E sweep had issues${NC}"
    tail -20 /tmp/validate_green_e2e.log
    ((FAILED++))
fi

# Gate 3: Weaviate schema
echo -e "\n${BLUE}Gate 3: Weaviate Schema${NC}"
if curl -s http://localhost:8090/v1/schema 2>/dev/null | jq -e '.classes | length >= 3' > /dev/null 2>&1; then
    CLASS_COUNT=$(curl -s http://localhost:8090/v1/schema | jq '.classes | length')
    echo -e "  ${GREEN}✅ Weaviate: $CLASS_COUNT classes${NC}"
    ((PASSED++))
else
    echo -e "  ${YELLOW}⚠️  Weaviate schema incomplete or not running${NC}"
    echo "     Run: make weaviate-seed"
    ((FAILED++))
fi

# Gate 4: Artifacts exist
echo -e "\n${BLUE}Gate 4: Artifacts${NC}"
check "Docker snapshot" "test -f artifacts/captures/docker-ps.txt"
check "Health matrix" "test -f artifacts/captures/health-matrix.json"
check "E2E report" "ls artifacts/captures/full-evaluation-*.md > /dev/null 2>&1"

# Gate 5: FastVLM (if running)
echo -e "\n${BLUE}Gate 5: FastVLM${NC}"
if curl -s http://127.0.0.1:8811/health > /dev/null 2>&1; then
    check "FastVLM health" "bash scripts/fastvlm_health.sh"
    check "FastVLM metrics" "curl -s http://127.0.0.1:8811/metrics | grep -q fastvlm_requests_total"
    check "Lineage built" "test -f artifacts/lineage/lineage.txt"
else
    echo -e "  ${YELLOW}ℹ️  FastVLM not running (optional)${NC}"
fi

# Gate 6: Git state
echo -e "\n${BLUE}Gate 6: Git State${NC}"
check "No uncommitted changes" "git diff --quiet"
check "No untracked files" "test -z \"\$(git ls-files --others --exclude-standard)\""

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL GATES PASSED${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🎯 Ready to tag as green!"
    echo ""
    echo "Next steps:"
    echo "  git tag -a v0.9.1-green -m 'E2E sweep + routing + Weaviate seeded'"
    echo "  git push --tags"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  $FAILED GATES FAILED${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Fix issues above, then rerun:"
    echo "  bash scripts/validate_green.sh"
    echo ""
    exit 1
fi
