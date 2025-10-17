#!/bin/bash
# Start FastVLM vision server
# Port 8088 | MLX-optimized vision-language model

set -e

cd "$(dirname "$0")/../.."

export FASTVLM_PORT=8088
export FASTVLM_HOST=127.0.0.1
export PYTHONUNBUFFERED=1

echo "═══════════════════════════════════════════════════════════════════"
echo "🔍 Starting FastVLM Server"
echo "═══════════════════════════════════════════════════════════════════"
echo "   Port: $FASTVLM_PORT"
echo "   Host: $FASTVLM_HOST"
echo "   Model: FastVLM (MLX-optimized)"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Check if fastvlm package is available
if python3 -c "import mlx" 2>/dev/null; then
    echo "✅ MLX available"
else
    echo "⚠️  MLX not found - install with: pip install mlx mlx-vlm"
    echo "   Falling back to placeholder mode"
fi

# Start server
cd services/fastvlm
python3 server.py

