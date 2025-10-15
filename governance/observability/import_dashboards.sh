#!/usr/bin/env bash
# Import NeuroForge dashboards into Grafana

set -euo pipefail
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

: "${GRAFANA_URL:?Set GRAFANA_URL (e.g., http://localhost:3000)}"
: "${GRAFANA_API_KEY:?Create a Grafana API key with Admin role}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

import_one() {
  local file="$1"
  local filename=$(basename "$file")
  
  printf 'Importing %s ... ' "$filename"
  
  # Wrap dashboard JSON in required format
  local payload=$(cat <<EOF
{
  "dashboard": $(cat "$file"),
  "overwrite": true,
  "message": "Imported via automation"
}
EOF
)
  
  response=$(curl -sS -X POST "${GRAFANA_URL}/api/dashboards/db" \
    -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$payload")
  
  if printf '%s' "$response" | grep -q '"status":"success"'; then
    printf 'OK\n'
  else
    printf 'FAIL\n'
    printf '  Response: %s\n' "$response"
    return 1
  fi
}

printf '%s\n' "NeuroForge Dashboard Import"
printf '%s\n' "==========================="
printf '\n'

# Import all dashboards
import_one "$SCRIPT_DIR/dashboards/redaction_dashboard.json"
import_one "$SCRIPT_DIR/dashboards/ops_window_dashboard.json"
import_one "$SCRIPT_DIR/dashboards/rag_performance_dashboard.json"

printf '\n%s\n' "========================================" 
printf '%s\n' "OK: All dashboards imported"
printf '\n%s\n' "Access at: ${GRAFANA_URL}/dashboards"
