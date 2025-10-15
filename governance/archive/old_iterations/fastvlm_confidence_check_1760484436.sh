#!/usr/bin/env bash
# FastVLM 90-Second Confidence Check
# Quick daily validation that everything is working

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          FastVLM 90-Second Confidence Check                    ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Health
echo -e "${BLUE}[1/5]${NC} Health check..."
if bash scripts/fastvlm_health.sh > /dev/null 2>&1; then
    echo -e "      ${GREEN}✅ FastVLM is healthy${NC}"
else
    echo -e "      ${RED}❌ FastVLM is not healthy${NC}"
    echo "      Start with: make fastvlm-server"
    exit 1
fi

# Test 2: Metrics endpoint responding
echo -e "${BLUE}[2/5]${NC} Metrics endpoint..."
if curl -s http://127.0.0.1:8811/metrics | grep -q "fastvlm_requests_total"; then
    echo -e "      ${GREEN}✅ Metrics available${NC}"
else
    echo -e "      ${YELLOW}⚠️  Metrics not responding${NC}"
fi

# Test 3: Prometheus scraping
echo -e "${BLUE}[3/5]${NC} Prometheus integration..."
if curl -s 'http://localhost:9090/api/v1/query?query=up{job="fastvlm"}' 2>/dev/null | jq -e '.data.result[0].value[1] == "1"' > /dev/null 2>&1; then
    echo -e "      ${GREEN}✅ Prometheus scraping successfully${NC}"
else
    echo -e "      ${YELLOW}⚠️  Prometheus not scraping (may be expected if monitoring not running)${NC}"
fi

# Test 4: Request rate (deadman check)
echo -e "${BLUE}[4/5]${NC} Request rate..."
REQUEST_RATE=$(curl -s 'http://localhost:9090/api/v1/query?query=rate(fastvlm_requests_total[5m])' 2>/dev/null | jq -r '.data.result[0].value[1] // "0"')
if [ "$REQUEST_RATE" != "0" ]; then
    echo -e "      ${GREEN}✅ Requests flowing (${REQUEST_RATE}/s)${NC}"
else
    echo -e "      ${YELLOW}ℹ️  No recent requests (idle or fresh start)${NC}"
fi

# Test 5: Restart count
echo -e "${BLUE}[5/6]${NC} Watchdog restart count..."
if [ -f /tmp/fastvlm_watchdog_restarts.count ]; then
    RESTART_COUNT=$(cat /tmp/fastvlm_watchdog_restarts.count)
    if [ "$RESTART_COUNT" -eq 0 ]; then
        echo -e "      ${GREEN}✅ No restarts (stable)${NC}"
    elif [ "$RESTART_COUNT" -lt 3 ]; then
        echo -e "      ${YELLOW}ℹ️  ${RESTART_COUNT} restart(s) (acceptable)${NC}"
    else
        echo -e "      ${YELLOW}⚠️  ${RESTART_COUNT} restarts (investigate if flapping)${NC}"
        echo "        Check: make fastvlm-watchdog-logs"
    fi
else
    echo -e "      ${GREEN}✅ No restarts recorded${NC}"
fi

# Test 6: Canary test (catch silent regressions)
echo -e "${BLUE}[6/6]${NC} Canary test (quality check)..."
CANARY_IMAGE="fastvlm/assets/canary/chart.png"
if [ -f "$CANARY_IMAGE" ]; then
    if python3 scripts/athena_vision.py "$CANARY_IMAGE" "One sentence summary." > /tmp/fastvlm_canary.out 2>/dev/null; then
        # Check for expected keywords in output
        if grep -qiE "chart|bar|graph|data|trend" /tmp/fastvlm_canary.out; then
            echo -e "      ${GREEN}✅ Canary passed (model working correctly)${NC}"
        else
            echo -e "      ${RED}❌ Canary failed (unexpected output)${NC}"
            echo "        Model may have wrong weights or path"
            echo "        Output: $(cat /tmp/fastvlm_canary.out | head -1)"
        fi
    else
        echo -e "      ${YELLOW}⚠️  Canary inference failed (server may be slow)${NC}"
    fi
else
    echo -e "      ${YELLOW}ℹ️  Canary image not found (skipping)${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ FastVLM Confidence Check Complete${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Quick Stats:"
if curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:latency_p95_ms:5m' 2>/dev/null | jq -e '.data.result[0]' > /dev/null 2>&1; then
    P95=$(curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:latency_p95_ms:5m' | jq -r '.data.result[0].value[1]')
    echo "   p95 latency: ${P95}ms"
fi
if curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:success_rate:5m' 2>/dev/null | jq -e '.data.result[0]' > /dev/null 2>&1; then
    SUCCESS=$(curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:success_rate:5m' | jq -r '.data.result[0].value[1]')
    SUCCESS_PCT=$(echo "$SUCCESS * 100" | bc | cut -d. -f1)
    echo "   Success rate: ${SUCCESS_PCT}%"
fi
echo ""
echo "🔧 Commands:"
echo "   make fastvlm-metrics          # View live metrics"
echo "   make fastvlm-logs             # Server logs"
echo "   make fastvlm-watchdog-logs    # Watchdog logs"
echo ""

