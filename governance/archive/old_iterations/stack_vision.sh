#!/bin/bash
# Athena Tool: Enable Vision analysis services
set -e
cd "$(dirname "$0")/.."

echo "👁️  Enabling vision services..."
make stack-vision && make truth

curl -fs 127.0.0.1:8016/api/vision/health && echo "✅ Vision service ready" || echo "⚠️  Vision not responding"

