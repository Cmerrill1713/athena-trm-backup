#!/usr/bin/env bash
# Final 10-Minute Pre-Publish Sanity Check
set -euo pipefail

echo "🔍 PRE-PUBLISH SANITY CHECK"
echo "=========================================="
echo "This is the FINAL gate before publish"
echo ""

cd "$(dirname "$0")/.."

PASS=0
FAIL=0

# ========================================
# 1. DMG Verification
# ========================================
echo "1️⃣  DMG Verification"
echo "   (Manual: Verify on clean Mac)"
echo "   [ ] DMG opens without Gatekeeper warnings"
echo "   [ ] App launches successfully"
echo "   [ ] First-Run Wizard completes"
echo "   [ ] Offline lock shows as ON"
echo ""
read -p "   Press Enter if DMG verified on clean Mac..."
((PASS++))

# ========================================
# 2. Live API Calls
# ========================================
echo ""
echo "2️⃣  Live API Calls (2 capabilities)"
echo "   Starting API..."

# Start API in background
python3 -m uvicorn api:app --host 127.0.0.1 --port 8765 &
API_PID=$!
sleep 3

# Test summarize
echo "   Testing: summarize..."
SUMM_RESULT=$(curl -s -X POST http://127.0.0.1:8765/capability/summarize \
  -H 'Content-Type: application/json' \
  -d '{"record":{"id":"TEST-1","subject":"Test","body":"Hello"},"params":{}}')

SUMM_SCORE=$(echo "$SUMM_RESULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for event in data.get('trace', {}).get('events', []):
    if event['label'] == 'primary_result':
        print(event['data']['score'])
        break
" 2>/dev/null || echo "0")

if (( $(echo "$SUMM_SCORE >= 0.70" | bc -l) )); then
    echo "   ✅ summarize: score $SUMM_SCORE ≥ 0.70"
    ((PASS++))
else
    echo "   ❌ summarize: score $SUMM_SCORE < 0.70"
    ((FAIL++))
fi

# Test plan
echo "   Testing: plan..."
PLAN_RESULT=$(curl -s -X POST http://127.0.0.1:8765/capability/plan \
  -H 'Content-Type: application/json' \
  -d '{"record":{"id":"TEST-2","subject":"Plan test","body":"Create a plan"},"params":{}}')

PLAN_SCORE=$(echo "$PLAN_RESULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for event in data.get('trace', {}).get('events', []):
    if event['label'] == 'primary_result':
        print(event['data']['score'])
        break
" 2>/dev/null || echo "0")

if (( $(echo "$PLAN_SCORE >= 0.70" | bc -l) )); then
    echo "   ✅ plan: score $PLAN_SCORE ≥ 0.70"
    ((PASS++))
else
    echo "   ❌ plan: score $PLAN_SCORE < 0.70"
    ((FAIL++))
fi

# Cleanup
kill $API_PID 2>/dev/null || true

# ========================================
# 3. Bandit Snapshot
# ========================================
echo ""
echo "3️⃣  Bandit & Telemetry Snapshot"

mkdir -p ../releases/v0.9.2

if [ -f "state/bandit.json" ]; then
    cp state/bandit.json ../releases/v0.9.2/bandit-launch.json
    echo "   ✅ Bandit snapshot saved"
    ((PASS++))
else
    echo "   ❌ Bandit state not found"
    ((FAIL++))
fi

if [ -f "state/telemetry.sqlite" ]; then
    cp state/telemetry.sqlite ../releases/v0.9.2/telemetry-launch.sqlite
    echo "   ✅ Telemetry snapshot saved"
    ((PASS++))
else
    echo "   ⚠️  Telemetry DB not found (acceptable if first run)"
    ((PASS++))
fi

# ========================================
# 4. Shadow Configuration
# ========================================
echo ""
echo "4️⃣  Shadow Execution Configuration"

SHADOW_SUMM=$(grep -A 3 "summarize:" policies.yaml | grep "shadow_percent" | awk '{print $2}' || echo "0.0")
SHADOW_PLAN=$(grep -A 3 "plan:" policies.yaml | grep "shadow_percent" | awk '{print $2}' || echo "0.0")

echo "   summarize shadow: $SHADOW_SUMM"
echo "   plan shadow: $SHADOW_PLAN"

if (( $(echo "$SHADOW_SUMM >= 0.2" | bc -l) )) && (( $(echo "$SHADOW_PLAN >= 0.2" | bc -l) )); then
    echo "   ✅ Shadow rates configured (recommend 0.5 for first 24h)"
    ((PASS++))
else
    echo "   ⚠️  Shadow rates low (recommend 0.5 for launch)"
fi

# ========================================
# FINAL RESULT
# ========================================
echo ""
echo "=========================================="
echo "📊 SANITY CHECK RESULTS"
echo "=========================================="
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "READY TO PUBLISH! 🚀"
    echo ""
    echo "Next steps:"
    echo "  1. Create GitHub Release"
    echo "  2. Attach NeuroForge.dmg + checksum"
    echo "  3. Attach state snapshots"
    echo "  4. Use RELEASE_NOTES_TEMPLATE.md"
    echo "  5. Publish!"
    echo ""
    exit 0
else
    echo "❌ SANITY CHECK FAILED"
    echo ""
    echo "Fix issues before publishing!"
    echo ""
    exit 1
fi
