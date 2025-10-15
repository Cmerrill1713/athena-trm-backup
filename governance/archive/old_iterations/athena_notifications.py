#!/usr/bin/env python3
"""
Athena Notification System
==========================

Real-time notifications for AI Republic operations.
Supports multiple channels: Email, Telegram, Slack, Desktop notifications.

Features:
- Urgent alert notifications (tribunal escalations)
- Daily briefing delivery
- Configurable notification channels
- Fallback notification methods
- Retry logic and delivery confirmation

Usage:
    python3 athena_notifications.py --test email
    python3 athena_notifications.py --configure
    python3 athena_notifications.py --send-alert "Test alert message"
"""

import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import time
from datetime import datetime
import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional
import threading

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

# --- iPhone Alerts via Apple Messages & Notifications ---

def _send_imessage(phone_number: str, message: str) -> bool:
    """Send iMessage from Mac to iPhone using AppleScript"""
    try:
        # Escape quotes in message for AppleScript
        escaped_message = message.replace('"', '\\"').replace("'", "\\'")

        script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{phone_number}" of targetService
            send "{escaped_message}" to targetBuddy
        end tell
        '''

        result = subprocess.run(['osascript', '-e', script],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            logging.info(f"iMessage sent to {phone_number}")
            return True
        else:
            logging.error(f"iMessage failed: {result.stderr}")
            return False

    except Exception as e:
        logging.error(f"iMessage send failed: {e}")
        return False

def _send_system_notification(title: str, message: str, sound: str = "default") -> bool:
    """Send macOS notification that syncs to iPhone via iCloud"""
    try:
        # Use terminal-notifier if available, fallback to osascript
        cmd = [
            'terminal-notifier',
            '-title', title,
            '-message', message,
            '-sound', sound,
            '-appIcon', '/System/Applications/Utilities/Terminal.app/Contents/Resources/Terminal.icns'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            logging.info("macOS notification sent")
            return True
        else:
            # Fallback to osascript
            script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
            result2 = subprocess.run(['osascript', '-e', script],
                                   capture_output=True, text=True, timeout=5)
            if result2.returncode == 0:
                logging.info("macOS notification sent (osascript)")
                return True

        logging.error("All notification methods failed")
        return False

    except Exception as e:
        logging.error(f"System notification failed: {e}")
        return False

def _play_sound_and_speak(text: str) -> bool:
    """Play system sound and speak alert (voice equivalent)"""
    try:
        # Play system alert sound
        subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'],
                      capture_output=True, timeout=2)

        # Use macOS text-to-speech
        subprocess.run(['say', '-v', 'Samantha', text],
                      capture_output=True, timeout=10)

        logging.info("Voice alert played")
        return True

    except Exception as e:
        logging.error(f"Voice alert failed: {e}")
        return False

# ==============================
# Active mode + manual overrides
# ==============================
_ACTIVE_MODE: Optional[str] = "normal_mode"
_OVERRIDE_UNTIL_EPOCH: Optional[float] = None
_OVERRIDE_SOURCE: Optional[str] = None

def get_active_mode() -> Optional[str]:
    return _ACTIVE_MODE

def _set_active_mode(name: str):
    global _ACTIVE_MODE
    _ACTIVE_MODE = name

def apply_manual_override(mode: str, source: str, ttl_seconds: int = 900, reason: str = ""):
    """
    Elevate human command above autonomous triggers for TTL.
    """
    global _OVERRIDE_UNTIL_EPOCH, _OVERRIDE_SOURCE
    _set_active_mode(mode)
    _OVERRIDE_UNTIL_EPOCH = time.time() + ttl_seconds
    _OVERRIDE_SOURCE = source
    audit_event("manual_override_applied", {
        "mode": mode, "source": source, "ttl_s": ttl_seconds, "reason": reason
    })

def is_override_active() -> bool:
    return bool(_OVERRIDE_UNTIL_EPOCH and time.time() < _OVERRIDE_UNTIL_EPOCH)

def clear_manual_override():
    global _OVERRIDE_UNTIL_EPOCH, _OVERRIDE_SOURCE
    _OVERRIDE_UNTIL_EPOCH = None
    _OVERRIDE_SOURCE = None
    audit_event("manual_override_cleared", {})

def send_tier1_immediate(message:str):
    # Tier 1 (0s): instant iMessage + system notification
    phone_number = os.getenv("IPHONE_NUMBER", os.getenv("ATHENA_ALERT_PHONE", ""))
    if phone_number:
        _send_imessage(phone_number, f"🚨 Athena Alert: {message}")
    _send_system_notification("AI Republic Alert", message, "Ping")
    return True

def send_tier2_followup(details:str):
    # Tier 2 (+2s): richer iMessage (split long messages) + notification
    time.sleep(2)
    phone_number = os.getenv("IPHONE_NUMBER", os.getenv("ATHENA_ALERT_PHONE", ""))

    chunks = [details[i:i+1450] for i in range(0, len(details), 1450)]
    for idx, c in enumerate(chunks, 1):
        prefix = "" if len(chunks)==1 else f"({idx}/{len(chunks)}) "
        if phone_number:
            _send_imessage(phone_number, prefix + c)
        _send_system_notification("AI Republic Details", prefix + c, "Blow")
    return True

def send_tier3_escalation(tts_text:str, minutes_to_escalate:int, ack_id:str):
    # Tier 3 (+N min unless acknowledged): voice alert + repeated notifications
    def _monitor():
        deadline = time.time() + minutes_to_escalate*60
        ack_path = f"/tmp/athena_alert_ack_{ack_id}"
        notified = False

        while time.time() < deadline:
            if os.path.exists(ack_path):
                # Play acknowledgment confirmation
                _play_sound_and_speak("Alert acknowledged. Standing down.")
                _send_system_notification("Alert Acknowledged", "Escalation stopped.", "Blow")
                return

            # Send escalating notifications every 30 seconds
            if not notified or (time.time() - notified) > 30:
                _play_sound_and_speak(tts_text)
                _send_system_notification("AI REPUBLIC EMERGENCY", tts_text, "Sosumi")
                notified = time.time()

            time.sleep(5)

        # If we reach here, escalation timed out without acknowledgment
        _play_sound_and_speak("Alert escalation timed out. System requires attention.")
        _send_system_notification("ESCALATION TIMEOUT", "Alert was not acknowledged. Manual intervention required.", "Funk")

    threading.Thread(target=_monitor, daemon=True).start()
    return True

# Quiet Hours Configuration
QUIET_HOURS_ENABLED = os.getenv("QUIET_HOURS_ENABLED", "false").lower() == "true"
QUIET_HOURS_START = int(os.getenv("QUIET_HOURS_START", "22"))  # 10 PM
QUIET_HOURS_END = int(os.getenv("QUIET_HOURS_END", "8"))      # 8 AM

# Focus Mode Integration (iPhone)
FOCUS_MODE_ENABLED = os.getenv("FOCUS_MODE_ENABLED", "false").lower() == "true"
FOCUS_MODE_CHECK_INTERVAL = int(os.getenv("FOCUS_MODE_CHECK_INTERVAL", "300"))  # 5 minutes

# Calendar Integration
CALENDAR_ENABLED = os.getenv("CALENDAR_ENABLED", "false").lower() == "true"
CALENDAR_BUSY_KEYWORDS = os.getenv("CALENDAR_BUSY_KEYWORDS", "meeting,sleep,busy,do not disturb").split(",")

# Location-Based Alerting
LOCATION_ENABLED = os.getenv("LOCATION_ENABLED", "false").lower() == "true"
LOCATION_CHECK_INTERVAL = int(os.getenv("LOCATION_CHECK_INTERVAL", "600"))  # 10 minutes
LOCATION_HOME_NETWORKS = os.getenv("LOCATION_HOME_NETWORKS", "").split(",") if os.getenv("LOCATION_HOME_NETWORKS") else []
LOCATION_WORK_NETWORKS = os.getenv("LOCATION_WORK_NETWORKS", "").split(",") if os.getenv("LOCATION_WORK_NETWORKS") else []
LOCATION_TRAVEL_KEYWORDS = os.getenv("LOCATION_TRAVEL_KEYWORDS", "hotel,airport,travel,remote").split(",")

# Geofencing (GPS-based)
GEOFENCING_ENABLED = os.getenv("GEOFENCING_ENABLED", "false").lower() == "true"
GEOFENCING_CHECK_INTERVAL = int(os.getenv("GEOFENCING_CHECK_INTERVAL", "300"))  # 5 minutes

# Geographic zones (lat,lng,radius_meters)
HOME_LAT = float(os.getenv("HOME_LAT", "0"))
HOME_LNG = float(os.getenv("HOME_LNG", "0"))
HOME_RADIUS = int(os.getenv("HOME_RADIUS", "100"))  # meters

WORK_LAT = float(os.getenv("WORK_LAT", "0"))
WORK_LNG = float(os.getenv("WORK_LNG", "0"))
WORK_RADIUS = int(os.getenv("WORK_RADIUS", "200"))  # meters

# Travel detection (distance from home > threshold)
TRAVEL_DISTANCE_THRESHOLD = int(os.getenv("TRAVEL_DISTANCE_THRESHOLD", "50000"))  # 50km

# Advanced Geofencing Features
ADAPTIVE_RADIUS_ENABLED = os.getenv("ADAPTIVE_RADIUS_ENABLED", "false").lower() == "true"
TRANSITION_SMOOTHING_ENABLED = os.getenv("TRANSITION_SMOOTHING_ENABLED", "false").lower() == "true"
TRANSITION_COOLDOWN_SECONDS = int(os.getenv("TRANSITION_COOLDOWN_SECONDS", "300"))  # 5 minutes

# Zone Chaining & Predictive Awareness
ZONE_CHAINING_ENABLED = os.getenv("ZONE_CHAINING_ENABLED", "false").lower() == "true"
LEARNING_THRESHOLD = int(os.getenv("LEARNING_THRESHOLD", "3"))  # Visits needed to learn a location
PREDICTIVE_HORIZON_HOURS = int(os.getenv("PREDICTIVE_HORIZON_HOURS", "2"))  # Hours to look ahead
CHAIN_CONFIDENCE_THRESHOLD = float(os.getenv("CHAIN_CONFIDENCE_THRESHOLD", "0.7"))  # 70% confidence

# Adaptive radius multipliers (based on context)
RADIUS_HOME_DAY_MULTIPLIER = float(os.getenv("RADIUS_HOME_DAY_MULTIPLIER", "1.0"))    # Daytime home
RADIUS_HOME_NIGHT_MULTIPLIER = float(os.getenv("RADIUS_HOME_NIGHT_MULTIPLIER", "1.5")) # Nighttime home (larger)
RADIUS_WORK_WEEKDAY_MULTIPLIER = float(os.getenv("RADIUS_WORK_WEEKDAY_MULTIPLIER", "1.0")) # Work weekdays
RADIUS_WORK_WEEKEND_MULTIPLIER = float(os.getenv("RADIUS_WORK_WEEKEND_MULTIPLIER", "0.8")) # Work weekends (smaller)

def is_focus_mode_active() -> bool:
    """Check if iPhone Focus mode is active (simplified - would need iCloud API)"""
    if not FOCUS_MODE_ENABLED:
        return False

    # Check for explicit focus mode override (for testing/simulations)
    focus_override = os.getenv("FOCUS_MODE_ACTIVE", "false").lower() == "true"
    if focus_override:
        return True

    # In a real implementation, this would query iCloud for Focus mode status
    # For now, we use a simplified heuristic based on time
    from datetime import datetime
    now = datetime.now()
    current_hour = now.hour

    # Assume Focus mode active during typical sleep hours
    # This is a placeholder - real implementation would check iPhone/iCloud
    return is_quiet_hours()

def is_calendar_busy() -> bool:
    """Check if calendar shows user as busy (simplified)"""
    if not CALENDAR_ENABLED:
        return False

    # In a real implementation, this would query Calendar API
    # For now, check for busy keywords in a status file
    try:
        with open(os.path.expanduser("~/.ai_republic_calendar_status"), "r") as f:
            status = f.read().strip().lower()
            return any(keyword.strip() in status for keyword in CALENDAR_BUSY_KEYWORDS)
    except:
        return False

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two GPS coordinates in meters (Haversine formula)"""
    from math import radians, sin, cos, sqrt, atan2

    # Earth's radius in meters
    R = 6371000

    # Convert to radians
    lat1_rad, lng1_rad = radians(lat1), radians(lng1)
    lat2_rad, lng2_rad = radians(lat2), radians(lng2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c

def get_current_gps_location() -> tuple:
    """Get current GPS coordinates (simplified - would use actual GPS)"""
    # Check for GPS override (for testing)
    gps_override = os.getenv("GPS_OVERRIDE", "")
    if gps_override:
        try:
            lat, lng = map(float, gps_override.split(","))
            return lat, lng
        except:
            pass

    # In a real implementation, this would query GPS/location services
    # For now, check location status file for coordinates
    try:
        with open(os.path.expanduser("~/.ai_republic_gps_status"), "r") as f:
            line = f.read().strip()
            lat, lng = map(float, line.split(","))
            return lat, lng
    except:
        pass

    # Return default (would be current device location in real implementation)
    return 0.0, 0.0

def get_adaptive_radius(zone_type: str) -> int:
    """Calculate adaptive radius based on time, day, and context"""
    if not ADAPTIVE_RADIUS_ENABLED:
        return HOME_RADIUS if zone_type == "home" else WORK_RADIUS

    from datetime import datetime
    now = datetime.now()
    current_hour = now.hour
    weekday = now.weekday() < 5  # Monday-Friday

    if zone_type == "home":
        # Home radius: larger at night for safety buffer
        if 22 <= current_hour or current_hour < 6:  # Night hours
            return int(HOME_RADIUS * RADIUS_HOME_NIGHT_MULTIPLIER)
        else:  # Daytime
            return int(HOME_RADIUS * RADIUS_HOME_DAY_MULTIPLIER)
    elif zone_type == "work":
        # Work radius: smaller on weekends when fewer people
        if weekday:
            return int(WORK_RADIUS * RADIUS_WORK_WEEKDAY_MULTIPLIER)
        else:
            return int(WORK_RADIUS * RADIUS_WORK_WEEKEND_MULTIPLIER)

    return HOME_RADIUS if zone_type == "home" else WORK_RADIUS

def check_transition_cooldown(last_transition: float, current_time: float) -> bool:
    """Check if enough time has passed since last transition to prevent spam"""
    if not TRANSITION_SMOOTHING_ENABLED:
        return True

    return (current_time - last_transition) >= TRANSITION_COOLDOWN_SECONDS

def learn_location_patterns():
    """Learn frequently visited locations and movement patterns"""
    if not ZONE_CHAINING_ENABLED:
        return

    try:
        current_lat, current_lng = get_current_gps_location()
        if current_lat == 0.0 and current_lng == 0.0:
            return

        import time
        current_time = time.time()

        # Load existing patterns
        patterns_file = "/tmp/ai_republic_location_patterns.json"
        try:
            with open(patterns_file, "r") as f:
                patterns = json.load(f)
        except:
            patterns = {"locations": {}, "chains": {}}

        # Round coordinates to create location clusters (reduce GPS noise)
        lat_rounded = round(current_lat, 4)  # ~10m precision
        lng_rounded = round(current_lng, 4)

        location_key = f"{lat_rounded},{lng_rounded}"

        # Record visit
        if location_key not in patterns["locations"]:
            patterns["locations"][location_key] = {
                "visits": 0,
                "first_visit": current_time,
                "last_visit": current_time,
                "coordinates": [current_lat, current_lng],
                "visit_times": []
            }

        patterns["locations"][location_key]["visits"] += 1
        patterns["locations"][location_key]["last_visit"] = current_time
        patterns["locations"][location_key]["visit_times"].append(current_time)

        # Keep only recent visits (last 30 days)
        cutoff_time = current_time - (30 * 24 * 60 * 60)
        patterns["locations"][location_key]["visit_times"] = [
            t for t in patterns["locations"][location_key]["visit_times"] if t > cutoff_time
        ]

        # Save patterns
        with open(patterns_file, "w") as f:
            json.dump(patterns, f)

    except Exception as e:
        print(f"Pattern learning error: {e}")

def predict_next_location(current_location: str, current_time: float) -> dict:
    """Predict next location based on movement patterns"""
    if not ZONE_CHAINING_ENABLED:
        return {"location": "unknown", "confidence": 0.0, "eta_seconds": 0}

    try:
        patterns_file = "/tmp/ai_republic_location_patterns.json"
        with open(patterns_file, "r") as f:
            patterns = json.load(f)

        # Find movement chains involving current location
        current_lat, current_lng = get_current_gps_location()
        current_key = f"{round(current_lat, 4)},{round(current_lng, 4)}"

        best_prediction = {"location": "unknown", "confidence": 0.0, "eta_seconds": 0}

        # Look for chains starting from current location
        for chain_key, chain_data in patterns.get("chains", {}).items():
            if chain_key.startswith(current_key + "->"):
                next_location = chain_key.split("->")[1]
                confidence = chain_data.get("confidence", 0.0)
                avg_time = chain_data.get("avg_transition_seconds", 0)

                if confidence > best_prediction["confidence"]:
                    best_prediction = {
                        "location": next_location,
                        "confidence": confidence,
                        "eta_seconds": avg_time
                    }

        return best_prediction

    except Exception as e:
        print(f"Prediction error: {e}")
        return {"location": "unknown", "confidence": 0.0, "eta_seconds": 0}

def get_location_alert_profile(location: str) -> dict:
    """Get alert profile for a learned location"""
    if not ZONE_CHAINING_ENABLED:
        return {"name": "unknown", "alert_modifier": 1.0, "description": "Unknown location"}

    try:
        patterns_file = "/tmp/ai_republic_location_patterns.json"
        with open(patterns_file, "r") as f:
            patterns = json.load(f)

        # Check if this is a learned location
        for loc_key, loc_data in patterns.get("locations", {}).items():
            if loc_data["visits"] >= LEARNING_THRESHOLD:
                # This is a frequently visited location
                lat, lng = loc_data["coordinates"]

                # Determine location type based on patterns
                if is_near_home(lat, lng):
                    return {
                        "name": "home-like",
                        "alert_modifier": 1.2,  # Slightly more permissive
                        "description": "Frequently visited home-like location"
                    }
                elif is_near_work(lat, lng):
                    return {
                        "name": "work-like",
                        "alert_modifier": 0.8,  # More restrictive
                        "description": "Frequently visited work-like location"
                    }
                else:
                    return {
                        "name": "recurring",
                        "alert_modifier": 0.9,  # Slightly more restrictive
                        "description": "Frequently visited location"
                    }

        return {"name": "unknown", "alert_modifier": 1.0, "description": "Unknown location"}

    except Exception:
        return {"name": "unknown", "alert_modifier": 1.0, "description": "Error determining profile"}

def is_near_home(lat: float, lng: float) -> bool:
    """Check if coordinates are near home zone"""
    home_distance = calculate_distance(lat, lng, HOME_LAT, HOME_LNG)
    return home_distance <= HOME_RADIUS * 2  # 2x radius for "near home"

def is_near_work(lat: float, lng: float) -> bool:
    """Check if coordinates are near work zone"""
    work_distance = calculate_distance(lat, lng, WORK_LAT, WORK_LNG)
    return work_distance <= WORK_RADIUS * 2  # 2x radius for "near work"

def detect_location_by_geofence() -> str:
    """Detect location using GPS geofencing with adaptive radius and transition smoothing"""
    if not GEOFENCING_ENABLED:
        return "unknown"

    try:
        current_lat, current_lng = get_current_gps_location()

        # Skip if no valid GPS coordinates
        if current_lat == 0.0 and current_lng == 0.0:
            return "unknown"

        # Get current time for transition smoothing
        import time
        current_time = time.time()

        # Check last known location and transition time
        last_location = "unknown"
        last_transition = 0.0
        try:
            with open("/tmp/ai_republic_geofence_state.json", "r") as f:
                state = json.load(f)
                last_location = state.get("location", "unknown")
                last_transition = state.get("last_transition", 0.0)
        except:
            pass

        # Check distance to home (with adaptive radius)
        home_radius = get_adaptive_radius("home")
        home_distance = calculate_distance(current_lat, current_lng, HOME_LAT, HOME_LNG)

        # Check distance to work (with adaptive radius)
        work_radius = get_adaptive_radius("work")
        work_distance = calculate_distance(current_lat, current_lng, WORK_LAT, WORK_LNG)

        # Determine current zone
        current_zone = "unknown"
        if home_distance <= home_radius:
            current_zone = "home"
        elif work_distance <= work_radius:
            current_zone = "work"
        elif home_distance > TRAVEL_DISTANCE_THRESHOLD:
            current_zone = "travel"

        # Apply transition smoothing (hysteresis)
        if TRANSITION_SMOOTHING_ENABLED and last_location != current_zone:
            # If transitioning from home to work, require stronger signal
            if last_location == "home" and current_zone == "work":
                # Need to be deeper into work zone to prevent bouncing
                if work_distance > work_radius * 0.7:  # Require 70% confidence
                    current_zone = "home"  # Stay in home
            elif last_location == "work" and current_zone == "home":
                # Need to be deeper into home zone
                if home_distance > home_radius * 0.7:
                    current_zone = "work"  # Stay in work

            # Check cooldown period
            if not check_transition_cooldown(last_transition, current_time):
                current_zone = last_location  # Prevent rapid transitions
            else:
                # Update transition state
                state = {
                    "location": current_zone,
                    "last_transition": current_time,
                    "lat": current_lat,
                    "lng": current_lng
                }
                try:
                    with open("/tmp/ai_republic_geofence_state.json", "w") as f:
                        json.dump(state, f)
                except:
                    pass

        return current_zone

    except Exception as e:
        print(f"Geofencing error: {e}")
        return "unknown"

def get_current_location() -> str:
    """Determine current location context with geofencing priority"""
    if not LOCATION_ENABLED:
        return "unknown"

    # Check for explicit location override (for testing/simulations)
    location_override = os.getenv("LOCATION_OVERRIDE", "").lower()
    if location_override in ["home", "work", "travel"]:
        return location_override

    # Priority 1: GPS Geofencing (most accurate)
    geofence_location = detect_location_by_geofence()
    if geofence_location != "unknown":
        return geofence_location

    # Priority 2: WiFi network detection
    try:
        import subprocess
        result = subprocess.run(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Parse SSID from airport output
            for line in result.stdout.split('\n'):
                if 'SSID:' in line:
                    ssid = line.split('SSID:')[1].strip()
                    if ssid in LOCATION_HOME_NETWORKS:
                        return "home"
                    elif ssid in LOCATION_WORK_NETWORKS:
                        return "work"
    except:
        pass

    # Priority 3: Travel keywords in status files
    try:
        with open(os.path.expanduser("~/.ai_republic_location_status"), "r") as f:
            location_status = f.read().strip().lower()
            if any(keyword.strip() in location_status for keyword in LOCATION_TRAVEL_KEYWORDS):
                return "travel"
    except:
        pass

    # Priority 4: Time-based default (9-5 work, else home)
    from datetime import datetime
    now = datetime.now()
    current_hour = now.hour
    weekday = now.weekday() < 5  # Monday-Friday

    if 9 <= current_hour <= 17 and weekday:
        return "work"  # Business hours on weekdays
    else:
        return "home"  # Default assumption

def should_send_alert_by_location(severity: str, location: str) -> bool:
    """Check if alert should be sent based on location context"""
    # Always send critical alerts regardless of location
    if severity in ["urgent", "critical"]:
        return True

    # Location-specific rules
    if location == "home":
        # At home: more permissive, allow most alerts
        return severity in ["info", "warning", "urgent", "critical"]

    elif location == "work":
        # At work: stricter, suppress info alerts during work hours
        return severity in ["warning", "urgent", "critical"]

    elif location == "travel":
        # While traveling: minimal alerts, only warnings and above
        return severity in ["warning", "urgent", "critical"]

    # Unknown location: default to restrictive
    return severity in ["warning", "urgent", "critical"]

def should_send_alert_smart(severity: str) -> bool:
    """Enhanced alert filtering with Focus mode, calendar, and location awareness"""
    # Always send critical alerts (emergency override)
    if severity in ["urgent", "critical"]:
        return True

    # Get current context
    location = get_current_location()
    focus_active = is_focus_mode_active()
    calendar_busy = is_calendar_busy()

    # Priority order: most restrictive rule wins
    # 1. Focus mode (highest priority - user explicitly requested silence)
    if focus_active:
        return False  # Suppress all non-critical during Focus

    # 2. Location-based rules
    if not should_send_alert_by_location(severity, location):
        return False

    # 3. Calendar busy (meeting/conference calls)
    if calendar_busy:
        if severity == "info":
            return False  # Suppress info during busy calendar
        # Allow warnings and above
        return True

    # 4. Fall back to standard quiet hours logic
    return should_send_alert(severity)

def update_smart_alerting():
    """Update alerting behavior based on current context with predictive awareness"""
    focus_active = is_focus_mode_active()
    calendar_busy = is_calendar_busy()
    quiet_hours = is_quiet_hours()
    location = get_current_location()

    # Learn location patterns for zone chaining
    learn_location_patterns()

    # Get predictive context
    prediction = predict_next_location(location, time.time())
    location_profile = get_location_alert_profile(location)

    context = {
        "focus_mode": focus_active,
        "calendar_busy": calendar_busy,
        "quiet_hours": quiet_hours,
        "location": location,
        "predicted_next": prediction.get("location", "unknown"),
        "prediction_confidence": prediction.get("confidence", 0.0),
        "eta_seconds": prediction.get("eta_seconds", 0),
        "location_profile": location_profile,
        "timestamp": time.time()
    }

    # Save context for dashboard
    try:
        with open("/tmp/ai_republic_context.json", "w") as f:
            json.dump(context, f)
    except:
        pass

    return context

def is_quiet_hours() -> bool:
    """Check if current time is within quiet hours"""
    if not QUIET_HOURS_ENABLED:
        return False

    from datetime import datetime
    now = datetime.now()
    current_hour = now.hour

    if QUIET_HOURS_START > QUIET_HOURS_END:  # e.g., 22:00 to 08:00
        return current_hour >= QUIET_HOURS_START or current_hour < QUIET_HOURS_END
    else:  # e.g., 01:00 to 06:00
        return QUIET_HOURS_START <= current_hour < QUIET_HOURS_END

def should_send_alert(severity: str) -> bool:
    """Determine if alert should be sent based on severity and quiet hours"""
    if severity == "info":
        # Info alerts never sent during quiet hours
        return not is_quiet_hours()
    elif severity == "warning":
        # Warning alerts sent but without voice during quiet hours
        return True
    elif severity == "urgent" or severity == "critical":
        # Critical alerts always sent (emergency override)
        return True
    return True

def should_send_voice_alert(severity: str) -> bool:
    """Determine if voice alert should be sent"""
    if is_quiet_hours():
        # During quiet hours, only send voice for critical alerts
        return severity in ["urgent", "critical"]
    return True

# Voice notification system for weekly summaries
VOICE_NOTIFICATIONS_ENABLED = os.getenv("VOICE_NOTIFICATIONS_ENABLED", "false").lower() == "true"
VOICE_NOTIFICATION_CONTEXTS = os.getenv("VOICE_NOTIFICATION_CONTEXTS", "driving,focus").split(",")  # When to use voice
VOICE_SUMMARY_LENGTH = os.getenv("VOICE_SUMMARY_LENGTH", "brief").lower()  # brief, normal, detailed

# Command routing system
COMMAND_ROUTING_ENABLED = os.getenv("COMMAND_ROUTING_ENABLED", "false").lower() == "true"

# Voice activation system - Korono-first architecture
VOICE_ACTIVATION_ENABLED = os.getenv("VOICE_ACTIVATION_ENABLED", "false").lower() == "true"
WAKE_WORD = os.getenv("WAKE_WORD", "hey athena").lower()
VOICE_ACTIVATION_TIMEOUT = int(os.getenv("VOICE_ACTIVATION_TIMEOUT", "10"))  # seconds

# Korono-first voice stack
VOICE_ENGINE = os.getenv("VOICE_ENGINE", "korono")  # korono, whisper, google
KORONO_STT_MODEL = os.getenv("KORONO_STT_MODEL", "korono-stt-v1")
KORONO_TTS_VOICE = os.getenv("KORONO_TTS_VOICE", "athena-neutral")
KORONO_SAMPLE_RATE = int(os.getenv("KORONO_SAMPLE_RATE", "16000"))
KORONO_VAD = os.getenv("KORONO_VAD", "true").lower() == "true"

# Wake word (Porcupine-only, no competition)
USE_PORCUPINE_WAKE = os.getenv("USE_PORCUPINE_WAKE", "true").lower() == "true"
WAKE_SENSITIVITY = float(os.getenv("WAKE_SENSITIVITY", "0.5"))

# Voice behavior
VOICE_HALF_DUPLEX = os.getenv("VOICE_HALF_DUPLEX", "true").lower() == "true"
PHRASE_TIME_LIMIT = int(os.getenv("PHRASE_TIME_LIMIT", "3"))
VOICE_OVERRIDE_TTL = int(os.getenv("VOICE_OVERRIDE_TTL", "900"))  # 15 minutes

# Legacy support (deprecated)
USE_LOCAL_STT = os.getenv("USE_LOCAL_STT", "false").lower() == "true"
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")

# Context-reactive macros
CONTEXT_MACROS_ENABLED = os.getenv("CONTEXT_MACROS_ENABLED", "false").lower() == "true"
MACRO_CHECK_INTERVAL = int(os.getenv("MACRO_CHECK_INTERVAL", "60"))  # seconds
COMMAND_INTENT_SCHEMA = {
    "status": ["status", "health", "check", "system", "dashboard"],
    "alerts": ["alerts", "notifications", "warnings", "issues"],
    "controls": ["start", "stop", "restart", "enable", "disable", "configure"],
    "queries": ["what", "how", "when", "where", "why", "analyze", "explain"],
    "actions": ["acknowledge", "dismiss", "escalate", "resolve"]
}

# Voice acknowledgment system
_ack_listeners = {}

def should_use_voice_notifications() -> bool:
    """Determine if voice notifications should be used based on context"""
    if not VOICE_NOTIFICATIONS_ENABLED:
        return False

    # Check current context
    context = update_smart_alerting()

    # Use voice during focus mode (hands-free)
    if context.get("focus_mode"):
        return "focus" in VOICE_NOTIFICATION_CONTEXTS

    # Use voice when location suggests driving/travel
    location = context.get("location", "")
    if location in ["travel", "driving"] or context.get("predicted_next") == "travel":
        return "driving" in VOICE_NOTIFICATION_CONTEXTS

    # Use voice during quiet hours (complementary to text)
    if context.get("quiet_hours"):
        return "quiet" in VOICE_NOTIFICATION_CONTEXTS

    return False

def generate_voice_summary(weekly_data: dict) -> str:
    """Generate a spoken summary of weekly learning data"""
    confidence = weekly_data.get("overall_confidence", 0)
    patterns_found = weekly_data.get("patterns_found", 0)
    prep_time = weekly_data.get("preferred_prep_time", 0)
    recommendations = len(weekly_data.get("recommendations", []))

    if VOICE_SUMMARY_LENGTH == "brief":
        summary = f"Athena weekly summary: Confidence {confidence} percent, {patterns_found} patterns found, {recommendations} recommendations ready."
    elif VOICE_SUMMARY_LENGTH == "detailed":
        summary = f"Athena weekly learning summary. Overall confidence is {confidence} percent. Found {patterns_found} behavioral patterns. Your preferred preparation time is {prep_time} minutes. {recommendations} recommendations are ready for review. Check the dashboard for full details."
    else:  # normal
        summary = f"Athena weekly update: Confidence at {confidence} percent with {patterns_found} patterns identified. Preferred prep time is {prep_time} minutes. {recommendations} recommendations available in the dashboard."

    return summary

def send_voice_notification(message: str, priority: str = "info") -> bool:
    """Send a voice notification using macOS text-to-speech"""
    try:
        # Use macOS 'say' command for text-to-speech
        import subprocess
        result = subprocess.run(["say", message], capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"Voice notification failed: {e}")
        return False

def classify_command_intent(text: str) -> dict:
    """Classify user command intent using enhanced keyword matching"""
    if not COMMAND_ROUTING_ENABLED:
        return {"intent": "unknown", "confidence": 0.0, "action": None}

    text_lower = text.lower().strip()

    # Enhanced keyword schema with phrases and patterns
    enhanced_schema = {
        "status": ["status", "health", "check", "system", "dashboard", "running", "working", "how is", "what's up"],
        "alerts": ["alerts", "notifications", "warnings", "issues", "problems", "acknowledge", "dismiss", "clear"],
        "controls": ["start", "stop", "restart", "enable", "disable", "configure", "turn on", "turn off"],
        "queries": ["what", "how", "when", "where", "why", "analyze", "explain", "tell me", "show me"],
        "actions": ["acknowledge", "dismiss", "escalate", "resolve", "confirm", "got it", "understood"]
    }

    # Calculate scores using both word matches and phrase matches
    intent_scores = {}
    for intent, keywords in enhanced_schema.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                # Give higher weight to exact phrase matches
                if keyword in ["what's up", "how is", "show me", "tell me", "turn on", "turn off", "got it"]:
                    score += 2
                else:
                    score += 1
        intent_scores[intent] = score

    # Find best intent
    best_intent = max(intent_scores, key=intent_scores.get)
    max_score = intent_scores[best_intent]

    # Normalize confidence (max possible score is around 10-15)
    confidence = min(max_score / 5.0, 1.0)  # Normalize to 0-1 range

    # Determine action based on intent + context
    action = determine_command_action(best_intent, text_lower, confidence)

    return {
        "intent": best_intent,
        "confidence": confidence,
        "action": action,
        "original_text": text
    }

def determine_command_action(intent: str, text: str, confidence: float) -> dict:
    """Determine specific action to take based on classified intent"""
    if confidence < 0.1:  # Lower confidence threshold
        return {"type": "clarify", "message": "I didn't understand that command. Try 'system status', 'check alerts', or 'acknowledge'."}

    if intent == "status":
        return {"type": "status_report", "target": "system"}

    elif intent == "alerts":
        if "acknowledge" in text or "dismiss" in text or "clear" in text:
            return {"type": "alert_action", "action": "acknowledge"}
        return {"type": "alert_query", "filter": "active"}

    elif intent == "controls":
        if "start" in text or "enable" in text or "turn on" in text:
            return {"type": "service_control", "action": "start", "service": extract_service_name(text)}
        elif "stop" in text or "disable" in text or "turn off" in text:
            return {"type": "service_control", "action": "stop", "service": extract_service_name(text)}
        elif "restart" in text:
            return {"type": "service_control", "action": "restart", "service": extract_service_name(text)}
        return {"type": "clarify", "message": "Specify what to start, stop, or restart."}

    elif intent == "queries":
        return {"type": "information_query", "topic": extract_query_topic(text)}

    elif intent == "actions":
        return {"type": "alert_action", "action": "acknowledge"}

    return {"type": "unknown"}

def extract_service_name(text: str) -> str:
    """Extract service name from control command"""
    services = ["alerting", "monitoring", "learning", "dashboard", "voice", "location"]
    for service in services:
        if service in text:
            return service
    return "unknown"

def extract_query_topic(text: str) -> str:
    """Extract topic from query command"""
    topics = ["alerts", "status", "performance", "learning", "system", "health"]
    for topic in topics:
        if topic in text:
            return topic
    return "general"

def execute_command_action(action: dict) -> str:
    """Execute the determined command action and return response"""
    action_type = action.get("type")

    if action_type == "status_report":
        context = update_smart_alerting()
        return f"System Status: {len([k for k, v in context.items() if isinstance(v, bool) and v])} services active. Confidence: {context.get('location_profile', {}).get('alert_modifier', 1.0):.1f}x"

    elif action_type == "alert_query":
        return "Active alerts: 0 critical, 0 warnings. All systems nominal."

    elif action_type == "alert_action":
        return f"Alert {action.get('action', 'processed')}."

    elif action_type == "service_control":
        service = action.get("service", "unknown")
        cmd_action = action.get("action", "unknown")
        return f"Service '{service}' {cmd_action} command acknowledged."

    elif action_type == "information_query":
        topic = action.get("topic", "general")
        return f"Information about {topic}: Available in dashboard."

    elif action_type == "clarify":
        return action.get("message", "Please clarify your request.")

    return "Command executed."

def process_voice_command(text: str) -> str:
    """Process a voice command through the routing system with voice arbitration"""
    if not COMMAND_ROUTING_ENABLED:
        return "Voice commands are not enabled."

    # Special handling for diagnostics and tuning commands
    if "diagnostics" in text.lower() or "diagnostic" in text.lower():
        return generate_voice_diagnostics()

    if "tune" in text.lower() or "voice tune" in text.lower():
        return voice_tune_command(text)

    # Classify intent
    classification = classify_command_intent(text)

    # Log for learning
    print(f"Command classified: {classification}")

    # Voice priority arbitration - voice commands can override automation
    intent = classification.get("intent", "")
    if intent in ["status", "alerts", "controls"] and "override" in text.lower():
        # Voice command conflicts with automation - apply override
        mode_to_override = voice_command_to_mode(intent)
        if mode_to_override:
            apply_manual_override(mode_to_override, "voice", VOICE_OVERRIDE_TTL)
            audit_event("voice_override_applied", {
                "command": text,
                "intent": intent,
                "mode": mode_to_override,
                "ttl_seconds": VOICE_OVERRIDE_TTL
            })

    # Execute action
    response = execute_command_action(classification["action"])

    return response

def voice_command_to_mode(intent):
    """Map voice command intent to operational mode for override"""
    mapping = {
        "status": "normal_mode",
        "alerts": "normal_mode",
        "controls": None  # Depends on specific command
    }
    return mapping.get(intent)

def generate_voice_diagnostics():
    """Generate comprehensive voice system diagnostics"""
    diagnostics = []

    # System uptime
    uptime = get_system_uptime_human()
    diagnostics.append(f"System uptime {uptime}")

    # Voice engine health
    if VOICE_ENGINE_INSTANCE:
        health = VOICE_ENGINE_INSTANCE.health()
        stt_status = "OK" if health.get("stt") else "FAIL"
        tts_status = "OK" if health.get("tts") else "FAIL"
        diagnostics.append(f"Voice engine {stt_status}/{tts_status}")
    else:
        diagnostics.append("Voice engine not initialized")

    # Wake word status with buffer info
    buffer_info = f", buffer {VOICE_PRE_TRIGGER_BUFFER_MS}ms" if VOICE_BUFFER_CALIBRATION_ENABLED else ""
    diagnostics.append(f"Wake word '{WAKE_WORD}' active{buffer_info}")

    # Hot reload status
    hot_reload_status = "enabled" if VOICE_ENGINE_STARTED else "disabled"
    diagnostics.append(f"Hot reload {hot_reload_status}")

    # Voice tuning info
    tuning_info = f"Min gain {VOICE_MIN_GAIN}, sensitivity {WAKE_SENSITIVITY}"
    diagnostics.append(f"Voice tuning: {tuning_info}")

    # Command routing
    routing_status = "enabled" if COMMAND_ROUTING_ENABLED else "disabled"
    diagnostics.append(f"Command routing {routing_status}")

    # Macro system
    macro_count = len(MACRO_TEMPLATES) if MACRO_TEMPLATES else 0
    active_macros = len([m for m in ACTIVE_MACROS.keys() if ACTIVE_MACROS[m].get("expires_at", float('inf')) > time.time()])
    diagnostics.append(f"Macros loaded {macro_count}, active {active_macros}")

    # Join all diagnostics
    return ". ".join(diagnostics)

def initialize_voice_activation():
    """Initialize voice activation with Korono-first architecture and idempotent safeguards"""
    global VOICE_ENGINE_INSTANCE, VOICE_ENGINE_STARTED

    if not VOICE_ACTIVATION_ENABLED:
        print("Voice activation is disabled")
        return False

    # Idempotent initialization - prevent multiple starts
    with VOICE_ENGINE_LOCK:
        if VOICE_ENGINE_STARTED:
            print("✅ Voice activation already running")
            return True

        # Initialize voice engine based on configuration
        if VOICE_ENGINE == "korono":
            VOICE_ENGINE_INSTANCE = KoronoEngine(
                stt_model=KORONO_STT_MODEL,
                tts_voice=KORONO_TTS_VOICE,
                sample_rate=KORONO_SAMPLE_RATE,
                vad_enabled=KORONO_VAD
            )
        elif VOICE_ENGINE == "whisper":
            # Fallback to legacy Whisper implementation
            print("⚠️ Using legacy Whisper engine - consider upgrading to Korono")
            return initialize_cloud_voice_activation()
        else:
            print(f"❌ Unknown voice engine: {VOICE_ENGINE}")
            return False

        # Start the engine
        if not VOICE_ENGINE_INSTANCE.start():
            print("❌ Voice engine failed to start")
            return False

        # Mark as started
        VOICE_ENGINE_STARTED = True

    # Start the wake word listener
    if USE_PORCUPINE_WAKE:
        success = initialize_porcupine_wake_listener()
    else:
        print("❌ Porcupine wake word is required for Korono-first architecture")
        return False

    if success:
        # Start watchdog thread
        start_voice_watchdog()

        # Start hot reload monitor
        initialize_voice_hot_reload_monitor()

        # Auto-calibrate pre-trigger buffer
        calibrate_pre_trigger_buffer()

        print("🎤 Korono-first voice activation fully initialized")
        print(f"   Engine: {VOICE_ENGINE}")
        print(f"   Wake Word: '{WAKE_WORD}'")
        print(f"   STT Model: {KORONO_STT_MODEL}")
        print(f"   TTS Voice: {KORONO_TTS_VOICE}")
        print(f"   Half-Duplex: {VOICE_HALF_DUPLEX}")
        print(f"   Pre-trigger Buffer: {VOICE_PRE_TRIGGER_BUFFER_MS}ms")
        print("   Hot Reload: Enabled")

    return success

def initialize_porcupine_wake_listener():
    """Initialize Porcupine wake word listener with Korono STT integration"""
    try:
        import pvporcupine
        import pyaudio
        import struct
        import threading
        import time

        def wake_listener_loop():
            # Initialize Porcupine
            try:
                if WAKE_WORD == "hey athena":
                    keyword = pvporcupine.KEYWORDS["hey google"]  # Closest match
                elif WAKE_WORD == "computer":
                    keyword = pvporcupine.KEYWORDS["computer"]
                elif WAKE_WORD == "alexa":
                    keyword = pvporcupine.KEYWORDS["alexa"]
                else:
                    print(f"❌ Unsupported wake word: {WAKE_WORD}. Using 'hey google'.")
                    keyword = pvporcupine.KEYWORDS["hey google"]

                porcupine = pvporcupine.create(keywords=[keyword])
                print("✅ Porcupine wake word engine initialized")

            except Exception as e:
                print(f"❌ Porcupine initialization failed: {e}")
                return

            # Audio setup
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )

            print("🎧 Listening for wake word...")

            try:
                while VOICE_ENGINE_STARTED:
                    # Read audio frame
                    pcm = audio_stream.read(porcupine.frame_length)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                    # Check for wake word
                    keyword_index = porcupine.process(pcm)

                    if keyword_index >= 0:
                        print("🎯 Wake word detected!")

                        # Play confirmation beep
                        play_confirmation_beep()

                        # Process command with Korono
                        success = process_korono_command_session(pa, porcupine.sample_rate)
                        if not success:
                            print("❌ Command processing failed")

            except KeyboardInterrupt:
                print("🛑 Voice activation stopped")
            finally:
                audio_stream.close()
                pa.terminate()
                porcupine.delete()

        # Start listener in background thread
        listener_thread = threading.Thread(target=wake_listener_loop, daemon=True)
        listener_thread.start()

        return True

    except ImportError as e:
        print(f"❌ Missing dependencies for voice activation: {e}")
        print("Install: pip install pvporcupine pyaudio")
        return False
    except Exception as e:
        print(f"❌ Voice activation setup failed: {e}")
        return False

def process_korono_command_session(pa, sample_rate):
    """Process a command session using Korono STT after wake word detection"""
    try:

        # Pause STT during any pending TTS (half-duplex)
        if VOICE_HALF_DUPLEX and VOICE_ENGINE_INSTANCE:
            VOICE_ENGINE_INSTANCE.pause_stt()

        # Record command audio
        command_audio = record_command_audio_session(pa, sample_rate, duration=PHRASE_TIME_LIMIT)

        # Resume STT
        if VOICE_HALF_DUPLEX and VOICE_ENGINE_INSTANCE:
            time.sleep(0.25)  # Brief pause to avoid self-triggering
            VOICE_ENGINE_INSTANCE.resume_stt()

        if command_audio is None:
            return False

        # Transcribe with Korono
        if VOICE_ENGINE_INSTANCE:
            command_text = VOICE_ENGINE_INSTANCE.stt(command_audio, sample_rate)
            command_text = command_text.strip()

            if command_text:
                print(f"📝 Korono STT: '{command_text}'")

                # Process command
                response = process_voice_command(command_text)

                # Generate context-aware voice response
                if response:
                    speak_with_context(response)

                return True
            else:
                print("❌ No speech detected or transcription failed")
                return False
        else:
            print("❌ Voice engine not available")
            return False

    except Exception as e:
        print(f"❌ Command processing error: {e}")
        return False

def record_command_audio_session(pa, sample_rate, duration=3.0):
    """Record command audio with proper session handling"""
    try:

        # Open audio stream for command recording
        stream = pa.open(
            rate=sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=1024
        )

        frames = []
        start_time = time.time()

        while time.time() - start_time < duration:
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)

        stream.close()

        # Convert to bytes for Korono
        audio_data = b''.join(frames)
        return audio_data

    except Exception as e:
        print(f"❌ Audio recording failed: {e}")
        return None

def speak_with_context(text):
    """Speak text with context-aware voice styling"""
    if not VOICE_ENGINE_INSTANCE:
        print(f"🤖 {text}")
        return

    # Get current mode for voice styling
    current_mode = get_active_mode() or "normal_mode"
    style = VOICE_STYLES.get(current_mode, VOICE_STYLES["normal_mode"])

    try:
        # Generate speech with mode-appropriate voice
        if hasattr(VOICE_ENGINE_INSTANCE, '_tts_client'):
            # Temporarily switch voice if Korono supports it
            original_voice = VOICE_ENGINE_INSTANCE._tts_client.voice
            VOICE_ENGINE_INSTANCE._tts_client.voice = style["voice"]

        audio_data = VOICE_ENGINE_INSTANCE.tts(text)

        # Apply gain
        gain = max(style["gain"], VOICE_MIN_GAIN)
        if gain != 1.0:
            audio_data = apply_audio_gain(audio_data, gain)

        # Play audio (half-duplex: pause STT during playback)
        if VOICE_HALF_DUPLEX:
            VOICE_ENGINE_INSTANCE.pause_stt()

        play_audio_blocking(audio_data, KORONO_SAMPLE_RATE)

        if VOICE_HALF_DUPLEX:
            time.sleep(0.5)  # Extra buffer
            VOICE_ENGINE_INSTANCE.resume_stt()

        # Restore original voice
        if hasattr(VOICE_ENGINE_INSTANCE, '_tts_client'):
            VOICE_ENGINE_INSTANCE._tts_client.voice = original_voice

    except Exception as e:
        print(f"❌ Voice synthesis failed: {e}")
        print(f"🤖 {text}")  # Fallback to text

def apply_audio_gain(audio_bytes, gain):
    """Apply gain to PCM16 audio data"""
    try:
        import numpy as np

        # Convert bytes to int16 array
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

        # Apply gain
        audio_array = (audio_array * gain).astype(np.int16)

        # Clip to prevent distortion
        audio_array = np.clip(audio_array, -32768, 32767)

        # Convert back to bytes
        return audio_array.tobytes()

    except Exception:
        return audio_bytes  # Return unchanged on error

def play_audio_blocking(audio_bytes, sample_rate):
    """Play audio data in blocking mode"""
    try:
        # Use macOS afplay for audio playback
        import subprocess
        import tempfile
        import os

        # Write to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

            # Simple WAV header + PCM16 data (basic implementation)
            wav_data = create_wav_header(audio_bytes, sample_rate, 1, 16)
            temp_file.write(wav_data)

        # Play with afplay
        subprocess.run(['afplay', temp_path], check=True, timeout=10)

        # Clean up
        os.unlink(temp_path)

    except Exception as e:
        print(f"❌ Audio playback failed: {e}")

def create_wav_header(pcm_data, sample_rate, channels, bits_per_sample):
    """Create minimal WAV header for PCM16 data"""
    import struct

    data_size = len(pcm_data)
    header_size = 44
    file_size = header_size + data_size - 8

    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', file_size, b'WAVE', b'fmt ', 16, 1, channels,
        sample_rate, sample_rate * channels * bits_per_sample // 8,
        channels * bits_per_sample // 8, bits_per_sample, b'data', data_size)

    return header + pcm_data

def start_voice_watchdog():
    """Start voice engine watchdog for health monitoring"""
    def watchdog_loop():
        while VOICE_ENGINE_STARTED:
            try:
                time.sleep(30)  # Check every 30 seconds

                if VOICE_ENGINE_INSTANCE:
                    health = VOICE_ENGINE_INSTANCE.health()
                    if health.get("status") != "healthy":
                        print("⚠️ Voice engine health check failed, attempting recovery...")

                        # Attempt restart
                        if VOICE_ENGINE_INSTANCE.start():
                            print("✅ Voice engine recovered")
                            audit_event("voice_watchdog_recovery", health)
                        else:
                            print("❌ Voice engine recovery failed")
                            audit_event("voice_watchdog_failure", health)

            except Exception as e:
                print(f"❌ Voice watchdog error: {e}")
                time.sleep(30)

    watchdog_thread = threading.Thread(target=watchdog_loop, daemon=True)
    watchdog_thread.start()
    print("👁️ Voice watchdog started")

def check_voice_config_hot_reload():
    """Check for voice configuration changes and hot reload if needed"""
    global VOICE_CONFIG_LAST_MODIFIED, VOICE_STYLES, VOICE_MIN_GAIN
    global KORONO_TTS_VOICE, WAKE_SENSITIVITY, VOICE_OVERRIDE_TTL

    if not os.path.exists(VOICE_CONFIG_FILE):
        return False

    try:
        current_mtime = os.path.getmtime(VOICE_CONFIG_FILE)
        if current_mtime <= VOICE_CONFIG_LAST_MODIFIED:
            return False

        # Load new configuration
        with open(VOICE_CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # Update voice styles
        if 'voice_styles' in config:
            VOICE_STYLES.update(config['voice_styles'])
            print("🔄 Hot reloaded voice styles")

        # Update global settings
        if 'voice_min_gain' in config:
            VOICE_MIN_GAIN = config['voice_min_gain']

        if 'korono_tts_voice' in config:
            KORONO_TTS_VOICE = config['korono_tts_voice']

        if 'wake_sensitivity' in config:
            WAKE_SENSITIVITY = config['wake_sensitivity']

        if 'voice_override_ttl' in config:
            VOICE_OVERRIDE_TTL = config['voice_override_ttl']

        VOICE_CONFIG_LAST_MODIFIED = current_mtime
        audit_event("voice_config_hot_reload", {"config_file": VOICE_CONFIG_FILE})
        print("🔄 Voice configuration hot reloaded")

        return True

    except Exception as e:
        print(f"❌ Voice config hot reload failed: {e}")
        return False

def calibrate_pre_trigger_buffer():
    """Auto-calibrate pre-trigger buffer based on system performance"""
    global VOICE_PRE_TRIGGER_BUFFER_MS

    if not VOICE_BUFFER_CALIBRATION_ENABLED:
        return

    try:
        # Measure system audio latency (simplified)
        # In production, this would measure actual audio pipeline latency
        measured_latency_ms = 150  # Placeholder - real measurement would be here

        # Set buffer to 2x measured latency + 100ms safety margin
        optimal_buffer = (measured_latency_ms * 2) + 100
        optimal_buffer = max(200, min(optimal_buffer, 800))  # Clamp to reasonable range

        if abs(optimal_buffer - VOICE_PRE_TRIGGER_BUFFER_MS) > 50:  # Only change if significant difference
            VOICE_PRE_TRIGGER_BUFFER_MS = optimal_buffer
            print(f"🎯 Auto-calibrated pre-trigger buffer to {optimal_buffer}ms")
            audit_event("pre_trigger_buffer_calibrated", {
                "buffer_ms": optimal_buffer,
                "measured_latency": measured_latency_ms
            })

    except Exception as e:
        print(f"❌ Pre-trigger buffer calibration failed: {e}")

def initialize_voice_hot_reload_monitor():
    """Start hot reload monitoring for voice configuration"""
    def hot_reload_monitor():
        while VOICE_ENGINE_STARTED:
            try:
                check_voice_config_hot_reload()
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"❌ Hot reload monitor error: {e}")
                time.sleep(5)

    if VOICE_ENGINE_STARTED:
        monitor_thread = threading.Thread(target=hot_reload_monitor, daemon=True)
        monitor_thread.start()
        print("🔄 Voice hot reload monitor started")

def save_voice_config_example():
    """Save an example voice configuration file for hot reload"""
    try:
        os.makedirs(os.path.dirname(VOICE_CONFIG_FILE), exist_ok=True)

        example_config = {
            "voice_styles": {
                "meeting_mode": {
                    "voice": "athena-quiet",
                    "gain": 0.85,
                    "brief": True
                },
                "emergency_mode": {
                    "voice": "athena-urgent",
                    "gain": 1.2,
                    "brief": True
                },
                "custom_mode": {
                    "voice": "athena-professional",
                    "gain": 1.0,
                    "brief": False
                }
            },
            "voice_min_gain": 0.8,
            "korono_tts_voice": "athena-neutral",
            "wake_sensitivity": 0.4,
            "voice_override_ttl": 1200,
            "_comments": {
                "voice_styles": "Mode-specific voice configurations",
                "voice_min_gain": "Minimum gain to prevent quiet speech",
                "korono_tts_voice": "Default TTS voice",
                "wake_sensitivity": "Wake word detection sensitivity (0.3-0.7)",
                "voice_override_ttl": "Override duration in seconds"
            }
        }

        with open(VOICE_CONFIG_FILE, 'w') as f:
            json.dump(example_config, f, indent=2)

        print(f"💾 Saved example voice config to {VOICE_CONFIG_FILE}")
        print("Edit this file and changes will hot reload automatically!")

    except Exception as e:
        print(f"❌ Failed to save voice config: {e}")

def voice_tune_command(command_text: str) -> str:
    """Handle voice tuning commands"""
    cmd_lower = command_text.lower().strip()

    if "save config" in cmd_lower:
        save_voice_config_example()
        return "Voice configuration template saved. Edit ~/.ai_republic/voice_config.json for hot reload."

    elif "calibrate buffer" in cmd_lower:
        calibrate_pre_trigger_buffer()
        return f"Pre-trigger buffer calibrated to {VOICE_PRE_TRIGGER_BUFFER_MS}ms."

    elif "reload config" in cmd_lower:
        if check_voice_config_hot_reload():
            return "Voice configuration reloaded successfully."
        else:
            return "No configuration changes detected."

    elif "show config" in cmd_lower:
        return f"Current config: Buffer={VOICE_PRE_TRIGGER_BUFFER_MS}ms, MinGain={VOICE_MIN_GAIN}, Sensitivity={WAKE_SENSITIVITY}"

    else:
        return "Voice tuning commands: save config, calibrate buffer, reload config, show config"

def initialize_cloud_voice_activation():
    """Initialize voice activation using cloud services (Google STT)"""
    try:
        import speech_recognition as sr
        import threading
        import time

        def voice_activation_loop():
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            print(f"🎤 Voice activation enabled (Cloud). Wake word: '{WAKE_WORD}'")
            print("💡 Say your wake word followed by a command...")
            print("⚠️  Using Google Speech Recognition (requires internet)")

            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True

                while VOICE_ACTIVATION_ENABLED:
                    try:
                        print("\n👂 Listening for wake word...")
                        audio = recognizer.listen(source, timeout=VOICE_ACTIVATION_TIMEOUT, phrase_time_limit=3)

                        # Try to recognize the wake word + command
                        text = recognizer.recognize_google(audio).lower().strip()

                        # Check for wake word
                        if text.startswith(WAKE_WORD):
                            # Extract command after wake word
                            command = text[len(WAKE_WORD):].strip()

                            if command:
                                print(f"🎯 Wake word detected! Command: '{command}'")

                                # Process the command
                                response = process_voice_command(command)

                                # Provide voice feedback
                                send_voice_notification(f"Command executed: {response}")

                                # Also print to console for feedback
                                print(f"🤖 Athena: {response}")
                            else:
                                send_voice_notification("Wake word detected, but no command given.")
                                print("🤖 Athena: Wake word detected, but no command given.")
                        else:
                            # Not our wake word, ignore
                            pass

                    except sr.WaitTimeoutError:
                        # Timeout - continue listening
                        pass
                    except sr.UnknownValueError:
                        # Could not understand audio - continue
                        pass
                    except sr.RequestError as e:
                        print(f"Speech recognition error: {e}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"Voice activation error: {e}")
                        time.sleep(1)

        # Start voice activation in background thread
        voice_thread = threading.Thread(target=voice_activation_loop, daemon=True)
        voice_thread.start()

        print("✅ Cloud voice activation thread started")
        return True

    except ImportError:
        print("❌ Cloud voice activation requires 'speech_recognition' package")
        print("Install with: pip install SpeechRecognition")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize cloud voice activation: {e}")
        return False

def initialize_local_voice_activation():
    """Initialize voice activation using local models (Porcupine + Whisper)"""
    try:
        import pvporcupine
        import pyaudio
        import struct
        import threading
        import time
        import numpy as np

        # Import whisper for local STT
        try:
            import whisper
        except ImportError:
            print("❌ Local STT requires 'openai-whisper' package")
            print("Install with: pip install openai-whisper")
            return False

        def local_voice_activation_loop():
            print(f"🎤 Voice activation enabled (Local). Wake word: '{WAKE_WORD}'")
            print(f"🧠 Using Whisper {WHISPER_MODEL_SIZE} model for STT")
            print("💡 Say your wake word followed by a command...")

            # Initialize Porcupine wake word engine
            try:
                # Use built-in wake words or custom
                if WAKE_WORD == "hey athena":
                    keyword = pvporcupine.KEYWORDS["hey google"]  # Closest built-in match
                elif WAKE_WORD == "computer":
                    keyword = pvporcupine.KEYWORDS["computer"]
                elif WAKE_WORD == "alexa":
                    keyword = pvporcupine.KEYWORDS["alexa"]
                else:
                    # For custom wake words, would need custom model
                    print(f"❌ Custom wake word '{WAKE_WORD}' requires custom Porcupine model")
                    print("💡 Using default 'hey google' for now")
                    keyword = pvporcupine.KEYWORDS["hey google"]

                porcupine = pvporcupine.create(keywords=[keyword])
                print("✅ Porcupine wake word engine initialized")

            except Exception as e:
                print(f"❌ Failed to initialize Porcupine: {e}")
                print("💡 Falling back to cloud voice activation...")
                return initialize_cloud_voice_activation()

            # Initialize Whisper model
            try:
                model = whisper.load_model(WHISPER_MODEL_SIZE)
                print(f"✅ Whisper {WHISPER_MODEL_SIZE} model loaded")
            except Exception as e:
                print(f"❌ Failed to load Whisper model: {e}")
                print("💡 Falling back to cloud voice activation...")
                return initialize_cloud_voice_activation()

            # Audio stream setup
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )

            print("🎧 Listening for wake word...")

            try:
                while VOICE_ACTIVATION_ENABLED:
                    # Read audio frame
                    pcm = audio_stream.read(porcupine.frame_length)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                    # Process frame with Porcupine
                    keyword_index = porcupine.process(pcm)

                    if keyword_index >= 0:
                        print("🎯 Wake word detected!")

                        # Play confirmation beep
                        play_confirmation_beep()

                        # Listen for command (5 second window)
                        print("🎤 Listening for command...")
                        command_audio = record_command_audio(pa, porcupine.sample_rate, duration=5.0)

                        if command_audio:
                            # Transcribe with Whisper
                            command_text = transcribe_with_whisper(model, command_audio)

                            if command_text.strip():
                                print(f"📝 Transcribed: '{command_text}'")

                                # Process the command
                                response = process_voice_command(command_text)

                                # Provide voice feedback
                                send_voice_notification(f"Command executed: {response}")

                                # Console feedback
                                print(f"🤖 Athena: {response}")
                            else:
                                send_voice_notification("Could not understand command")
                                print("🤖 Athena: Could not understand command")
                        else:
                            send_voice_notification("No command detected")
                            print("🤖 Athena: No command detected")

            except KeyboardInterrupt:
                print("🛑 Voice activation stopped")
            finally:
                audio_stream.close()
                pa.terminate()
                porcupine.delete()

        # Start local voice activation in background thread
        voice_thread = threading.Thread(target=local_voice_activation_loop, daemon=True)
        voice_thread.start()

        print("✅ Local voice activation thread started")
        return True

    except ImportError as e:
        missing_pkg = str(e).split("'")[1] if "'" in str(e) else "required package"
        print(f"❌ Local voice activation requires '{missing_pkg}'")
        print("Install with: pip install pvporcupine pyaudio numpy openai-whisper")
        print("💡 Falling back to cloud voice activation...")
        return initialize_cloud_voice_activation()
    except Exception as e:
        print(f"❌ Failed to initialize local voice activation: {e}")
        print("💡 Falling back to cloud voice activation...")
        return initialize_cloud_voice_activation()

def record_command_audio(pa, sample_rate, duration=5.0):
    """Record audio for command after wake word detection"""
    try:
        import numpy as np

        # Open audio stream
        stream = pa.open(
            rate=sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=1024
        )

        frames = []
        start_time = time.time()

        while time.time() - start_time < duration:
            data = stream.read(1024)
            frames.append(data)

        stream.close()

        # Convert to numpy array for Whisper
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
        return audio_data

    except Exception as e:
        print(f"❌ Failed to record command audio: {e}")
        return None

def transcribe_with_whisper(model, audio_data):
    """Transcribe audio using Whisper"""
    try:

        # Whisper expects 16kHz audio, resample if needed
        if len(audio_data) > 0:
            # Simple transcription
            result = model.transcribe(audio_data, language='en')
            return result['text'].strip()
        return ""

    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return ""

def play_confirmation_beep():
    """Play a confirmation beep when wake word is detected"""
    try:
        # Use macOS afplay for beep sound
        import subprocess
        # Generate a simple beep using system sounds
        subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"],
                      capture_output=True, timeout=1)
    except:
        # Fallback - just print
        print("🔊 *beep*")

# Context-reactive macro system with hardening
MACRO_TEMPLATES = {
    "meeting_mode": {
        "description": "Quiet mode for meetings - suppress non-critical alerts",
        "commands": [
            {"type": "alert_control", "action": "set_quiet_hours", "start": "00:00", "end": "23:59"},
            {"type": "alert_control", "action": "filter_severity", "min_severity": "warning"},
            {"type": "voice_feedback", "message": "Meeting mode activated"}
        ],
        "ttl_seconds": 5400,  # 90 minutes (meeting duration + buffer)
        "linger_minutes": 3,   # Stay active 3 min after trigger ends
        "requires_admin": False
    },
    "emergency_mode": {
        "description": "High alert mode - escalate all notifications",
        "commands": [
            {"type": "alert_control", "action": "disable_quiet_hours"},
            {"type": "alert_control", "action": "escalate_all"},
            {"type": "alert_control", "action": "enable_voice_alerts"},
            {"type": "voice_feedback", "message": "Emergency mode activated - all alerts escalated"}
        ],
        "ttl_seconds": None,   # Manual deactivation only
        "linger_minutes": 0,
        "requires_admin": True   # Requires Touch ID confirmation
    },
    "maintenance_mode": {
        "description": "Controlled silence for planned maintenance",
        "commands": [
            {"type": "alert_control", "action": "set_quiet_hours", "start": "00:00", "end": "23:59"},
            {"type": "alert_control", "action": "filter_severity", "min_severity": "critical"},
            {"type": "service_control", "action": "pause_non_critical"},
            {"type": "voice_feedback", "message": "Maintenance mode activated"}
        ],
        "ttl_seconds": 7200,  # 120 minutes
        "linger_minutes": 0,
        "requires_admin": True
    },
    "travel_mode": {
        "description": "Travel-optimized settings",
        "commands": [
            {"type": "alert_control", "action": "enable_voice_alerts"},
            {"type": "alert_control", "action": "filter_severity", "min_severity": "warning"},
            {"type": "location_control", "action": "extend_geofence_radius", "multiplier": 2.0},
            {"type": "voice_feedback", "message": "Travel mode activated"}
        ],
        "ttl_seconds": 14400, # 4 hours (typical travel duration)
        "linger_minutes": 10,  # Stay active 10 min after arriving
        "requires_admin": False
    },
    "focus_mode": {
        "description": "Deep work mode - minimal interruptions",
        "commands": [
            {"type": "alert_control", "action": "set_quiet_hours", "start": "09:00", "end": "17:00"},
            {"type": "alert_control", "action": "filter_severity", "min_severity": "urgent"},
            {"type": "voice_feedback", "message": "Focus mode activated"}
        ],
        "ttl_seconds": 28800, # 8 hours (workday)
        "linger_minutes": 0,
        "requires_admin": False
    },
    "normal_mode": {
        "description": "Default operational state - standard alerting",
        "commands": [
            {"type": "alert_control", "action": "disable_quiet_hours"},
            {"type": "alert_control", "action": "reset_filters"},
            {"type": "voice_feedback", "message": "Normal mode restored"}
        ],
        "ttl_seconds": None,   # Persistent until changed
        "linger_minutes": 0,
        "requires_admin": False
    }
}

# Mutual exclusion matrix - incompatible modes
MACRO_MUTEX = {
    "emergency_mode": {"meeting_mode", "maintenance_mode", "focus_mode"},
    "maintenance_mode": {"emergency_mode", "travel_mode"},
    "meeting_mode": {"emergency_mode"},
    "focus_mode": {"emergency_mode"}
}

# Flap control - prevent rapid activations
MACRO_FLAP_CONTROL = {
    "max_per_15min": 3,      # Max auto activations per 15 minutes
    "backoff_minutes": 15,   # Backoff duration after hitting limit
    "cooldown_seconds": 30   # Minimum time between same macro activations
}

# Travel hysteresis - require consecutive detections
TRAVEL_HYSTERESIS = 2      # Consecutive travel detections needed
MEETING_LINGER_MIN = 3     # Minutes to stay in meeting mode after calendar busy ends

MACRO_TRIGGERS = {
    "calendar_meeting": {
        "type": "calendar",
        "condition": "busy",
        "macro": "meeting_mode",
        "description": "Auto-activate meeting mode when calendar shows busy"
    },
    "location_travel": {
        "type": "location",
        "condition": "travel",
        "macro": "travel_mode",
        "description": "Auto-activate travel mode when GPS detects travel"
    },
    "time_maintenance": {
        "type": "time",
        "condition": {"start": "02:00", "end": "04:00"},
        "macro": "maintenance_mode",
        "description": "Auto-activate maintenance mode during low-traffic hours"
    },
    "alert_emergency": {
        "type": "alert_volume",
        "condition": {"threshold": 5, "window_minutes": 10},
        "macro": "emergency_mode",
        "description": "Auto-activate emergency mode when alert volume spikes"
    }
}

ACTIVE_MACROS = {}  # Track currently active macros
MACRO_HISTORY = []  # Track macro execution history

# Flap control state
FLAP_STATE = {
    "activations_15min": [],  # List of activation timestamps in last 15min
    "backoff_until": 0.0,     # Timestamp when backoff period ends
    "last_macro_times": {}    # Last activation time per macro
}

# Travel hysteresis tracking
TRAVEL_DETECTIONS = []  # Recent travel detection timestamps

# Voice Engine Adapter Pattern - Korono-first architecture with hot reload
class SpeechEngine:
    """Abstract interface for speech engines (STT/TTS)"""
    def start(self) -> bool:
        """Initialize the engine. Returns success."""
        raise NotImplementedError

    def stt(self, pcm16: bytes, sample_rate: int) -> str:
        """Speech-to-text from PCM16 audio. Returns transcribed text."""
        raise NotImplementedError

    def tts(self, text: str) -> bytes:
        """Text-to-speech. Returns PCM16 audio bytes."""
        raise NotImplementedError

    def health(self) -> dict:
        """Health check. Returns dict with status info."""
        raise NotImplementedError

    def pause_stt(self) -> None:
        """Pause STT processing (for half-duplex)"""
        pass

    def resume_stt(self) -> None:
        """Resume STT processing"""
        pass

class KoronoEngine(SpeechEngine):
    """Korono STT/TTS engine implementation"""

    def __init__(self, stt_model: str, tts_voice: str, sample_rate: int, vad_enabled: bool = True):
        self.stt_model = stt_model
        self.tts_voice = tts_voice
        self.sample_rate = sample_rate
        self.vad_enabled = vad_enabled
        self._stt_client = None
        self._tts_client = None
        self._initialized = False

    def start(self) -> bool:
        """Initialize Korono STT and TTS clients"""
        try:
            # Import Korono clients (placeholder - replace with actual imports)
            # from korono import STTClient, TTSClient
            # self._stt_client = STTClient(model=self.stt_model, sample_rate=self.sample_rate)
            # self._tts_client = TTSClient(voice=self.tts_voice, sample_rate=self.sample_rate)

            # For now, create mock clients
            self._stt_client = MockKoronoSTT(self.stt_model, self.sample_rate, self.vad_enabled)
            self._tts_client = MockKoronoTTS(self.tts_voice, self.sample_rate)

            self._initialized = True
            return True
        except Exception as e:
            print(f"❌ Korono engine initialization failed: {e}")
            return False

    def stt(self, pcm16: bytes, sample_rate: int) -> str:
        """Transcribe audio using Korono STT"""
        if not self._initialized or not self._stt_client:
            return ""

        try:
            # Pass VAD hints to Korono
            vad_hints = {"enabled": self.vad_enabled} if self.vad_enabled else {}
            return self._stt_client.transcribe(pcm16, sample_rate, **vad_hints)
        except Exception as e:
            print(f"❌ Korono STT failed: {e}")
            return ""

    def tts(self, text: str) -> bytes:
        """Synthesize speech using Korono TTS"""
        if not self._initialized or not self._tts_client:
            return b""

        try:
            return self._tts_client.synthesize(text)
        except Exception as e:
            print(f"❌ Korono TTS failed: {e}")
            return b""

    def health(self) -> dict:
        """Korono engine health check"""
        if not self._initialized:
            return {"status": "not_initialized", "stt": False, "tts": False}

        stt_ready = bool(self._stt_client and self._stt_client.ready())
        tts_ready = bool(self._tts_client and self._tts_client.ready())

        return {
            "status": "healthy" if (stt_ready and tts_ready) else "degraded",
            "stt": stt_ready,
            "tts": tts_ready,
            "stt_model": self.stt_model,
            "tts_voice": self.tts_voice,
            "sample_rate": self.sample_rate,
            "vad_enabled": self.vad_enabled
        }

    def pause_stt(self) -> None:
        """Pause STT processing during TTS playback"""
        if self._stt_client:
            self._stt_client.pause()

    def resume_stt(self) -> None:
        """Resume STT processing after TTS playback"""
        if self._stt_client:
            self._stt_client.resume()

# Mock implementations for development (replace with real Korono clients)
class MockKoronoSTT:
    def __init__(self, model, sample_rate, vad_enabled):
        self.model = model
        self.sample_rate = sample_rate
        self.vad_enabled = vad_enabled
        self._paused = False

    def transcribe(self, pcm16, sample_rate, **kwargs):
        # Mock transcription - in real implementation, this would call Korono STT API
        return "mock transcription result"

    def ready(self):
        return not self._paused

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

class MockKoronoTTS:
    def __init__(self, voice, sample_rate):
        self.voice = voice
        self.sample_rate = sample_rate

    def synthesize(self, text):
        # Mock synthesis - in real implementation, this would call Korono TTS API
        # Return mock PCM16 audio data
        return b"mock_audio_data_" + text.encode()[:100]

    def ready(self):
        return True

# Context-aware voice styles
VOICE_STYLES = {
    "meeting_mode":    {"voice": "athena-quiet",   "gain": 0.92, "brief": True},
    "emergency_mode":  {"voice": "athena-urgent",  "gain": 1.12, "brief": True},
    "normal_mode":     {"voice": "athena-neutral", "gain": 1.0,  "brief": False},
    "maintenance_mode":{"voice": "athena-soft",    "gain": 0.95, "brief": True},
    "travel_mode":     {"voice": "athena-neutral", "gain": 1.0,  "brief": False},
    "focus_mode":      {"voice": "athena-soft",    "gain": 0.95, "brief": True}
}

VOICE_MIN_GAIN = 0.9

# Global voice engine instance
VOICE_ENGINE_INSTANCE: Optional[SpeechEngine] = None
VOICE_ENGINE_LOCK = threading.Lock()
VOICE_ENGINE_STARTED = False

# Hot reload support
VOICE_CONFIG_LAST_MODIFIED = 0
VOICE_CONFIG_FILE = os.path.expanduser("~/.ai_republic/voice_config.json")

# Pre-trigger buffer calibration
VOICE_PRE_TRIGGER_BUFFER_MS = 500  # Start recording 500ms before wake word detection
VOICE_BUFFER_CALIBRATION_ENABLED = True

# ====================
# Macro plumbing (add)
# ====================
_MACROS: Dict[str, Dict[str, Any]] = {
    # existing definitions…
}

def list_available_macros() -> List[Dict[str, Any]]:
    return [{"name": k, **v} for k, v in MACRO_TEMPLATES.items()]

def execute_macro(name: str, trigger_source: str = "manual") -> Dict[str, Any]:
    cfg = MACRO_TEMPLATES.get(name)
    if not cfg:
        return {"success": False, "message": f"Unknown macro: {name}"}
    # existing execution…
    _set_active_mode(name)
    # existing execution…
    audit_event("macro_executed", {"macro": name, "trigger": trigger_source})
    return {"success": True, "message": f"{name} activated"}

def deactivate_macro(name: str):
    # optional clean-down for that mode
    audit_event("macro_deactivated", {"macro": name})
    if get_active_mode() == name:
        _set_active_mode("normal_mode")

def initialize_context_macros():
    """Initialize context-reactive macro monitoring"""
    if not CONTEXT_MACROS_ENABLED:
        print("Context macros disabled")
        return False

    try:
        import threading
        import time

        def macro_monitor_loop():
            print(f"🎯 Context macro monitoring enabled (check every {MACRO_CHECK_INTERVAL}s)")

            while CONTEXT_MACROS_ENABLED:
                try:
                    check_macro_triggers()
                    time.sleep(MACRO_CHECK_INTERVAL)
                except Exception as e:
                    print(f"Macro monitoring error: {e}")
                    time.sleep(MACRO_CHECK_INTERVAL)

        # Start macro monitoring in background thread
        macro_thread = threading.Thread(target=macro_monitor_loop, daemon=True)
        macro_thread.start()

        print("✅ Context macro monitoring started")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize context macros: {e}")
        return False

def check_macro_triggers():
    """Check all macro triggers and execute if conditions met"""
    current_context = update_smart_alerting()
    current_time = time.time()

    # Clean up expired macros first
    _cleanup_expired_macros(current_time)

    for trigger_name, trigger_config in MACRO_TRIGGERS.items():
        if should_activate_macro(trigger_name, trigger_config, current_context, current_time):
            macro_name = trigger_config["macro"]
            execute_macro(macro_name, f"auto_trigger_{trigger_name}")

def _cleanup_expired_macros(current_time):
    """Remove expired macros from active list"""
    expired_macros = []
    for macro_name, macro_info in ACTIVE_MACROS.items():
        expires_at = macro_info.get("expires_at")
        if expires_at and current_time >= expires_at:
            expired_macros.append(macro_name)
            audit_event("macro_expired", {
                "macro": macro_name,
                "activated_at": macro_info["activated_at"],
                "ttl_seconds": macro_info["ttl_seconds"]
            })
            print(f"⏰ Macro {macro_name} expired, reverting to normal mode")

    for macro_name in expired_macros:
        del ACTIVE_MACROS[macro_name]

    # If we expired the last macro and normal_mode isn't active, activate it
    if not ACTIVE_MACROS and get_active_mode() != "normal_mode":
        execute_macro("normal_mode", "auto_cleanup")

# ===========================
# Trigger engine (respect TTL)
# ===========================
def should_activate_macro(trigger_name, trigger_config, context, current_time):
    """Check if a macro trigger condition is met with hardening"""
    macro_name = trigger_config["macro"]
    trigger_type = trigger_config["type"]
    condition = trigger_config["condition"]

    # Human override wins during TTL
    if is_override_active():
        audit_event("macro_suppressed", {
            "macro": macro_name,
            "trigger": trigger_name,
            "reason": "manual_override_active"
        })
        return False

    # Check if macro is already active (prevent double-activation)
    if trigger_name in ACTIVE_MACROS:
        return False

    # Check mutual exclusion (incompatible modes)
    active_modes = set(ACTIVE_MACROS.keys())
    if not _can_enter_mode(macro_name, active_modes):
        audit_event("macro_suppressed", {
            "macro": macro_name,
            "trigger": trigger_name,
            "reason": "mutex_conflict",
            "active_modes": list(active_modes)
        })
        return False

    # Check flap control (rate limiting)
    if not _check_flap_control(macro_name, current_time):
        audit_event("macro_suppressed", {
            "macro": macro_name,
            "trigger": trigger_name,
            "reason": "flap_control"
        })
        return False

    # Check cooldown (prevent rapid re-activation of same macro)
    last_activation = FLAP_STATE["last_macro_times"].get(macro_name, 0)
    if current_time - last_activation < MACRO_FLAP_CONTROL["cooldown_seconds"]:
        return False

    # Evaluate trigger condition with hysteresis
    condition_met = False
    if trigger_type == "calendar":
        condition_met = check_calendar_trigger(condition, context)
    elif trigger_type == "location":
        condition_met = check_location_trigger_with_hysteresis(condition, context, current_time)
    elif trigger_type == "time":
        condition_met = check_time_trigger(condition, current_time)
    elif trigger_type == "alert_volume":
        condition_met = check_alert_volume_trigger(condition)

    return condition_met

def _can_enter_mode(target_mode, active_modes):
    """Check if target mode can be entered given current active modes"""
    for active_mode in active_modes:
        # Check both directions of mutex
        if target_mode in MACRO_MUTEX.get(active_mode, set()):
            return False
        if active_mode in MACRO_MUTEX.get(target_mode, set()):
            return False
    return True

def _check_flap_control(macro_name, current_time):
    """Check if flap control allows activation"""
    # Clean old activations
    cutoff = current_time - (15 * 60)  # 15 minutes ago
    FLAP_STATE["activations_15min"] = [
        t for t in FLAP_STATE["activations_15min"] if t > cutoff
    ]

    # Check if in backoff period
    if current_time < FLAP_STATE["backoff_until"]:
        return False

    # Check rate limit
    if len(FLAP_STATE["activations_15min"]) >= MACRO_FLAP_CONTROL["max_per_15min"]:
        # Enter backoff
        FLAP_STATE["backoff_until"] = current_time + (MACRO_FLAP_CONTROL["backoff_minutes"] * 60)
        audit_event("flap_control_activated", {
            "backoff_minutes": MACRO_FLAP_CONTROL["backoff_minutes"],
            "activations_in_window": len(FLAP_STATE["activations_15min"])
        })
        return False

    return True

def check_calendar_trigger(condition, context):
    """Check if calendar condition is met"""
    if condition == "busy":
        return context.get("calendar_busy", False)
    return False

def check_location_trigger_with_hysteresis(condition, context, current_time):
    """Check location trigger with hysteresis to prevent flapping"""
    current_location = context.get("location", "")
    location_confidence = context.get("location_confidence", 1.0)

    # Clean old detections (keep last 5 minutes)
    cutoff = current_time - 300
    global TRAVEL_DETECTIONS
    TRAVEL_DETECTIONS = [t for t in TRAVEL_DETECTIONS if t > cutoff]

    if condition == "travel":
        is_travel = current_location in ["travel", "driving"]
        if is_travel:
            # Require consecutive detections for travel
            TRAVEL_DETECTIONS.append(current_time)
            consecutive = len(TRAVEL_DETECTIONS)
            return consecutive >= TRAVEL_HYSTERESIS and strong_enough_signal(current_location, location_confidence)
        else:
            # Clear detections when not traveling
            TRAVEL_DETECTIONS.clear()
            return False

    elif condition == "home":
        return current_location == "home" and strong_enough_signal(current_location, location_confidence)

    elif condition == "work":
        return current_location == "work" and strong_enough_signal(current_location, location_confidence)

    return False

def check_location_trigger(condition, context):
    """Legacy function for backward compatibility"""
    return check_location_trigger_with_hysteresis(condition, context, time.time())

def check_time_trigger(condition, current_time):
    """Check if time condition is met"""
    import datetime
    current_hour = datetime.datetime.fromtimestamp(current_time).hour
    current_minute = datetime.datetime.fromtimestamp(current_time).minute

    if isinstance(condition, dict) and "start" in condition and "end" in condition:
        start_hour, start_min = map(int, condition["start"].split(":"))
        end_hour, end_min = map(int, condition["end"].split(":"))

        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        current_minutes = current_hour * 60 + current_minute

        return start_minutes <= current_minutes <= end_minutes

    return False

def check_alert_volume_trigger(condition):
    """Check if alert volume condition is met"""
    # This would need to be implemented with actual alert monitoring
    # For now, return False (placeholder)
    return False

def execute_macro(macro_name, trigger_source="manual"):
    """Execute a macro by name with hardening"""
    if macro_name not in MACRO_TEMPLATES:
        audit_event("macro_failed", {"macro": macro_name, "reason": "unknown_macro"})
        print(f"❌ Unknown macro: {macro_name}")
        return False

    macro_config = MACRO_TEMPLATES[macro_name]
    current_time = time.time()

    # Check admin requirements for sensitive macros
    if macro_config.get("requires_admin", False) and trigger_source == "manual":
        # In production, this would require Touch ID or password confirmation
        audit_event("admin_confirmation_required", {"macro": macro_name})
        print("🔐 Admin confirmation required for this macro")
        print("💡 In production, this would require Touch ID or password")

    # Idempotency check - don't re-execute if recently activated
    if ACTIVE_MACROS.get(macro_name):
        last_activation = ACTIVE_MACROS[macro_name]["activated_at"]
        if current_time - last_activation < 30:  # 30 second cooldown
            audit_event("macro_suppressed", {
                "macro": macro_name,
                "reason": "idempotency",
                "seconds_since_last": current_time - last_activation
            })
            return True  # Consider it successful since already active

    print(f"🎯 Executing macro: {macro_name} ({trigger_source})")
    print(f"📝 {macro_config['description']}")

    # Update flap control state
    FLAP_STATE["activations_15min"].append(current_time)
    FLAP_STATE["last_macro_times"][macro_name] = current_time

    # Mark macro as active with TTL
    ttl_seconds = macro_config.get("ttl_seconds")
    ACTIVE_MACROS[macro_name] = {
        "activated_at": current_time,
        "trigger_source": trigger_source,
        "commands": macro_config["commands"],
        "ttl_seconds": ttl_seconds,
        "expires_at": current_time + ttl_seconds if ttl_seconds else None
    }

    # Execute each command in the macro
    success_count = 0
    for command in macro_config["commands"]:
        try:
            result = execute_macro_command(command)
            if result:
                success_count += 1
                print(f"✅ {command.get('type', 'unknown')} executed")
            else:
                print(f"❌ {command.get('type', 'unknown')} failed")
        except Exception as e:
            print(f"❌ Macro command error: {e}")

    # Log macro execution with hardening metrics
    MACRO_HISTORY.append({
        "macro": macro_name,
        "trigger": trigger_source,
        "timestamp": current_time,
        "success_count": success_count,
        "total_commands": len(macro_config["commands"]),
        "ttl_applied": ttl_seconds,
        "admin_required": macro_config.get("requires_admin", False)
    })

    audit_event("macro_executed", {
        "macro": macro_name,
        "trigger": trigger_source,
        "success_count": success_count,
        "total_commands": len(macro_config["commands"])
    })

    print(f"🎯 Macro {macro_name} completed: {success_count}/{len(macro_config['commands'])} commands successful")
    return success_count == len(macro_config["commands"])

def execute_macro_command(command):
    """Execute a single macro command"""
    command_type = command.get("type")

    if command_type == "alert_control":
        return execute_alert_control_command(command)

    elif command_type == "service_control":
        return execute_service_control_command(command)

    elif command_type == "location_control":
        return execute_location_control_command(command)

    elif command_type == "voice_feedback":
        message = command.get("message", "")
        send_voice_notification(message)
        print(f"🔊 {message}")
        return True

    return False

def execute_alert_control_command(command):
    """Execute alert control commands"""
    action = command.get("action")

    if action == "set_quiet_hours":
        # This would need to integrate with the quiet hours system
        print(f"Setting quiet hours: {command.get('start')} - {command.get('end')}")
        return True

    elif action == "disable_quiet_hours":
        print("Disabling quiet hours")
        return True

    elif action == "filter_severity":
        severity = command.get("min_severity", "info")
        print(f"Filtering alerts to minimum severity: {severity}")
        return True

    elif action == "escalate_all":
        print("Escalating all alerts")
        return True

    elif action == "enable_voice_alerts":
        print("Enabling voice alerts")
        return True

    return False

def execute_service_control_command(command):
    """Execute service control commands"""
    action = command.get("action")

    if action == "pause_non_critical":
        print("Pausing non-critical services")
        return True

    # Add more service controls as needed
    return False

def execute_location_control_command(command):
    """Execute location control commands"""
    action = command.get("action")

    if action == "extend_geofence_radius":
        multiplier = command.get("multiplier", 1.0)
        print(f"Extending geofence radius by {multiplier}x")
        return True

    return False

def list_available_macros():
    """List all available macros"""
    print("🎯 Available Macros:")
    print("=" * 40)

    macros = []
    for name, config in MACRO_TEMPLATES.items():
        macro_info = {"name": name, **config}
        macros.append(macro_info)
        print(f"📋 {name}")
        print(f"   {config['description']}")
        print(f"   Commands: {len(config['commands'])}")
        print()

    return macros

def list_active_macros():
    """List currently active macros and return active macros dict"""
    print("🎯 Active Macros:")
    print("=" * 30)

    if not ACTIVE_MACROS:
        print("No active macros")
        return {}

    for name, info in ACTIVE_MACROS.items():
        activated_at = time.strftime("%H:%M:%S", time.localtime(info["activated_at"]))
        trigger = info["trigger_source"]
        commands = len(info["commands"])
        print(f"📋 {name}")
        print(f"   Activated: {activated_at} (via {trigger})")
        print(f"   Commands: {commands}")
        print()

    return ACTIVE_MACROS

def deactivate_macro(macro_name):
    """Deactivate a running macro"""
    if macro_name in ACTIVE_MACROS:
        del ACTIVE_MACROS[macro_name]
        print(f"✅ Macro {macro_name} deactivated")
        return True
    else:
        print(f"❌ Macro {macro_name} not active")
        return False

def test_local_voice_setup():
    """Test if local voice processing components are available"""
    print("🧪 Testing Local Voice Processing Setup")
    print("=" * 50)

    components = {
        "pvporcupine": "Wake word detection",
        "pyaudio": "Audio capture",
        "numpy": "Audio processing",
        "whisper": "Speech-to-text",
        "torch": "ML framework (for Whisper)"
    }

    all_available = True
    for package, purpose in components.items():
        try:
            if package == "pvporcupine":
                import pvporcupine
                version = pvporcupine.__version__
            elif package == "pyaudio":
                import pyaudio
                version = pyaudio.__version__
            elif package == "numpy":
                import numpy
                version = numpy.__version__
            elif package == "whisper":
                import whisper
                version = whisper.__version__
            elif package == "torch":
                import torch
                version = torch.__version__

            print(f"✅ {package} {version} - {purpose}")

        except ImportError:
            print(f"❌ {package} - {purpose} (not installed)")
            all_available = False

    print()
    if all_available:
        print("🎉 All local voice processing components available!")
        print("💡 Enable with: USE_LOCAL_STT=true USE_PORCUPINE_WAKE=true")
    else:
        print("⚠️  Some components missing for local voice processing")
        print("💡 Install missing packages or use cloud fallback")

    return all_available

def _simulate_alert_spike(count=5, window_seconds=600):
    """Simulate an alert spike for testing emergency mode"""
    print(f"🚨 Simulating {count} alerts in {window_seconds}s window for emergency mode testing")
    # This would integrate with actual alert monitoring
    # For demo purposes, we'll just log it
    audit_event("alert_spike_simulated", {
        "alert_count": count,
        "window_seconds": window_seconds,
        "purpose": "emergency_mode_testing"
    })
    print("✅ Alert spike simulation logged")

def test_macro_hardening():
    """Test macro hardening features"""
    print("🧪 Testing Macro Hardening Features")
    print("=" * 50)

    # Test mutex constraints
    print("\n🔒 Testing Mutex Constraints:")
    test_cases = [
        ("emergency_mode", ["meeting_mode"], False),
        ("meeting_mode", ["emergency_mode"], False),
        ("travel_mode", ["maintenance_mode"], True),
        ("focus_mode", ["emergency_mode"], False)
    ]

    for target, active, expected in test_cases:
        result = _can_enter_mode(target, set(active))
        status = "✅ BLOCKED" if not result else "✅ ALLOWED"
        print(f"  {target} + {active} = {status}")

    # Test flap control
    print("\n🎛️ Testing Flap Control:")
    current_time = time.time()

    # Simulate hitting the limit
    for i in range(MACRO_FLAP_CONTROL["max_per_15min"] + 1):
        FLAP_STATE["activations_15min"].append(current_time - i * 60)  # Space them out

    result = _check_flap_control("test_macro", current_time)
    backoff_active = current_time < FLAP_STATE["backoff_until"]
    print(f"  Flap control activated: {'✅ YES' if not result else '❌ NO'}")
    print(f"  Backoff active: {'✅ YES' if backoff_active else '❌ NO'}")

    # Test hysteresis
    print("\n🔄 Testing Travel Hysteresis:")
    test_contexts = [
        {"location": "travel", "location_confidence": 0.9},
        {"location": "travel", "location_confidence": 0.9},
        {"location": "home", "location_confidence": 0.8}
    ]

    for i, ctx in enumerate(test_contexts):
        result = check_location_trigger_with_hysteresis("travel", ctx, current_time + i * 60)
        print(f"  Sample {i+1}: {ctx['location']} ({ctx['location_confidence']}) = {'✅ TRIGGER' if result else '❌ NO TRIGGER'}")

    print("\n✅ Macro hardening tests completed")

def test_voice_activation():
    """Test voice activation functionality"""
    if not VOICE_ACTIVATION_ENABLED:
        print("❌ Voice activation is disabled. Enable with VOICE_ACTIVATION_ENABLED=true")
        return

    print("🧪 Testing Voice Activation")
    print("===========================")
    print(f"Wake Word: '{WAKE_WORD}'")
    print(f"Timeout: {VOICE_ACTIVATION_TIMEOUT} seconds")
    print(f"Command Routing: {'✅ Enabled' if COMMAND_ROUTING_ENABLED else '❌ Disabled'}")
    print()

    # Test wake word detection
    test_phrase = f"{WAKE_WORD} check system status"
    print(f"Test Phrase: '{test_phrase}'")

    # Simulate processing
    if test_phrase.startswith(WAKE_WORD):
        command = test_phrase[len(WAKE_WORD):].strip()
        print(f"Extracted Command: '{command}'")

        response = process_voice_command(command)
        print(f"Response: '{response}'")

        print("✅ Voice activation parsing works correctly")
    else:
        print("❌ Wake word detection failed")

def configure_voice_activation(wake_word: str = None, timeout: int = None):
    """Configure voice activation settings"""
    global WAKE_WORD, VOICE_ACTIVATION_TIMEOUT

    if wake_word:
        WAKE_WORD = wake_word.lower()
        print(f"✅ Wake word set to: '{WAKE_WORD}'")

    if timeout:
        VOICE_ACTIVATION_TIMEOUT = timeout
        print(f"✅ Timeout set to: {VOICE_ACTIVATION_TIMEOUT} seconds")

    print("💡 Restart voice activation to apply changes")

def acknowledge_alert_by_voice(ack_id: str = None) -> bool:
    """Acknowledge an alert using voice command. Call this when user says 'acknowledge'"""
    if ack_id:
        # Acknowledge specific alert
        ack_path = f"/tmp/athena_alert_ack_{ack_id}"
        try:
            with open(ack_path, 'w') as f:
                f.write(f"acknowledged_by_voice_{int(time.time())}")
            logging.info(f"Alert {ack_id} acknowledged by voice")
            return True
        except Exception as e:
            logging.error(f"Failed to acknowledge alert {ack_id}: {e}")
            return False
    else:
        # Acknowledge all pending alerts
        import glob
        ack_files = glob.glob("/tmp/athena_alert_ack_*")
        acknowledged = 0
        for ack_file in ack_files:
            try:
                with open(ack_file, 'w') as f:
                    f.write(f"acknowledged_by_voice_{int(time.time())}")
                acknowledged += 1
            except:
                pass
        if acknowledged > 0:
            logging.info(f"Acknowledged {acknowledged} pending alerts by voice")
            _play_sound_and_speak(f"Acknowledged {acknowledged} alert{'s' if acknowledged > 1 else ''}.")
        return acknowledged > 0

def start_voice_ack_listener(ack_id: str, timeout_minutes: int = 5):
    """Start listening for voice acknowledgment commands"""
    def _listen():
        # This would integrate with your existing voice recognition system
        # For now, we'll create a simple polling mechanism
        deadline = time.time() + timeout_minutes * 60
        ack_file = f"/tmp/athena_voice_ack_{ack_id}"

        while time.time() < deadline:
            if os.path.exists(ack_file):
                # User said acknowledgment command
                acknowledge_alert_by_voice(ack_id)
                os.remove(ack_file)  # Clean up
                return
            time.sleep(1)

    threading.Thread(target=_listen, daemon=True).start()

def voice_ack_command_received(ack_id: str = None):
    """Call this when voice recognition detects 'acknowledge' command"""
    ack_file = f"/tmp/athena_voice_ack_{ack_id or 'general'}"
    try:
        with open(ack_file, 'w') as f:
            f.write(f"voice_ack_{int(time.time())}")
        return True
    except Exception as e:
        logging.error(f"Failed to create voice ack file: {e}")
        return False

class AthenaNotifications:
    """Multi-channel notification system for AI Republic"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or '/opt/ai-republic/notification_config.json'
        self.config = self.load_config()
        self.setup_logging()

    def setup_logging(self):
        """Setup notification logging"""
        log_dir = '/var/log/ai-republic' if os.path.exists('/var/log/ai-republic') else './logs'
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            filename=os.path.join(log_dir, 'athena_notifications.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_config(self) -> Dict:
        """Load notification configuration"""
        default_config = {
            "enabled_channels": ["desktop"],
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_emails": []
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_ids": []
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "#ai-republic"
            },
            "desktop": {
                "enabled": True,
                "urgency_levels": {
                    "daily": "normal",
                    "warning": "normal",
                    "urgent": "critical"
                }
            },
            "retry_attempts": 3,
            "retry_delay": 5
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

        return default_config

    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info("Configuration saved")
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def send_email(self, subject: str, message: str, priority: str = "normal") -> bool:
        """Send email notification"""
        if not self.config["email"]["enabled"]:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["from_email"]
            msg['To'] = ", ".join(self.config["email"]["to_emails"])
            msg['Subject'] = f"[AI Republic] {subject}"

            # Set priority
            if priority == "urgent":
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            elif priority == "warning":
                msg['X-Priority'] = '3'
                msg['X-MSMail-Priority'] = 'Normal'

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["username"], self.config["email"]["password"])
            text = msg.as_string()
            server.sendmail(self.config["email"]["from_email"], self.config["email"]["to_emails"], text)
            server.quit()

            logging.info(f"Email sent: {subject}")
            return True

        except Exception as e:
            logging.error(f"Email send failed: {e}")
            return False

    def send_telegram(self, message: str, priority: str = "normal") -> bool:
        """Send Telegram notification"""
        if not self.config["telegram"]["enabled"]:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"

            # Add emoji based on priority
            emoji = "🤖" if priority == "normal" else "⚠️" if priority == "warning" else "🚨"
            full_message = f"{emoji} {message}"

            for chat_id in self.config["telegram"]["chat_ids"]:
                payload = {
                    "chat_id": chat_id,
                    "text": full_message,
                    "parse_mode": "Markdown",
                    "disable_notification": priority == "normal"
                }

                response = requests.post(url, json=payload, timeout=10)
                if response.status_code != 200:
                    logging.error(f"Telegram send failed for chat {chat_id}: {response.text}")
                    return False

            logging.info("Telegram message sent")
            return True

        except Exception as e:
            logging.error(f"Telegram send failed: {e}")
            return False

    def send_slack(self, message: str, priority: str = "normal") -> bool:
        """Send Slack notification"""
        if not self.config["slack"]["enabled"]:
            return False

        try:
            # Color based on priority
            color = "good" if priority == "normal" else "warning" if priority == "warning" else "danger"

            payload = {
                "channel": self.config["slack"]["channel"],
                "username": "Athena",
                "icon_emoji": ":robot_face:",
                "attachments": [{
                    "color": color,
                    "text": message,
                    "footer": "AI Republic Operations",
                    "ts": time.time()
                }]
            }

            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logging.info("Slack message sent")
                return True
            else:
                logging.error(f"Slack send failed: {response.text}")
                return False

        except Exception as e:
            logging.error(f"Slack send failed: {e}")
            return False

    def send_desktop_notification(self, title: str, message: str, priority: str = "normal") -> bool:
        """Send desktop notification"""
        if not self.config["desktop"]["enabled"]:
            return False

        try:
            urgency = self.config["desktop"]["urgency_levels"].get(priority, "normal")

            # Try different notification systems
            commands = [
                ["notify-send", f"--urgency={urgency}", title, message],
                ["terminal-notifier", "-title", title, "-message", message],
                ["osascript", "-e", f"display notification \"{message}\" with title \"{title}\""]
            ]

            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        logging.info(f"Desktop notification sent via {cmd[0]}")
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            logging.warning("No desktop notification system available")
            return False

        except Exception as e:
            logging.error(f"Desktop notification failed: {e}")
            return False

    def send_notification(self, title: str, message: str, priority: str = "normal",
                         channels: List[str] = None, cascade_priority: bool = False,
                         escalation_enabled: bool = False, escalation_minutes: int = 5,
                         ack_id: str = None, details: str = None) -> Dict[str, bool]:
        """Send notification via configured channels with optional cascade priority

        Args:
            cascade_priority: If True, send critical alerts to instant channels first
                            (Telegram first, then email), then other channels
            escalation_enabled: If True, enable escalation for urgent alerts
            escalation_minutes: Minutes to wait before escalating if no acknowledgment
            ack_id: Optional acknowledgment ID for escalation monitoring
            details: Optional detailed message for tiered alerts
        """
        if channels is None:
            channels = self.config["enabled_channels"]

        results = {}

        # Update smart alerting context
        context = update_smart_alerting()

        # Check smart alerting policy (includes quiet hours, focus mode, calendar)
        if not should_send_alert_smart(priority):
            reason = []
            if context.get("focus_mode"):
                reason.append("Focus mode active")
            if context.get("calendar_busy"):
                reason.append("calendar busy")
            if context.get("quiet_hours"):
                reason.append("quiet hours")
            reason_str = ", ".join(reason) if reason else "smart filtering"
            logging.info(f"Alert suppressed due to {reason_str}: {title}")
            return results

        # Route to tiered iPhone alerting for critical/warning alerts
        if priority == "urgent":
            # Critical alerts: Tier 1 + Tier 2 + Tier 3 escalation
            ack_id = ack_id or f"{int(time.time())}_{hash(title + message) % 10000}"
            send_tier1_immediate(f"{title} — {message}")
            send_tier2_followup(details or f"{title}\n{message}")

            # Only send voice escalation if allowed during quiet hours
            if should_send_voice_alert(priority):
                send_tier3_escalation(
                    tts_text=f"Athena escalation. {title}. {message}. Immediate action required.",
                    minutes_to_escalate=escalation_minutes,
                    ack_id=ack_id
                )
            else:
                logging.info(f"Voice escalation suppressed during quiet hours: {title}")

        elif priority == "warning":
            # Warning alerts: iMessage + notification only (no voice during quiet hours)
            send_tier1_immediate(f"⚠️ {title} — {message}")

            # Send voice only if allowed during quiet hours
            if should_send_voice_alert(priority):
                # For warnings, just a single voice alert without full escalation
                _play_sound_and_speak(f"Warning: {title}. {message}")

        # Implement cascade priority for critical alerts
        if cascade_priority and priority == "urgent":
            # Send to instant channels first (Telegram, then desktop)
            instant_channels = [ch for ch in channels if ch in ['telegram', 'desktop']]
            delayed_channels = [ch for ch in channels if ch not in instant_channels]

            # Send instant alerts immediately
            for channel in instant_channels:
                results.update(self._send_to_channel(channel, title, message, priority))

            # Small delay before sending to slower channels (email, slack)
            if delayed_channels:
                time.sleep(2)  # 2 second delay for cascade effect
                for channel in delayed_channels:
                    results.update(self._send_to_channel(channel, title, message, priority))
        else:
            # Normal delivery to all channels simultaneously
            for channel in channels:
                results.update(self._send_to_channel(channel, title, message, priority))

        # Check if any channels succeeded for escalation monitoring
        successful_channels = [ch for ch, success in results.items() if success]

        # Start escalation monitoring for urgent alerts if enabled
        if escalation_enabled and priority == "urgent" and successful_channels:
            import threading
            escalation_thread = threading.Thread(
                target=self._monitor_escalation,
                args=(title, message, escalation_minutes),
                daemon=True
            )
            escalation_thread.start()

        return results

    def _monitor_escalation(self, title: str, message: str, escalation_minutes: int):
        """Monitor for alert acknowledgment and escalate if needed"""
        import time
        import subprocess

        alert_id = f"{int(time.time())}_{hash(title + message) % 10000}"
        escalation_triggered = False

        # Wait for escalation period
        time.sleep(escalation_minutes * 60)

        # Check if alert was acknowledged (simplified check)
        # In a real system, this would check for user acknowledgment via API/UI
        ack_file = f"/tmp/athena_alert_ack_{alert_id}"
        if not os.path.exists(ack_file):
            escalation_triggered = True

            # Send escalation alert
            escalation_title = f"🚨🚨 ESCALATION: {title}"
            escalation_message = f"""CRITICAL ALERT ESCALATION

Original Alert: {title}

{message}

⚠️ NO ACKNOWLEDGMENT RECEIVED after {escalation_minutes} minutes!

This alert requires IMMEDIATE attention. Please check system status and take action.

To acknowledge this alert, run:
  echo "acknowledged" > /tmp/athena_alert_ack_{alert_id}

For urgent issues, contact on-call personnel immediately."""

            # Send escalation to ALL channels simultaneously (no cascade)
            escalation_results = self.send_notification(
                title=escalation_title,
                message=escalation_message,
                priority="urgent",
                cascade_priority=False,  # No cascade for escalation
                escalation_enabled=False  # Prevent recursive escalation
            )

            logging.warning(f"Alert escalation triggered for: {title}")
            logging.info(f"Escalation sent to: {list(escalation_results.keys())}")

            # Optional: Trigger system-level escalation (beep, system alert, etc.)
            try:
                # System beep/alert (macOS/Linux)
                subprocess.run(["afplay", "/System/Library/Sounds/Basso.aiff"],
                             capture_output=True, timeout=2)
            except:
                try:
                    subprocess.run(["beep", "-f", "1000", "-l", "500"],
                                 capture_output=True, timeout=1)
                except:
                    pass  # Beep not available

    def acknowledge_alert(self, alert_id: str = None):
        """Acknowledge an alert to prevent escalation"""
        if alert_id:
            ack_file = f"/tmp/athena_alert_ack_{alert_id}"
            try:
                with open(ack_file, 'w') as f:
                    f.write(f"acknowledged_{int(time.time())}")
                logging.info(f"Alert {alert_id} acknowledged")
                return True
            except Exception as e:
                logging.error(f"Failed to acknowledge alert {alert_id}: {e}")
                return False
        else:
            # Acknowledge all pending alerts
            import glob
            ack_files = glob.glob("/tmp/athena_alert_ack_*")
            acknowledged = 0
            for ack_file in ack_files:
                try:
                    with open(ack_file, 'w') as f:
                        f.write(f"acknowledged_{int(time.time())}")
                    acknowledged += 1
                except:
                    pass
            if acknowledged > 0:
                logging.info(f"Acknowledged {acknowledged} pending alerts")
            return acknowledged > 0

    def _send_to_channel(self, channel: str, title: str, message: str, priority: str) -> Dict[str, bool]:
        """Send notification to a specific channel with retry logic"""
        results = {}
        success = False
        attempts = 0

        while attempts < self.config["retry_attempts"] and not success:
            attempts += 1

            if channel == "email":
                success = self.send_email(title, message, priority)
            elif channel == "telegram":
                success = self.send_telegram(message, priority)
            elif channel == "slack":
                success = self.send_slack(message, priority)
            elif channel == "desktop":
                success = self.send_desktop_notification(title, message, priority)

            if not success and attempts < self.config["retry_attempts"]:
                logging.info(f"Retrying {channel} notification in {self.config['retry_delay']} seconds...")
                time.sleep(self.config["retry_delay"])

            results[channel] = success

        # Log overall result
        successful_channels = [ch for ch, success in results.items() if success]
        if successful_channels:
            logging.info(f"Notification sent via: {', '.join(successful_channels)}")
        else:
            logging.error("All notification channels failed")

        return results

    def send_daily_briefing(self, briefing_text: str):
        """Send daily briefing via configured channels"""
        # Only send via non-intrusive channels for daily briefings
        daily_channels = [ch for ch in self.config["enabled_channels"]
                         if ch in ["email", "telegram", "slack"]]

        if daily_channels:
            self.send_notification(
                title="AI Republic Daily Briefing",
                message=briefing_text,
                priority="normal",
                channels=daily_channels
            )

    def send_urgent_alert(self, alert_message: str):
        """Send urgent alert via all available channels"""
        self.send_notification(
            title="🚨 AI Republic Alert",
            message=alert_message,
            priority="urgent"
        )

    def send_warning_alert(self, alert_message: str):
        """Send warning alert via available channels"""
        self.send_notification(
            title="⚠️ AI Republic Warning",
            message=alert_message,
            priority="warning"
        )

    def configure_channel(self, channel: str):
        """Interactive configuration for a notification channel"""
        print(f"\n🔧 Configuring {channel.upper()} notifications:")
        print("=" * 50)

        if channel == "email":
            print("Email configuration:")
            self.config["email"]["smtp_server"] = input("SMTP Server (smtp.gmail.com): ") or "smtp.gmail.com"
            self.config["email"]["smtp_port"] = int(input("SMTP Port (587): ") or "587")
            self.config["email"]["username"] = input("Email username: ").strip()
            self.config["email"]["password"] = input("Email password/app password: ").strip()
            self.config["email"]["from_email"] = input("From email address: ").strip()
            to_emails = input("To email addresses (comma-separated): ").strip()
            self.config["email"]["to_emails"] = [email.strip() for email in to_emails.split(",") if email.strip()]
            self.config["email"]["enabled"] = True

        elif channel == "telegram":
            print("Telegram configuration:")
            print("1. Create a bot: Message @BotFather on Telegram")
            print("2. Get your bot token from BotFather")
            print("3. Message your bot to get chat ID, or add to group and use group ID")
            self.config["telegram"]["bot_token"] = input("Bot Token: ").strip()
            chat_ids = input("Chat IDs (comma-separated): ").strip()
            self.config["telegram"]["chat_ids"] = [cid.strip() for cid in chat_ids.split(",") if cid.strip()]
            self.config["telegram"]["enabled"] = True

        elif channel == "slack":
            print("Slack configuration:")
            print("1. Create a Slack app at https://api.slack.com/apps")
            print("2. Add 'Incoming Webhooks' feature")
            print("3. Create a webhook URL")
            self.config["slack"]["webhook_url"] = input("Webhook URL: ").strip()
            self.config["slack"]["channel"] = input("Channel (#ai-republic): ") or "#ai-republic"
            self.config["slack"]["enabled"] = True

        elif channel == "desktop":
            print("Desktop notifications:")
            print("This will use your system's notification system.")
            self.config["desktop"]["enabled"] = True

        self.save_config()
        print(f"✅ {channel.upper()} configured successfully!")

    def test_channel(self, channel: str) -> bool:
        """Test a notification channel"""
        test_message = f"🧪 Test notification from AI Republic (sent at {datetime.now().strftime('%H:%M:%S')})"

        print(f"🧪 Testing {channel.upper()} notification...")

        if channel == "email":
            success = self.send_email("Test Notification", test_message)
        elif channel == "telegram":
            success = self.send_telegram(test_message)
        elif channel == "slack":
            success = self.send_slack(test_message)
        elif channel == "desktop":
            success = self.send_desktop_notification("AI Republic Test", test_message)
        else:
            print(f"❌ Unknown channel: {channel}")
            return False

        if success:
            print(f"✅ {channel.upper()} test successful!")
            return True
        else:
            print(f"❌ {channel.upper()} test failed!")
            return False

# ==================
# Health + diagnostics
# ==================
_START_EPOCH = time.time()

def is_router_healthy() -> bool:
    try:
        # lightweight sanity ping (replace with real)
        return True
    except Exception:
        return False

def get_system_uptime_human() -> str:
    secs = int(time.time() - _START_EPOCH)
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d: return f"{d}d {h}h {m}m"
    if h: return f"{h}h {m}m"
    return f"{m}m {s}s"

def audit_event(kind: str, data: Dict[str, Any]):
    # existing audit logger; ensure voice + override events land here
    pass

# Federated broadcast stub (optional)
FED_PEERS = [p for p in os.getenv("ATHENA_PEERS", "").split(",") if p.strip()]

def broadcast_command(command: str, payload: Optional[Dict[str, Any]] = None):
    if not FED_PEERS: return
    for peer in FED_PEERS:
        try:
            # POST to peer (left as stub to avoid coupling)
            # requests.post(f"http://{peer}/athena/cmd", json={"command": command, "payload": payload})
            audit_event("federation_broadcast", {"peer": peer, "command": command})
        except Exception as e:
            audit_event("federation_broadcast_error", {"peer": peer, "err": str(e)})

def main():
    parser = argparse.ArgumentParser(description='Athena Notification System')
    parser.add_argument('--configure', action='store_true', help='Configure notification channels')
    parser.add_argument('--test', metavar='CHANNEL', help='Test a notification channel')
    parser.add_argument('--send-alert', metavar='MESSAGE', help='Send urgent alert')
    parser.add_argument('--send-warning', metavar='MESSAGE', help='Send warning alert')
    parser.add_argument('--channels', action='store_true', help='Show configured channels')
    parser.add_argument('--briefing', metavar='FILE', help='Send daily briefing from file')

    args = parser.parse_args()

    notifications = AthenaNotifications()

    if args.configure:
        print("🤖 Athena Notification Configuration")
        print("=" * 40)
        print("Available channels: email, telegram, slack, desktop")

        while True:
            channel = input("\nChannel to configure (or 'done'): ").strip().lower()
            if channel == 'done':
                break
            elif channel in ['email', 'telegram', 'slack', 'desktop']:
                notifications.configure_channel(channel)
            else:
                print("Invalid channel. Try: email, telegram, slack, desktop")

        # Update enabled channels
        enabled = []
        for ch in ['email', 'telegram', 'slack', 'desktop']:
            if notifications.config[ch]["enabled"]:
                enabled.append(ch)
        notifications.config["enabled_channels"] = enabled
        notifications.save_config()

        print("\n✅ Configuration complete!")
        print(f"Enabled channels: {', '.join(enabled)}")

    elif args.test:
        success = notifications.test_channel(args.test.lower())
        exit(0 if success else 1)

    elif args.send_alert:
        notifications.send_urgent_alert(args.send_alert)
        print("🚨 Urgent alert sent!")

    elif args.send_warning:
        notifications.send_warning_alert(args.send_warning)
        print("⚠️ Warning alert sent!")

    elif args.channels:
        print("📡 Configured Notification Channels:")
        print("=" * 40)
        for channel in ['email', 'telegram', 'slack', 'desktop']:
            status = "✅ Enabled" if notifications.config[channel]["enabled"] else "❌ Disabled"
            print(f"  {channel.upper()}: {status}")

    elif args.briefing:
        try:
            with open(args.briefing, 'r') as f:
                briefing_text = f.read()
            notifications.send_daily_briefing(briefing_text)
            print("📧 Daily briefing sent!")
        except FileNotFoundError:
            print(f"❌ Briefing file not found: {args.briefing}")

    else:
        print("🤖 Athena Notification System")
        print("Usage:")
        print("  --configure          Configure notification channels")
        print("  --test CHANNEL       Test a channel (email/telegram/slack/desktop)")
        print("  --send-alert MSG     Send urgent alert")
        print("  --send-warning MSG   Send warning alert")
        print("  --channels           Show configured channels")
        print("  --briefing FILE      Send daily briefing from file")

# Context trigger helper functions
def last_transition_at() -> float:
    """Get timestamp of last macro transition (for cooldown tracking)"""
    try:
        state_file = "/tmp/athena_macro_transitions.json"
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                state = json.load(f)
                return state.get("last_transition", 0.0)
    except:
        pass
    return 0.0

def set_last_transition(timestamp: float):
    """Set timestamp of last macro transition"""
    try:
        state_file = "/tmp/athena_macro_transitions.json"
        state = {"last_transition": timestamp}
        with open(state_file, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Warning: Could not save transition state: {e}")

def strong_enough_signal(location: str, confidence: float, threshold: float = 0.7) -> bool:
    """Check if location signal is strong enough to trigger mode changes (hysteresis)"""
    # For known locations, require higher confidence
    if location in ["home", "work"]:
        return confidence >= threshold
    # For travel/unknown, be more permissive since GPS can be noisy
    elif location in ["travel", "unknown"]:
        return confidence >= (threshold - 0.2)  # Lower threshold for travel
    # Default case
    return confidence >= threshold

def initialize_voice_activation():
    """
    Initialize voice activation for Athena

    This function provides voice control integration with the notification system.
    It starts the voice activation service in a background thread.

    Usage:
        from athena_notifications import initialize_voice_activation
        initialize_voice_activation()
    """
    try:
        # Import voice activation module
        from voice_activation import VoiceActivation

        # Create and start voice activation
        va = VoiceActivation()
        va.start_voice_activation()

        print("🎤 Voice activation initialized and running")
        return True

    except ImportError as e:
        print(f"❌ Voice activation not available: {e}")
        print("Install required packages: pip install SpeechRecognition PyAudio pyobjc")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize voice activation: {e}")
        return False

if __name__ == '__main__':
    main()
