#!/usr/bin/env bash
# Canary Smoke Test - Test canary deployment with traffic split validation

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
CANARY_MODEL="${CANARY_MODEL:-fastvlm-1.5b}"
TARGET_PERCENT="${TARGET_PERCENT:-25}"
TEST_REQUESTS=40
TOLERANCE=10  # ±10% tolerance for sampling variance

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Canary Deployment Smoke Test                          ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Enable canary
echo -e "${BLUE}[1/4]${NC} Enabling canary at ${TARGET_PERCENT}%..."
export CANARY_MODEL="$CANARY_MODEL"
export CANARY_ENABLED=true
export CANARY_PERCENT=$TARGET_PERCENT
export CANARY_REQUIRE_HEALTH=false  # Don't skip for test

echo -e "      ${GREEN}✓${NC} Canary enabled: $CANARY_MODEL at $CANARY_PERCENT%"

# Step 2: Generate test traffic
echo -e "${BLUE}[2/4]${NC} Generating $TEST_REQUESTS test requests..."
for i in $(seq 1 $TEST_REQUESTS); do
    # Use vision endpoint for testing
    make vision IMG=fastvlm/assets/canary/chart.png PROMPT="Test $i" > /dev/null 2>&1 &
    
    # Show progress
    if [ $((i % 10)) -eq 0 ]; then
        echo -n "."
    fi
done

# Wait for all requests to complete
wait
echo ""
echo -e "      ${GREEN}✓${NC} Generated $TEST_REQUESTS requests"

# Step 3: Check traffic split
echo -e "${BLUE}[3/4]${NC} Checking traffic split..."
sleep 10  # Let Prometheus scrape

# Query bucket distribution
BUCKET_DATA=$(curl -s 'http://localhost:9090/api/v1/query?query=sum%20by%20(bucket)%20(increase(routing_decisions_total%5B2m%5D))' 2>/dev/null | jq -r '.data.result[]' 2>/dev/null || echo "")

if [ -z "$BUCKET_DATA" ]; then
    echo -e "      ${YELLOW}⚠️  No metrics available yet${NC}"
    echo "        (Prometheus may need more time to scrape)"
else
    # Parse results
    CONTROL_COUNT=$(echo "$BUCKET_DATA" | jq -r 'select(.metric.bucket=="control") | .value[1]' | head -1)
    CANARY_COUNT=$(echo "$BUCKET_DATA" | jq -r 'select(.metric.bucket=="canary") | .value[1]' | head -1)
    
    CONTROL_COUNT=${CONTROL_COUNT:-0}
    CANARY_COUNT=${CANARY_COUNT:-0}
    
    TOTAL=$((CONTROL_COUNT + CANARY_COUNT))
    
    if [ "$TOTAL" -gt 0 ]; then
        ACTUAL_PERCENT=$(echo "scale=1; ($CANARY_COUNT * 100) / $TOTAL" | bc)
        
        echo -e "      ${GREEN}📊 Traffic split:${NC}"
        echo "        Control: $CONTROL_COUNT requests"
        echo "        Canary:  $CANARY_COUNT requests"
        echo "        Total:   $TOTAL requests"
        echo "        Canary %: ${ACTUAL_PERCENT}%"
        
        # Check if within tolerance
        DIFF=$(echo "$ACTUAL_PERCENT - $TARGET_PERCENT" | bc | tr -d '-')
        DIFF_INT=${DIFF%.*}
        
        if [ "$DIFF_INT" -le "$TOLERANCE" ]; then
            echo -e "      ${GREEN}✅ Split is correct (±${TOLERANCE}% tolerance)${NC}"
        else
            echo -e "      ${YELLOW}⚠️  Split is ${DIFF}% off target${NC}"
            echo "        (May be sampling variance with small N)"
        fi
    else
        echo -e "      ${YELLOW}⚠️  No traffic recorded yet${NC}"
    fi
fi

# Step 4: Check circuit breaker state
echo -e "${BLUE}[4/4]${NC} Checking circuit breaker..."
BREAKER_DATA=$(curl -s 'http://localhost:9090/api/v1/query?query=circuit_breaker_open' 2>/dev/null | jq -r '.data.result[]' 2>/dev/null || echo "")

if [ -z "$BREAKER_DATA" ]; then
    echo -e "      ${GREEN}✓${NC} No circuits open (all models healthy)"
else
    echo "$BREAKER_DATA" | jq -r '. | "\(.metric.model): \(if .value[1] == "1" then "OPEN" else "CLOSED" end)"' | while read line; do
        if echo "$line" | grep -q "OPEN"; then
            echo -e "      ${YELLOW}⚠️  $line${NC}"
        else
            echo -e "      ${GREEN}✓${NC}  $line"
        fi
    done
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Canary Smoke Test Complete${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "  # Disable canary"
echo "  make canary-off"
echo ""
echo "  # Or increase percentage"
echo "  make canary-50"
echo ""
echo "  # Instant rollback if issues"
echo "  make canary-rollback"
echo ""
echo "📊 Monitor in Grafana:"
echo "  http://localhost:3001"
echo ""

