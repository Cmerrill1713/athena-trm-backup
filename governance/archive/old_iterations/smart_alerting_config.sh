#!/bin/bash
# Smart Alerting Configuration - Focus Mode & Calendar Integration
# Advanced AI Republic alerting that adapts to your iPhone and schedule

echo "🧠 AI Republic Smart Alerting Configuration"
echo "=========================================="

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

# Voice Notifications
VOICE_NOTIFICATIONS_ENABLED="false"
VOICE_NOTIFICATION_CONTEXTS="focus,driving"
VOICE_SUMMARY_LENGTH="normal"

# Voice Activation (Wake Word)
VOICE_ACTIVATION_ENABLED="false"
WAKE_WORD="hey athena"
VOICE_ACTIVATION_TIMEOUT="10"

# Korono-First Voice Stack
VOICE_ENGINE="korono"
KORONO_STT_MODEL="korono-stt-v1"
KORONO_TTS_VOICE="athena-neutral"
KORONO_SAMPLE_RATE="16000"
KORONO_VAD="true"
USE_PORCUPINE_WAKE="true"
WAKE_SENSITIVITY="0.5"
VOICE_HALF_DUPLEX="true"
PHRASE_TIME_LIMIT="3"
VOICE_OVERRIDE_TTL="900"

# Legacy Local Voice (deprecated)
USE_LOCAL_STT="false"
WHISPER_MODEL_SIZE="tiny"

# Context-Reactive Macros
CONTEXT_MACROS_ENABLED="false"
MACRO_CHECK_INTERVAL="60"
EOF
fi

echo ""
echo "Current Smart Alerting Configuration:"
echo "====================================="

