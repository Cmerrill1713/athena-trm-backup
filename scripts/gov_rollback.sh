#!/usr/bin/env bash
set -euo pipefail
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.athena-governance.yml}"
# Fast rollback path: restart services and point exec state to safe version
echo "[rollback] restarting services and restoring safe version marker..."
docker compose -f "$COMPOSE_FILE" restart governance-orchestrator
# If you persist state in a volume/file, you can reset it here:
SAFE_JSON='{"safe_version":"v1.8","current_version":"v1.8"}'
printf "%s" "$SAFE_JSON" > state/exec_state.json
echo "[rollback] ✅ done"
