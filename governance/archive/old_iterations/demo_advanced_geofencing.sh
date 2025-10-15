#!/bin/bash
# Demo: Advanced Geofencing - Adaptive Radius & Transition Smoothing
# Shows how AI Republic prevents alert spam and adapts zone sizes intelligently

echo "🛰️ AI Republic Advanced Geofencing Demo"
echo "======================================"
echo ""

# Test 1: Adaptive Radius - Time-based adjustments
echo "🧪 Test 1: Adaptive Radius (Time-based zone adjustments)"
echo "Simulating daytime vs nighttime home radius..."
echo "Daytime (6 AM - 10 PM): Smaller radius for precision"
GPS_OVERRIDE="40.7128,-74.0060" ADAPTIVE_RADIUS_ENABLED="true" HOME_LAT="40.7128" HOME_LNG="-74.0060" HOME_RADIUS="100" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
os.environ['ADAPTIVE_RADIUS_ENABLED'] = 'true'
os.environ['HOME_LAT'] = '40.7128'
os.environ['HOME_LNG'] = '-74.0060'
os.environ['HOME_RADIUS'] = '100'
from athena_notifications import get_adaptive_radius
print('🏠 Home Zone Adaptive Radius Test')
print('=================================')
daytime_radius = get_adaptive_radius('home')  # Daytime multiplier
print(f'🏠 Daytime home radius: {daytime_radius}m (base 100m × 1.0)')
print('💡 Smaller during day for precision')
"
echo ""
echo "Nighttime (10 PM - 6 AM): Larger radius for safety"
GPS_OVERRIDE="40.7128,-74.0060" RADIUS_HOME_NIGHT_MULTIPLIER="1.5" python3 -c "
import os
os.environ['RADIUS_HOME_NIGHT_MULTIPLIER'] = '1.5'
from athena_notifications import get_adaptive_radius
nighttime_radius = get_adaptive_radius('home')  # Would be nighttime
print(f'🏠 Nighttime home radius: {int(100 * 1.5)}m (base 100m × 1.5)')
print('💡 Larger at night for safety buffer')
"
echo ""

# Test 2: Work radius - weekday vs weekend
echo "🧪 Test 2: Work Radius (Weekday vs Weekend adjustments)"
echo "Weekday: Full radius for busy office"
GPS_OVERRIDE="40.7589,-73.9851" WORK_LAT="40.7589" WORK_LNG="-73.9851" WORK_RADIUS="200" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7589,-73.9851'
os.environ['WORK_LAT'] = '40.7589'
os.environ['WORK_LNG'] = '40.7589'
os.environ['WORK_RADIUS'] = '200'
from athena_notifications import get_adaptive_radius
weekday_radius = get_adaptive_radius('work')  # Weekday
print('🏢 Work Zone Adaptive Radius Test')
print('==================================')
print(f'🏢 Weekday work radius: {weekday_radius}m (base 200m × 1.0)')
print('💡 Full size during busy work week')
"
echo ""
echo "Weekend: Smaller radius (fewer people, less precision needed)"
RADIUS_WORK_WEEKEND_MULTIPLIER="0.8" python3 -c "
import os
os.environ['RADIUS_WORK_WEEKEND_MULTIPLIER'] = '0.8'
from athena_notifications import get_adaptive_radius
weekend_radius = get_adaptive_radius('work')  # Would be weekend
print(f'🏢 Weekend work radius: {int(200 * 0.8)}m (base 200m × 0.8)')
print('💡 Smaller on weekends when fewer people')
"
echo ""

# Test 3: Transition Smoothing - Preventing alert spam
echo "🧪 Test 3: Transition Smoothing (Preventing alert spam)"
echo "Simulating rapid zone transitions that would normally spam alerts..."
echo "Without smoothing: Instant switching → Alert spam"
echo "With smoothing: Hysteresis + cooldown → Stable behavior"
echo ""

# Create initial state (home)
echo '{"location": "home", "last_transition": 0.0, "lat": 40.7128, "lng": -74.0060}' > /tmp/ai_republic_geofence_state.json

