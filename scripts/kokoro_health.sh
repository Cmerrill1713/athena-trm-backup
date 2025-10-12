#!/bin/bash
# Quick health check for Kokoro TTS server

KOKORO_URL="http://127.0.0.1:8020"

# Try health endpoint with 2-second timeout
if curl -fsS -m 2 "$KOKORO_URL/health" > /dev/null 2>&1; then
    echo "✅ Kokoro is UP"
    curl -s "$KOKORO_URL/health" | jq -r '"🎤 Model: \(.model), Voices: \(.voices | join(", "))"'
    exit 0
else
    echo "❌ KOKORO_DOWN"
    echo "   Start with: make kokoro-start"
    exit 1
fi

