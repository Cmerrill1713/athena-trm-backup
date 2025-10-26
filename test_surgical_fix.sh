#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🔬 Testing Surgical Fixes - Undeniably Real AGI Demo"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "== 1. Frontend Tools Health"
curl -fsS http://localhost:8413/health | jq .
echo ""

echo "== 2. AGI Core Health"
curl -fsS http://localhost:8000/health | jq .
echo ""

echo "== 3. Execute AGI Task (expect 3-5 minute build + launch + probe)"
echo "   This will:"
echo "   • Invalidate cache (modify Swift source)"
echo "   • Clean build (3-5 min, fans spin)"
echo "   • Wait for binary to exist"
echo "   • Launch app frontmost"
echo "   • Run typing probe with transcript"
echo ""

curl -N -sS -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Build, launch, and verify typing focus with visible evidence",
    "context": {
      "repo_root": "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp"
    },
    "tools": [
      "mcp.shell",
      "frontend.xcode_build",
      "frontend.app_launch",
      "frontend.ui_typing_probe"
    ],
    "max_steps": 10
  }' | jq -C .

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Test complete! Check the trace for:"
echo "   • invalidator → tool_success (source modified)"
echo "   • builder → tool_success (duration >60s)"
echo "   • runner → tool_success (binary discovered, launched)"
echo "   • qa → tool_success (transcript with 3 cycles)"
echo "════════════════════════════════════════════════════════════════"


