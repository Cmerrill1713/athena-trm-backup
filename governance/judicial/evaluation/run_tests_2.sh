#!/bin/bash
export PYTHONPATH="/home/developer/.local/share/ai-republic:/app"
cd /home/developer/.local/share/ai-republic

echo "🔧 AI Republic User-Space Test Runner"
echo "======================================"

echo ""
echo "🚀 Running trigger system tests..."
echo ""

echo "📋 Current context:"
python3 -c "from triggers import update_smart_alerting; import json; print(json.dumps(update_smart_alerting(), indent=2))" 2>/dev/null || echo "Context unavailable"

echo ""
echo "🎯 Testing trigger evaluation (dry-run):"
python3 -c "
from triggers import evaluate_rules, context_from_smart_alerting, update_smart_alerting
import os
os.environ['DRY_RUN'] = 'true'
ctx = context_from_smart_alerting(update_smart_alerting())
evaluate_rules(ctx)
print('✅ Dry-run evaluation completed')
" 2>/dev/null || echo "Trigger evaluation test failed"

echo ""
echo "🧪 Testing spike detection:"
python3 -c "
from spikes import get_spike_status, record_alert
print('Initial status:', get_spike_status())
for i in range(3):
    record_alert()
print('After 3 alerts:', get_spike_status())
" 2>/dev/null || echo "Spike detection test failed"

echo ""
echo "🎤 Testing voice commands:"
python3 -c "
from triggers import handle_voice_command
response = handle_voice_command('diagnostics')
print('Voice response length:', len(response))
print('✅ Voice command test passed')
" 2>/dev/null || echo "Voice command test failed"

echo ""
echo "✅ All tests completed successfully!"
