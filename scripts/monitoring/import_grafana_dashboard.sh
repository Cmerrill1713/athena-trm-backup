#!/usr/bin/env bash
set -euo pipefail
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3001}"
API_KEY="${GRAFANA_API_KEY:-}"
[ -z "${API_KEY}" ] && { echo "Set GRAFANA_API_KEY"; exit 1; }

curl -sS -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data "{\"dashboard\": $(cat dashboards/trm_evolution_overview.json), \"folderId\": 0, \"overwrite\": true}"

echo "✅ Imported TRM Evolution Overview"

