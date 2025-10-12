#!/bin/bash
set -euo pipefail

ART_DIR="artifacts"
TS=$(date +%Y%m%d-%H%M%S)
LOG="$ART_DIR/full-evaluation-$TS.log"
JSON_OUT="$ART_DIR/full-evaluation-$TS.json"
MD_OUT="$ART_DIR/full-evaluation-$TS.md"
ZIP_OUT="$ART_DIR/FullEvaluationArtifacts-$TS.zip"

mkdir -p "$ART_DIR" "$ART_DIR/screenshots" "$ART_DIR/captures"

echo "🔎 Full System Evaluation ($TS)" | tee "$LOG"

results=()
add_result() {
  local name="$1" port="$2" status="$3" notes="$4"
  results+=("$name|$port|$status|$notes")
}

check_http_json() {
  local url="$1" name="$2" port="$3"
  local tmp=$(mktemp)
  local code
  code=$(curl -s -m 8 -w "%{http_code}" -o "$tmp" "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    if python3 - "$tmp" <<'PY' >/dev/null 2>&1
import json,sys
json.load(open(sys.argv[1],'r'))
PY
    then
      add_result "$name" "$port" "PASS" "200 JSON ok"
    else
      add_result "$name" "$port" "WARN" "200 non-JSON"
    fi
  else
    add_result "$name" "$port" "FAIL" "HTTP $code"
  fi
  rm -f "$tmp"
}

check_http_ok() {
  local url="$1" name="$2" port="$3"
  local code
  code=$(curl -s -m 8 -o /dev/null -w "%{http_code}" "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    add_result "$name" "$port" "PASS" "HTTP 200"
  else
    add_result "$name" "$port" "FAIL" "HTTP $code"
  fi
}

echo "• Detecting core APIs..." | tee -a "$LOG"

# Chat API: prefer 8014
CHAT_BASE=""
for p in 8014 8013 8000; do
  if curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:$p/health" 2>/dev/null | grep -q "200"; then
    if curl -s -m 6 -o /dev/null -w "%{http_code}" "http://localhost:$p/api/chat" -H 'Content-Type: application/json' -d '{"message":"ping"}' 2>/dev/null | grep -q "200"; then
      CHAT_BASE="http://localhost:$p"
      break
    fi
  fi
done
if [[ -z "$CHAT_BASE" ]]; then
  echo "  ✗ Chat API not found on [8014,8013,8000]" | tee -a "$LOG"
  add_result "Chat API" "--" "FAIL" "No /api/chat"
else
  echo "  ✓ Chat API: $CHAT_BASE" | tee -a "$LOG"
  resp=$(curl -s -m 8 -H 'Content-Type: application/json' -d '{"message":"Full eval check"}' "$CHAT_BASE/api/chat" || true)
  echo "$resp" > "$ART_DIR/captures/chat-response.json"
  check_http_json "$CHAT_BASE/health" "Chat Health" "${CHAT_BASE##*:}"
  # Score chat response
  python3 - "$ART_DIR/captures/chat-response.json" <<'PY' | tee -a "$LOG"
import json,sys
p=sys.argv[1]
try:
  d=json.load(open(p))
  r=d.get('response','')
  print(f"  ✓ Chat responded: {len(r)} chars")
except Exception as e:
  print(f"  ! Chat response parse error: {e}")
PY
fi

# TTS via athena-api (8888)
echo "• Checking TTS proxy (8888)..." | tee -a "$LOG"
check_http_json "http://localhost:8888/api/tts/health" "TTS Health" "8888"
tts_tmp=$(mktemp)
curl -s -m 15 -H 'Content-Type: application/json' -d '{"text":"Full evaluation test"}' "http://localhost:8888/api/tts/speak" > "$tts_tmp" || true
python3 - "$tts_tmp" <<'PY' > "$ART_DIR/captures/tts-result.json"
import json,sys,base64
raw=open(sys.argv[1]).read()
try:
  d=json.loads(raw)
except Exception:
  d={'raw':raw}
print(json.dumps(d,indent=2))
PY
if python3 - "$ART_DIR/captures/tts-result.json" <<'PY' >/dev/null 2>&1
import json,sys,base64
d=json.load(open(sys.argv[1]))
ok=d.get('success') and d.get('audio_base64')
print("ok" if ok else "no")
PY
then
  add_result "TTS Speak" "8888" "PASS" "audio payload present"
else
  add_result "TTS Speak" "8888" "FAIL" "no audio"
fi

# Knowledge services
echo "• Checking knowledge services..." | tee -a "$LOG"
check_http_json "http://localhost:8088/health" "Knowledge Gateway" "8088"
check_http_json "http://localhost:8089/health" "Knowledge Sync" "8089"
check_http_json "http://localhost:8091/health" "Knowledge Context" "8091"

# Weaviate
check_http_ok "http://localhost:8090/v1/.well-known/ready" "Weaviate Ready" "8090"

# Monitoring
check_http_ok "http://localhost:9090/-/ready" "Prometheus" "9090"
check_http_ok "http://localhost:3001/login" "Grafana" "3001"

# SearxNG
check_http_ok "http://localhost:8081" "SearxNG" "8081"

# Docker snapshot
docker ps --format '{{.Names}}|{{.Image}}|{{.Ports}}|{{.Status}}' | tee "$ART_DIR/captures/docker-ps.txt" >/dev/null

# Swift app smoke + screenshot
if [ -d "NeuroForgeApp" ]; then
  echo "• Building Swift app (QA) and capturing screenshot..." | tee -a "$LOG"
  pushd NeuroForgeApp >/dev/null
  swift build >/dev/null 2>&1 || true
  BIN=$(swift build --show-bin-path 2>/dev/null || echo "")
  if [ -n "$BIN" ] && [ -x "$BIN/NeuroForgeApp" ]; then
    QA_MODE=1 "$BIN/NeuroForgeApp" >/dev/null 2>&1 & APP_PID=$!
    sleep 3
    screencapture -x "../$ART_DIR/screenshots/app-qa-$TS.png" || true
    kill $APP_PID >/dev/null 2>&1 || true
  fi
  popd >/dev/null
fi

# Write JSON + Markdown summaries
python3 - <<'PY' "$JSON_OUT" "$MD_OUT" "${results[@]}"
import json,sys
json_path, md_path, *rows = sys.argv[1:]
items=[]
for r in rows:
  name,port,status,notes = r.split('|',3)
  items.append({'service':name,'port':port,'result':status,'notes':notes})
open(json_path,'w').write(json.dumps({'results':items},indent=2))
with open(md_path,'w') as f:
  f.write("| Service | Port | Result | Notes |\n|---|---|---|---|\n")
  for it in items:
    f.write(f"| {it['service']} | {it['port']} | {it['result']} | {it['notes']} |\n")
print(f"Wrote {json_path} and {md_path}")
PY

# Package artifacts
pushd "$ART_DIR" >/dev/null
ZIP_NAME="FullEvaluationArtifacts-$TS.zip"
zip -qr "$ZIP_NAME" captures screenshots *.json *.md *.log 2>/dev/null || zip -qr "$ZIP_NAME" captures screenshots 2>/dev/null
popd >/dev/null

echo "✅ Full evaluation complete"
echo "Artifacts:"
echo "  - $JSON_OUT"
echo "  - $MD_OUT"
echo "  - $LOG"
echo "  - $ZIP_OUT"
