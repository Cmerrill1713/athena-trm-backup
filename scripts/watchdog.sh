#!/usr/bin/env bash
# Stack Watchdog - Self-Healing Orchestration
# Monitors services and auto-recovers from failures

set -euo pipefail

# Configuration
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"           # Seconds between checks
MAX_RETRIES="${MAX_RETRIES:-3}"                  # Max recovery attempts before giving up
RECOVERY_COOLDOWN="${RECOVERY_COOLDOWN:-60}"     # Seconds to wait after recovery
NOTIFY_WEBHOOK="${NOTIFY_WEBHOOK:-}"             # Optional webhook for notifications

# Service configuration
BRIDGE_BASE="${BRIDGE_BASE:-http://127.0.0.1:8014}"
UAT_BASE="${UAT_BASE:-http://127.0.0.1:8181}"
ATHENA_BASE="${ATHENA_BASE:-http://127.0.0.1:8090}"

# State tracking
RECOVERY_COUNT=0
LAST_RECOVERY_TIME=0
WATCHDOG_START_TIME=$(date +%s)

# Logging
LOG_FILE="${LOG_FILE:-/tmp/watchdog_stack.log}"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

# Send notification (optional)
notify() {
    local message="$1"
    local status="${2:-info}"

    # Use dedicated notification script if available
    local notify_script="$(dirname "$0")/notify.sh"
    if [ -x "$notify_script" ]; then
        "$notify_script" "$message" "$status" 2>/dev/null || true
    elif [ -n "$NOTIFY_WEBHOOK" ]; then
        # Fallback to simple curl
        curl -s -X POST "$NOTIFY_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🤖 Stack Watchdog: $message\", \"status\":\"$status\"}" \
            > /dev/null 2>&1 || true
    fi
}

# Check service health
check_service() {
    local name="$1"
    local url="$2"

    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$url/health" 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        return 0
    else
        return 1
    fi
}

# Check for ghost processes
check_ghosts() {
    local bridge_pids=$(lsof -ti:8014 2>/dev/null | wc -l | xargs)
    local athena_pids=$(lsof -ti:8090 2>/dev/null | wc -l | xargs)
    local uat_pids=$(lsof -ti:8181 2>/dev/null | wc -l | xargs)

    # Uvicorn with --reload has 2 PIDs (parent + worker), so > 2 = ghosts
    # Allow 0 (service down), 1 (single process), or 2 (reload mode)
    if [[ "$bridge_pids" -gt 2 ]] || [[ "$athena_pids" -gt 2 ]] || [[ "$uat_pids" -gt 2 ]]; then
        return 1
    fi

    return 0
}

# Perform health check on all services
health_check() {
    local bridge_ok=0
    local uat_ok=0
    local athena_ok=0
    local ghosts_ok=0

    check_service "Bridge" "$BRIDGE_BASE" && bridge_ok=1
    check_service "UAT" "$UAT_BASE" && uat_ok=1
    check_service "Athena" "$ATHENA_BASE" && athena_ok=1
    check_ghosts && ghosts_ok=1

    if [[ "$bridge_ok" == "1" ]] && [[ "$uat_ok" == "1" ]] && [[ "$athena_ok" == "1" ]] && [[ "$ghosts_ok" == "1" ]]; then
        return 0  # All healthy
    else
        # Log what's wrong
        [[ "$bridge_ok" == "0" ]] && log_warn "Bridge unhealthy"
        [[ "$uat_ok" == "0" ]] && log_warn "UAT unhealthy"
        [[ "$athena_ok" == "0" ]] && log_warn "Athena unhealthy"
        [[ "$ghosts_ok" == "0" ]] && log_warn "Ghost processes detected"
        return 1  # Something is broken
    fi
}

