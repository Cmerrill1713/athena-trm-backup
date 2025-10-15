#!/usr/bin/env bash
# Stack Watchdog - Self-Healing Orchestration
# Monitors stack health and auto-recovers from failures

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
LOGFILE="${LOGFILE:-/tmp/stack_watchdog.log}"
INCIDENT_LOG="${INCIDENT_LOG:-/tmp/stack_incidents.log}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"  # seconds
MAX_RESTARTS_PER_HOUR="${MAX_RESTARTS_PER_HOUR:-5}"
BACKOFF_SECONDS="${BACKOFF_SECONDS:-60}"

# Notification settings
NOTIFY_SLACK="${NOTIFY_SLACK:-0}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
NOTIFY_TELEGRAM="${NOTIFY_TELEGRAM:-0}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Service endpoints
BRIDGE_URL="${BRIDGE_URL:-http://127.0.0.1:8014}"
ATHENA_URL="${ATHENA_URL:-http://127.0.0.1:8090}"
UAT_URL="${UAT_URL:-http://127.0.0.1:8181}"
ATH_TOKEN="${ATH_TOKEN:-supersecret}"
UAT_TOKEN="${UAT_TOKEN:-supersecret}"

# ============================================================================
# State Management
# ============================================================================

RESTART_COUNT_FILE="/tmp/stack_watchdog_restarts"
LAST_RESTART_FILE="/tmp/stack_watchdog_last_restart"

get_restart_count() {
    if [[ -f "$RESTART_COUNT_FILE" ]]; then
        cat "$RESTART_COUNT_FILE"
    else
        echo 0
    fi
}

increment_restart_count() {
    local count=$(get_restart_count)
    echo $((count + 1)) > "$RESTART_COUNT_FILE"
}

reset_restart_count() {
    echo 0 > "$RESTART_COUNT_FILE"
}

get_last_restart_time() {
    if [[ -f "$LAST_RESTART_FILE" ]]; then
        cat "$LAST_RESTART_FILE"
    else
        echo 0
    fi
}

set_last_restart_time() {
    date +%s > "$LAST_RESTART_FILE"
}

# Prune old restarts (older than 1 hour)
prune_old_restarts() {
    local now=$(date +%s)
    local last_restart=$(get_last_restart_time)
    local age=$((now - last_restart))

    if [[ $age -gt 3600 ]]; then
        reset_restart_count
    fi
}

check_restart_limit() {
    prune_old_restarts
    local count=$(get_restart_count)

    if [[ $count -ge $MAX_RESTARTS_PER_HOUR ]]; then
        log "ERROR" "Restart limit exceeded ($count restarts in last hour). Entering backoff."
        return 1
    fi
    return 0
}

# ============================================================================
# Logging
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$level] $message" | tee -a "$LOGFILE"

    # Log incidents separately
    if [[ "$level" == "INCIDENT" || "$level" == "ERROR" || "$level" == "HEAL" ]]; then
        echo "[$timestamp] [$level] $message" >> "$INCIDENT_LOG"
    fi
}

# ============================================================================
# Notifications
# ============================================================================

