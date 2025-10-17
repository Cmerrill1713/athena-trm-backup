#!/bin/bash
# Safe app launcher with crash handling

pkill -9 NeuroForgeApp 2>/dev/null || true
sleep 1

cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp

echo "🚀 Building NeuroForgeApp..."
swift build

if [ $? -eq 0 ]; then
    echo "✅ Build successful"
    echo "🏃 Launching app..."
    .build/debug/NeuroForgeApp 2>&1 | tee /tmp/neuroforge.log &
    APP_PID=$!
    echo "📝 App PID: $APP_PID"
    echo "📋 Logs: /tmp/neuroforge.log"
    echo ""
    echo "To check logs: tail -f /tmp/neuroforge.log"
    echo "To kill app: kill $APP_PID"
else
    echo "❌ Build failed"
    exit 1
fi
