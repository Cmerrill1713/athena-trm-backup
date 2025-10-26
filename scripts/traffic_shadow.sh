#!/bin/bash
# Shadow traffic mirroring with drift detection
# Mirrors production traffic to shadow stack for validation

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
SHADOW_LOG="$LOG_DIR/shadow_traffic.log"
DRIFT_LOG="$LOG_DIR/drift_analysis.log"

# Configuration
SHADOW_PERCENTAGE=${1:-5}  # Default 5% mirror
SHADOW_AGI_PORT=${SHADOW_AGI_PORT:-8001}  # Shadow AGI port
PROD_AGI_PORT=${PROD_AGI_PORT:-8000}     # Production AGI port

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting shadow traffic mirroring at ${SHADOW_PERCENTAGE}%" >> "$SHADOW_LOG"

cd "$SCRIPT_DIR"

# Start shadow stack
start_shadow_stack() {
    echo "🚀 Starting shadow stack on port $SHADOW_AGI_PORT..."
    
    # Start shadow AGI with dry-run flags
    AGI_SERVICE_PORT=$SHADOW_AGI_PORT \
    DRY_RUN=true \
    SHADOW_MODE=true \
    python3 -m uvicorn agi_core.agi_service:app \
        --host 0.0.0.0 \
        --port $SHADOW_AGI_PORT \
        --timeout-keep-alive 300 \
        --log-level info &
    
    SHADOW_AGI_PID=$!
    echo $SHADOW_AGI_PID > /tmp/shadow_agi.pid
    
    # Wait for shadow to be ready
    for i in {1..30}; do
        if curl -sf "http://localhost:$SHADOW_AGI_PORT/health" >/dev/null 2>&1; then
            echo "✅ Shadow stack ready" >> "$SHADOW_LOG"
            return 0
        fi
        sleep 2
    done
    
    echo "health" >> "$SHADOW_LOG"
    return 1
}

# Stop shadow stack
stop_shadow_stack() {
    echo "🛑 Stopping shadow stack..."
    if [ -f /tmp/shadow_agi.pid ]; then
        kill $(cat /tmp/shadow_agi.pid) 2>/dev/null || true
        rm -f /tmp/shadow_agi.pid
    fi
    echo "✅ Shadow stack stopped" >> "$SHADOW_LOG"
}

# Mirror traffic and analyze drift
mirror_traffic() {
    local duration_minutes=${1:-60}
    local end_time=$(($(date +%s) + duration_minutes * 60))
    
    echo "📊 Mirroring traffic for $duration_minutes minutes..." >> "$SHADOW_LOG"
    
    local request_count=0
    local drift_count=0
    
    while [ $(date +%s) -lt $end_time ]; do
        # Sample requests to mirror (simplified - in real implementation, 
        # this would intercept actual production traffic)
        
        # Generate test request
        local test_request='{
            "objective": "test shadow mirroring",
            "context": {},
            "tools": [],
            "max_steps": 2,
            "flags": {"adaptive_trm": true}
        }'
        
        # Send to production
        local prod_response=$(curl -sS -X POST "http://localhost:$PROD_AGI_PORT/api/execute" \
            -H 'Content-Type: application/json' \
            -d "$test_request" 2>/dev/null || echo '{"error":"prod_failed"}')
        
        # Send to shadow (drop response)
        local shadow_response=$(curl -sS -X POST "http://localhost:$SHADOW_AGI_PORT/api/execute" \
            -H 'Content-Type: application/json' \
            -d "$test_request" 2>/dev/null || echo '{"error":"shadow_failed"}')
        
        # Analyze drift
        local prod_status=$(echo "$prod_response" | jq -r '.status // "error"' 2>/dev/null)
        local shadow_status=$(echo "$shadow_response" | jq -r '.status // "error"' 2>/dev/null)
        
        if [ "$prod_status" != "$shadow_status" ]; then
            drift_count=$((drift_count + 1))
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Drift detected: prod=$prod_status, shadow=$shadow_status" >> "$DRIFT_LOG"
        fi
        
        request_count=$((request_count + 1))
        
        # Log progress every 10 requests
        if [ $((request_count % 10)) -eq 0 ]; then
            local drift_rate=$((drift_count * 100 / request_count))
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Requests: $request_count, Drift: $drift_count (${drift_rate}%)" >> "$SHADOW_LOG"
        fi
        
        sleep 5
    done
    
    # Final drift analysis
    local final_drift_rate=$((drift_count * 100 / request_count))
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Final drift rate: ${final_drift_rate}% ($drift_count/$request_count)" >> "$SHADOW_LOG"
    
    if [ $final_drift_rate -gt 10 ]; then
        echo "❌ High drift rate detected: ${final_drift_rate}%" >> "$SHADOW_LOG"
        return 1
    else
        echo "✅ Drift rate acceptable: ${final_drift_rate}%" >> "$SHADOW_LOG"
        return 0
    fi
}

# Main execution
case "${2:-start}" in
    "start")
        start_shadow_stack
        mirror_traffic "${3:-60}"  # Default 60 minutes
        stop_shadow_stack
        ;;
    "stop")
        stop_shadow_stack
        ;;
    "stats")
        echo "📊 Shadow traffic statistics:"
        echo "=== Recent Shadow Logs ==="
        tail -20 "$SHADOW_LOG" 2>/dev/null || echo "No shadow logs yet"
        echo ""
        echo "=== Drift Analysis ==="
        tail -10 "$DRIFT_LOG" 2>/dev/null || echo "No drift detected"
        ;;
    *)
        echo "Usage: $0 <percentage> [start|stop|stats] [duration_minutes]"
        echo "Example: $0 5 start 60  # Mirror 5% traffic for 60 minutes"
        ;;
esac
