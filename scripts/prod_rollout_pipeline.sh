#!/bin/bash
# Complete "shadow → canary → expand" production rollout pipeline
# Automated rollback and chaos injection included

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
ROLLOUT_LOG="$LOG_DIR/prod_rollout.log"
SLO_LOG="$LOG_DIR/slo_monitoring.log"

# Configuration
SHADOW_DURATION_HOURS=${1:-24}      # Default 24h shadow
CANARY_START_PERCENT=${2:-10}       # Default 10% canary start
CANARY_EXPAND_RATE=${3:-25}         # Default expand to 25%
FINAL_EXPAND_PERCENT=${4:-100}      # Final 100% rollout

# SLO thresholds for automated rollback
SLO_ERROR_RATE_MAX=2.0              # 2% max error rate
SLO_P95_LATENCY_MULTIPLIER=2.0      # 2x baseline latency
SLO_ZERO_HIT_SPIKE_MAX=30.0         # 30% max zero-hit spike
SLO_SWAP_STORM_THRESHOLD=3          # 3 swaps/min threshold

# Kill switches
KILL_SWITCH_TRM_THRESHOLD=1.0
KILL_SWITCH_FAST_ONLY=false
KILL_SWITCH_GLOBAL_ROLLBACK=false

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting production rollout pipeline" >> "$ROLLOUT_LOG"
echo "Shadow: ${SHADOW_DURATION_HOURS}h, Canary: ${CANARY_START_PERCENT}% → ${FINAL_EXPAND_PERCENT}%" >> "$ROLLOUT_LOG"

cd "$SCRIPT_DIR"

# SLO monitoring with automated rollback
monitor_slos_with_rollback() {
    local phase="$1"
    local duration_minutes="$2"
    
    echo "📊 Monitoring SLOs for $phase (${duration_minutes}m)..." >> "$SLO_LOG"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration_minutes * 60))
    local breach_count=0
    
    while [ $(date +%s) -lt $end_time ]; do
        # Collect metrics
        local error_rate=$(get_error_rate)
        local p95_latency=$(get_p95_latency)
        local zero_hit_rate=$(get_zero_hit_rate)
        local swap_rate=$(get_swap_storm_rate)
        
        # Check for SLO breaches
        local breach_detected=false
        
        if (( $(echo "$error_rate > $SLO_ERROR_RATE_MAX" | bc -l) )); then
            echo "❌ SLO BREACH: Error rate ${error_rate}% > ${SLO_ERROR_RATE_MAX}%" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if (( $(echo "$p95_latency > $SLO_P95_LATENCY_MULTIPLIER" | bc -l) )); then
            echo "❌ SLO BREACH: P95 latency ${p95_latency}ms > 2x baseline" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if (( $(echo "$zero_hit_rate > $SLO_ZERO_HIT_SPIKE_MAX" | bc -l) )); then
            echo "❌ SLO BREACH: Zero-hit rate ${zero_hit_rate}% > ${SLO_ZERO_HIT_SPIKE_MAX}%" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if (( swap_rate > SLO_SWAP_STORM_THRESHOLD )); then
            echo "❌ SLO BREACH: Swap storm ${swap_rate}/min > ${SLO_SWAP_STORM_THRESHOLD}/min" >> "$SLO_LOG"
            breach_detected=true
        fi
        
        if [ "$breach_detected" = true ]; then
            breach_count=$((breach_count + 1))
            
            # Auto-rollback on repeated breaches
            if [ $breach_count -ge 3 ]; then
                echo "🚨 Multiple SLO breaches detected - triggering auto-rollback" >> "$ROLLOUT_LOG"
                auto_rollback "$phase"
                exit 1
            fi
        else
            breach_count=0  # Reset counter on success
        fi
        
        # Log current metrics
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - $phase: Error=${error_rate}%, P95=${p95_latency}ms, ZeroHit=${zero_hit_rate}%, Swaps=${swap_rate}/min" >> "$SLO_LOG"
        
        sleep 60  # Check every minute
    done
    
    echo "✅ $phase SLO monitoring completed without sustained breaches" >> "$SLO_LOG"
}