# Recovery procedure
recover() {
    local current_time=$(date +%s)
    local time_since_last=$((current_time - LAST_RECOVERY_TIME))

    # Check if we're in cooldown
    if [[ "$time_since_last" -lt "$RECOVERY_COOLDOWN" ]]; then
        log_warn "In recovery cooldown (${time_since_last}s/${RECOVERY_COOLDOWN}s)"
        return 1
    fi

    # Check max retries
    if [[ "$RECOVERY_COUNT" -ge "$MAX_RETRIES" ]]; then
        log_error "Max recovery attempts reached ($MAX_RETRIES). Manual intervention required."
        notify "Stack auto-heal failed after $MAX_RETRIES attempts. Manual intervention needed." "error"
        return 1
    fi

    log_warn "Initiating self-heal procedure (attempt $((RECOVERY_COUNT + 1))/$MAX_RETRIES)..."
    notify "Stack self-healing initiated (attempt $((RECOVERY_COUNT + 1))/$MAX_RETRIES)" "warning"

    # Step 1: Kill ghosts
    log "Step 1/4: Killing ghost processes..."
    lsof -ti:8014,8090,8181 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 2

    # Step 2: Clean shutdown (in case anything survived)
    log "Step 2/4: Clean shutdown..."
    cd "$(dirname "$0")/.." && make stack-down > /dev/null 2>&1 || true
    sleep 1

    # Step 3: Restart stack
    log "Step 3/4: Restarting stack..."
    cd "$(dirname "$0")/.." && make stack-up > /dev/null 2>&1
    sleep 5

    # Step 4: Validate recovery
    log "Step 4/4: Validating recovery..."
    if health_check; then
        log_success "Self-heal successful! Stack recovered."
        notify "Stack self-healing successful! All services restored." "success"

        # Update state
        RECOVERY_COUNT=$((RECOVERY_COUNT + 1))
        LAST_RECOVERY_TIME=$current_time

        # Run truth check for logs
        cd "$(dirname "$0")/.." && make truth > /tmp/watchdog_truth.log 2>&1 || true

        return 0
    else
        log_error "Recovery validation failed. Will retry on next cycle."
        RECOVERY_COUNT=$((RECOVERY_COUNT + 1))
        LAST_RECOVERY_TIME=$current_time
        return 1
    fi
}

# Watchdog main loop
watchdog_loop() {
    log "🤖 Stack Watchdog started"
    log "Configuration:"
    log "  Check interval: ${CHECK_INTERVAL}s"
    log "  Max retries: $MAX_RETRIES"
    log "  Recovery cooldown: ${RECOVERY_COOLDOWN}s"
    log "  Log file: $LOG_FILE"
    log ""

    notify "Stack Watchdog started. Autonomous healing enabled." "info"

    local cycle=0
    local consecutive_healthy=0

    while true; do
        cycle=$((cycle + 1))

        if health_check; then
            consecutive_healthy=$((consecutive_healthy + 1))

            # Log every 10th healthy check (reduce log spam)
            if [[ $((cycle % 10)) -eq 0 ]]; then
                log "✅ Stack healthy (cycle $cycle, consecutive: $consecutive_healthy)"
            fi

            # Reset recovery count after 10 consecutive healthy checks
            if [[ "$consecutive_healthy" -ge 10 ]] && [[ "$RECOVERY_COUNT" -gt 0 ]]; then
                log_success "Stack stable. Resetting recovery counter."
                RECOVERY_COUNT=0
            fi
        else
            log_error "Stack unhealthy detected (cycle $cycle)"
            consecutive_healthy=0

            # Attempt recovery
            if recover; then
                log_success "Recovery successful. Resuming monitoring..."
            else
                log_warn "Recovery incomplete. Will retry on next cycle."
            fi
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    log "🛑 Watchdog stopping (received signal)..."
    notify "Stack Watchdog stopped." "info"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Show status
show_status() {
    local uptime=$(($(date +%s) - WATCHDOG_START_TIME))
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║          Stack Watchdog Status                         ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo "Uptime: ${uptime}s"
    echo "Recovery attempts: $RECOVERY_COUNT / $MAX_RETRIES"
    echo "Last recovery: $(if [ $LAST_RECOVERY_TIME -eq 0 ]; then echo 'Never'; else echo "$(($(date +%s) - LAST_RECOVERY_TIME))s ago"; fi)"
    echo ""
    echo "Service status:"
    check_service "Bridge" "$BRIDGE_BASE" && echo "  ✅ Bridge" || echo "  ❌ Bridge"
    check_service "UAT" "$UAT_BASE" && echo "  ✅ UAT" || echo "  ❌ UAT"
    check_service "Athena" "$ATHENA_BASE" && echo "  ✅ Athena" || echo "  ❌ Athena"
    check_ghosts && echo "  ✅ No ghosts" || echo "  ⚠️  Ghost processes detected"
    echo ""
}

# Main execution
case "${1:-start}" in
    start)
        watchdog_loop
        ;;
    status)
        show_status
        ;;
    test)
        log "🧪 Running health check test..."
        if health_check; then
            log_success "All services healthy!"
            exit 0
        else
            log_error "Stack unhealthy"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|status|test}"
        exit 1
        ;;
esac