notify_slack() {
    local message="$1"

    if [[ "$NOTIFY_SLACK" == "1" && -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🤖 Stack Watchdog: $message\"}" \
            &>/dev/null || true
    fi
}

notify_telegram() {
    local message="$1"

    if [[ "$NOTIFY_TELEGRAM" == "1" && -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=🤖 Stack Watchdog: $message" \
            &>/dev/null || true
    fi
}

notify() {
    local message="$1"
    notify_slack "$message"
    notify_telegram "$message"
}

# ============================================================================
# Health Checks
# ============================================================================

check_service_health() {
    local service="$1"
    local url="$2"
    local token="${3:-}"

    local headers=""
    if [[ -n "$token" ]]; then
        headers="-H \"Authorization: Bearer $token\""
    fi

    local response=$(eval curl -s -w "\\n%{http_code}" $headers "$url/health" 2>/dev/null || echo "000")
    local http_code=$(echo "$response" | tail -n 1)
    local body=$(echo "$response" | head -n -1)

    if [[ "$http_code" == "200" ]]; then
        local status=$(echo "$body" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
        if [[ "$status" == "healthy" || "$status" == "ok" ]]; then
            return 0
        fi
    fi

    return 1
}

count_pids_on_ports() {
    local count=0
    for port in 8014 8090 8181; do
        local pids=$(lsof -ti:$port 2>/dev/null | wc -l | tr -d ' ')
        count=$((count + pids))
    done
    echo $count
}

detect_ghosts() {
    local total_pids=$(count_pids_on_ports)

    # Expected: 3 PIDs (one per service)
    # Ghost detected if > 3
    if [[ $total_pids -gt 3 ]]; then
        return 0  # Ghosts found
    fi
    return 1  # No ghosts
}

check_stack_health() {
    local issues=()

    # Check Bridge
    if ! check_service_health "Bridge" "$BRIDGE_URL" ""; then
        issues+=("Bridge unhealthy/unreachable")
    fi

    # Check Athena
    if ! check_service_health "Athena" "$ATHENA_URL" "$ATH_TOKEN"; then
        issues+=("Athena unhealthy/unreachable")
    fi

    # Check UAT
    if ! check_service_health "UAT" "$UAT_URL" "$UAT_TOKEN"; then
        issues+=("UAT unhealthy/unreachable")
    fi

    # Check for ghosts
    if detect_ghosts; then
        local pid_count=$(count_pids_on_ports)
        issues+=("Ghost processes detected ($pid_count PIDs, expected 3)")
    fi

    if [[ ${#issues[@]} -eq 0 ]]; then
        return 0  # Healthy
    else
        # Print issues to stdout
        printf '%s\n' "${issues[@]}"
        return 1  # Unhealthy
    fi
}

# ============================================================================
# Self-Healing Actions
# ============================================================================

self_heal() {
    local reason="$1"

    log "INCIDENT" "Stack unhealthy: $reason"

    # Check restart limit
    if ! check_restart_limit; then
        log "ERROR" "Cannot self-heal: restart limit exceeded. Entering backoff for $BACKOFF_SECONDS seconds."
        notify "⚠️ Stack unhealthy but restart limit exceeded. Manual intervention required: $reason"
        sleep $BACKOFF_SECONDS
        return 1
    fi

    log "HEAL" "Initiating self-heal sequence..."
    notify "🔧 Self-healing initiated: $reason"

    # Step 1: Kill ghosts
    log "HEAL" "Step 1/4: Killing ghosts (nuke-ports)..."
    cd "$WORKSPACE_ROOT"
    make nuke-ports >> "$LOGFILE" 2>&1 || true
    sleep 2

    # Step 2: Start stack
    log "HEAL" "Step 2/4: Starting stack..."
    if make stack-up >> "$LOGFILE" 2>&1; then
        log "HEAL" "Stack started successfully"
    else
        log "ERROR" "Stack startup failed"
        notify "❌ Self-heal FAILED: Stack startup failed"
        return 1
    fi

    sleep 3

    # Step 3: Verify health
    log "HEAL" "Step 3/4: Verifying health..."
    if check_stack_health >/dev/null 2>&1; then
        log "HEAL" "Health check passed"
    else
        log "ERROR" "Health check failed after restart"
        notify "❌ Self-heal FAILED: Health check failed after restart"
        return 1
    fi

    # Step 4: Run smoke tests
    log "HEAL" "Step 4/4: Running smoke tests..."
    if make athena-tests-smoke >> "$LOGFILE" 2>&1; then
        log "HEAL" "Smoke tests passed"
    else
        log "WARN" "Smoke tests failed (stack is up but tests failing)"
        notify "⚠️ Self-heal PARTIAL: Stack up but smoke tests failed"
    fi

    # Success
    increment_restart_count
    set_last_restart_time
    log "HEAL" "✅ Self-heal complete. Restart count: $(get_restart_count)/hour"
    notify "✅ Self-heal successful: Stack recovered from: $reason"

    return 0
}

# ============================================================================
# Main Loop
# ============================================================================

main() {
    log "INFO" "Stack Watchdog starting..."
    log "INFO" "Check interval: ${CHECK_INTERVAL}s"
    log "INFO" "Max restarts/hour: $MAX_RESTARTS_PER_HOUR"
    log "INFO" "Workspace: $WORKSPACE_ROOT"

    # Initialize restart tracking
    reset_restart_count

    while true; do
        if issues=$(check_stack_health 2>&1); then
            # Healthy
            local pid_count=$(count_pids_on_ports)
            log "INFO" "✅ Stack healthy (PIDs: $pid_count)"
        else
            # Unhealthy - issues contains the problems
            log "INCIDENT" "❌ Stack unhealthy: $issues"

            # Attempt self-heal
            if self_heal "$issues"; then
                log "INFO" "Self-heal successful, resuming monitoring"
            else
                log "ERROR" "Self-heal failed, will retry after backoff"
                sleep $BACKOFF_SECONDS
            fi
        fi

        sleep $CHECK_INTERVAL
    done
}

# ============================================================================
# Signal Handling
# ============================================================================

cleanup() {
    log "INFO" "Stack Watchdog stopping (signal received)..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================================
# Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
