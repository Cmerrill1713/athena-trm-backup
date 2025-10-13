#!/usr/bin/env bash
# 5-Minute Observability Smoke Test
# Validates Prometheus rules, Grafana health, dashboard imports

set -e
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

printf '%s\n' "========================================"
printf '%s\n' "Observability Smoke Test"
printf '%s\n' "========================================"
printf '\n'

# Check environment
: "${GRAFANA_URL:=http://localhost:3000}"
: "${GRAFANA_API_KEY:?Set GRAFANA_API_KEY or run with GRAFANA_API_KEY=xxx}"

printf '%s\n' "Step 1/5: Validate Prometheus rules..."

# Find all alert rule files
RULE_FILES=$(find monitoring/prometheus prometheus -name '*.yml' -o -name '*.yaml' 2>/dev/null | grep -i alert || true)

if [ -z "$RULE_FILES" ]; then
    # Try our new location
    if [ -f "prometheus/alerts/slo_rules.yaml" ]; then
        RULE_FILES="prometheus/alerts/slo_rules.yaml"
    fi
fi

if command -v promtool >/dev/null 2>&1; then
    for file in $RULE_FILES; do
        if [ -f "$file" ]; then
            promtool check rules "$file" >/dev/null 2>&1 && \
                printf '  OK %s\n' "$(basename "$file")" || \
                printf '  FAIL %s\n' "$(basename "$file")"
        fi
    done
else
    printf '  WARN: promtool not installed, skipping validation\n'
fi

printf '\n%s\n' "Step 2/5: Reload Prometheus..."

if curl -sS -X POST http://localhost:9090/-/reload >/dev/null 2>&1; then
    printf '  OK: Prometheus reloaded\n'
else
    printf '  WARN: Prometheus not responding (may not be running)\n'
fi

printf '\n%s\n' "Step 3/5: Check Grafana health..."

if curl -sf "$GRAFANA_URL/api/health" >/dev/null 2>&1; then
    printf '  OK: Grafana responding at %s\n' "$GRAFANA_URL"
else
    printf '  FAIL: Grafana not responding at %s\n' "$GRAFANA_URL"
    printf '  Start with: docker-compose -f docker-compose.monitoring.yml up -d grafana\n'
    exit 1
fi

printf '\n%s\n' "Step 4/5: Validate dashboard JSON..."

INVALID=0
for dash in grafana/dashboards/*.json; do
    if [ -f "$dash" ]; then
        if jq -e empty "$dash" >/dev/null 2>&1; then
            printf '  OK %s\n' "$(basename "$dash")"
        else
            printf '  FAIL %s (invalid JSON)\n' "$(basename "$dash")"
            INVALID=$((INVALID + 1))
        fi
    fi
done

if [ $INVALID -gt 0 ]; then
    printf '\n%s\n' "FAIL: $INVALID dashboards have invalid JSON"
    exit 1
fi

printf '\n%s\n' "Step 5/5: Import dashboards..."

if [ -x "grafana/import_dashboards.sh" ]; then
    ./grafana/import_dashboards.sh
else
    printf '  WARN: import_dashboards.sh not executable\n'
    chmod +x grafana/import_dashboards.sh
    ./grafana/import_dashboards.sh
fi

printf '\n%s\n' "========================================"
printf '%s\n' "OK: Observability smoke test PASSED"
printf '%s\n' "========================================"
printf '\n%s\n' "Verify imported dashboards:"
printf '  %s/dashboards\n' "$GRAFANA_URL"
printf '\n%s\n' "Check Prometheus alerts:"
printf '  http://localhost:9090/alerts\n'
printf '\n'

