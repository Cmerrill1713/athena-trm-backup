#!/usr/bin/env bash
set -euo pipefail
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:?missing webhook}"
STATUS="${1:-UNKNOWN}"
shift || true
MSG="${*:-No details}"

payload=$(jq -n \
  --arg status "$STATUS" \
  --arg text "$MSG" \
  '{text: ("*Governance Decision:* " + $status + "\n" + $text)}')

curl -s -X POST -H 'Content-type: application/json' \
  --data "$payload" "$SLACK_WEBHOOK_URL" >/dev/null
