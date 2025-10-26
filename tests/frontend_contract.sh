#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "Frontend Contract Test - Verify Typing & Focus"
echo "════════════════════════════════════════════════════════════════"

APP_BIN=$(ls -td ~/Library/Developer/Xcode/DerivedData/NeuroForgeApp-*/Build/Products/Debug/NeuroForgeApp.app/Contents/MacOS/NeuroForgeApp 2>/dev/null | head -n1)

if [ ! -x "$APP_BIN" ]; then
    echo "❌ Build missing. Run: xcodebuild -project NeuroForgeApp/NeuroForgeApp.xcodeproj -scheme NeuroForgeApp -configuration Debug"
    exit 1
fi

echo -e "\n== 1. Launch App"
pkill -x NeuroForgeApp || true
sleep 1
"$APP_BIN" &
APP_PID=$!
sleep 3
echo "✅ App launched (PID: $APP_PID)"

echo -e "\n== 2. Gateway Metrics Baseline"
B=$(curl -s http://127.0.0.1:8015/metrics 2>/dev/null | grep -Eo 'llm_gateway_calls_total[^ ]* [0-9\.]+' | awk '{print $NF}' | head -n1 || echo "0")
echo "Baseline: $B calls"

echo -e "\n== 3. MCP Typing Probe (3 cycles)"
PROBE_RESULT=$(curl -s -X POST http://localhost:8413/tool/ui_typing_probe \
  -H 'content-type: application/json' \
  -d '{
    "bundle_id": "com.neuroforge.NeuroForgeApp",
    "text": "AGI contract test",
    "send": "enter",
    "repeat": 3
  }' 2>/dev/null || echo '{"success": false}')

echo "$PROBE_RESULT" | jq .

PROBE_SUCCESS=$(echo "$PROBE_RESULT" | jq -r '.success // false')
if [ "$PROBE_SUCCESS" != "true" ]; then
    echo "❌ Typing probe failed"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Typing probe passed"

echo -e "\n== 4. Gateway Metrics After"
sleep 2
A=$(curl -s http://127.0.0.1:8015/metrics 2>/dev/null | grep -Eo 'llm_gateway_calls_total[^ ]* [0-9\.]+' | awk '{print $NF}' | head -n1 || echo "0")
echo "After: $A calls"

echo -e "\n== 5. Verify Metrics Increment"
python3 - <<PY
b = float("${B}" or 0)
a = float("${A}" or 0)
if a <= b:
    print(f"❌ Gateway calls did not increase: before={b} after={a}")
    exit(1)
print(f"✅ Metrics incremented: {b} -> {a}")
PY

echo -e "\n== 6. Cleanup"
kill $APP_PID 2>/dev/null || true

echo -e "\n════════════════════════════════════════════════════════════════"
echo "✅ Frontend Contract Test PASSED"
echo "════════════════════════════════════════════════════════════════"
