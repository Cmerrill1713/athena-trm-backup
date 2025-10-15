#!/bin/bash
# Demo: GPS Geofencing - Radius-based Location Detection
# Shows how AI Republic uses GPS coordinates for precise location awareness

echo "🌍 AI Republic GPS Geofencing Demo"
echo "=================================="
echo ""

# Test 1: Home Zone Detection
echo "🧪 Test 1: Home Zone Detection"
echo "Simulating GPS coordinates within home radius..."
GPS_OVERRIDE="40.7128,-74.0060" GEOFENCING_ENABLED="true" HOME_LAT="40.7128" HOME_LNG="-74.0060" HOME_RADIUS="1000" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7128,-74.0060'
os.environ['GEOFENCING_ENABLED'] = 'true'
os.environ['HOME_LAT'] = '40.7128'
os.environ['HOME_LNG'] = '-74.0060'
os.environ['HOME_RADIUS'] = '1000'
from athena_notifications import detect_location_by_geofence, get_current_location, calculate_distance
print('🏠 Home Zone Test')
print('================')
location = detect_location_by_geofence()
print(f'GPS Geofence Detection: {location}')
overall_location = get_current_location()
print(f'Overall Location Context: {overall_location}')
distance = calculate_distance(40.7128, -74.0060, 40.7128, -74.0060)
print(f'Distance from home: {distance:.0f}m (within {1000}m radius)')
"
echo ""

# Test 2: Work Zone Detection
echo "🧪 Test 2: Work Zone Detection"
echo "Simulating GPS coordinates within work radius..."
GPS_OVERRIDE="40.7589,-73.9851" WORK_LAT="40.7589" WORK_LNG="-73.9851" WORK_RADIUS="500" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '40.7589,-73.9851'
os.environ['WORK_LAT'] = '40.7589'
os.environ['WORK_LNG'] = '-73.9851'
os.environ['WORK_RADIUS'] = '500'
from athena_notifications import detect_location_by_geofence, get_current_location, calculate_distance
print('🏢 Work Zone Test')
print('================')
location = detect_location_by_geofence()
print(f'GPS Geofence Detection: {location}')
overall_location = get_current_location()
print(f'Overall Location Context: {overall_location}')
distance = calculate_distance(40.7589, -73.9851, 40.7589, -73.9851)
print(f'Distance from work: {distance:.0f}m (within {500}m radius)')
"
echo ""

# Test 3: Travel Detection
echo "🧪 Test 3: Travel Detection"
echo "Simulating GPS coordinates far from home (>50km)..."
GPS_OVERRIDE="34.0522,-118.2437" TRAVEL_DISTANCE_THRESHOLD="50000" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '34.0522,-118.2437'
os.environ['TRAVEL_DISTANCE_THRESHOLD'] = '50000'
from athena_notifications import detect_location_by_geofence, get_current_location, calculate_distance
print('✈️ Travel Detection Test')
print('=======================')
location = detect_location_by_geofence()
print(f'GPS Geofence Detection: {location}')
overall_location = get_current_location()
print(f'Overall Location Context: {overall_location}')
distance = calculate_distance(34.0522, -118.2437, 40.7128, -74.0060)
print(f'Distance from home: {distance/1000:.1f}km (>50km threshold)')
"
echo ""

# Test 4: Unknown Location
echo "🧪 Test 4: Unknown Location"
echo "Simulating GPS coordinates outside all defined zones..."
GPS_OVERRIDE="35.6762,139.6503" python3 -c "
import os
os.environ['GPS_OVERRIDE'] = '35.6762,139.6503'
from athena_notifications import detect_location_by_geofence, get_current_location, calculate_distance
print('❓ Unknown Location Test')
print('=======================')
location = detect_location_by_geofence()
print(f'GPS Geofence Detection: {location}')
overall_location = get_current_location()
print(f'Overall Location Context: {overall_location}')
home_dist = calculate_distance(35.6762, 139.6503, 40.7128, -74.0060)
work_dist = calculate_distance(35.6762, 139.6503, 40.7589, -73.9851)
print(f'Distance from home: {home_dist/1000:.1f}km')
print(f'Distance from work: {work_dist/1000:.1f}km')
print('Result: Falls back to WiFi/time-based detection')
"
echo ""

# Test 5: Priority System Demonstration
echo "🧪 Test 5: Detection Priority System"
echo "GPS Geofencing > WiFi Networks > Travel Keywords > Time Defaults"
echo ""
echo "Priority Order:"
echo "1. GPS Geofencing (most accurate, ~10m precision)"
echo "2. WiFi Network SSID matching"
echo "3. Travel keywords in status files"
echo "4. Time-based defaults (9-5 work, else home)"
echo ""

GPS_OVERRIDE="40.7128,-74.0060" LOCATION_OVERRIDE="" python3 -c "
import os
# Clear overrides to show priority system
if 'GPS_OVERRIDE' in os.environ: del os.environ['GPS_OVERRIDE']
if 'LOCATION_OVERRIDE' in os.environ: del os.environ['LOCATION_OVERRIDE']
from athena_notifications import get_current_location
print('🔄 Priority System Test')
print('======================')
print('With GPS override cleared, location falls back to WiFi/time detection')
location = get_current_location()
print(f'Current location: {location}')
print('💡 GPS provides highest accuracy when available')
"
echo ""

echo "🎯 Geofencing Demo Complete!"
echo ""
echo "Geofencing Behavior Matrix:"
echo "Zone       | Detection Method | Alert Behavior"
echo "-----------|------------------|----------------"
echo "Home       | GPS radius       | ✅ All alerts"
echo "Work       | GPS radius       | ❌ Info, ✅ Warnings+"
echo "Travel     | Distance >50km   | ❌ Info, ✅ Warnings"
echo "Unknown    | WiFi/Time        | ⚙️ Configurable"
echo ""
echo "Accuracy Levels:"
echo "📍 GPS Geofencing: ~10-50m precision"
echo "📶 WiFi Networks: Building/room level"
echo "🏷️ Status Keywords: Manual override"
echo "🕐 Time Defaults: Schedule-based"
echo ""
echo "Setup Commands:"
echo "• Configure zones: ./geofencing_config.sh"
echo "• Test coordinates: GPS_OVERRIDE=\"lat,lng\" python3 script.py"
echo "• Manual GPS: echo \"lat,lng\" > ~/.ai_republic_gps_status"
echo ""
echo "Real-world Examples:"
echo "🏠 Home driveway → Automatic 'home' mode → All alerts welcome"
echo "🏢 Office building → Automatic 'work' mode → Professional filtering"
echo "✈️ Airport (50km away) → Automatic 'travel' mode → Minimal alerts"
