#!/usr/bin/env bash
# FastVLM Warmup - Send tiny image to warm up model at boot
# Run this after FastVLM starts to make first user request fast

set -e

echo "🔥 Warming up FastVLM..."

# Wait for FastVLM to be ready
for i in {1..30}; do
    if curl -sf http://127.0.0.1:8811/health >/dev/null 2>&1; then
        echo "✅ FastVLM is up"
        break
    fi
    sleep 2
done

# Create 1x1 test image
TEMP_IMG=$(mktemp --suffix=.png)
# Create tiny 1x1 transparent PNG
echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$TEMP_IMG"

# Send warmup request
echo "Sending warmup request..."
curl -sf -X POST http://127.0.0.1:8811/v1/vision \
  -F "image=@$TEMP_IMG" \
  -F 'prompt=test' >/dev/null 2>&1 && echo "✅ Warmup complete" || echo "⚠️  Warmup failed (model may still be loading)"

# Cleanup
rm -f "$TEMP_IMG"

echo "🎯 FastVLM ready for user requests"
