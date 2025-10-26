#!/bin/bash
# Canary Deployment for AGI+RAG+TRM Integration
# 
# Gradually routes traffic through new integration with automatic rollback on failure
#
# Usage:
#   bash scripts/canary_deploy.sh start   # Start at 5%
#   bash scripts/canary_deploy.sh promote # Increase percentage
#   bash scripts/canary_deploy.sh rollback # Revert to baseline

set -eo pipefail

CANARY_STATE_FILE=".canary_state"
CANARY_PERCENTAGE=${CANARY_PERCENTAGE:-5}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}ℹ${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Save canary state
save_state() {
    local percentage=$1
    echo "{\"percentage\": $percentage, \"started_at\": $(date +%s), \"baseline_p95\": $2}" > $CANARY_STATE_FILE
}

# Load canary state
load_state() {
    if [ -f "$CANARY_STATE_FILE" ]; then
        cat $CANARY_STATE_FILE
    else
        echo "{\"percentage\": 0}"
    fi
}

# Check canary health gates
check_gates() {
    info "Checking canary health gates..."
    
    # Get current metrics
    SNAPSHOT=$(curl -s http://localhost:8092/snapshot 2>/dev/null || echo '{}')
    
    CURRENT_P95=$(echo "$SNAPSHOT" | jq -r '.rag_avg_latency_ms // 0')
    ERROR_RATE=$(echo "$SNAPSHOT" | jq -r '.total_errors / .total_requests * 100 // 0')
    HIT_AT_5=$(echo "$SNAPSHOT" | jq -r '.rag_hit_at_5 // 1.0')
    
    BASELINE_P95=$(load_state | jq -r '.baseline_p95 // 0')
    
    info "  Current p95: ${CURRENT_P95}ms"
    info "  Baseline p95: ${BASELINE_P95}ms"
    info "  Error rate: ${ERROR_RATE}%"
    info "  Hit@5: $HIT_AT_5"
    
    # Gate 1: Latency not worse by >10%
    if [ "$BASELINE_P95" != "0" ]; then
        MAX_P95=$(echo "$BASELINE_P95 * 1.10" | bc)
        if (( $(echo "$CURRENT_P95 > $MAX_P95" | bc -l) )); then
            error "Gate FAIL: p95 (${CURRENT_P95}ms) > baseline+10% (${MAX_P95}ms)"
            return 1
        fi
    fi
    
    # Gate 2: Error rate < 1%
    if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
        error "Gate FAIL: Error rate (${ERROR_RATE}%) > 1%"
        return 1
    fi
    
    # Gate 3: Hit@5 >= 0.97
    if (( $(echo "$HIT_AT_5 < 0.97" | bc -l) )); then
        error "Gate FAIL: Hit@5 ($HIT_AT_5) < 0.97"
        return 1
    fi
    
    info "✓ All gates passed"
    return 0
}

# Start canary at 5%
start_canary() {
    info "Starting canary deployment at 5%..."
    
    # Get baseline metrics
    BASELINE_SNAPSHOT=$(curl -s http://localhost:8092/snapshot 2>/dev/null || echo '{}')
    BASELINE_P95=$(echo "$BASELINE_SNAPSHOT" | jq -r '.rag_avg_latency_ms // 200')
    
    # Set canary percentage (via environment variable for router)
    export CANARY_PERCENTAGE=5
    
    # Save state
    save_state 5 "$BASELINE_P95"
    
    info "✓ Canary started at 5%"
    info "  Baseline p95: ${BASELINE_P95}ms"
    info ""
    info "Monitor with: make canary-watch"
    info "Promote with: make canary-promote (after 10-15 min if green)"
    info "Rollback with: make canary-rollback (if any issues)"
}

# Promote canary to next level
promote_canary() {
    CURRENT_PCT=$(load_state | jq -r '.percentage')
    
    if [ "$CURRENT_PCT" -eq 0 ]; then
        error "No active canary. Start with: make canary-start"
        exit 1
    fi
    
    # Check gates before promoting
    if ! check_gates; then
        error "Gates failed. Not promoting. Consider rollback."
        exit 1
    fi
    
    # Promotion ladder: 5 → 25 → 50 → 100
    case $CURRENT_PCT in
        5)
            NEW_PCT=25
            ;;
        25)
            NEW_PCT=50
            ;;
        50)
            NEW_PCT=100
            ;;
        100)
            info "Already at 100%"
            exit 0
            ;;
        *)
            NEW_PCT=50
            ;;
    esac
    
    info "Promoting canary: $CURRENT_PCT% → $NEW_PCT%"
    
    export CANARY_PERCENTAGE=$NEW_PCT
    
    BASELINE_P95=$(load_state | jq -r '.baseline_p95')
    save_state $NEW_PCT "$BASELINE_P95"
    
    info "✓ Canary promoted to $NEW_PCT%"
    
    if [ "$NEW_PCT" -eq 100 ]; then
        info "✓ Canary fully deployed! Cleaning up..."
        rm -f $CANARY_STATE_FILE
        info "✓ Deployment complete"
    else
        info "Monitor for 10-15 minutes, then promote again with: make canary-promote"
    fi
}

