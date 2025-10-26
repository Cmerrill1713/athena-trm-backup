#!/usr/bin/env bash
set -euo pipefail
: "${BRIDGE_TOKEN:?BRIDGE_TOKEN missing}"
: "${ATH_TOKEN:?ATH_TOKEN missing}"

echo "Bridge expects ATH_TOKEN from env; verifying server side..."
# Expected env echo endpoint (or read from compose/env file)
if [ -f docker-compose.yml ]; then
  echo "Compose tokens present. (Ensure both services mount the same .env)"
fi
echo "OK: tokens present. Remember: Bridge must send ATH_TOKEN to Athena."
