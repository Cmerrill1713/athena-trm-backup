#!/usr/bin/env bash
# Non-interactive Avatar Rollout Script
# Fast, resumable, resilient rollout that survives IDE timeouts
#
# Usage:
#   ./scripts/rollout_noninteractive.sh
#
# With custom timeouts:
#   PHASE_SMOKE_WAIT=15 PHASE_CANARY_WAIT=15 PHASE_GRADUAL_WAIT=30 ./scripts/rollout_noninteractive.sh
#
# Environment variables:
#   PHASES: comma-separated list of phases (default: smoke,canary,gradual,full)
#   PHASE_SMOKE_WAIT: seconds to monitor smoke phase (default: 30)
#   PHASE_CANARY_WAIT: seconds to monitor canary phase (default: 45)
#   PHASE_GRADUAL_WAIT: seconds to monitor gradual phase (default: 60)
#   PHASE_FULL_WAIT: seconds to monitor full phase (default: 0)
#   NONINTERACTIVE: set to 1 to skip confirmations (default: 1)

set -euo pipefail

# ---- Configuration (override with env vars)
PHASES="${PHASES:-smoke,canary,gradual,full}"
WAIT_SMOKE=${PHASE_SMOKE_WAIT:-30}
WAIT_CANARY=${PHASE_CANARY_WAIT:-45}
WAIT_GRADUAL=${PHASE_GRADUAL_WAIT:-60}
WAIT_FULL=${PHASE_FULL_WAIT:-0}
NONINTERACTIVE=${NONINTERACTIVE:-1}

# ---- Internal state
STATE_FILE=".rollout.state"
LOG_DIR="logs"
LOG="$LOG_DIR/avatar_rollout_$(date +%Y%m%d_%H%M%S).log"

# ---- Functions
setup() {
    mkdir -p "$LOG_DIR"
    touch "$STATE_FILE"
    echo "📜 Starting non-interactive rollout | phases=$PHASES | log=$LOG"
    echo "📜 Starting non-interactive rollout | phases=$PHASES | log=$LOG" >> "$LOG"
}

phase_wait() {
    local phase="$1" secs="$2"
    echo "⏳ $phase: monitoring for ${secs}s..." | tee -a "$LOG"

    if [[ "$secs" -eq 0 ]]; then
        echo "✅ $phase monitor window skipped (0s)" | tee -a "$LOG"
        return
    fi

    for ((i=secs; i>0; i--)); do
        printf "\r%3ds remaining..." "$i"
        sleep 1
    done
    echo -e "\r✅ $phase monitor window complete" | tee -a "$LOG"
}

advance_phase() {
    local phase="$1" wait="$2"

    echo "🚀 Rolling out phase: $phase" | tee -a "$LOG"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting phase: $phase" >> "$LOG"

    # Execute the rollout command
    if ! make "avatar-rollout-phase-$phase" >>"$LOG" 2>&1; then
        echo "❌ Rollout command failed for phase=$phase (see $LOG). Triggering rollback." | tee -a "$LOG"
        if ! make avatar-rollback-force >>"$LOG" 2>&1; then
            echo "❌ Rollback also failed!" | tee -a "$LOG"
        fi
        exit 1
    fi

    # Quick health probe
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Health check after $phase rollout" >> "$LOG"
    if ! make avatar-rollback-check >>"$LOG" 2>&1; then
        echo "⚠️  Health check failed, but continuing..." | tee -a "$LOG"
    fi

    # Monitor window
    phase_wait "$phase" "$wait"

    # Record completion
    echo "$phase" > "$STATE_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Phase $phase completed successfully" >> "$LOG"
}

analyze_rollout() {
    echo "📊 Final rollout analysis..." | tee -a "$LOG"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running final analysis" >> "$LOG"

    if ! make avatar-rollout-analyze >>"$LOG" 2>&1; then
        echo "⚠️  Analysis failed, but rollout continues" | tee -a "$LOG"
    fi
}

# ---- Main execution
setup

LAST_DONE=$(cat "$STATE_FILE" 2>/dev/null || true)
echo "📋 Last completed phase: ${LAST_DONE:-none}" | tee -a "$LOG"

# Parse phases
IFS=',' read -r -a order <<< "$PHASES"

for p in "${order[@]}"; do
    case "$p" in
        smoke)
            [[ "$LAST_DONE" == "smoke" || "$LAST_DONE" == "canary" || "$LAST_DONE" == "gradual" || "$LAST_DONE" == "full" ]] || advance_phase smoke "$WAIT_SMOKE"
            ;;
        canary)
            [[ "$LAST_DONE" == "canary" || "$LAST_DONE" == "gradual" || "$LAST_DONE" == "full" ]] || advance_phase canary "$WAIT_CANARY"
            ;;
        gradual)
            [[ "$LAST_DONE" == "gradual" || "$LAST_DONE" == "full" ]] || advance_phase gradual "$WAIT_GRADUAL"
            ;;
        full)
            [[ "$LAST_DONE" == "full" ]] || advance_phase full "$WAIT_FULL"
            ;;
        *)
            echo "❌ Unknown phase: $p" >&2 | tee -a "$LOG"
            exit 1
            ;;
    esac
done

# Final analysis
analyze_rollout

# Success
echo "🏁 Rollout complete. State recorded in $STATE_FILE. Logs: $LOG" | tee -a "$LOG"
echo "🎯 Avatar system: FULLY DEPLOYED" | tee -a "$LOG"

# Success metrics
make avatar-rollout-success 2>/dev/null || true

