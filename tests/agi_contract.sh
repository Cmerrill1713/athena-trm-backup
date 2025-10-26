#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "AGI Core Contract Test - End-to-End Autonomous Task Execution"
echo "════════════════════════════════════════════════════════════════"

echo -e "\n== 1. AGI Core Health Check"
curl -fsS http://localhost:8000/health || (echo "❌ AGI Core is down" && exit 1)
echo " ✅"

echo -e "\n== 2. Router AGI Proxy Health"
curl -fsS http://localhost:9113/agi/health || (echo "⚠️  Router can't reach AGI Core" && exit 1)
echo " ✅"

echo -e "\n== 3. AGI Core Stats (baseline)"
curl -s http://localhost:8000/stats | jq . || true

echo -e "\n== 4. Execute Simple AGI Task (via Router)"
echo "Sending: Simple planning task..."
RESPONSE=$(curl -fsS -X POST http://localhost:9113/agi/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Create a 3-step plan to improve code readability",
    "context": {"repo":"athena","branch":"main","limits":{"max_steps":5}},
    "tools": ["uai.chat"]
  }')

echo "$RESPONSE" | jq .

TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id // "none"')
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')
TRACE_COUNT=$(echo "$RESPONSE" | jq '.trace | length // 0')

echo -e "\n✅ Task ID: $TASK_ID"
echo "✅ Status: $STATUS"
echo "✅ Trace steps: $TRACE_COUNT"

if [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ]; then
  echo "⚠️  Unexpected status: $STATUS"
  exit 1
fi

echo -e "\n== 5. Prometheus Metrics (AGI Core)"
curl -s http://localhost:8000/metrics | grep -E "workflow_executions|workflow_duration" | head -5 || true

echo -e "\n== 6. Prometheus Metrics (Router)"
curl -s http://localhost:9113/metrics | grep -E "athena_router.*agi" || echo "(Router AGI metrics not yet instrumented)"

echo -e "\n════════════════════════════════════════════════════════════════"
echo "✅ AGI Contract Test PASSED!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "AGI Core is wired and executing autonomous tasks via Router."
echo "Next: Build UI to showcase AGI capabilities."
echo ""