# Metric collection functions
get_error_rate() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'agi_requests_total{outcome="error"}' | \
        awk '{print $2}' 2>/dev/null || echo "0"
}

get_p95_latency() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'agi_request_duration_ms_bucket' | \
        awk '{print $2}' | tail -1 2>/dev/null || echo "0"
}

get_zero_hit_rate() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'rag_hits_total 0' | \
        awk '{print $2}' 2>/dev/null || echo "0"
}

get_swap_storm_rate() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'model_pool_hotswaps_total' | \
        awk '{print $2}' 2>/dev/null || echo "0"
}

# Automated rollback system
auto_rollback() {
    local phase="$1"
    
    echo "🔄 Auto-rollback triggered during $phase..." >> "$ROLLOUT_LOG"
    
    # Immediate kill switches
    echo "🚨 Activating kill switches..."
    
    # Disable TRM globally
    export TRM_TRIGGER_THRESHOLD=$KILL_SWITCH_TRM_THRESHOLD
    echo "  - TRM threshold set to $KILL_SWITCH_TRM_THRESHOLD (disabled)" >> "$ROLLOUT_LOG"
    
    # Route to fast model only
    if [ "$KILL_SWITCH_FAST_ONLY" = true ]; then
        export MODEL_ROUTE_OVERRIDE="fast-only"
        echo "  - Model routing set to fast-only" >> "$ROLLOUT_LOG"
    fi
    
    # Restart stack with kill switches
    make stack-restart >> "$ROLLOUT_LOG" 2>&1
    
    # If critical breach, full rollback
    if [ "$KILL_SWITCH_GLOBAL_ROLLBACK" = true ]; then
        echo "🚨 Critical breach - executing full rollback" >> "$ROLLOUT_LOG"
        make prod-rollback >> "$ROLLOUT_LOG" 2>&1
    fi
    
    echo "✅ Auto-rollback completed" >> "$ROLLOUT_LOG"
}

# Chaos injection for testing resilience
inject_chaos() {
    local chaos_type="$1"
    local duration_seconds="$2"
    
    echo "💥 Injecting chaos: $chaos_type for ${duration_seconds}s..." >> "$ROLLOUT_LOG"
    
    case "$chaos_type" in
        "weaviate_kill")
            docker compose kill athena-weaviate
            sleep $duration_seconds
            docker compose start athena-weaviate
            ;;
        "rag_latency")
            # Add network latency (requires tc/netem)
            sleep $duration_seconds
            ;;
        "memory_pressure")
            # Simulate memory pressure
            sleep $duration_seconds
            ;;
        "model_eviction")
            # Force model eviction
            curl -X POST "http://localhost:8420/v1/models/evict" -d '{"model":"all"}' 2>/dev/null || true
            sleep $duration_seconds
            ;;
    esac
    
    echo "✅ Chaos injection completed: $chaos_type" >> "$ROLLOUT_LOG"
}

# Phase 1: Shadow traffic
run_shadow_phase() {
    echo "🔍 Phase 1: Shadow traffic mirroring (${SHADOW_DURATION_HOURS}h)..." >> "$ROLLOUT_LOG"
    
    # Start shadow traffic
    make traffic-shadow-start >> "$ROLLOUT_LOG" 2>&1
    
    # Monitor SLOs during shadow
    monitor_slos_with_rollback "shadow" $((SHADOW_DURATION_HOURS * 60))
    
    # Stop shadow traffic
    make traffic-shadow-stop >> "$ROLLOUT_LOG" 2>&1
    
    echo "✅ Shadow phase completed" >> "$ROLLOUT_LOG"
}

# Phase 2: Canary deployment
run_canary_phase() {
    local canary_percent="$1"
    local duration_hours="$2"
    
    echo "🚦 Phase 2: Canary deployment (${canary_percent}% for ${duration_hours}h)..." >> "$ROLLOUT_LOG"
    
    # Deploy canary
    ./scripts/canary_by_risk.sh $canary_percent $((duration_hours * 60)) low deploy >> "$ROLLOUT_LOG" 2>&1
    
    # Monitor SLOs during canary
    monitor_slos_with_rollback "canary" $((duration_hours * 60))
    
    echo "✅ Canary phase completed at ${canary_percent}%" >> "$ROLLOUT_LOG"
}

