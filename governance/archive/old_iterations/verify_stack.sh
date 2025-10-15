#!/usr/bin/env bash
set -euo pipefail

BASE_BRIDGE=${BASE_BRIDGE:-http://127.0.0.1:8014}
TOKEN=${BRIDGE_TOKEN:-}

h() { code=$(curl -s -o /dev/null -w "%{http_code}" "$1"); printf "%-40s %s\n" "$1" "$code"; }

echo "== Healthchecks =="
for u in \
  "$BASE_BRIDGE/health" \
  http://127.0.0.1:8090/health \
  http://127.0.0.1:8181/health \
  http://127.0.0.1:8015/ready \
  http://127.0.0.1:8016/ready \
  http://127.0.0.1:8020/health \
  http://127.0.0.1:8811/health \
  http://127.0.0.1:11434/api/tags \
  http://127.0.0.1:8080/v1/meta ; do
  h "$u"
done

echo "== Bridge chat (text/message/swift-kind) =="
HDR=(-H "Content-Type: application/json")
[ -n "$TOKEN" ] && HDR+=(-H "Authorization: Bearer $TOKEN")
curl -fsS "${HDR[@]}" -d '{"text":"ping"}'        "$BASE_BRIDGE/api/chat" | jq '.reply' >/dev/null
curl -fsS "${HDR[@]}" -d '{"message":"ping"}'     "$BASE_BRIDGE/api/chat" | jq '.reply' >/dev/null
curl -fsS "${HDR[@]}" -d '{"kind":"chat","text":"ping"}' "$BASE_BRIDGE/api/chat" | jq '.reply' >/dev/null
echo "Bridge chat OK"

echo "== RAG / Vision / TTS spot checks =="
curl -fsS -X POST http://127.0.0.1:8015/api/rag/query -H "Content-Type: application/json" -d '{"query":"test","k":1}' | head -c 80 >/dev/null && echo "RAG OK"

# Vision requires proper image data
echo '{"kind":"vision.describe","prompt":"test","imageBase64":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="}' | \
  curl -fsS -X POST http://127.0.0.1:8016/api/vision/describe -H "Content-Type: application/json" -d @- | head -c 80 >/dev/null && echo "Vision OK"

curl -fsS -X POST http://127.0.0.1:8020/synthesize -H "Content-Type: application/json" -d '{"text":"hello","voice":"af_heart"}' | head -c 80 >/dev/null && echo "Kokoro TTS OK"

echo "== MCP Store sanity =="
if curl -fsS http://127.0.0.1:8411/health 2>/dev/null | jq -e '.ok==true' >/dev/null 2>&1; then
  echo "MCP Store health OK"
  curl -fsS -H 'Content-Type: application/json' \
    -d '{"agent":"verifier","service":"bridge","status":"PASS","summary":"post-ship verify"}' \
    http://127.0.0.1:8411/v1/store/results | jq -r '.id' >/dev/null && echo "MCP Store write OK"
else
  echo "MCP Store not available (optional)"
fi

echo "== DONE =="
echo "✅ All critical services verified"
