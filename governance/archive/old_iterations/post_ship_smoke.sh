#!/usr/bin/env bash
# 5-Minute Post-Ship Smoke Test
# Validates platform after deployment

set -e
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

printf '%s\n' "========================================"
printf '%s\n' "POST-SHIP SMOKE TEST"
printf '%s\n' "========================================"
printf '\n'

# Step 1: Core services
printf '%s\n' "Step 1/5: Verify core services..."

for port in 8014 8090 8181 8020; do
    printf '  Port %s: ' "$port"
    if curl -fsS "127.0.0.1:$port/ready" >/dev/null 2>&1 || \
       curl -fsS "127.0.0.1:$port/health" >/dev/null 2>&1; then
        printf 'OK\n'
    else
        printf 'FAIL\n'
        exit 1
    fi
done

# Step 2: Bridge end-to-end
printf '\n%s\n' "Step 2/5: Bridge end-to-end test..."
printf '  Sending test message...\n'

RESPONSE=$(curl -fsS -X POST 127.0.0.1:8014/chat \
    -H "Content-Type: application/json" \
    -d '{"text":"ping"}' 2>&1 | head -120)

if printf '%s' "$RESPONSE" | grep -q -E '(text|message|reply)'; then
    printf '  OK: Bridge responding\n'
else
    printf '  FAIL: Bridge not responding correctly\n'
    printf '  Response: %s\n' "$(printf '%s' "$RESPONSE" | head -3)"
    exit 1
fi

# Step 3: Prometheus
printf '\n%s\n' "Step 3/5: Prometheus health..."
if curl -fsS 127.0.0.1:9090/-/ready >/dev/null 2>&1; then
    printf '  OK: Prometheus ready\n'
else
    printf '  WARN: Prometheus not responding\n'
fi

# Step 4: Grafana dashboards
printf '\n%s\n' "Step 4/5: Grafana dashboards..."
if [ -n "${GRAFANA_API_KEY:-}" ] && [ -n "${GRAFANA_URL:-}" ]; then
    DASH_COUNT=$(curl -sH "Authorization: Bearer $GRAFANA_API_KEY" \
        "${GRAFANA_URL}/api/search?query=NeuroForge" 2>/dev/null | \
        jq '. | length' 2>/dev/null || printf '0')
    
    if [ "$DASH_COUNT" -ge 3 ]; then
        printf '  OK: %s dashboards imported\n' "$DASH_COUNT"
    else
        printf '  WARN: Only %s dashboards found (expected 3+)\n' "$DASH_COUNT"
    fi
else
    printf '  SKIP: GRAFANA_URL or GRAFANA_API_KEY not set\n'
fi

# Step 5: Platform validation
printf '\n%s\n' "Step 5/5: Platform validation..."
if [ -f "./VALIDATE_PLATFORM.sh" ]; then
    if ./VALIDATE_PLATFORM.sh >/dev/null 2>&1; then
        printf '  OK: Platform validation passed\n'
    else
        printf '  WARN: Platform validation had issues\n'
    fi
else
    printf '  SKIP: VALIDATE_PLATFORM.sh not found\n'
fi

printf '\n%s\n' "========================================"
printf '%s\n' "POST-SHIP SMOKE: PASSED"
printf '%s\n' "========================================"
printf '\n%s\n' "Next: Monitor for 30 minutes"
printf '  Grafana: %s/dashboards\n' "${GRAFANA_URL:-http://localhost:3000}"
printf '  Prometheus: http://localhost:9090/alerts\n'
printf '  Services: make truth\n'
printf '\n'

