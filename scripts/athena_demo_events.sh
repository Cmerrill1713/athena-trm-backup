#!/usr/bin/env bash
set -euo pipefail

API="${ATHENA_API:-http://localhost:8787}"
TOKEN="${ATHENA_API_TOKEN:-test}"

echo "🎬 Firing demo events at $API..."

# Check if backend is up
if ! curl -sf "$API/healthz" >/dev/null 2>&1; then
  echo "⚠️  Backend not responding at $API"
  echo "   Start backend first: make backend-dev"
  exit 0
fi

echo "📢 Sending Critical Alert..."
curl -sS -X POST "$API/alerts/critical" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "severity":"critical",
    "title":"DB p95 latency breach",
    "affectedSystems":["db-primary","api"],
    "recommendedActions":["acknowledge","investigate"]
  }' >/dev/null

sleep 0.5

echo "⚖️  Sending Tribunal Decision..."
curl -sS -X POST "$API/governance/tribunal" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "summary":"Router rollback decision",
    "recommendation":"Uphold",
    "confidence":0.82,
    "deadline":30
  }' >/dev/null

sleep 0.5

echo "🚨 Sending Emergency Alert..."
curl -sS -X POST "$API/system/emergency" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "riskLevel":"high",
    "countdownSec":10,
    "actions":["pause federation","scale core"]
  }' >/dev/null

echo "✅ Demo events sent successfully"
echo "   Watch for pop-outs in Athena app!"

