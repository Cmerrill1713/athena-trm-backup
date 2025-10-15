#!/usr/bin/env bash
set -euo pipefail
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.athena-governance.yml}"
STACK_NAME="${STACK_NAME:-athena-governance}"
PROM_URL="${PROM_URL:-http://localhost:9090}"

echo "[deploy] running pre-deploy governance gate..."
python3 scripts/gov_predeploy_gate.py

echo "[deploy] bringing up ${STACK_NAME}..."
docker compose -f "$COMPOSE_FILE" pull
docker compose -f "$COMPOSE_FILE" up -d

echo "[deploy] waiting 30s, then verifying canary window..."
sleep 30

# Optional: hit canary API or just sanity check metrics exist
curl -sf ${PROM_URL}/-/healthy >/dev/null || { echo "Prometheus not healthy"; exit 1; }

echo "[deploy] ✅ deploy started; monitor canary dashboards/alerts."
