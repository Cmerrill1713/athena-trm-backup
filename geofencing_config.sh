#!/bin/bash
# Geofencing Configuration - GPS-based Location Detection
# Set up geographic zones for automatic location awareness

echo "🌍 AI Republic Geofencing Configuration"
echo "======================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Creating basic configuration..."
    cat > .env << 'EOF'
# Apple-native iPhone alerting (FREE - no external services required)
IPHONE_NUMBER="+1YOURIPHONE"
ATHENA_ALERT_PHONE="+1YOURIPHONE"

# Quiet Hours Configuration
QUIET_HOURS_ENABLED="true"
QUIET_HOURS_START="22"
QUIET_HOURS_END="8"

# Smart Alerting (Focus Mode, Calendar & Location)
FOCUS_MODE_ENABLED="false"
FOCUS_MODE_CHECK_INTERVAL="300"
CALENDAR_ENABLED="false"
CALENDAR_BUSY_KEYWORDS="meeting,sleep,busy,do not disturb"
LOCATION_ENABLED="false"
LOCATION_CHECK_INTERVAL="600"
LOCATION_HOME_NETWORKS=""
LOCATION_WORK_NETWORKS=""
LOCATION_TRAVEL_KEYWORDS="hotel,airport,travel,remote"

# Geofencing (GPS-based)
GEOFENCING_ENABLED="false"
GEOFENCING_CHECK_INTERVAL="300"
HOME_LAT="0"
HOME_LNG="0"
HOME_RADIUS="100"
WORK_LAT="0"
WORK_LNG="0"
WORK_RADIUS="200"
TRAVEL_DISTANCE_THRESHOLD="50000"

# Advanced Geofencing Features
ADAPTIVE_RADIUS_ENABLED="false"
TRANSITION_SMOOTHING_ENABLED="false"
TRANSITION_COOLDOWN_SECONDS="300"
RADIUS_HOME_DAY_MULTIPLIER="1.0"
RADIUS_HOME_NIGHT_MULTIPLIER="1.5"
RADIUS_WORK_WEEKDAY_MULTIPLIER="1.0"
RADIUS_WORK_WEEKEND_MULTIPLIER="0.8"
EOF
fi

echo ""
echo "Current Geofencing Configuration:"
echo "================================="

