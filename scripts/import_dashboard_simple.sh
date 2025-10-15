#!/usr/bin/env bash
set -euo pipefail

# Simple dashboard import using basic auth
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
DASHBOARD_FILE="dashboards/trm_evolution_overview.json"

echo "📊 Importing TRM Evolution dashboard..."

# Wrap dashboard JSON in the required format
DASHBOARD_JSON=$(jq -n \
  --argfile dash "$DASHBOARD_FILE" \
  '{
    dashboard: $dash,
    folderId: 0,
    overwrite: true
  }')

# Import
RESPONSE=$(curl -s -X POST \
  "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d "$DASHBOARD_JSON")

echo "$RESPONSE" | jq

if echo "$RESPONSE" | jq -e '.status == "success"' >/dev/null 2>&1; then
  echo "✅ Dashboard imported successfully"
  DASH_URL=$(echo "$RESPONSE" | jq -r '.url')
  echo "   View at: ${GRAFANA_URL}${DASH_URL}"
else
  echo "❌ Import failed"
  exit 1
fi

