#!/usr/bin/env bash
# Orchestrator Preflight - Validates capability SLAs
set -euo pipefail

echo "🔍 Preflight (capability SLAs)"
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
    "body": "Validate orchestration SLAs",
    "sla_mins_left": 999
}

passed = 0
failed = 0

for cap in ("summarize", "plan"):
    print("\\n Testing {} capability...".format(cap))

    try:
        res = run_capability(cap, record, {"max_tokens": 128})
        out = res["output"]
        trace = res["trace"]

        # Check required fields
        assert out.get("tldr") is not None, "{} missing tldr".format(cap)
        assert out.get("next_action") is not None, "{} missing next_action".format(cap)

        # Check latency SLA
        lat = out.get("metrics", {}).get("latency_ms", 99999)
        assert lat <= 1500, "{} latency too high: {}ms (max 1500ms)".format(cap, lat)

        # Check score
        score = None
        for event in trace.get("events", []):
            if event["label"] == "primary_result":
                score = event["data"].get("score", 0)
                break

        if score is not None:
            assert score >= 0.7, "{} score too low: {:.2f} (min 0.7)".format(cap, score)

        score_str = "{:.2f}".format(score) if score else "N/A"
        print("  ✅ {} OK (latency: {}ms, score: {})".format(cap, lat, score_str))
        passed += 1

    except AssertionError as e:
        print("  ❌ {} FAILED: {}".format(cap, e))
        failed += 1
    except Exception as e:
        print("  ❌ {} ERROR: {}".format(cap, e))
        failed += 1

print("\\n" + "="*50)
print("Preflight Results: {} passed, {} failed".format(passed, failed))

if failed == 0:
    print("🎉 Preflight OK - All SLAs met")
    sys.exit(0)
else:
    print("❌ Preflight FAILED - Fix issues before proceeding")
    sys.exit(1)
PY

exit_code=$?
if [[ $exit_code -eq 0 ]]; then
    echo ""
    echo "✅ PREFLIGHT PASSED"
    echo "Ready for build/packaging"
else
    echo ""
    echo "❌ PREFLIGHT FAILED"
    echo "Fix capability issues before proceeding"
fi

exit $exit_code