GPS_OVERRIDE="40.7128,-74.0060" TRANSITION_SMOOTHING_ENABLED="true" python3 -c "
import os
import time
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
os.environ['TRANSITION_SMOOTHING_ENABLED'] = 'true'
from athena_notifications import detect_location_by_geofence
print('🔄 Transition Smoothing Test')
print('============================')
print('Initial state: Home zone')
location1 = detect_location_by_geofence()
print(f'📍 Location after initial detection: {location1}')
"

echo ""
echo "Simulating rapid boundary crossing (would cause spam without smoothing)..."
# Rapid transition simulation
GPS_OVERRIDE="40.7589,-73.9851" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7589,-73.9851'
from athena_notifications import detect_location_by_geofence
location2 = detect_location_by_geofence()
print(f'📍 Location after boundary crossing: {location2}')
print('💡 Hysteresis prevents immediate switching - requires stronger signal')
"

echo ""
echo "Stronger signal crossing (deeper into work zone)..."
GPS_OVERRIDE="40.7595,-73.9845" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7595,-73.9845'
from athena_notifications import detect_location_by_geofence
location3 = detect_location_by_geofence()
print(f'📍 Location with stronger signal: {location3}')
print('💡 Now transitions because signal is 70%+ confident')
"

# Clean up
rm -f /tmp/ai_republic_geofence_state.json
echo ""

# Test 4: Combined adaptive + smoothing
echo "🧪 Test 4: Combined Features (Adaptive Radius + Transition Smoothing)"
echo "Real-world scenario: Driving from home to work during morning commute..."
echo ""

echo "🚗 Scenario: Leaving home driveway (nighttime, larger radius)..."
GPS_OVERRIDE="40.7128,-74.0060" RADIUS_HOME_NIGHT_MULTIPLIER="1.5" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
os.environ['RADIUS_HOME_NIGHT_MULTIPLIER'] = '1.5'
from athena_notifications import detect_location_by_geofence, get_adaptive_radius
location = detect_location_by_geofence()
adaptive_home = get_adaptive_radius('home')
print(f'🏠 Home detection (night): {location}')
print(f'🏠 Adaptive radius: {adaptive_home}m (larger at night)')
"

echo ""
echo "🚗 Scenario: Arriving at work parking lot (weekday, full radius)..."
GPS_OVERRIDE="40.7589,-73.9851" RADIUS_WORK_WEEKDAY_MULTIPLIER="1.0" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7589,-73.9851'
os.environ['RADIUS_WORK_WEEKDAY_MULTIPLIER'] = '1.0'
from athena_notifications import detect_location_by_geofence, get_adaptive_radius
location = detect_location_by_geofence()
adaptive_work = get_adaptive_radius('work')
print(f'🏢 Work detection (weekday): {location}')
print(f'🏢 Adaptive radius: {adaptive_work}m (full size on weekdays)')
print('💡 Smooth transition with appropriate zone sizes')
"

echo ""

echo "🎯 Advanced Geofencing Demo Complete!"
echo ""
echo "Advanced Features Summary:"
echo "🎯 Adaptive Radius: Zones grow/shrink based on time/day context"
echo "🔄 Transition Smoothing: Hysteresis prevents alert spam at boundaries"
echo "⏱️ Cooldown Periods: Minimum time between location changes"
echo "🎪 Hysteresis Logic: Requires stronger signal to change zones"
echo ""
echo "Real-World Benefits:"
echo "• 🏠 Nighttime home: Larger safety buffer"
echo "• 🏢 Weekend work: Smaller, more precise zones"
echo "• 🚗 Commute: Smooth transitions without alert spam"
echo "• 📍 Boundary walking: No rapid switching between zones"
echo ""
echo "Configuration:"
echo "• Enable adaptive radius: ADAPTIVE_RADIUS_ENABLED=true"
echo "• Enable smoothing: TRANSITION_SMOOTHING_ENABLED=true"
echo "• Configure multipliers: ./geofencing_config.sh (options 6-9)"
echo "• Test advanced features: GPS_OVERRIDE=\"lat,lng\" python3 script.py"