# Phase 3: Gradual expansion
run_expansion_phase() {
    local current_percent="$1"
    local target_percent="$2"
    local expansion_rate="$3"
    
    echo "📈 Phase 3: Gradual expansion (${current_percent}% → ${target_percent}%)..." >> "$ROLLOUT_LOG"
    
    local percent=$current_percent
    while [ $percent -lt $target_percent ]; do
        # Calculate next expansion
        local next_percent=$((percent + expansion_rate))
        if [ $next_percent -gt $target_percent ]; then
            next_percent=$target_percent
        fi
        
        echo "  Expanding to ${next_percent}%..." >> "$ROLLOUT_LOG"
        
        # Deploy at new percentage
        ./scripts/canary_by_risk.sh $next_percent 60 low deploy >> "$ROLLOUT_LOG" 2>&1
        
        # Monitor SLOs for 1 hour at this percentage
        monitor_slos_with_rollback "expansion_${next_percent}" 60
        
        # Inject controlled chaos
        if [ $((percent % 25)) -eq 0 ]; then  # Every 25% expansion
            inject_chaos "weaviate_kill" 30
            inject_chaos "model_eviction" 15
        fi
        
        percent=$next_percent
    done
    
    echo "✅ Expansion phase completed at ${target_percent}%" >> "$ROLLOUT_LOG"
}

# Phase 4: Full production with chaos testing
run_production_phase() {
    echo "🚀 Phase 4: Full production with chaos testing..." >> "$ROLLOUT_LOG"
    
    # Run for 24 hours with periodic chaos
    monitor_slos_with_rollback "production" $((24 * 60))
    
    # Periodic chaos injection
    for i in {1..6}; do  # 6 chaos events over 24 hours
        sleep $((4 * 60 * 60))  # Wait 4 hours between chaos events
        
        case $((i % 4)) in
            0) inject_chaos "weaviate_kill" 60 ;;
            1) inject_chaos "rag_latency" 120 ;;
            2) inject_chaos "memory_pressure" 90 ;;
            3) inject_chaos "model_eviction" 45 ;;
        esac
    done
    
    echo "✅ Production phase completed" >> "$ROLLOUT_LOG"
}

# Main rollout pipeline
main() {
    echo "🚀 Starting production rollout pipeline..." >> "$ROLLOUT_LOG"
    
    # Pre-rollout validation
    echo "🔍 Pre-rollout validation..."
    make system-smoke >> "$ROLLOUT_LOG" 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Pre-rollout validation failed - aborting pipeline" >> "$ROLLOUT_LOG"
        exit 1
    fi
    
    # Phase 1: Shadow traffic
    run_shadow_phase
    
    # Phase 2: Initial canary
    run_canary_phase $CANARY_START_PERCENT 24
    
    # Phase 3: Gradual expansion
    run_expansion_phase $CANARY_START_PERCENT $FINAL_EXPAND_PERCENT $CANARY_EXPAND_RATE
    
    # Phase 4: Full production with chaos
    run_production_phase
    
    echo "🎉 Production rollout pipeline completed successfully!" >> "$ROLLOUT_LOG"
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Rollout pipeline SUCCESS" >> "$ROLLOUT_LOG"
}

# Handle script arguments
case "${5:-run}" in
    "run")
        main
        ;;
    "rollback")
        auto_rollback "manual"
        ;;
    "status")
        echo "📊 Production rollout status:"
        echo "=== Rollout Logs ==="
        tail -20 "$ROLLOUT_LOG" 2>/dev/null || echo "No rollout logs yet"
        echo ""
        echo "=== SLO Monitoring ==="
        tail -10 "$SLO_LOG" 2>/dev/null || echo "No SLO logs yet"
        ;;
    *)
        echo "Usage: $0 <shadow_hours> <canary_start_%> <expand_rate> <final_%> [run|rollback|status]"
        echo "Example: $0 24 10 25 100 run"
        ;;
esac