if grep -q "FOCUS_MODE_ENABLED" .env 2>/dev/null; then
    FOCUS_ENABLED=$(grep "FOCUS_MODE_ENABLED" .env | cut -d'=' -f2 | tr -d '"')
    CALENDAR_ENABLED_VAL=$(grep "CALENDAR_ENABLED" .env | cut -d'=' -f2 | tr -d '"')
    BUSY_KEYWORDS=$(grep "CALENDAR_BUSY_KEYWORDS" .env | cut -d'=' -f2 | tr -d '"')
    LOCATION_ENABLED_VAL=$(grep "LOCATION_ENABLED" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    HOME_NETWORKS=$(grep "LOCATION_HOME_NETWORKS" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    WORK_NETWORKS=$(grep "LOCATION_WORK_NETWORKS" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    VOICE_ENABLED=$(grep "VOICE_NOTIFICATIONS_ENABLED" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    VOICE_CONTEXTS=$(grep "VOICE_NOTIFICATION_CONTEXTS" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    VOICE_LENGTH=$(grep "VOICE_SUMMARY_LENGTH" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    VOICE_ACTIVATION_ENABLED_VAL=$(grep "VOICE_ACTIVATION_ENABLED" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    WAKE_WORD_VAL=$(grep "WAKE_WORD" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    VOICE_TIMEOUT=$(grep "VOICE_ACTIVATION_TIMEOUT" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    LOCAL_STT_ENABLED=$(grep "USE_LOCAL_STT" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    PORCUPINE_ENABLED=$(grep "USE_PORCUPINE_WAKE" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    WHISPER_MODEL=$(grep "WHISPER_MODEL_SIZE" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")
    MACROS_ENABLED=$(grep "CONTEXT_MACROS_ENABLED" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "false")
    MACRO_INTERVAL=$(grep "MACRO_CHECK_INTERVAL" .env | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")

    echo "🎯 Focus Mode Integration: $([ "$FOCUS_ENABLED" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    echo "📅 Calendar Integration: $([ "$CALENDAR_ENABLED_VAL" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    if [ "$CALENDAR_ENABLED_VAL" = "true" ]; then
        echo "📝 Busy Keywords: $BUSY_KEYWORDS"
    fi
    echo "📍 Location Integration: $([ "$LOCATION_ENABLED_VAL" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    if [ "$LOCATION_ENABLED_VAL" = "true" ]; then
        echo "🏠 Home Networks: ${HOME_NETWORKS:-Not configured}"
        echo "🏢 Work Networks: ${WORK_NETWORKS:-Not configured}"
    fi
        echo "🗣️ Voice Notifications: $([ "$VOICE_ENABLED" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    if [ "$VOICE_ENABLED" = "true" ]; then
        echo "🎯 Voice Contexts: $VOICE_CONTEXTS"
        echo "📏 Voice Length: $VOICE_LENGTH"
    fi
    echo "🎤 Voice Activation: $([ "$VOICE_ACTIVATION_ENABLED_VAL" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    if [ "$VOICE_ACTIVATION_ENABLED_VAL" = "true" ]; then
        echo "🔑 Wake Word: \"$WAKE_WORD_VAL\""
        echo "⏰ Timeout: ${VOICE_TIMEOUT}s"
        echo "🎵 Voice Engine: $VOICE_ENGINE"
        if [ "$VOICE_ENGINE" = "korono" ]; then
            echo "🧠 STT Model: $KORONO_STT_MODEL"
            echo "🔊 TTS Voice: $KORONO_TTS_VOICE"
            echo "🎧 Wake Engine: $([ "$PORCUPINE_ENABLED" = "true" ] && echo "Porcupine" || echo "Cloud")"
            echo "📞 Half-Duplex: $([ "$VOICE_HALF_DUPLEX" = "true" ] && echo "Enabled" || echo "Disabled")"
        fi
    fi
    echo "🎯 Context Macros: $([ "$MACROS_ENABLED" = "true" ] && echo "✅ ENABLED" || echo "❌ DISABLED")"
    if [ "$MACROS_ENABLED" = "true" ]; then
        echo "⏰ Check Interval: ${MACRO_INTERVAL}s"
        echo "📋 Available Macros: meeting_mode, emergency_mode, maintenance_mode, travel_mode, focus_mode"
    fi
else
    echo "⚠️  Smart alerting not configured yet"
fi

echo ""
echo "Smart Alerting Features:"
echo "========================"
echo "🎯 Focus Mode: Respects iPhone Do Not Disturb, Sleep, Work modes"
echo "📅 Calendar: Suppresses alerts during meetings/events"
echo "📍 Location: Adapts behavior based on home/work/travel context"
echo "🕐 Quiet Hours: Time-based filtering (already configured)"
echo "🚨 Critical Override: Emergency alerts always get through"
echo ""
echo "Alert Behavior Matrix:"
echo "Context       | Info | Warning | Critical"
echo "--------------|------|---------|---------"
echo "Normal        | ✅    | ✅+🎤    | ✅+🎤+ESC"
echo "Quiet Hours   | ❌    | ✅       | ✅+🎤+ESC"
echo "Focus Mode    | ❌    | ❌       | ✅+🎤+ESC"
echo "Calendar Busy | ❌    | ✅       | ✅+🎤+ESC"
echo "At Home       | ✅    | ✅+🎤    | ✅+🎤+ESC"
echo "At Work       | ❌    | ✅+🎤    | ✅+🎤+ESC"
echo "Traveling     | ❌    | ✅       | ✅+🎤+ESC"

echo ""
    echo "Configuration Options:"
echo "1. Enable Focus Mode integration"
echo "2. Disable Focus Mode integration"
echo "3. Enable Calendar integration"
echo "4. Disable Calendar integration"
echo "5. Configure busy keywords"
echo "6. Enable Location integration"
echo "7. Disable Location integration"
echo "8. Configure home/work networks"
echo "9. Enable GPS Geofencing"
echo "10. Configure geofence zones"
echo "11. Enable Zone Chaining"
echo "12. Configure predictive settings"
echo "13. Enable Voice Notifications"
echo "14. Configure voice settings"
echo "15. Enable Voice Activation"
echo "16. Configure wake word"
echo "17. Enable Local Voice Processing"
echo "18. Enable Context Macros"
echo "19. Test smart alerting"
echo "20. Show current context"
echo "21. Exit"

read -p "Choose option (1-21): " choice

case $choice in
    1)
        echo "Enabling Focus Mode integration..."
        sed -i.bak 's/FOCUS_MODE_ENABLED=.*/FOCUS_MODE_ENABLED="true"/' .env
        echo "✅ Focus Mode integration enabled"
        echo "📝 Note: This uses time-based heuristics. Full iCloud API integration would require additional setup."
        ;;
    2)
        echo "Disabling Focus Mode integration..."
        sed -i.bak 's/FOCUS_MODE_ENABLED=.*/FOCUS_MODE_ENABLED="false"/' .env
        echo "✅ Focus Mode integration disabled"
        ;;
    3)
        echo "Enabling Calendar integration..."
        sed -i.bak 's/CALENDAR_ENABLED=.*/CALENDAR_ENABLED="true"/' .env
        echo "✅ Calendar integration enabled"
        echo "📝 Create ~/.ai_republic_calendar_status file with your status (e.g., 'meeting', 'busy')"
        ;;
    4)
        echo "Disabling Calendar integration..."
        sed -i.bak 's/CALENDAR_ENABLED=.*/CALENDAR_ENABLED="false"/' .env
        echo "✅ Calendar integration disabled"
        ;;
    5)
        read -p "Enter busy keywords (comma-separated): " keywords
        sed -i.bak "s/CALENDAR_BUSY_KEYWORDS=.*/CALENDAR_BUSY_KEYWORDS=\"$keywords\"/" .env
        echo "✅ Busy keywords updated: $keywords"
        ;;
    6)
        echo "Enabling Location integration..."
        sed -i.bak 's/LOCATION_ENABLED=.*/LOCATION_ENABLED="true"/' .env
        echo "✅ Location integration enabled"
        echo "📝 Configure WiFi networks with option 8"
        echo "📝 Create ~/.ai_republic_location_status file for travel status"
        ;;
    7)
        echo "Disabling Location integration..."
        sed -i.bak 's/LOCATION_ENABLED=.*/LOCATION_ENABLED="false"/' .env
        echo "✅ Location integration disabled"
        ;;
    8)
        echo "Configuring home and work WiFi networks..."
        echo "Current WiFi network detection:"
        /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep "SSID:" | head -1
        echo ""
        read -p "Enter home network names (comma-separated): " home_networks
        read -p "Enter work network names (comma-separated): " work_networks
        sed -i.bak "s/LOCATION_HOME_NETWORKS=.*/LOCATION_HOME_NETWORKS=\"$home_networks\"/" .env
        sed -i.bak "s/LOCATION_WORK_NETWORKS=.*/LOCATION_WORK_NETWORKS=\"$work_networks\"/" .env
        echo "✅ WiFi networks configured"
        echo "🏠 Home: $home_networks"
        echo "🏢 Work: $work_networks"
        ;;
    9)
        echo "Enabling GPS Geofencing..."
        sed -i.bak 's/GEOFENCING_ENABLED=.*/GEOFENCING_ENABLED="true"/' .env
        echo "✅ GPS Geofencing enabled"
        echo "📝 Configure geographic zones with option 10"
        echo "📝 Use ./geofencing_config.sh for detailed GPS setup"
        ;;
    10)
        echo "Launching geofencing configuration..."
        if [ -f "./geofencing_config.sh" ]; then
            ./geofencing_config.sh
        else
            echo "❌ geofencing_config.sh not found"
            echo "💡 Run the geofencing setup separately"
        fi
        ;;
    11)
        echo "Enabling Zone Chaining & Predictive Awareness..."
        sed -i.bak 's/ZONE_CHAINING_ENABLED=.*/ZONE_CHAINING_ENABLED="true"/' .env
        echo "✅ Zone chaining enabled"
        echo "📝 Configure predictive settings with option 12"
        echo "🧠 System will learn your location patterns and predict movements"
        ;;
    12)
        echo "Configuring zone chaining predictive settings..."
        echo "Zone chaining learns your movement patterns and predicts next locations"
        echo ""
        read -p "Learning threshold (visits needed to learn location, default 3): " threshold
        threshold=${threshold:-3}
        read -p "Predictive horizon (hours to look ahead, default 2): " horizon
        horizon=${horizon:-2}
        read -p "Chain confidence threshold (0.0-1.0, default 0.7): " confidence
        confidence=${confidence:-0.7}

        sed -i.bak "s/LEARNING_THRESHOLD=.*/LEARNING_THRESHOLD=\"$threshold\"/" .env
        sed -i.bak "s/PREDICTIVE_HORIZON_HOURS=.*/PREDICTIVE_HORIZON_HOURS=\"$horizon\"/" .env
        sed -i.bak "s/CHAIN_CONFIDENCE_THRESHOLD=.*/CHAIN_CONFIDENCE_THRESHOLD=\"$confidence\"/" .env
        echo "✅ Zone chaining settings configured"
        echo "📊 Learning threshold: $threshold visits"
        echo "🔮 Predictive horizon: ${horizon}h"
        echo "🎯 Confidence threshold: ${confidence}"
        ;;
    13)
        echo "Enabling Voice Notifications for weekly summaries..."
        sed -i.bak 's/VOICE_NOTIFICATIONS_ENABLED=.*/VOICE_NOTIFICATIONS_ENABLED="true"/' .env
        echo "✅ Voice notifications enabled"
        echo "📝 Configure contexts and length with option 14"
        echo "🗣️ Voice summaries will play during specified contexts"
        ;;
    14)
        echo "Configuring voice notification settings..."
        echo "Voice notifications provide spoken weekly summaries in specific contexts"
        echo ""
        read -p "Voice contexts (comma-separated: focus,driving,quiet): " voice_contexts
        voice_contexts=${voice_contexts:-focus,driving}
        read -p "Voice summary length (brief/normal/detailed): " voice_length
        voice_length=${voice_length:-normal}

        sed -i.bak "s/VOICE_NOTIFICATION_CONTEXTS=.*/VOICE_NOTIFICATION_CONTEXTS=\"$voice_contexts\"/" .env
        sed -i.bak "s/VOICE_SUMMARY_LENGTH=.*/VOICE_SUMMARY_LENGTH=\"$voice_length\"/" .env
        echo "✅ Voice notification settings configured"
        echo "🎯 Contexts: $voice_contexts"
        echo "📏 Length: $voice_length"
        ;;
    15)
        echo "Enabling Voice Activation (Wake Word)..."
        sed -i.bak 's/VOICE_ACTIVATION_ENABLED=.*/VOICE_ACTIVATION_ENABLED="true"/' .env
        echo "✅ Voice activation enabled"
        echo "🔑 Configure wake word with option 16"
        echo "🎤 Say your wake word + command to trigger actions"
        ;;
    16)
        echo "Configuring Voice Activation settings..."
        echo "Voice activation allows hands-free control using wake words"
        echo ""
        read -p "Wake word (e.g., 'hey athena', 'computer'): " wake_word
        wake_word=${wake_word:-hey athena}
        read -p "Timeout seconds (5-30): " timeout
        timeout=${timeout:-10}

        sed -i.bak "s/WAKE_WORD=.*/WAKE_WORD=\"$wake_word\"/" .env
        sed -i.bak "s/VOICE_ACTIVATION_TIMEOUT=.*/VOICE_ACTIVATION_TIMEOUT=\"$timeout\"/" .env
        echo "✅ Voice activation settings configured"
        echo "🔑 Wake word: \"$wake_word\""
        echo "⏰ Timeout: ${timeout}s"
        ;;
    17)
        echo "Enabling Local Voice Processing (Porcupine + Whisper)..."
        echo "This provides offline, privacy-focused voice activation"
        echo ""
        echo "Required packages: pvporcupine pyaudio numpy openai-whisper torch"
        echo "⚠️  First run will download Whisper model (~150MB)"
        echo ""

        read -p "Enable local STT with Whisper? (y/n): " enable_stt
        if [ "$enable_stt" = "y" ] || [ "$enable_stt" = "Y" ]; then
            sed -i.bak 's/USE_LOCAL_STT=.*/USE_LOCAL_STT="true"/' .env
            echo "✅ Local STT enabled (Whisper)"
        fi

        read -p "Enable Porcupine wake word detection? (y/n): " enable_porcupine
        if [ "$enable_porcupine" = "y" ] || [ "$enable_porcupine" = "Y" ]; then
            sed -i.bak 's/USE_PORCUPINE_WAKE=.*/USE_PORCUPINE_WAKE="true"/' .env
            echo "✅ Porcupine wake word detection enabled"
        fi

        read -p "Whisper model size (tiny/base/small/medium): " model_size
        model_size=${model_size:-tiny}
        sed -i.bak "s/WHISPER_MODEL_SIZE=.*/WHISPER_MODEL_SIZE=\"$model_size\"/" .env
        echo "✅ Whisper model set to: $model_size"

        echo ""
        echo "🎉 Local voice processing configured!"
        echo "💡 Test setup with: python3 -c 'from athena_notifications import test_local_voice_setup; test_local_voice_setup()'"
        ;;
    18)
        echo "Enabling Context-Reactive Macros..."
        echo "Macros automatically adapt system behavior based on context"
        echo ""

        read -p "Check interval in seconds (60-300): " interval
        interval=${interval:-60}

        sed -i.bak 's/CONTEXT_MACROS_ENABLED=.*/CONTEXT_MACROS_ENABLED="true"/' .env
        sed -i.bak "s/MACRO_CHECK_INTERVAL=.*/MACRO_CHECK_INTERVAL=\"$interval\"/" .env
        echo "✅ Context macros enabled"
        echo "⏰ Check interval: ${interval}s"
        echo ""
        echo "Available Macros:"
        echo "• meeting_mode - Auto-quiet for calendar meetings"
        echo "• travel_mode - Travel-optimized settings"
        echo "• focus_mode - Deep work minimal interruptions"
        echo "• maintenance_mode - Controlled silence for maintenance"
        echo "• emergency_mode - High alert escalation"
        ;;
    19)
        echo "Testing smart alerting behavior..."
        python3 -c "
from athena_notifications import should_send_alert_smart, update_smart_alerting, is_focus_mode_active, is_calendar_busy, is_quiet_hours, get_current_location
import json

print('🧪 Smart Alerting Test Results')
print('==============================')
context = update_smart_alerting()
print(f'Current Context: {json.dumps(context, indent=2)}')
print()
print('Alert Delivery Test:')
print(f'  Info alert would send: {should_send_alert_smart(\"info\")}')
print(f'  Warning alert would send: {should_send_alert_smart(\"warning\")}')
print(f'  Critical alert would send: {should_send_alert_smart(\"urgent\")}')
print()
print('Context Breakdown:')
print(f'  Quiet hours active: {is_quiet_hours()}')
print(f'  Focus mode active: {is_focus_mode_active()}')
print(f'  Calendar busy: {is_calendar_busy()}')
print(f'  Current location: {get_current_location()}')
        "
        ;;
    18)
        echo "Current smart alerting context:"
        python3 -c "
from athena_notifications import update_smart_alerting
import json
context = update_smart_alerting()
print(json.dumps(context, indent=2))
        "
        ;;
    19)
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
echo "Test with: python3 test_iphone_alerts.py cascade"
