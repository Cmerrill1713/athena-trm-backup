#!/bin/bash
# Restart RAG, Vision, Kokoro with Prometheus metrics

set -e

echo "🔄 Restarting services with Prometheus metrics..."
echo ""

# Kill ALL processes on these ports (multiple attempts)
echo "🛑 Stopping existing services..."
for port in 8015 8016 8020; do
    # Try multiple times
    for i in {1..3}; do
        lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null || true
        sleep 1
    done
    echo "  ✅ Port $port cleared"
done

sleep 3

# Verify ports are free
echo ""
echo "🔍 Verifying ports are free..."
for port in 8015 8016 8020; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  ⚠️  Port $port still in use!"
    else
        echo "  ✅ Port $port is free"
    fi
done

sleep 2

# Start services
echo ""
echo "🚀 Starting services..."

cd /Users/christianmerrill/Documents/GitHub

# Start RAG
echo "  🚀 Starting RAG..."
source .venv/bin/activate
cd AI-Projects/universal-ai-tools
python rag_service.py > ../../logs/rag_metrics.log 2>&1 &
echo $! > ../../pids/rag.pid
cd ../..

sleep 4

# Start Vision
echo "  🚀 Starting Vision..."
cd AI-Projects/universal-ai-tools
python vision_rag_service.py > ../../logs/vision_metrics.log 2>&1 &
echo $! > ../../pids/vision.pid
cd ../..

sleep 4

# Start Kokoro
echo "  🚀 Starting Kokoro..."
cd kokoro
python kokoro_tts_service.py > ../logs/kokoro_metrics.log 2>&1 &
echo $! > ../pids/kokoro.pid
cd ..

echo ""
echo "⏳ Waiting 10 seconds for services to start..."
sleep 10

# Verify
echo ""
echo "🧪 Verifying services..."
python3 << 'PYEOF'
import requests

services = [
    ("RAG", "http://localhost:8015/metrics"),
    ("Vision", "http://localhost:8016/metrics"),
    ("Kokoro", "http://localhost:8020/metrics"),
]

for name, url in services:
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            print(f"  ✅ {name} - /metrics working")
        else:
            print(f"  ❌ {name} - Status {r.status_code}")
    except:
        print(f"  ❌ {name} - Not responding")
PYEOF

echo ""
echo "✅ Restart complete!"
echo "🌐 Check Prometheus targets: http://localhost:9091/targets"
