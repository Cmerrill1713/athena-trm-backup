#!/usr/bin/env bash
# Automated Avatar Drift Check
# Runs periodic checks to detect changes from golden baseline
# Use with cron: 0 */12 * * * /path/to/scripts/drift_check.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$REPO_ROOT/logs"
DRIFT_LOG="$LOG_DIR/drift_check_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ---- Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$DRIFT_LOG"
}

error() {
    echo -e "${RED}❌ ERROR: $*${NC}" | tee -a "$DRIFT_LOG"
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING: $*${NC}" | tee -a "$DRIFT_LOG"
}

success() {
    echo -e "${GREEN}✅ $*${NC}" | tee -a "$DRIFT_LOG"
}

# ---- Check functions
check_backend_health() {
    log "Checking backend health..."
    if curl -s --max-time 5 http://localhost:8035/v1/healthz | jq -e '.ok == true' >/dev/null 2>&1; then
        success "Backend health check passed"
        return 0
    else
        error "Backend health check failed"
        return 1
    fi
}

check_avatar_api() {
    log "Checking avatar API..."
    if curl -s --max-time 5 http://localhost:8035/v1/avatar/status >/dev/null 2>&1; then
        success "Avatar API check passed"
        return 0
    else
        error "Avatar API check failed"
        return 1
    fi
}

check_metrics() {
    log "Checking metrics endpoint..."
    if curl -s --max-time 5 http://localhost:9108/metrics | grep -q "athena_http_requests_total"; then
        success "Metrics check passed"
        return 0
    else
        error "Metrics check failed"
        return 1
    fi
}

check_git_status() {
    log "Checking git status..."
    cd "$REPO_ROOT"

    # Check for uncommitted changes
    if git status --porcelain | grep -v "^?? " | head -5 | grep -q .; then
        warning "Uncommitted changes detected:"
        git status --porcelain | head -5 | tee -a "$DRIFT_LOG"
        return 1
    else
        success "Git status clean"
        return 0
    fi
}

check_rollout_state() {
    log "Checking rollout state..."
    if [ -f ".rollout.state" ]; then
        STATE=$(cat .rollout.state)
        if [ "$STATE" = "full" ]; then
            success "Rollout state: $STATE (expected)"
            return 0
        else
            warning "Rollout state: $STATE (expected: full)"
            return 1
        fi
    else
        error "Rollout state file missing"
        return 1
    fi
}

check_recent_logs() {
    log "Checking recent error logs..."

    # Check for recent errors in avatar rollout logs
    if ls "$LOG_DIR"/avatar_rollout_*.log >/dev/null 2>&1; then
        LATEST_LOG=$(ls -t "$LOG_DIR"/avatar_rollout_*.log | head -1)
        if grep -q "ERROR\|FAILED\|❌" "$LATEST_LOG" 2>/dev/null; then
            warning "Errors found in recent logs: $LATEST_LOG"
            grep -C2 "ERROR\|FAILED\|❌" "$LATEST_LOG" | head -10 | tee -a "$DRIFT_LOG"
            return 1
        else
            success "Recent logs clean"
            return 0
        fi
    else
        warning "No recent avatar rollout logs found"
        return 1
    fi
}

send_alert() {
    local message="$1"
    log "ALERT: $message"

    # Here you could add email, Slack, Discord, etc. notifications
    # For now, just log it prominently

    echo "==================================================" | tee -a "$DRIFT_LOG"
    echo "🚨 DRIFT ALERT: $message" | tee -a "$DRIFT_LOG"
    echo "==================================================" | tee -a "$DRIFT_LOG"
}

cleanup_old_logs() {
    # Keep only last 10 drift check logs
    find "$LOG_DIR" -name "drift_check_*.log" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
}

# ---- Main execution
mkdir -p "$LOG_DIR"

log "🚀 Starting automated avatar drift check"
log "Log file: $DRIFT_LOG"

DRIFT_DETECTED=0

# Run all checks
check_backend_health || DRIFT_DETECTED=1
check_avatar_api || DRIFT_DETECTED=1
check_metrics || DRIFT_DETECTED=1
check_git_status || DRIFT_DETECTED=1
check_rollout_state || DRIFT_DETECTED=1
check_recent_logs || DRIFT_DETECTED=1

# Summary
log ""
log "📊 Drift Check Summary"
echo "==================================================" | tee -a "$DRIFT_LOG"

if [ $DRIFT_DETECTED -eq 0 ]; then
    success "✅ All checks passed - system stable"
    echo "Avatar system remains in golden state" | tee -a "$DRIFT_LOG"
else
    send_alert "Drift detected - system may have changed from golden baseline"
    echo "⚠️  Review logs above and consider reverting to golden state" | tee -a "$DRIFT_LOG"
fi

echo "==================================================" | tee -a "$DRIFT_LOG"
log "Drift check complete. Log: $DRIFT_LOG"

# Cleanup old logs
cleanup_old_logs

# Exit with status
exit $DRIFT_DETECTED