if grep -q "GEOFENCING_ENABLED" .env 2>/dev/null; then
    GEOFENCE_ENABLED=$(grep "GEOFENCING_ENABLED" .env | cut -d'=' -f2 | tr -d '"')
    HOME_LAT_VAL=$(grep "HOME_LAT" .env | cut -d'=' -f2 | tr -d '"')
    HOME_LNG_VAL=$(grep "HOME_LNG" .env | cut -d'=' -f2 | tr -d '"')
    HOME_RADIUS_VAL=$(grep "HOME_RADIUS" .env | cut -d'=' -f2 | tr -d '"')
    WORK_LAT_VAL=$(grep "WORK_LAT" .env | cut -d'=' -f2 | tr -d '"')
    WORK_LNG_VAL=$(grep "WORK_LNG" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "0")
    WORK_RADIUS_VAL=$(grep "WORK_RADIUS" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "200")
    TRAVEL_THRESHOLD=$(grep "TRAVEL_DISTANCE_THRESHOLD" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "50000")

    echo "🌍 Geofencing: $([ "$GEOFENCE_ENABLED" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    if [ "$GEOFENCE_ENABLED" = "true" ]; then
        echo "🏠 Home Zone: $HOME_LAT_VAL, $HOME_LNG_VAL (${HOME_RADIUS_VAL}m radius)"
        echo "🏢 Work Zone: $WORK_LAT_VAL, $WORK_LNG_VAL (${WORK_RADIUS_VAL}m radius)"
        echo "✈️ Travel Threshold: ${TRAVEL_THRESHOLD}m from home"
    fi

    ADAPTIVE_ENABLED=$(grep "ADAPTIVE_RADIUS_ENABLED" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    SMOOTHING_ENABLED=$(grep "TRANSITION_SMOOTHING_ENABLED" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")

    echo "🎯 Adaptive Radius: $([ "$ADAPTIVE_ENABLED" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    echo "🔄 Transition Smoothing: $([ "$SMOOTHING_ENABLED" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
else
    echo "⚠️  Geofencing not configured yet"
fi

echo ""
echo "Geofencing Features:"
echo "==================="
echo "📍 GPS-based location detection with radius zones"
echo "🏠 Home zone: Relaxed alerting (all alerts)"
echo "🏢 Work zone: Professional alerting (warnings+) "
echo "✈️ Travel detection: Distance-based (>50km from home)"
echo "🔄 Automatic switching: No manual intervention needed"
echo "📱 Location priority: GPS > WiFi > Time-based defaults"
echo ""
echo "Advanced Features:"
echo "🎯 Adaptive Radius: Auto-adjust zone sizes based on time/day"
echo "🔄 Transition Smoothing: Prevent alert spam when crossing boundaries"
echo "🕐 Time-based multipliers: Larger home radius at night, smaller work radius on weekends"
echo "⏱️ Cooldown periods: Minimum time between location transitions"
echo ""
echo "Setup Process:"
echo "1. Get GPS coordinates for home and work locations"
echo "2. Configure geographic zones with radii"
echo "3. Test location detection"
echo "4. Enable automatic geofencing"

echo ""
echo "Configuration Options:"
echo "1. Enable geofencing"
echo "2. Disable geofencing"
echo "3. Configure home location"
echo "4. Configure work location"
echo "5. Configure travel threshold"
echo "6. Enable adaptive radius"
echo "7. Configure radius multipliers"
echo "8. Enable transition smoothing"
echo "9. Configure smoothing settings"
echo "10. Test GPS coordinates"
echo "11. Test geofence detection"
echo "12. Show current GPS location"
echo "13. Exit"

read -p "Choose option (1-13): " choice

case $choice in
    1)
        echo "Enabling geofencing..."
        sed -i.bak 's/GEOFENCING_ENABLED=.*/GEOFENCING_ENABLED="true"/' .env
        echo "✅ Geofencing enabled"
        echo "📝 Configure zones with options 3-5"
        ;;
    2)
        echo "Disabling geofencing..."
        sed -i.bak 's/GEOFENCING_ENABLED=.*/GEOFENCING_ENABLED="false"/' .env
        echo "✅ Geofencing disabled"
        ;;
    3)
        echo "Configuring home location..."
        echo "Get your home GPS coordinates from:"
        echo "• Google Maps: Right-click location → 'What's here?'"
        echo "• Apple Maps: Share location → Coordinates"
        echo "• Online: latlong.net or similar"
        echo ""
        read -p "Home latitude (e.g., 40.7128): " home_lat
        read -p "Home longitude (e.g., -74.0060): " home_lng
        read -p "Home radius in meters (default 100): " home_radius
        home_radius=${home_radius:-100}

        sed -i.bak "s/HOME_LAT=.*/HOME_LAT=\"$home_lat\"/" .env
        sed -i.bak "s/HOME_LNG=.*/HOME_LNG=\"$home_lng\"/" .env
        sed -i.bak "s/HOME_RADIUS=.*/HOME_RADIUS=\"$home_radius\"/" .env
        echo "✅ Home zone configured: $home_lat, $home_lng (${home_radius}m)"
        ;;
    4)
        echo "Configuring work location..."
        echo "Get your work GPS coordinates (same method as home)"
        echo ""
        read -p "Work latitude: " work_lat
        read -p "Work longitude: " work_lng
        read -p "Work radius in meters (default 200): " work_radius
        work_radius=${work_radius:-200}

        sed -i.bak "s/WORK_LAT=.*/WORK_LAT=\"$work_lat\"/" .env
        sed -i.bak "s/WORK_LNG=.*/WORK_LNG=\"$work_lng\"/" .env
        sed -i.bak "s/WORK_RADIUS=.*/WORK_RADIUS=\"$work_radius\"/" .env
        echo "✅ Work zone configured: $work_lat, $work_lng (${work_radius}m)"
        ;;
    5)
        echo "Configuring travel detection threshold..."
        echo "Distance from home that triggers 'travel' mode (in meters)"
        echo "Examples:"
        echo "• 50000 = 50km (good for most cities)"
        echo "• 100000 = 100km (good for large metro areas)"
        echo "• 500000 = 500km (good for international travel)"
        echo ""
        read -p "Travel distance threshold (meters): " travel_threshold
        sed -i.bak "s/TRAVEL_DISTANCE_THRESHOLD=.*/TRAVEL_DISTANCE_THRESHOLD=\"$travel_threshold\"/" .env
        echo "✅ Travel threshold set to ${travel_threshold}m"
        ;;
    6)
        echo "Enabling adaptive radius..."
        sed -i.bak 's/ADAPTIVE_RADIUS_ENABLED=.*/ADAPTIVE_RADIUS_ENABLED="true"/' .env
        echo "✅ Adaptive radius enabled"
        echo "📝 Configure multipliers with option 7"
        echo "💡 Home radius: 1.0x daytime, 1.5x nighttime"
        echo "💡 Work radius: 1.0x weekdays, 0.8x weekends"
        ;;
    7)
        echo "Configuring adaptive radius multipliers..."
        echo "Current settings adjust zone sizes based on time and day:"
        echo "• Home: Larger at night (safer buffer)"
        echo "• Work: Smaller on weekends (fewer people)"
        echo ""
        read -p "Home daytime multiplier (default 1.0): " home_day
        home_day=${home_day:-1.0}
        read -p "Home nighttime multiplier (default 1.5): " home_night
        home_night=${home_night:-1.5}
        read -p "Work weekday multiplier (default 1.0): " work_weekday
        work_weekday=${work_weekday:-1.0}
        read -p "Work weekend multiplier (default 0.8): " work_weekend
        work_weekend=${work_weekend:-0.8}

        sed -i.bak "s/RADIUS_HOME_DAY_MULTIPLIER=.*/RADIUS_HOME_DAY_MULTIPLIER=\"$home_day\"/" .env
        sed -i.bak "s/RADIUS_HOME_NIGHT_MULTIPLIER=.*/RADIUS_HOME_NIGHT_MULTIPLIER=\"$home_night\"/" .env
        sed -i.bak "s/RADIUS_WORK_WEEKDAY_MULTIPLIER=.*/RADIUS_WORK_WEEKDAY_MULTIPLIER=\"$work_weekday\"/" .env
        sed -i.bak "s/RADIUS_WORK_WEEKEND_MULTIPLIER=.*/RADIUS_WORK_WEEKEND_MULTIPLIER=\"$work_weekend\"/" .env
        echo "✅ Adaptive radius multipliers configured"
        ;;
    8)
        echo "Enabling transition smoothing..."
        sed -i.bak 's/TRANSITION_SMOOTHING_ENABLED=.*/TRANSITION_SMOOTHING_ENABLED="true"/' .env
        echo "✅ Transition smoothing enabled"
        echo "📝 Configure cooldown settings with option 9"
        echo "💡 Prevents alert spam when crossing zone boundaries"
        ;;
    9)
        echo "Configuring transition smoothing settings..."
        echo "Transition smoothing prevents rapid location changes that could spam alerts"
        echo ""
        read -p "Cooldown period between transitions (seconds, default 300 = 5min): " cooldown
        cooldown=${cooldown:-300}

        sed -i.bak "s/TRANSITION_COOLDOWN_SECONDS=.*/TRANSITION_COOLDOWN_SECONDS=\"$cooldown\"/" .env
        echo "✅ Transition cooldown set to ${cooldown} seconds"
        ;;
    10)
        echo "Testing GPS coordinate input..."
        echo "This will test coordinate parsing and distance calculation"
        echo ""
        read -p "Test latitude 1: " lat1
        read -p "Test longitude 1: " lng1
        read -p "Test latitude 2: " lat2
        read -p "Test longitude 2: " lng2

        python3 -c "
