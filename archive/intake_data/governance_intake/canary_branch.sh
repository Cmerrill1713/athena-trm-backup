#!/usr/bin/env bash
# Athena Branch Canary System
# Auto-deploys canary per branch, monitors SLOs, promotes or rolls back

set -euo pipefail

# Configuration
BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"
COMMIT=$(git rev-parse --short HEAD)
CANARY_PORT="${CANARY_PORT:-8015}"
MIRROR_PERCENT="${MIRROR_PERCENT:-10}"
MONITOR_DURATION="${MONITOR_DURATION:-300}"  # 5 minutes
AUDIT_LOG="/tmp/athena_canary_audit.log"

# SLO thresholds
MAX_ERROR_RATE=0.01      # 1%
MAX_P95_MS=250
MAX_MTTR_S=60

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_audit() {
    local event="$1"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $event" >> "$AUDIT_LOG"
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🧠 ATHENA CANARY DEPLOYMENT                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Branch: ${YELLOW}$BRANCH${NC}"
echo -e "Commit: ${YELLOW}$COMMIT${NC}"
echo -e "Canary Port: ${YELLOW}$CANARY_PORT${NC}"
echo -e "Mirror: ${YELLOW}$MIRROR_PERCENT%${NC}"
echo ""

log_audit "DEPLOY_START branch=$BRANCH commit=$COMMIT port=$CANARY_PORT mirror=$MIRROR_PERCENT%"

# Step 1: Deploy canary
echo "📦 Step 1/5: Deploying canary..."
cd bridge
CANARY_MODE=1 \
USE_MOCK=0 \
python3 -m uvicorn adapter:app --port "$CANARY_PORT" --reload > /tmp/canary_$CANARY_PORT.log 2>&1 &
CANARY_PID=$!
echo "$CANARY_PID" > /tmp/canary.pid
cd ..

sleep 3

# Verify canary started
if ! curl -sf "http://127.0.0.1:$CANARY_PORT/health" > /dev/null; then
    echo -e "${RED}❌ Canary failed to start${NC}"
    log_audit "DEPLOY_FAILED branch=$BRANCH reason=startup_failed"
    kill $CANARY_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Canary deployed (PID: $CANARY_PID)${NC}"
log_audit "DEPLOY_SUCCESS branch=$BRANCH pid=$CANARY_PID"

# Step 2: Monitor SLOs
echo ""
echo "📊 Step 2/5: Monitoring SLOs for ${MONITOR_DURATION}s..."
echo "Metrics collection every 10s..."

SAMPLES=0
TOTAL_ERRORS=0
TOTAL_REQUESTS=0
MAX_LATENCY=0

for i in $(seq 1 $((MONITOR_DURATION / 10))); do
    # Send test request
    START=$(date +%s%N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$CANARY_PORT/health" 2>/dev/null || echo "000")
    END=$(date +%s%N)
    LATENCY_MS=$(( (END - START) / 1000000 ))
    
    SAMPLES=$((SAMPLES + 1))
    TOTAL_REQUESTS=$((TOTAL_REQUESTS + 1))
    
    if [[ "$HTTP_CODE" =~ ^5 ]]; then
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
    fi
    
    if [[ "$LATENCY_MS" -gt "$MAX_LATENCY" ]]; then
        MAX_LATENCY=$LATENCY_MS
    fi
    
    # Progress indicator
    if [[ $((i % 6)) -eq 0 ]]; then
        echo -n "."
    fi
    
    sleep 10
done

echo ""
echo -e "${GREEN}✅ Monitoring complete${NC}"

# Step 3: Calculate metrics
ERROR_RATE=$(echo "scale=4; $TOTAL_ERRORS / $TOTAL_REQUESTS" | bc)
ERROR_PERCENT=$(echo "scale=2; $ERROR_RATE * 100" | bc)

echo ""
echo "📊 Step 3/5: Canary metrics:"
echo "  Requests: $TOTAL_REQUESTS"
echo "  Errors: $TOTAL_ERRORS"
echo "  Error rate: ${ERROR_PERCENT}%"
echo "  Max latency: ${MAX_LATENCY}ms"
echo ""

log_audit "METRICS branch=$BRANCH requests=$TOTAL_REQUESTS errors=$TOTAL_ERRORS error_rate=$ERROR_PERCENT% max_latency=${MAX_LATENCY}ms"

# Step 4: Decision
echo "🎯 Step 4/5: Promotion decision..."

SHOULD_PROMOTE=true
REJECT_REASON=""

# Check error rate
if (( $(echo "$ERROR_RATE > $MAX_ERROR_RATE" | bc -l) )); then
    SHOULD_PROMOTE=false
    REJECT_REASON="Error rate ${ERROR_PERCENT}% > ${MAX_ERROR_RATE}%"
fi

# Check latency
if [[ "$MAX_LATENCY" -gt "$MAX_P95_MS" ]]; then
    SHOULD_PROMOTE=false
    REJECT_REASON="Max latency ${MAX_LATENCY}ms > ${MAX_P95_MS}ms"
fi

# Step 5: Promote or rollback
echo ""
if [ "$SHOULD_PROMOTE" = "true" ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✅ CANARY PROMOTED ✅                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Branch: ${GREEN}$BRANCH${NC}"
    echo -e "Metrics: Error ${ERROR_PERCENT}%, Latency ${MAX_LATENCY}ms"
    echo ""
    echo "Canary passed SLO gates. Safe to merge."
    
    log_audit "PROMOTE branch=$BRANCH commit=$COMMIT error_rate=$ERROR_PERCENT% latency=${MAX_LATENCY}ms"
    
    # Keep canary running for now (manual cleanup)
    echo ""
    echo "Canary still running on :$CANARY_PORT"
    echo "Stop with: kill $(cat /tmp/canary.pid)"
    
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              ❌ CANARY REJECTED ❌                         ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Branch: $BRANCH${NC}"
    echo -e "${RED}Reason: $REJECT_REASON${NC}"
    echo ""
    echo "Canary failed SLO gates. Do not merge."
    
    log_audit "ROLLBACK branch=$BRANCH commit=$COMMIT reason=\"$REJECT_REASON\""
    
    # Step 5: Auto-cleanup failed canary
    echo ""
    echo "🧹 Cleaning up failed canary..."
    kill $(cat /tmp/canary.pid) 2>/dev/null || true
    rm /tmp/canary.pid 2>/dev/null || true
    echo -e "${GREEN}✅ Canary environment torn down${NC}"
    
    log_audit "CLEANUP branch=$BRANCH status=complete"
    
    echo ""
    echo -e "${YELLOW}Fix the issues and try again.${NC}"
    
    exit 1
fi

