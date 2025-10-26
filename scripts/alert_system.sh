#!/bin/bash
# ============================================================================
# ATHENA LOCAL ALERT SYSTEM
# Sends macOS notifications on validation failures
# NO CLOUD - 100% local
# ============================================================================

set -euo pipefail

# Configuration
ALERT_LOG="artifacts/alerts.log"
ALERT_SOUND="Glass"  # macOS sound: Basso, Blow, Bottle, Frog, Funk, Glass, Hero, Morse, Ping, Pop, Purr, Sosumi, Submarine, Tink

send_alert() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"  # critical, normal, low
    
    # Log alert
    echo "[$(date)] ALERT: $title - $message" >> "$ALERT_LOG"
    
    # Send macOS notification
    osascript -e "display notification \"$message\" with title \"⚠️ Athena Alert\" subtitle \"$title\" sound name \"$ALERT_SOUND\""
    
    # If critical, also speak it
    if [ "$urgency" = "critical" ]; then
        say "Athena alert: $title. $message" &
    fi
    
    echo "🚨 Alert sent: $title"
}

send_success() {
    local message="$1"
    
    # Log success
    echo "[$(date)] SUCCESS: $message" >> "$ALERT_LOG"
    
    # Send notification
    osascript -e "display notification \"$message\" with title \"✅ Athena Status\" sound name \"Ping\""
}

# ============================================================================
# PARSE VALIDATION RESULTS
# ============================================================================

if [ ! -f "artifacts/validation_latest.json" ]; then
    send_alert "Validation Missing" "No validation results found. Run ./validate_and_recover.sh" "normal"
    exit 1
fi

# Read results
ISSUES=$(jq -r '.issues_found // 0' artifacts/validation_latest.json 2>/dev/null || echo "0")
FIXED=$(jq -r '.issues_fixed // 0' artifacts/validation_latest.json 2>/dev/null || echo "0")
DOC_COUNT=$(jq -r '.doc_count // 0' artifacts/validation_latest.json 2>/dev/null || echo "0")
DRIFT_PCT=$(jq -r '.drift_pct // 0' artifacts/validation_latest.json 2>/dev/null || echo "0")

# ============================================================================
# ALERT LOGIC
# ============================================================================

if [ "$ISSUES" -eq 0 ]; then
    # All healthy
    send_success "All systems healthy! DocsV2: $DOC_COUNT, Drift: ${DRIFT_PCT}%"
    
elif [ "$FIXED" -eq "$ISSUES" ]; then
    # Issues found but auto-recovered
    send_alert "Auto-Recovered" "Found $ISSUES issues and fixed them all!" "normal"
    
else
    # Unresolved issues
    UNRESOLVED=$((ISSUES - FIXED))
    
    if [ "$UNRESOLVED" -ge 3 ]; then
        # Critical - multiple failures
        send_alert "CRITICAL FAILURES" "$UNRESOLVED unresolved issues! Check logs immediately!" "critical"
    else
        # Warning - some failures
        send_alert "Manual Fix Needed" "$UNRESOLVED issues need attention. Check artifacts/validation_latest.log" "normal"
    fi
fi

# ============================================================================
# DRIFT ALERTS
# ============================================================================

# Convert drift_pct to integer for comparison
DRIFT_INT=$(echo "$DRIFT_PCT" | cut -d. -f1)

if [ "${DRIFT_INT:-0}" -gt 15 ]; then
    send_alert "Significant Drift" "Knowledge base drifted ${DRIFT_PCT}% from baseline!" "critical"
elif [ "${DRIFT_INT:-0}" -gt 10 ]; then
    send_alert "Moderate Drift" "Knowledge base drifted ${DRIFT_PCT}% from baseline" "normal"
fi

# ============================================================================
# SPECIFIC SERVICE ALERTS
# ============================================================================

# Check for specific failures
if [ -f "artifacts/validation_latest.log" ]; then
    if grep -q "Weaviate.*FAIL" artifacts/validation_latest.log; then
        send_alert "Weaviate Down" "Knowledge base is unreachable!" "critical"
    fi
    
    if grep -q "Router.*FAIL" artifacts/validation_latest.log; then
        send_alert "Router Down" "Routing service is unhealthy!" "critical"
    fi
    
    if grep -q "corpus.*0" artifacts/validation_latest.log; then
        send_alert "Corpus Empty" "Knowledge base has 0 documents! Restore from backup!" "critical"
    fi
fi

echo "✅ Alert processing complete"
exit 0

