#!/bin/bash
# Complete real-world validation pipeline
# Safe production validation with zero user impact

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
VALIDATION_LOG="$LOG_DIR/real_world_validation.log"

# Configuration
SHADOW_DURATION_HOURS=${1:-12}      # Default 12h shadow
CANARY_START_PERCENT=${2:-1}        # Default 1% canary start
CANARY_EXPAND_RATE=${3:-5}          # Default expand by 5%

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting real-world validation pipeline" >> "$VALIDATION_LOG"

cd "$SCRIPT_DIR"

# Phase 0: Preconditions
run_phase0_preconditions() {
    echo "🏷️ Phase 0: Setting up preconditions..." >> "$VALIDATION_LOG"
    
    if ./scripts/phase0_preconditions.sh run >> "$VALIDATION_LOG" 2>&1; then
        echo "✅ Phase 0 completed: Preconditions ready" >> "$VALIDATION_LOG"
        return 0
    else
        echo "❌ Phase 0 failed: Preconditions not ready" >> "$VALIDATION_LOG"
        return 1
    fi
}

# Phase 1: Shadow traffic validation
run_phase1_shadow() {
    echo "🔍 Phase 1: Shadow traffic validation (${SHADOW_DURATION_HOURS}h)..." >> "$VALIDATION_LOG"
    
    # Start shadow traffic
    echo "  - Starting shadow traffic mirroring..." >> "$VALIDATION_LOG"
    make traffic-shadow-start >> "$VALIDATION_LOG" 2>&1
    
    # Run shadow validation gates
    echo "  - Running shadow validation gates..." >> "$VALIDATION_LOG"
    local shadow_duration_minutes=$((SHADOW_DURATION_HOURS * 60))
    
    if ./scripts/shadow_validation_gates.sh validate $shadow_duration_minutes >> "$VALIDATION_LOG" 2>&1; then
        echo "✅ Phase 1 completed: Shadow validation passed" >> "$VALIDATION_LOG"
        
        # Stop shadow traffic
        make traffic-shadow-stop >> "$VALIDATION_LOG" 2>&1
        return 0
    else
        echo "❌ Phase 1 failed: Shadow validation failed" >> "$VALIDATION_LOG"
        
        # Stop shadow traffic and rollback
        make traffic-shadow-stop >> "$VALIDATION_LOG" 2>&1
        make prod-rollout-rollback >> "$VALIDATION_LOG" 2>&1
        return 1
    fi
}

# Phase 2: Canary deployment
run_phase2_canary() {
    echo "🚦 Phase 2: Canary deployment (${CANARY_START_PERCENT}%)..." >> "$VALIDATION_LOG"
    
    # Deploy initial canary
    echo "  - Deploying ${CANARY_START_PERCENT}% canary..." >> "$VALIDATION_LOG"
    make canary-deploy >> "$VALIDATION_LOG" 2>&1
    
    # Monitor canary for 2 hours
    echo "  - Monitoring canary for 2 hours..." >> "$VALIDATION_LOG"
    local canary_duration_minutes=120
    
    # Check canary promotion gates
    local canary_percent=$CANARY_START_PERCENT
    local expand_percent=$CANARY_EXPAND_RATE
    
    while [ $canary_percent -lt 10 ]; do
        echo "  - Checking canary promotion gates at ${canary_percent}%..." >> "$VALIDATION_LOG"
        
        # Check SLOs for promotion
        local error_rate=$(curl -s "http://localhost:9093/metrics" | grep 'agi_requests_total{outcome="error"}' | awk '{print $2}' 2>/dev/null || echo "0")
        local p95_latency=$(curl -s "http://localhost:9093/metrics" | grep 'agi_request_duration_ms_bucket' | awk '{print $2}' | tail -1 2>/dev/null || echo "0")
        
        # Promotion gates
        if (( $(echo "$error_rate > 0.5" | bc -l) )); then
            echo "❌ Canary promotion failed: Error rate ${error_rate}% > 0.5%" >> "$VALIDATION_LOG"
            make canary-rollback >> "$VALIDATION_LOG" 2>&1
            return 1
        fi
        
        if (( $(echo "$p95_latency > 2000" | bc -l) )); then
            echo "❌ Canary promotion failed: P95 latency ${p95_latency}ms > 2000ms" >> "$VALIDATION_LOG"
            make canary-rollback >> "$VALIDATION_LOG" 2>&1
            return 1
        fi
        
        echo "✅ Canary promotion gates passed at ${canary_percent}%" >> "$VALIDATION_LOG"
        
        # Expand canary
        canary_percent=$((canary_percent + expand_percent))
        if [ $canary_percent -gt 10 ]; then
            canary_percent=10
        fi
        
        echo "  - Expanding canary to ${canary_percent}%..." >> "$VALIDATION_LOG"
        ./scripts/canary_by_risk.sh $canary_percent 60 low deploy >> "$VALIDATION_LOG" 2>&1
        
        sleep 60  # Monitor for 1 hour at each percentage
    done
    
    echo "✅ Phase 2 completed: Canary deployment successful" >> "$VALIDATION_LOG"
    return 0
}

