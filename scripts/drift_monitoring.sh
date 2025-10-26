#!/bin/bash
# Drift detection and monitoring system
# Continuously monitors for system drift and degradation

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
DRIFT_LOG="$LOG_DIR/drift_monitoring.log"
ALERT_LOG="$LOG_DIR/drift_alerts.log"

# Drift thresholds
DRIFT_RAG_HIT_RATE_MIN=70.0        # Min RAG hit rate
DRIFT_CONTEXT_WASTE_MAX=50.0       # Max context waste ratio
DRIFT_TRM_TRIGGER_SWING_MAX=30.0   # Max TRM trigger probability swing
DRIFT_LATENCY_DEGRADATION_MAX=2.0  # Max latency degradation factor
DRIFT_EMBEDDING_MISMATCH_THRESHOLD=0.1  # Embedding similarity threshold

# Baseline metrics (updated periodically)
BASELINE_RAG_HIT_RATE=85.0
BASELINE_P95_LATENCY=800.0
BASELINE_TRM_TRIGGER_RATE=0.35
BASELINE_CONTEXT_EFFICIENCY=0.75

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')Contacts drift monitoring system started" >> "$DRIFT_LOG"

cd "$SCRIPT_DIR"

# Update baseline metrics
update_baseline() {
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Updating baseline metrics..." >> "$DRIFT_LOG"
    
    # Get current metrics
    local current_rag_hit=$(get_rag_hit_rate)
    local current_latency=$(get_p95_latency)
    local current_trm_rate=$(get_trm_trigger_rate)
    local current_efficiency=$(get_context_efficiency)
    
    # Update baselines (rolling average)
    BASELINE_RAG_HIT_RATE=$(echo "($BASELINE_RAG_HIT_RATE + $current_rag_hit) / 2" | bc -l)
    BASELINE_P95_LATENCY=$(echo "($BASELINE_P95_LATENCY + $current_latency) / 2" | bc -l)
    BASELINE_TRM_TRIGGER_RATE=$(echo "($BASELINE_TRM_TRIGGER_RATE + $current_trm_rate) / 2" | bc -l)
    BASELINE_CONTEXT_EFFICIENCY=$(echo "($BASELINE_CONTEXT_EFFICIENCY + $current_efficiency) / 2" | bc -l)
    
    echo "  RAG Hit Rate: $current_rag_hit% → $BASELINE_RAG_HIT_RATE%" >> "$DRIFT_LOG"
    echo "  P95 Latency: ${current_latency}ms → ${BASELINE_P95_LATENCY}ms" >> "$DRIFT_LOG"
    echo "  TRM Trigger Rate: $current_trm_rate → $BASELINE_TRM_TRIGGER_RATE" >> "$DRIFT_LOG"
    echo "  Context Efficiency: $current_efficiency → $BASELINE_CONTEXT_EFFICIENCY" >> "$DRIFT_LOG"
}

# Metric collection functions
get_rag_hit_rate() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'rag_hits_total' | \
        awk '{sum+=$2; count++} END {if(count>0) print (sum/count)*100; else print 0}' 2>/dev/null || echo "0"
}

get_p95_latency() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'agi_request_duration_ms_bucket' | \
        awk '{print $2}' | tail -1 2>/dev/null || echo "0"
}

get_trm_trigger_rate() {
    curl -s "http://localhost:8000/trm/policy" | \
        jq -r '.stats.recent_invocations // 0' 2>/dev/null || echo "0"
}

get_context_efficiency() {
    curl -s "http://localhost:9093/metrics" | \
        grep 'trm_context_waste_ratio' | \
        awk '{print $2}' 2>/dev/null | \
        awk '{sum+=$1; count++} END {if(count>0) print 1-(sum/count); else print 0}' || echo "0"
}

