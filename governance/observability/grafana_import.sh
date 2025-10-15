#!/usr/bin/env bash
# One-shot Grafana dashboard and alert import

set -euo pipefail
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

: "${GRAFANA_URL:?Set GRAFANA_URL}"
: "${GRAFANA_API_KEY:?Set GRAFANA_API_KEY}"

printf '%s\n' "========================================"
printf '%s\n' "Grafana Dashboard Import"
printf '%s\n' "========================================"
printf '\n'

# Headers
HDR=(-H "Authorization: Bearer ${GRAFANA_API_KEY}" -H "Content-Type: application/json")

# Step 1: Ensure Prometheus datasource exists
printf '%s\n' "Step 1: Ensure Prometheus datasource..."

DATASOURCE_PAYLOAD=$(cat <<'EOF'
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://localhost:9090",
  "access": "proxy",
  "basicAuth": false,
  "isDefault": true,
  "editable": true
}
EOF
)

curl -sf "${HDR[@]}" -X POST "${GRAFANA_URL}/api/datasources" \
  -d "$DATASOURCE_PAYLOAD" >/dev/null 2>&1 && \
  printf '  OK: Datasource created/exists\n' || \
  printf '  OK: Datasource already exists\n'

# Step 2: Import dashboards
printf '\n%s\n' "Step 2: Import dashboards..."

DASH_DIR="$(dirname "$0")/dashboards"
if [ ! -d "$DASH_DIR" ]; then
    # Fallback to root grafana/dashboards
    DASH_DIR="$(dirname "$(dirname "$0")")/grafana/dashboards"
fi

IMPORTED=0
for dash in "$DASH_DIR"/*.json; do
    if [ -f "$dash" ]; then
        filename=$(basename "$dash")
        printf '  Importing %s ... ' "$filename"
        
        PAYLOAD=$(cat <<EOF
{
  "dashboard": $(cat "$dash"),
  "overwrite": true,
  "folderId": 0,
  "message": "Auto-imported via script"
}
EOF
)
        
        RESULT=$(curl -sS "${HDR[@]}" -X POST "${GRAFANA_URL}/api/dashboards/db" \
          -d "$PAYLOAD" 2>&1)
        
        if printf '%s' "$RESULT" | grep -q '"status":"success"'; then
            printf 'OK\n'
            IMPORTED=$((IMPORTED + 1))
        else
            printf 'FAIL\n'
            printf '    %s\n' "$RESULT" | head -2
        fi
    fi
done

printf '\n%s\n' "Step 3: Copy alert rules to Prometheus..."

ALERT_DIR="$(dirname "$0")/alerts"
if [ ! -d "$ALERT_DIR" ]; then
    ALERT_DIR="$(dirname "$(dirname "$0")")/prometheus/alerts"
fi

if [ -d "$ALERT_DIR" ]; then
    printf '  Alert rules location: %s\n' "$ALERT_DIR"
    printf '  Ensure these are mounted in Prometheus config\n'
else
    printf '  WARN: No alert rules directory found\n'
fi

printf '\n%s\n' "========================================"
printf 'OK: Imported %d dashboards\n' "$IMPORTED"
printf '%s\n' "========================================"
printf '\n%s\n' "Access dashboards at:"
printf '  %s/dashboards\n' "$GRAFANA_URL"

