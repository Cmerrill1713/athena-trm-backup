#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🧠 Starting AGI Core"
echo "════════════════════════════════════════════════════════════════"

cd /Users/christianmerrill/Documents/GitHub

# Set environment
export PYTHONUNBUFFERED=1
export AGI_STATE_DIR=./state/agi
export MCP_URL=http://localhost:8412
export UAI_URL=http://localhost:8080
export GATEWAY_URL=http://localhost:8888
export FASTVLM_URL=http://localhost:8088
export KOKORO_URL=http://localhost:8091

echo "Starting AGI Core on port 8000..."
echo "Press Ctrl+C to stop"
echo "════════════════════════════════════════════════════════════════"
echo ""

python3 -m uvicorn agi_core.agi_service:app --host 0.0.0.0 --port 8000
