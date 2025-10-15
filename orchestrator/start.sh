#!/bin/bash
set -e

echo "🎯 Starting Governance Orchestrator..."

# Run migrations or setup if needed
if [ ! -f "/app/state/exec_state.json" ]; then
    echo "📝 Initializing state file..."
    mkdir -p /app/state
    cat > /app/state/exec_state.json << 'STATE'
{
  "safe_version": "v1.8.0",
  "current_version": "v1.9.0-canary",
  "promotions_frozen_until": null,
  "freeze_promotions": false,
  "rollback_in_progress": false,
  "last_updated": 0.0
}
STATE
fi

# Start the service
exec python3 -m uvicorn app:app --host 0.0.0.0 --port ${ORCH_PORT:-8000}
