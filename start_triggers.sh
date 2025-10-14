#!/bin/bash
# Athena Context Trigger Engine Startup Script
# Add to launchd for automatic startup

cd "$(dirname "$0")"

echo "🎯 Starting Athena Context Trigger Engine..."
echo "📊 Monitoring for time + location + calendar triggers"
echo "⚙️  Configuration:"
echo "   - Check interval: ${MACRO_CHECK_INTERVAL:-30}s"
echo "   - Cooldown: ${TRANSITION_COOLDOWN_SECONDS:-300}s"
echo "   - Hysteresis: ${HYSTERESIS_CONFIDENCE:-0.7}"
echo "   - Enabled: ${CONTEXT_MACROS_ENABLED:-true}"
echo ""

# Start the trigger engine
exec python3 triggers.py
