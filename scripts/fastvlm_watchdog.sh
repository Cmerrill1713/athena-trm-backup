#!/usr/bin/env bash
# FastVLM Watchdog - Monitors and restarts FastVLM if it crashes or hangs
# Run this via LaunchAgent for 24/7 reliability

set -euo pipefail

LOG_FILE="/tmp/fastvlm_watchdog.log"
HEALTH_CHECK_INTERVAL=60  # Check every 60 seconds
MAX_RESTART_ATTEMPTS=3
RESTART_BACKOFF=10  # Seconds between restart attempts

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

check_health() {
    bash "$(dirname "$0")/fastvlm_health.sh" > /dev/null 2>&1
}

start_server() {
    log "Starting FastVLM server..."
    
    cd /Users/christianmerrill/Documents/GitHub/fastvlm
    export FASTVLM_ROOT="$(pwd)/ml-fastvlm"
    export FASTVLM_MODEL="checkpoints/fastvlm_1.5b_stage3"
    export ENV="prod"
    export BUILD_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    
    # Start server in background
    nohup python3 fastvlm_server.py > /tmp/fastvlm_server.log 2>&1 &
    SERVER_PID=$!
    
    log "FastVLM started with PID $SERVER_PID"
    
    # Wait for warmup (30 seconds)
    log "Waiting for warmup..."
    sleep 30
    
    if check_health; then
        log "✅ FastVLM healthy after startup"
        return 0
    else
        log "⚠️ FastVLM failed health check after startup"
        return 1
    fi
}

restart_server() {
    local attempt=$1
    
    log "Restart attempt $attempt/$MAX_RESTART_ATTEMPTS"
    
    # Circuit breaker: prevent restart storms
    WINDOW=600  # 10 min window
    MAX_RESTARTS_IN_WINDOW=3
    TIMESTAMPS_FILE="/tmp/fastvlm_restart_timestamps"
    CIRCUIT_FILE="/tmp/fastvlm_circuit_breaker"
    NOW=$(date +%s)
    
    # Initialize files
    touch "$TIMESTAMPS_FILE"
    
    # Prune old timestamps outside window
    awk -v now="$NOW" -v win="$WINDOW" '{ if (now-$1 < win) print }' "$TIMESTAMPS_FILE" > "$TIMESTAMPS_FILE.tmp" && mv "$TIMESTAMPS_FILE.tmp" "$TIMESTAMPS_FILE"
    
    # Count recent restarts
    RECENT_COUNT=$(wc -l < "$TIMESTAMPS_FILE" | tr -d ' ')
    
    # Check circuit breaker
    if [ "$RECENT_COUNT" -ge "$MAX_RESTARTS_IN_WINDOW" ]; then
        log "🚨 Circuit breaker TRIPPED: $RECENT_COUNT restarts in last ${WINDOW}s"
        log "   Holding off to prevent restart storm"
        
        # Set circuit breaker flag for metrics
        echo "1" > "$CIRCUIT_FILE"
        echo "$NOW" > "/tmp/fastvlm_circuit_opened_at"
        
        # Wait before allowing more restarts
        sleep 600  # 10 minutes
        
        # Reset circuit
        echo "0" > "$CIRCUIT_FILE"
        > "$TIMESTAMPS_FILE"  # Clear history
        
        log "Circuit breaker reset after cooldown"
        return 1
    fi
    
    # Record this restart attempt
    echo "$NOW" >> "$TIMESTAMPS_FILE"
    
    # Kill existing process
    pkill -f fastvlm_server.py || true
    sleep 2
    
    # Wait with exponential backoff
    local wait_time=$((RESTART_BACKOFF * attempt))
    log "Waiting ${wait_time}s before restart..."
    sleep "$wait_time"
    
    if start_server; then
        # Increment restart counter for Prometheus (persists across reboots)
        RESTART_COUNT_FILE="/tmp/fastvlm_watchdog_restarts.count"
        if [ -f "$RESTART_COUNT_FILE" ]; then
            count=$(cat "$RESTART_COUNT_FILE")
            echo $((count + 1)) > "$RESTART_COUNT_FILE"
        else
            echo 1 > "$RESTART_COUNT_FILE"
        fi
        
        # Record timestamp of last successful restart
        echo "$NOW" > "/tmp/fastvlm_last_restart_ts"
        
        log "📊 Total restarts: $(cat $RESTART_COUNT_FILE)"
        log "📊 Recent restarts (${WINDOW}s): $(wc -l < $TIMESTAMPS_FILE | tr -d ' ')"
        
        return 0
    else
        return 1
    fi
}

# Main watchdog loop
log "FastVLM watchdog started"

# Initial startup
if ! pgrep -f fastvlm_server.py > /dev/null; then
    log "Server not running, starting..."
    if ! start_server; then
        log "❌ Initial startup failed"
        exit 1
    fi
fi

# Monitoring loop
consecutive_failures=0
restart_attempts=0

while true; do
    sleep "$HEALTH_CHECK_INTERVAL"
    
    if check_health; then
        # Healthy - reset counters
        if [ $consecutive_failures -gt 0 ]; then
            log "✅ Server recovered"
        fi
        consecutive_failures=0
        restart_attempts=0
    else
        # Unhealthy
        consecutive_failures=$((consecutive_failures + 1))
        log "⚠️ Health check failed ($consecutive_failures consecutive)"
        
        # Restart after 2 consecutive failures
        if [ $consecutive_failures -ge 2 ]; then
            restart_attempts=$((restart_attempts + 1))
            
            if [ $restart_attempts -le $MAX_RESTART_ATTEMPTS ]; then
                if restart_server "$restart_attempts"; then
                    consecutive_failures=0
                fi
            else
                log "❌ Max restart attempts exceeded - giving up"
                log "Manual intervention required"
                exit 1
            fi
        fi
    fi
done

