#!/usr/bin/env bash
# Trigger a test Prometheus alert to verify routing

set -e
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

printf '%s\n' "========================================"
printf '%s\n' "Test Alert Trigger"
printf '%s\n' "========================================"
printf '\n'

# Create temporary smoke alert rule
SMOKE_RULE=$(cat <<'EOF'
groups:
  - name: smoke_test
    interval: 10s
    rules:
      - alert: NeuroForge_Smoke_Alert
        expr: vector(1)  # Always true
        for: 30s
        labels:
          severity: warning
          team: test
        annotations:
          summary: "Smoke alert - test routing"
          description: "This is a test alert. Will auto-clear when rule is removed."
EOF
)

# Write to temp file
TEMP_RULE="/tmp/smoke_alert.yaml"
printf '%s' "$SMOKE_RULE" > "$TEMP_RULE"

printf '%s\n' "Created test alert rule:"
printf '  Alert: NeuroForge_Smoke_Alert\n'
printf '  Fires after: 30 seconds\n'
printf '  Severity: warning\n'
printf '\n'

# Validate rule
if command -v promtool >/dev/null 2>&1; then
    if promtool check rules "$TEMP_RULE" >/dev/null 2>&1; then
        printf '%s\n' "OK: Rule syntax valid"
    else
        printf '%s\n' "FAIL: Invalid rule syntax"
        exit 1
    fi
fi

printf '\n%s\n' "To enable this alert:"
printf '  1. Copy to Prometheus:\n'
printf '     cp %s prometheus/alerts/\n' "$TEMP_RULE"
printf '  2. Reload Prometheus:\n'
printf '     make prom-reload\n'
printf '  3. Wait 30 seconds\n'
printf '  4. Check alerts:\n'
printf '     curl http://localhost:9090/api/v1/alerts | jq ".data[] | select(.labels.alertname==\"NeuroForge_Smoke_Alert\")"\n'
printf '\n%s\n' "To remove:"
printf '  1. Delete file:\n'
printf '     rm prometheus/alerts/smoke_alert.yaml\n'
printf '  2. Reload:\n'
printf '     make prom-reload\n'
printf '\n'

printf '%s\n' "========================================"
printf '%s\n' "Test alert rule ready at: $TEMP_RULE"
printf '%s\n' "========================================"

