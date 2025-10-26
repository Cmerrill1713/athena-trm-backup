#!/bin/bash
# Risk-based canary deployment with kill switches
# Gradual rollout with automated rollback on SLO breaches

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
CANARY_LOG="$LOG_DIR/canary_deployment.log"
SLO_LOG="$LOG_DIR/slo_monitoring.log"

# Configuration
CANARY_PERCENTAGE=${1:-5}
DURATION_MINUTES=${2:-60}
RISK_LEVEL=${3:-"low"}  # low, medium, high

# SLO thresholds
SLO_ERROR_RATE_MAX=1.0      # 1% max error rate
SLO_P95_LATENCY_MAX=2000    # 2s max P95 latency
SLO_GOLDEN_SCORE_MIN=80     # 80% min golden score
SLO_AVAILABILITY_MIN=99.5   # 99.5% min availability

# Kill switches
KILL_SWITCH_TRM_THRESHOLD=1.0
KILL_SWITCH_MODEL_ROUTE="safe-mini"
KILL_SWITCH_GLOBAL_ROLLBACK=false

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')... Risk level: $RISK_LEVEL, Percentage: ${CANARY_PERCENTAGE}%, Duration: ${DURATION_MINUTES}m" >> "$CANARY_LOG"

cd "$SCRIPT_DIR"

# Risk-based traffic segmentation
setup_risk_segmentation() {
    case "$RISK_LEVEL" in
        "low")
            echo "🟢 Low-risk canary: Internal traffic only"
            export CANARY_USER_FILTER="internal_team=true"
            export CANARY_TENANT_FILTER="beta_customer=false"
            ;;
        "medium")
            echo "🟡 Medium-risk canary: Beta customers"
            export CANARY_USER_FILTER="beta_customer=true"
            export CANARY_TENANT_FILTER="production=false"
            ;;
        "high")
            echo "🔴 High-risk canary: Production traffic"
            export CANARY_USER_FILTER="production=true"
            export CANARY_TENANT_FILTER="critical=false"
            ;;
    esac
}

# Monitor SLOs during canary
monitor_slos() {
    local start_time=$(date +%s)
    local end_time=$((start_time + DURATION_MINUTES * 60))
    
    echo "📊 Monitoring SLOs for $DURATION_MINUTES minutes..." >> "$SLO_LOG"
    
    while [ $(date +%s) -lt $end_time ]; do
        # Check error rate
        local error_rate=$(curl -s "http://localhost:9093/metrics" | \
            grep 'agi_requests_total{outcome="error"}' | \
            awk '{print $2}' || echo "0")
        
        # Check P95 latency
        local p95_latency=$(curl -s "http://localhost:9093/metrics" | \
            grep 'agi_request_duration_ms_bucket' | \
            awk '{print $2}' | tail -1 || echo "0")
        
        # Check golden score
        local golden_score=$(make rag-golden 2>/dev/null | \
            grep "Passed" | awk '{print $2}' | cut -d'/' -f1 || echo "0")
        
        # Check availability
        local availability=$(curl -s "http://localhost:8000/health" | \
            jq -r '.status' 2>/dev/null || echo "error")
        
        # Log SLO status
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Error: ${error_rate}%, P95: ${p95_latency}ms, Golden: ${golden_score}%, Available: $availability" >> "$SLO_LOG"
        
        # Check for SLO breaches
        local breach_detected=false
        
        if (( $(echo "$error_rate > $SLO_ERROR_RATE_MAX" | bc -l) )); then
            echo "❌ SLO BREACH: Error rate ${error_rate}% > ${SLO_ERROR_RATE_MAX}%" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if (( $(echo "$p95_latency > $SLO_P95_LATENCY_MAX" | bc -l) )); then
            echo "❌ SLO BREACH: P95 latency ${p95_latency}ms > ${SLO_P95_LATENCY_MAX}ms" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if (( golden_score < SLO_GOLDEN_SCORE_MIN )); then
            echo "❌ SLO BREACH: Golden score ${golden_score}% < ${SLO_GOLDEN_SCORE_MIN}%" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if [ "$availability" != "ok" ]; then
            echo "❌ SLO BREACH: Availability not OK" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        # Trigger rollback on breach
        if [ "$breach_detected" = true ]; then
            echo "🚨 SLO breach detected - triggering rollback" >> "$CANARY_LOG"
            rollback_canary
            exit 1
        fi
        
        sleep 30
    done
    
    echo "✅ Canary period completed without SLO breaches" >> "$CANARY_LOG"
}

# Rollback mechanisms
rollback_canary() {
    echo "🔄 Rolling back canary deployment..." >> "$CANARY_LOG"
    
    case "${4:-soft}" in
        "soft")
            echo "🔧 Soft rollback: Disabling TRM and routing to safe model"
            export TRM_TRIGGER_THRESHOLD=$KILL_SWITCH_TRM_THRESHOLD
            export MODEL_ROUTE_OVERRIDE=$KILL_SWITCH_MODEL_ROUTE
            make stack-restart
            ;;
        "hard")
            echo "🚨 Hard rollback: Full production rollback"
            make prod-rollback
            ;;
    esac
    
    echo "✅ Rollback completed" >> "$CANARY_LOG"
}

# Deploy canary
deploy_canary() {
    echo "🚀 Deploying canary at ${CANARY_PERCENTAGE}% traffic..." >> "$CANARY_LOG"
    
    # Set canary flags
    export CANARY_PERCENTAGE=$CANARY_PERCENTAGE
    export CANARY_ENABLED=true
    
    # Start canary traffic
    ./scripts/ab_test_trm.sh $((DURATION_MINUTES * 60)) $((CANARY_PERCENTAGE / 100.0)) &
    CANARY_PID=$!
    
    echo "Canary PID: $CANARY_PID" >> "$CANARY_LOG"
    
    # Monitor SLOs
    monitor_slos
    
    # Stop canary traffic
    kill $CANARY_PID 2>/dev/null || true
    
    echo "✅ Canary deployment completed successfully" >> "$CANARY_LOG"
}

# Main execution
case "${4:-deploy}" in
    "deploy")
        setup_risk_segmentation
        deploy_canary
        ;;
    "rollback")
        rollback_canary "${5:-soft}"
        ;;
    "status")
        echo "📊 Canary deployment status:"
        echo "=== Recent Canary Logs ==="
        tail -20 "$CANARY_LOG" 2>/dev/null || echo "No canary logs yet"
        echo ""
        echo "=== SLO Monitoring ==="
        tail -10 "$SLO_LOG" 2>/dev/null || echo "No SLO logs yet"
        ;;
    *)
        echo "Usage: $0 <percentage> <duration_minutes> <risk_level> [deploy|rollback|status] [rollback_type]"
        echo "Risk levels: low, medium, high"
        echo "Rollback types: soft, hard"
        echo "Example: $0 5 60 low deploy"
        ;;
esac
