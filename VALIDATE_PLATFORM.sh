#!/usr/bin/env bash
# Platform Validation - E2E Smoke Test
# Tests: Core + Voice + RAG + Vision + Monitoring

set -euo pipefail

# ------------------------
# Pretty helpers
# ------------------------
pass() { printf "✅ %s\n" "$1"; }
fail() { printf "❌ %s\n" "$1"; exit 1; }
warn() { printf "⚠️  %s\n" "$1"; }
info() { printf "ℹ️  %s\n" "$1"; }

# Check dependencies
REQ_CMDS=(curl jq awk grep sed)
for c in "${REQ_CMDS[@]}"; do 
    command -v "$c" >/dev/null 2>&1 || fail "Missing dependency: $c"
done

# Service URLs
API=${API_BASE:-http://127.0.0.1:8014}
ATH=${ATHENA_BASE:-http://127.0.0.1:8090}
UAT=${UAT_BASE:-http://127.0.0.1:8181}
KOK=${KOKORO_BASE:-http://127.0.0.1:8020}
RAG=${RAG_BASE:-http://127.0.0.1:8015}
VRAG=${VISION_RAG_BASE:-http://127.0.0.1:8016}
VLM=${FASTVLM_BASE:-http://127.0.0.1:8811}
WEAV=${WEAVIATE_BASE:-http://127.0.0.1:8095}
PROM=${PROM_BASE:-http://127.0.0.1:9090}
GRAF=${GRAF_BASE:-http://127.0.0.1:3001}

WAIT_UNTIL() {
    local url="$1" name="$2" tries="${3:-20}" sleep_s="${4:-0.5}"
    for i in $(seq 1 "$tries"); do
        if curl -fsS "$url" >/dev/null 2>&1; then 
            pass "$name ready ($url)"
            return 0
        fi
        sleep "$sleep_s"
    done
    fail "$name not ready ($url)"
}

HEADER() {
    echo ""
    printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    printf " %s\n" "$1"
    printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        PLATFORM VALIDATION - E2E Smoke Test                ║"
echo "╚════════════════════════════════════════════════════════════╝"

# ------------------------
# 0) Preflight
# ------------------------
HEADER "0) Preflight (stack status)"
if command -v make >/dev/null 2>&1; then
    make -s truth 2>/dev/null || warn "Truth check failed (continuing)"
else
    warn "make not found (skipping truth check)"
fi

# ------------------------
# 1) Core Services
# ------------------------
HEADER "1) Core Services"
WAIT_UNTIL "$API/ready" "Bridge"
WAIT_UNTIL "$ATH/ready" "Athena"
WAIT_UNTIL "$UAT/ready" "UAT"

# ------------------------
# 2) Meta Headers on Chat
# ------------------------
HEADER "2) Chat + Meta Headers"
CHAT_TMP="$(mktemp)"
HDR_TMP="$(mktemp)"

curl -sS -D "$HDR_TMP" -H 'Content-Type: application/json' \
  -X POST "$API/api/chat" \
  --data '{"kind":"smalltalk","text":"Run a tiny health check and summarize in one sentence."}' \
  -o "$CHAT_TMP" 2>/dev/null || fail "Chat endpoint failed"

# Check response has content
if jq -e '.text // .content // .message // empty' "$CHAT_TMP" >/dev/null 2>&1; then
    CONTENT="$(jq -r '.text? // .content? // .message? // empty' "$CHAT_TMP")"
    if [ -n "$CONTENT" ]; then
        pass "Chat response has content (${#CONTENT} chars)"
    else
        fail "Chat response empty content"
    fi
else
    fail "Chat JSON missing expected fields"
fi

# Check for meta headers
META_ENABLED="$(grep -i '^x-meta-enabled:' "$HDR_TMP" 2>/dev/null | awk '{print tolower($2)}' | tr -d '\r' || true)"
CONF_HEADER="$(grep -i '^x-meta-confidence:' "$HDR_TMP" 2>/dev/null | awk '{print $2}' | tr -d '\r' || true)"

if [ "$META_ENABLED" = "true" ] || [ -n "$CONF_HEADER" ]; then
    pass "Meta headers present (confidence: ${CONF_HEADER:-n/a})"
else
    warn "No meta headers (ensure META_PROMPTING=1 exported before stack-up)"
fi

rm -f "$CHAT_TMP" "$HDR_TMP"

# ------------------------
# 3) Kokoro TTS (Voice)
# ------------------------
HEADER "3) Voice (Kokoro TTS)"
if curl -fsS "$KOK/health" 2>/dev/null | jq -e '.status=="ok"' >/dev/null 2>&1; then
    AUDIO_TMP="/tmp/tts_validation.wav"
    curl -fsS -X POST "$KOK/tts" \
        -H 'Content-Type: application/json' \
        --data '{"text":"Athena voice check successful.","voice":"af_heart","format":"wav"}' \
        -o "$AUDIO_TMP" 2>/dev/null || warn "Kokoro TTS request failed"
    
    if [ -s "$AUDIO_TMP" ]; then
        SIZE=$(stat -f%z "$AUDIO_TMP" 2>/dev/null || stat -c%s "$AUDIO_TMP" 2>/dev/null || echo "0")
        pass "Kokoro TTS produced audio (${SIZE} bytes)"
    else
        warn "Kokoro returned empty audio"
    fi
else
    warn "Kokoro not running at $KOK (start: make stack-voice)"
fi

# ------------------------
# 4) RAG Layer
# ------------------------
HEADER "4) RAG Layer"
if curl -fsS "$RAG/ready" >/dev/null 2>&1; then
    pass "RAG service ready ($RAG)"
    curl -fsS "$RAG/health" >/dev/null 2>&1 || warn "RAG /health endpoint missing"
else
    warn "RAG service not up at $RAG (start: make stack-rag)"
fi

# ------------------------
# 5) Vision Layer
# ------------------------
HEADER "5) Vision Layer"
if curl -fsS "$VLM/health" >/dev/null 2>&1; then
    pass "FastVLM ready ($VLM)"
else
    warn "FastVLM not up at $VLM (start: make stack-vision)"
fi

if curl -fsS "$VRAG/ready" >/dev/null 2>&1; then
    pass "Vision-RAG ready ($VRAG)"
else
    warn "Vision-RAG not up at $VRAG (start: make stack-vision)"
fi

# ------------------------
# 6) Weaviate (Port Fix Verification)
# ------------------------
HEADER "6) Weaviate (Port 8095)"
if curl -fsS "$WEAV/v1/.well-known/ready" >/dev/null 2>&1; then
    pass "Weaviate ready on :8095 (port conflict fixed!)"
elif curl -fsS "$WEAV" >/dev/null 2>&1; then
    pass "Weaviate responding on :8095"
else
    warn "Weaviate not running on :8095 (optional - run if needed)"
fi

# Verify not on old port
if lsof -ti:8090 2>/dev/null | grep -v "$(pgrep -f 'athena.api' || echo 'x')" >/dev/null 2>&1; then
    warn "Something else on port 8090 (should only be Athena)"
fi

# ------------------------
# 7) Monitoring
# ------------------------
HEADER "7) Monitoring (Prometheus + Grafana)"
if curl -fsS "$PROM/-/ready" >/dev/null 2>&1; then
    pass "Prometheus ready ($PROM)"
else
    warn "Prometheus not running (start: make monitoring-up)"
fi

if curl -fsS -o /dev/null "$GRAF/login" 2>/dev/null; then
    pass "Grafana reachable ($GRAF)"
else
    warn "Grafana not running (start: make monitoring-up)"
fi

# ------------------------
# 8) Frontend Handshake
# ------------------------
HEADER "8) Frontend Handshake"
HEALTH_JSON="$(curl -fsS "$API/health" 2>/dev/null || true)"
if [ -n "$HEALTH_JSON" ]; then
    pass "Bridge /health reachable (frontend should show green)"
    echo "$HEALTH_JSON" | jq '.' 2>/dev/null || echo "$HEALTH_JSON"
else
    warn "Bridge /health not responding"
fi

# ------------------------
# 9) Meta Behavior Sweep
# ------------------------
HEADER "9) Meta Confidence Sweep (Low → High)"
info "Testing confidence evolution across prompts..."

probe_meta() {
    local prompt="$1"
    local hdr="$(mktemp)" body="$(mktemp)"
    
    curl -sS -D "$hdr" -H 'Content-Type: application/json' \
        -X POST "$API/api/chat" \
        --data "{\"kind\":\"reasoning\",\"text\":\"$prompt\"}" \
        -o "$body" 2>/dev/null || return 1
    
    local conf="$(grep -i '^x-meta-confidence:' "$hdr" 2>/dev/null | awk '{print $2}' | tr -d '\r' || echo 'n/a')"
    local style="$(grep -i '^x-meta-style:' "$hdr" 2>/dev/null | awk '{print $2}' | tr -d '\r' || echo 'n/a')"
    
    printf "  • %-45s conf=%-6s style=%s\n" "$prompt" "$conf" "$style"
    rm -f "$hdr" "$body"
}

probe_meta "logs?"
probe_meta "backend errors last 5 minutes"
probe_meta "run smoke tests and summarize failures"

pass "Meta behavior sweep complete"

# ------------------------
# Summary
# ------------------------
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║               VALIDATION COMPLETE ✅                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 Next Steps:"
echo "   • Launch frontend: cd NeuroForgeApp && API_BASE=$API QA_MODE=1 swift run"
echo "   • Check full status: make stack-status-full"
echo "   • View logs: tail -f logs/*.log"
echo ""
echo "⚠️  Warnings are OK if you didn't start those optional services"
echo "✅ Core services are all you need for basic chat"
echo ""

