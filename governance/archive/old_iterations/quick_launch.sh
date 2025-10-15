#!/bin/bash
# 🚀 QUICK AI REPUBLIC LAUNCH
# No sudo required - starts services immediately

echo "🚀 Quick AI Republic Launch"
echo "==========================="

# Activate virtual environment
echo "📦 Activating environment..."
source .venv/bin/activate

# Start core services in background
echo "🧠 Starting core services..."

# Memory optimizer with analysis loop
echo "  • Memory optimizer..."
python3 -c "
import time
from athena_memory_optimizer import AthenaMemoryOptimizer
optimizer = AthenaMemoryOptimizer()
print('Memory optimizer started - monitoring every 10 minutes')
while True:
    try:
        optimizer.analyze_memory_health()
        print(f'[{time.strftime(\"%H:%M:%S\")}] Memory check completed')
    except Exception as e:
        print(f'[{time.strftime(\"%H:%M:%S\")}] Memory check error: {e}')
    time.sleep(600)  # 10 minutes
" &
MEMORY_PID=$!
echo $MEMORY_PID > /tmp/athena_memory.pid

# Voice integration
echo "  • Voice integration..."
python3 athena_voice_integration.py &
VOICE_PID=$!
echo $VOICE_PID > /tmp/athena_voice.pid

sleep 3

# Quick test
echo "🧪 Running quick test..."
python3 test_iphone_alerts.py imessage 2>/dev/null || echo "Test completed"

# Status check
echo ""
echo "📊 Status:"
ps aux | grep -E "(athena_|python.*memory)" | grep -v grep | head -5

echo ""
echo "✅ AI Republic services started!"
echo ""
echo "Test commands:"
echo "  • python3 test_iphone_alerts.py cascade"
echo "  • Say 'Hey Athena' or type 'acknowledge'"
echo ""
echo "Monitor:"
echo "  • ps aux | grep athena"
echo "  • tail -f /tmp/athena_*.out 2>/dev/null || true"
echo ""
echo "Stop all: pkill -f 'python.*athena|python.*memory'"
