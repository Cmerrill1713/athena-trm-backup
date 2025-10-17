#!/bin/bash
# Start Kokoro-82M TTS server
# Port 8091 | Fast, high-quality text-to-speech

set -e

cd "$(dirname "$0")/../.."

export KOKORO_PORT=8091
export KOKORO_HOST=127.0.0.1
export KOKORO_VOICE=en_US-female
export PYTHONUNBUFFERED=1

echo "═══════════════════════════════════════════════════════════════════"
echo "🎙️  Starting Kokoro-82M TTS Server"
echo "═══════════════════════════════════════════════════════════════════"
echo "   Port: $KOKORO_PORT"
echo "   Host: $KOKORO_HOST"
echo "   Voice: $KOKORO_VOICE"
echo "   Model: Kokoro-82M (82M parameters)"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Check if kokoro is available
if python3 -c "import kokoro_onnx" 2>/dev/null; then
    echo "✅ Kokoro ONNX available"
elif python3 -c "import piper" 2>/dev/null; then
    echo "✅ Piper TTS available (alternative)"
else
    echo "⚠️  Kokoro not found - install with: pip install kokoro-onnx"
    echo "   Or use Piper: pip install piper-tts"
    echo "   Falling back to placeholder mode (silent audio)"
fi

# Start server
cd services/kokoro
python3 server.py

