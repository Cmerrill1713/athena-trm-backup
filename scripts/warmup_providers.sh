#!/usr/bin/env bash
# Warmup all providers - makes first user request fast
# Run this at boot or after starting services

set -e

echo "🔥 Warming up all providers..."
echo ""

# Wait for services to be ready
echo "[1/4] Waiting for services to start..."
sleep 5

# Warmup FastVLM (vision)
echo "[2/4] Warming up FastVLM..."
if curl -sf http://127.0.0.1:8811/health >/dev/null 2>&1; then
    # Create tiny 1x1 PNG
    TEMP_IMG=$(mktemp /tmp/warmup.XXXXXX.png)
    echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -D > "$TEMP_IMG"

    curl -sf -X POST http://127.0.0.1:8811/v1/vision \
      -F "image=@$TEMP_IMG" \
      -F 'prompt=test' >/dev/null 2>&1 && echo "  ✅ FastVLM warmed up" || echo "  ⚠️  FastVLM warmup failed"

    rm -f "$TEMP_IMG"
else
    echo "  ⚠️  FastVLM not running"
fi

# Warmup Ollama
echo "[3/4] Warming up Ollama..."
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    MODEL=$(curl -s http://localhost:11434/api/tags | jq -r '.models[0].name' 2>/dev/null)
    if [ -n "$MODEL" ]; then
        curl -sf http://localhost:11434/api/generate \
          -d "{\"model\":\"$MODEL\",\"prompt\":\"test\",\"stream\":false}" >/dev/null 2>&1 && echo "  ✅ Ollama warmed up ($MODEL)" || echo "  ⚠️  Ollama warmup failed"
    else
        echo "  ⚠️  No Ollama models found"
    fi
else
    echo "  ⚠️  Ollama not running"
fi

# Warmup Chat API
echo "[4/4] Warming up Chat API..."
if curl -sf http://127.0.0.1:8014/health >/dev/null 2>&1; then
    echo "  ✅ Chat API ready"
else
    echo "  ⚠️  Chat API not running"
fi

echo ""
echo "🎯 Warmup complete! All providers ready for fast user requests."
