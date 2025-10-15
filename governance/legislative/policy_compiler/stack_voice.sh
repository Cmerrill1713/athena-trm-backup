#!/bin/bash
# Athena Tool: Enable Kokoro voice service
set -e
cd "$(dirname "$0")/.."

echo "🎙️  Enabling voice (Kokoro TTS)..."
make stack-voice && make truth

curl -fs 127.0.0.1:8020/health && echo "✅ Kokoro voice ready" || echo "⚠️  Kokoro not responding"