from athena_notifications import calculate_distance
try:
    distance = calculate_distance($lat1, $lng1, $lat2, $lng2)
    print(f'✅ Distance: {distance:.0f} meters ({distance/1000:.1f} km)')
except Exception as e:
    print(f'❌ Error: {e}')
        "
        ;;
    11)
        echo "Testing geofence detection..."
        echo "This simulates GPS location and tests zone detection"
        echo ""
        read -p "Test GPS latitude: " test_lat
        read -p "Test GPS longitude: " test_lng

        # Create temporary GPS status file
        echo "$test_lat,$test_lng" > ~/.ai_republic_gps_status

        python3 -c "
from athena_notifications import detect_location_by_geofence, calculate_distance
try:
    location = detect_location_by_geofence()
    print(f'📍 Detected location: {location}')

    # Show distances
    home_lat = float('$HOME_LAT_VAL')
    home_lng = float('$HOME_LNG_VAL')
    work_lat = float('$WORK_LAT_VAL')
    work_lng = float('$WORK_LNG_VAL')

    if home_lat != 0 or home_lng != 0:
        home_dist = calculate_distance($test_lat, $test_lng, home_lat, home_lng)
        print(f'🏠 Distance to home: {home_dist:.0f}m')

    if work_lat != 0 or work_lng != 0:
        work_dist = calculate_distance($test_lat, $test_lng, work_lat, work_lng)
        print(f'🏢 Distance to work: {work_dist:.0f}m')

except Exception as e:
    print(f'❌ Error: {e}')
        "

        rm -f ~/.ai_republic_gps_status
        ;;
    12)
        echo "Current GPS location detection:"
        python3 -c "
from athena_notifications import get_current_gps_location
try:
    lat, lng = get_current_gps_location()
    print(f'📍 Current GPS: {lat}, {lng}')
    if lat == 0.0 and lng == 0.0:
        print('⚠️  No GPS coordinates available (using defaults)')
        print('💡 Set GPS_OVERRIDE=\"lat,lng\" or create ~/.ai_republic_gps_status file')
except Exception as e:
    print(f'❌ Error: {e}')
        "
        ;;
    13)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        ;;
esac

echo ""
echo "Restart AI Republic services to apply changes:"
echo "pkill -f athena && ./quick_launch.sh"
echo ""
echo "Test geofencing with: GPS_OVERRIDE=\"40.7128,-74.0060\" python3 -c \"from athena_notifications import get_current_location; print(get_current_location())\""
