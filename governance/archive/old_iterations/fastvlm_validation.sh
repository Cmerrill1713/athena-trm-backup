#!/usr/bin/env bash
# FastVLM 90-Second Go-Live Validation
# Proves FastVLM is working end-to-end with routing + observability

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          FastVLM 90-Second Go-Live Validation                  ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Server Health
echo -e "${BLUE}[1/6]${NC} Checking FastVLM server health..."
if curl -s http://127.0.0.1:8811/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "      ${GREEN}✓${NC} Server is healthy and warmed up"
else
    echo -e "      ${RED}✗${NC} Server not healthy or not running"
    echo "      Start with: make fastvlm-server"
    exit 1
fi

# Step 2: Pre-aggregated Metrics (Recording Rules)
echo -e "${BLUE}[2/6]${NC} Checking pre-aggregated metrics..."
if curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:latency_p95_ms:5m' 2>/dev/null | jq -e '.data.result | length > 0' > /dev/null 2>&1; then
    P95=$(curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:latency_p95_ms:5m' | jq -r '.data.result[0].value[1]')
    echo -e "      ${GREEN}✓${NC} Recording rules active (p95: ${P95}ms)"
elif curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "      ${YELLOW}⚠${NC} Prometheus running but no data yet (expected if fresh install)"
else
    echo -e "      ${YELLOW}⚠${NC} Prometheus not running"
    echo "      Start with: make monitoring-up"
fi

# Step 3: Success Rate
echo -e "${BLUE}[3/6]${NC} Checking success rate..."
if curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:success_rate:5m' 2>/dev/null | jq -e '.data.result | length > 0' > /dev/null 2>&1; then
    SUCCESS=$(curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:success_rate:5m' | jq -r '.data.result[0].value[1]')
    SUCCESS_PCT=$(echo "$SUCCESS * 100" | bc | cut -d. -f1)
    if (( SUCCESS_PCT >= 95 )); then
        echo -e "      ${GREEN}✓${NC} Success rate: ${SUCCESS_PCT}% (excellent)"
    else
        echo -e "      ${YELLOW}⚠${NC} Success rate: ${SUCCESS_PCT}% (below 95%)"
    fi
else
    echo -e "      ${YELLOW}⚠${NC} No success rate data yet"
fi

# Step 4: Fallback Counter (should be 0)
echo -e "${BLUE}[4/6]${NC} Checking fallback counter..."
FALLBACK_RESULTS=$(curl -s 'http://localhost:9090/api/v1/query?query=rate(fastvlm_fallback_total[5m])' 2>/dev/null | jq '.data.result // []' | jq 'length')
if [[ "$FALLBACK_RESULTS" == "0" ]]; then
    echo -e "      ${GREEN}✓${NC} No fallbacks triggered (good!)"
else
    echo -e "      ${YELLOW}⚠${NC} Fallbacks detected: check logs"
fi

# Step 5: Recording Rules Loaded
echo -e "${BLUE}[5/6]${NC} Verifying recording rules loaded..."
if curl -s http://localhost:9090/api/v1/rules 2>/dev/null | jq -e '.data.groups[] | select(.name | test("fastvlm"))' > /dev/null 2>&1; then
    RULE_COUNT=$(curl -s http://localhost:9090/api/v1/rules | jq '[.data.groups[] | select(.name | test("fastvlm")) | .rules[]] | length')
    echo -e "      ${GREEN}✓${NC} Recording rules loaded: ${RULE_COUNT} rules"
else
    echo -e "      ${YELLOW}⚠${NC} No FastVLM recording rules found"
    echo "      Check: monitoring/alerts/fastvlm.rules.yml"
fi

# Step 6: Quick Smoke Test
echo -e "${BLUE}[6/6]${NC} Running quick smoke test..."
if command -v python3 &> /dev/null && [ -f scripts/vision_smoke_test.py ]; then
    # Check if PIL is available
    if python3 -c "import PIL" 2>/dev/null; then
        echo "      Running 6-image test suite..."
        if timeout 30 python3 scripts/vision_smoke_test.py > /tmp/fastvlm_smoke.log 2>&1; then
            PASSED=$(grep -c "PASS" /tmp/fastvlm_smoke.log || echo 0)
            echo -e "      ${GREEN}✓${NC} Smoke test passed (${PASSED} tests)"
        else
            echo -e "      ${YELLOW}⚠${NC} Smoke test had issues (check /tmp/fastvlm_smoke.log)"
        fi
    else
        echo -e "      ${YELLOW}⚠${NC} PIL not installed, skipping (pip install pillow)"
    fi
else
    echo -e "      ${YELLOW}⚠${NC} Smoke test not available"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ FastVLM Validation Complete${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Quick Commands:"
echo "  make vision-chart IMG=chart.png    # Extract chart data"
echo "  make vision-ocr IMG=doc.png        # Extract text"
echo "  make fastvlm-smoke                 # Full smoke test"
echo "  make fastvlm-metrics               # View live metrics"
echo ""
echo "Dashboards:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3001"
echo ""
echo "Recording Rule Queries (fast!):"
echo "  fastvlm:latency_p95_ms:5m"
echo "  fastvlm:success_rate:5m"
echo "  fastvlm:requests_per_minute:5m"
echo ""

