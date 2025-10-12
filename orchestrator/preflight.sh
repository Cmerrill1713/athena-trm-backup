#!/usr/bin/env bash
# Orchestrator Preflight - Blocks packaging when reality fails
set -euo pipefail

echo "🔍 Preflight (agent-agnostic orchestrator)"
echo "==========================================="

cd "$(dirname "$0")"

python3 - <<'PY'
import sys
sys.path.insert(0, ".")

from router import run_capability

# Test record
record = {
    "id": "PF-1",
    "subject": "Preflight check",
    "body": "Run capability checks",
    "sla_mins_left": 999
}

# Test summarize capability
print("Testing summarize capability...")
out1 = run_capability("summarize", record, {"max_tokens": 128})
assert out1["output"].get("tldr"), "❌ summarize failed"
print("✅ Summarize OK")

# Test plan capability
print("Testing plan capability...")
out2 = run_capability("plan", record, {})
assert out2["output"].get("next_action"), "❌ plan failed"
print("✅ Plan OK")

print("\n🎉 Preflight OK - All capabilities working")
PY

exit_code=$?
if [[ $exit_code -eq 0 ]]; then
    echo ""
    echo "✅ PREFLIGHT PASSED"
    echo "Ready to proceed with build/packaging"
else
    echo ""
    echo "❌ PREFLIGHT FAILED"
    echo "Fix capability issues before proceeding"
fi

exit $exit_code
