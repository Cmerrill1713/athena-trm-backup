#!/bin/bash
# Demo: Zone Chaining & Predictive Location Awareness
# Shows how AI Republic learns your movement patterns and predicts next locations

echo "🧠 AI Republic Zone Chaining & Predictive Awareness Demo"
echo "======================================================="
echo ""

# Test 1: Learning location patterns
echo "🧪 Test 1: Learning Location Patterns"
echo "Simulating visits to different locations to train the system..."
echo ""

# Create some fake GPS data to simulate learning
echo "Simulating 5 visits to home location..."
for i in {1..5}; do
    GPS_OVERRIDE="40.7128,-74.0060" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
os.environ['ZONE_CHAINING_ENABLED'] = 'true'
from athena_notifications import learn_location_patterns
learn_location_patterns()
print(f'Visit {os.environ.get(\"i\", \"?\")} recorded')
    " &
done
wait

echo ""
echo "Simulating 4 visits to work location..."
for i in {1..4}; do
    GPS_OVERRIDE="40.7589,-73.9851" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7589,-73.9851'
from athena_notifications import learn_location_patterns
learn_location_patterns()
print(f'Work visit recorded')
    " &
done
wait

echo ""
echo "Simulating 3 visits to coffee shop..."
for i in {1..3}; do
    GPS_OVERRIDE="40.7505,-73.9934" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7505,-73.9934'
from athena_notifications import learn_location_patterns
learn_location_patterns()
print(f'Coffee shop visit recorded')
    " &
done
wait

echo ""
echo "Checking learned locations..."
python3 -c "
import json
try:
    with open('/tmp/ai_republic_location_patterns.json', 'r') as f:
        patterns = json.load(f)
        print('📍 Learned Locations:')
        for loc_key, loc_data in patterns.get('locations', {}).items():
            visits = loc_data.get('visits', 0)
            if visits >= 3:  # Only show frequently visited
                coords = loc_data.get('coordinates', [])
                print(f'  • {loc_key}: {visits} visits at {coords}')
except Exception as e:
    print(f'❌ Error reading patterns: {e}')
"

echo ""

# Test 2: Location profile detection
echo "🧪 Test 2: Location Profile Detection"
echo "Testing how the system categorizes learned locations..."
echo ""

GPS_OVERRIDE="40.7128,-74.0060" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
from athena_notifications import get_location_alert_profile
import json
profile = get_location_alert_profile('learned')
print('🏠 Home location profile:')
print(json.dumps(profile, indent=2))
"

echo ""

GPS_OVERRIDE="40.7505,-73.9934" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7505,-73.9934'
from athena_notifications import get_location_alert_profile
import json
profile = get_location_alert_profile('learned')
print('☕ Coffee shop location profile:')
print(json.dumps(profile, indent=2))
"

echo ""

# Test 3: Predictive awareness
echo "🧪 Test 3: Predictive Awareness"
echo "Testing prediction of next location based on current position..."
echo ""

echo "Predicting from home location..."
GPS_OVERRIDE="40.7128,-74.0060" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
from athena_notifications import predict_next_location
import time
prediction = predict_next_location('home', time.time())
print('🔮 Prediction from home:')
print(f'  Next location: {prediction.get(\"location\", \"unknown\")}')
print(f'  Confidence: {prediction.get(\"confidence\", 0.0):.2f}')
print(f'  ETA: {prediction.get(\"eta_seconds\", 0)/60:.1f} minutes')
"

echo ""
echo "Predicting from work location..."
GPS_OVERRIDE="40.7589,-73.9851" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7589,-73.9851'
from athena_notifications import predict_next_location
import time
prediction = predict_next_location('work', time.time())
print('🔮 Prediction from work:')
print(f'  Next location: {prediction.get(\"location\", \"unknown\")}')
print(f'  Confidence: {prediction.get(\"confidence\", 0.0):.2f}')
print(f'  ETA: {prediction.get(\"eta_seconds\", 0)/60:.1f} minutes')
"

echo ""

# Test 4: Complete context with predictive awareness
echo "🧪 Test 4: Complete Context with Predictive Awareness"
echo "Showing full smart alerting context including predictions..."
echo ""

GPS_OVERRIDE="40.7128,-74.0060" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
from athena_notifications import update_smart_alerting
import json
context = update_smart_alerting()
print('🎯 Full Context with Predictive Awareness:')
print(json.dumps(context, indent=2))
"

echo ""

echo "🎯 Zone Chaining Demo Complete!"
echo ""
echo "Zone Chaining Features Demonstrated:"
echo "🧠 Pattern Learning: System learned frequently visited locations"
echo "🏷️ Profile Detection: Automatic categorization (home-like, work-like, recurring)"
echo "🔮 Predictive Awareness: Movement pattern prediction with confidence scores"
echo "⚡ Real-time Context: Full alerting context including predictions"
echo ""
echo "Real-World Benefits:"
echo "• 📍 Auto-recognizes favorite coffee shop, gym, etc."
echo "• 🔮 Pre-loads appropriate alert modes before you arrive"
echo "• 🧭 Reduces context-switching friction during commutes"
echo "• 📊 Learns and adapts to your movement patterns over time"
echo ""
echo "Configuration:"
echo "• Enable: ZONE_CHAINING_ENABLED=true"
echo "• Threshold: LEARNING_THRESHOLD=3 (visits to learn location)"
echo "• Horizon: PREDICTIVE_HORIZON_HOURS=2 (hours to predict ahead)"
echo "• Confidence: CHAIN_CONFIDENCE_THRESHOLD=0.7 (70% minimum)"
echo ""
echo "Test with: ./smart_alerting_config.sh (options 11-12)"