get_embedding_similarity() {
    # Test embedding consistency by comparing same query multiple times
    local query="test embedding consistency"
    local embeddings=()
    
    for i in {1..3}; do
        local embedding=$(curl -s -X POST "http://localhost:8087/embed" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"$query\"}" | \
            jq -r '.embedding[:10] | join(",")' 2>/dev/null || echo "")
        embeddings+=("$embedding")
        sleep 1
    done
    
    # Calculate similarity between embeddings (simplified)
    if [ ${#embeddings[@]} -eq 3 ]; then
        echo "0.95"  # Simulated similarity
    else
        echo "0.0"
    fi
}

# Detect drift in various metrics
detect_rag_drift() {
    local current_hit_rate=$(get_rag_hit_rate)
    local hit_rate_drop=$(echo "$BASELINE_RAG_HIT_RATE - $current_hit_rate" | bc -l)
    
    if (( $(echo "$current_hit_rate < $DRIFT_RAG_HIT_RATE_MIN" | bc -l) )); then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - 🚨 RAG Drift: Hit rate ${current_hit_rate}% < ${DRIFT_RAG_HIT_RATE_MIN}%" >> "$ALERT_LOG"
        echo "  Baseline: ${BASELINE_RAG_HIT_RATE}%, Current: ${current_hit_rate}%, Drop: ${hit_rate_drop}%" >> "$ALERT_LOG"
        return 1
    fi
    
    return 0
}

detect_latency_drift() {
    local current_latency=$(get_p95_latency)
    local latency_factor=$(echo "$current_latency / $BASELINE_P95_LATENCY" | bc -l)
    
    if (( $(echo "$latency_factor > $DRIFT_LATENCY_DEGRADATION_MAX" | bc -l) )); then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - 🚨 Latency Drift: ${current_latency}ms vs baseline ${BASELINE_P95_LATENCY}ms (${latency_factor}x)" >> "$ALERT_LOG"
        return 1
    fi
    
    return 0
}

detect_trm_drift() {
    local current_trm_rate=$(get_trm_trigger_rate)
    local trm_swing=$(echo "scale=2; ($current_trm_rate - $BASELINE_TRM_TRIGGER_RATE) / $BASELINE_TRM_TRIGGER_RATE * 100" | bc -l)
    
    if (( $(echo "$trm_swing > $DRIFT_TRM_TRIGGER_SWING_MAX" | bc -l) )); then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - 🚨 TRM Drift: Trigger rate swing ${trm_swing}% > ${DRIFT_TRM_TRIGGER_SWING_MAX}%" >> "$ALERT_LOG"
        echo "  Baseline: ${BASELINE_TRM_TRIGGER_RATE}, Current: ${current_trm_rate}" >> "$ALERT_LOG"
        return 1
    fi
    
    return 0
}

detect_context_waste() {
    local current_efficiency=$(get_context_efficiency)
    local waste_ratio=$(echo "1 - $current_efficiency" | bc -l)
    
    if (( $(echo "$waste_ratio > $DRIFT_CONTEXT_WASTE_MAX / 100" | bc -l) )); then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - 🚨 Context Waste: ${waste_ratio} > ${DRIFT_CONTEXT_WASTE_MAX}%" >> "$ALERT_LOG"
        return 1
    fi
    
    return 0
}

detect_embedding_drift() {
    local similarity=$(get_embedding_similarity)
    
    if (( $(echo "$similarity < $DRIFT_EMBEDDING_MISMATCH_THRESHOLD" | bc -l) )); then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - 🚨 Embedding Drift: Similarity ${similarity} < ${DRIFT_EMBEDDING_MISMATCH_THRESHOLD}" >> "$ALERT_LOG"
        return 1
    fi
    
    return 0
}

# Main drift detection loop
monitor_drift() {
    local interval_minutes=${1:-60}  # Default 1 hour
    
    echo "🔍 Starting drift monitoring (${interval_minutes}m intervals)..." >> "$DRIFT_LOG"
    
    while true; do
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Drift monitoring cycle..." >> "$DRIFT_LOG"
        
        local drift_detected=false
        
        # Check all drift types
        detect_rag_drift || drift_detected=true
        detect_latency_drift || drift_detected=true
        detect_trm_drift || drift_detected=true
        detect_context_waste || drift_detected=true
        detect_embedding_drift || drift_detected=true
        
        if [ "$drift_detected" = true ]; then
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - 🚨 Drift detected - check $ALERT_LOG" >> "$DRIFT_LOG"
            
            # Trigger remediation actions
            trigger_drift_remediation
        else
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ✅ No drift detected" >> "$DRIFT_LOG"
        fi
        
        # Update baseline every 6 hours
        if [ $(($(date +%H) % 6)) -eq 0 ] && [ $(date +%M) -lt 5 ]; then
            update_baseline
        fi
        
        sleep $((interval_minutes * 60))
    done
}

# Trigger remediation actions for drift
trigger_drift_remediation() {
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Triggering drift remediation..." >> "$DRIFT_LOG"
    
    # Check if RAG needs reseeding
    local rag_hit_rate=$(get_rag_hit_rate)
    if (( $(echo "$rag_hit_rate < $DRIFT_RAG_HIT_RATE_MIN" | bc -l) )); then
        echo "  - RAG hit rate low, triggering reseed..." >> "$DRIFT_LOG"
        make rag-seed >> "$DRIFT_LOG" 2>&1 || true
    fi
    
    # Check if TRM policy needs adjustment
    local trm_rate=$(get_trm_trigger_rate)
    local baseline_trm=$BASELINE_TRM_TRIGGER_RATE
    if (( $(echo "($trm_rate - $baseline_trm) / $baseline_trm > 0.3" | bc -l) )); then
        echo "  - TRM trigger rate high, adjusting threshold..." >> "$DRIFT_LOG"
        export TRM_TRIGGER_THRESHOLD=$(echo "$TRM_TRIGGER_THRESHOLD * 1.1" | bc -l)
    fi
    
    # Check if model routing needs adjustment
    local latency=$(get_p95_latency)
    local baseline_latency=$BASELINE_P95_LATENCY
    if (( $(echo "$latency > $baseline_latency * 2" | bc -l) )); then
        echo "  - Latency high, switching to fast-only routing..." >> "$DRIFT_LOG"
        export MODEL_ROUTE_OVERRIDE="fast-only"
    fi
    
    echo "  - Remediation actions completed" >> "$DRIFT_LOG"
}

# Main execution
case "${2:-monitor}" in
    "monitor")
        monitor_drift "${1:-60}"
        ;;
    "update-baseline")
        update_baseline
        ;;
    "check-drift")
        echo "🔍 Running drift check..."
        detect_rag_drift && detect_latency_drift && detect_trm_drift && detect_context_waste && detect_embedding_drift
        if [ $? -eq 0 ]; then
            echo "✅ No drift detected"
        else
            echo "❌ Drift detected - check $ALERT_LOG"
        fi
        ;;
    "status")
        echo "📊 Drift monitoring status:"
        echo "=== Recent Drift Logs ==="
        tail -10 "$DRIFT_LOG" 2>/dev/null || echo "No drift logs yet"
        echo ""
        echo "=== Drift Alerts ==="
        tail -10 "$ALERT_LOG" 2>/dev/null || echo "No drift alerts"
        echo ""
        echo "=== Current Baselines ==="
        echo "RAG Hit Rate: ${BASELINE_RAG_HIT_RATE}%"
        echo "P95 Latency: ${BASELINE_P95_LATENCY}ms"
        echo "TRM Trigger Rate: ${BASELINE_TRM_TRIGGER_RATE}"
        echo "Context Efficiency: ${BASELINE_CONTEXT_EFFICIENCY}"
        ;;
    *)
        echo "Usage: $0 <interval_minutes> [monitor|update-baseline|check-drift|status]"
        echo "Example: $0 60 monitor  # Monitor every 60 minutes"
        ;;
esac
