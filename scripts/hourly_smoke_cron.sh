#!/bin/bash
# Hourly system smoke test with alerting
# Run via cron: 0 * * * * /Users/christianmerrill/Documents/GitHub/scripts/hourly_smoke_cron.sh

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
SMOKE_LOG="$LOG_DIR/hourly_smoke.log"
ALERT_LOG="$LOG_DIR/smoke_alerts.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Run smoke test and capture output
echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting hourly smoke test" >> "$SMOKE_LOG"

if cd "$SCRIPT_DIR" && ./scripts/system_smoke.sh >> "$SMOKE_LOG" 2>&1; then
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ✅ Smoke test PASSED" >> "$SMOKE_LOG"
    exit 0
else
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ❌ Smoke test FAILED" >> "$SMOKE_LOG"
    
    # Alert on hard failures (not warnings)
    if grep -q "❌ Failed: [1-9]" "$SMOKE_LOG"; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - HARD FAILURE DETECTED" >> "$ALERT_LOG"
        
        # Send alert (customize this for your notification system)
        # Examples:
        # - Slack: curl -X POST -H 'Content-type: application/json' --data '{"text":"🚨 Athena System Smoke Test Failed"}' $SLACK_WEBHOOK
        # - Email: echo "Athena smoke test failed at $(date)" | mail -s "Athena Alert" admin@company.com
        # - PagerDuty: curl -X POST -H 'Content-type: application/json' --data '{"routing_key":"$PD_ROUTING_KEY","event_action":"trigger","payload":{"summary":"Athena System Smoke Test Failed"}}' https://events.pagerduty.com/v2/enqueue
        
        echo "🚨 ALERT: System smoke test failed - check $SMOKE_LOG"
    fi
    
    exit 1
fi