# Phase 3: Controlled chaos testing
run_phase3_chaos() {
    echo "💥 Phase 3: Controlled chaos testing..." >> "$VALIDATION_LOG"
    
    # Run chaos tests on canary traffic only
    echo "  - Running chaos tests on canary traffic..." >> "$VALIDATION_LOG"
    
    if make stage-chaos-test >> "$VALIDATION_LOG" 2>&1; then
        echo "✅ Phase 3 completed: Chaos testing passed" >> "$VALIDATION_LOG"
        return 0
    else
        echo "❌ Phase 3 failed: Chaos testing failed" >> "$VALIDATION_LOG"
        make canary-rollback >> "$VALIDATION_LOG" 2>&1
        return 1
    fi
}

# Phase 4: Human spot checks
run_phase4_human_validation() {
    echo "👥 Phase 4: Human spot checks..." >> "$VALIDATION_LOG"
    
    # Run human validation
    echo "  - Running human validation spot checks..." >> "$VALIDATION_LOG"
    if make human-validation >> "$VALIDATION_LOG" 2>&1; then
        echo "✅ Phase 4 completed: Human validation passed" >> "$VALIDATION_LOG"
        return 0
    else
        echo "❌ Phase 4 failed: Human validation failed" >> "$VALIDATION_LOG"
        make canary-rollback >> "$VALIDATION_LOG" 2>&1
        return 1
    fi
}

# Phase 5: Safe expansion
run_phase5_expansion() {
    echo "📈 Phase 5: Safe expansion..." >> "$VALIDATION_LOG"
    
    # Expand canary to full production
    echo "  - Expanding canary to full production..." >> "$VALIDATION_LOG"
    
    if make prod-rollout >> "$VALIDATION_LOG" 2>&1; then
        echo "✅ Phase 5 completed: Safe expansion successful" >> "$VALIDATION_LOG"
        return 0
    else
        echo "❌ Phase 5 failed: Safe expansion failed" >> "$VALIDATION_LOG"
        make prod-rollout-rollback >> "$VALIDATION_LOG" 2>&1
        return 1
    fi
}

# Main validation pipeline
main() {
    echo "🚀 Starting real-world validation pipeline..." >> "$VALIDATION_LOG"
    
    # Phase 0: Preconditions
    if ! run_phase0_preconditions; then
        echo "❌ Validation pipeline failed at Phase 0" >> "$VALIDATION_LOG"
        exit 1
    fi
    
    # Phase 1: Shadow traffic
    if ! run_phase1_shadow; then
        echo "❌ Validation pipeline failed at Phase 1" >> "$VALIDATION_LOG"
        exit 1
    fi
    
    # Phase 2: Canary deployment
    if ! run_phase2_canary; then
        echo "❌ Validation pipeline failed at Phase 2" >> "$VALIDATION_LOG"
        exit 1
    fi
    
    # Phase 3: Controlled chaos
    if ! run_phase3_chaos; then
        echo "❌ Validation pipeline failed at Phase 3" >> "$VALIDATION_LOG"
        exit 1
    fi
    
    # Phase 4: Human validation
    if ! run_phase4_human_validation; then
        echo "❌ Validation pipeline failed at Phase 4" >> "$VALIDATION_LOG"
        exit 1
    fi
    
    # Phase 5: Safe expansion
    if ! run_phase5_expansion; then
        echo "❌ Validation pipeline failed at Phase 5" >> "$VALIDATION_LOG"
        exit 1
    fi
    
    echo "🎉 Real-world validation pipeline completed successfully!" >> "$VALIDATION_LOG"
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Validation pipeline SUCCESS" >> "$VALIDATION_LOG"
}

# Handle script arguments
case "${4:-run}" in
    "run")
        main
        ;;
    "rollback")
        echo "🔄 Rolling back real-world validation..."
        make canary-rollback >> "$VALIDATION_LOG" 2>&1
        make prod-rollout-rollback >> "$VALIDATION_LOG" 2>&1
        echo "✅ Rollback completed"
        ;;
    "status")
        echo "📊 Real-world validation status:"
        echo "=== Recent Validation Logs ==="
        tail -20 "$VALIDATION_LOG" 2>/dev/null || echo "No validation logs yet"
        echo ""
        echo "=== Current System Status ==="
        make ops-status
        echo ""
        echo "=== Shadow Traffic Status ==="
        make traffic-shadow-stats
        echo ""
        echo "=== Canary Status ==="
        make canary-status
        ;;
    *)
        echo "Usage: $0 <shadow_hours> <canary_start_%> <expand_rate> [run|rollback|status]"
        echo "Example: $0 12 1 5 run  # 12h shadow, 1% canary start, expand by 5%"
        ;;
esac