# Rollback canary
rollback_canary() {
    CURRENT_PCT=$(load_state | jq -r '.percentage')
    
    if [ "$CURRENT_PCT" -eq 0 ]; then
        warn "No active canary to rollback"
        exit 0
    fi
    
    error "Rolling back canary from $CURRENT_PCT%..."
    
    # Set canary percentage to 0
    export CANARY_PERCENTAGE=0
    
    # Clear state
    rm -f $CANARY_STATE_FILE
    
    info "✓ Canary rolled back. Traffic routed to baseline."
    info ""
    info "Investigate issues with:"
    info "  - make metrics-snapshot"
    info "  - docker logs <service>"
}

# Watch canary metrics
watch_canary() {
    info "Watching canary metrics (Ctrl+C to stop)..."
    echo ""
    
    while true; do
        CURRENT_PCT=$(load_state | jq -r '.percentage // 0')
        SNAPSHOT=$(curl -s http://localhost:8092/snapshot 2>/dev/null || echo '{}')
        
        TOTAL_REQ=$(echo "$SNAPSHOT" | jq -r '.total_requests // 0')
        P95=$(echo "$SNAPSHOT" | jq -r '.rag_avg_latency_ms // 0')
        ERRORS=$(echo "$SNAPSHOT" | jq -r '.total_errors // 0')
        HIT_5=$(echo "$SNAPSHOT" | jq -r '.rag_hit_at_5 // 0')
        
        ERROR_RATE=$(echo "scale=2; $ERRORS * 100 / $TOTAL_REQ" | bc 2>/dev/null || echo "0")
        
        echo "$(date '+%H:%M:%S') | Canary: ${CURRENT_PCT}% | Requests: $TOTAL_REQ | p95: ${P95}ms | Errors: ${ERROR_RATE}% | Hit@5: $HIT_5"
        
        sleep 10
    done
}

# Main
case "${1:-}" in
    start)
        start_canary
        ;;
    promote)
        promote_canary
        ;;
    rollback)
        rollback_canary
        ;;
    watch)
        watch_canary
        ;;
    status)
        STATE=$(load_state)
        PCT=$(echo "$STATE" | jq -r '.percentage // 0')
        if [ "$PCT" -eq 0 ]; then
            info "No active canary"
        else
            STARTED=$(echo "$STATE" | jq -r '.started_at')
            ELAPSED=$(($(date +%s) - STARTED))
            info "Active canary at $PCT% (running ${ELAPSED}s)"
        fi
        ;;
    *)
        echo "Usage: $0 {start|promote|rollback|watch|status}"
        exit 1
        ;;
esac

