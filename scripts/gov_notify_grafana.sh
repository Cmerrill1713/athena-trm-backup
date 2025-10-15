#!/usr/bin/env bash
set -euo pipefail
GRAFANA_URL="${GRAFANA_URL:?}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:?}"
STATUS="${1:-UNKNOWN}"; shift || true
TEXT="${*:-}"
curl -s -X POST "$GRAFANA_URL/api/annotations" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"text\":\"Governance: $STATUS - $TEXT\",\"tags\":[\"governance\",\"$STATUS\"]}" >/dev/null
