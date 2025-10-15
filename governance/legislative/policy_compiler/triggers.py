#!/usr/bin/env python3
"""
Context-Triggered Macro System for Athena
==========================================

Automatically activates macros based on time, location, calendar, and system events.

Features:
- Time-based triggers (maintenance windows, business hours)
- Location-based triggers (home/work/travel geofencing)
- Calendar integration (meeting detection)
- System health monitoring
- Cooldown and hysteresis to prevent flapping
- Override-safe (manual macros always win)

Usage:
    python3 triggers.py  # Start monitoring
    python3 triggers.py --test  # Test trigger conditions
    python3 triggers.py --status  # Show active triggers and context
"""

import time
import os
import sys
import json
from dataclasses import dataclass
from collections import defaultdict, deque
import argparse

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

# Import from existing athena_notifications system
from athena_notifications import (
    execute_macro, list_active_macros, update_smart_alerting,  # returns dict: focus, calendar_busy, location, now, etc.
    last_transition_at, set_last_transition,  # state helpers (need to implement these)
    strong_enough_signal,  # hysteresis helper (need to implement this)
)

# Import spike detection
from spikes import alert_spike_detected, get_spike_status

# Configuration - can be overridden by environment variables
COOLDOWN_SECONDS = int(os.getenv("TRANSITION_COOLDOWN_SECONDS", "300"))  # 5 min between auto mode changes
CHECK_INTERVAL = int(os.getenv("MACRO_CHECK_INTERVAL", "30"))  # seconds
HYSTERESIS_CONFIDENCE = float(os.getenv("HYSTERESIS_CONFIDENCE", "0.7"))  # carry-over threshold
CONTEXT_MACROS_ENABLED = os.getenv("CONTEXT_MACROS_ENABLED", "true").lower() == "true"
AUTOMATIONS_PAUSED_UNTIL = 0  # timestamp when automations resume
OVERRIDE_TTL_MIN = int(os.getenv("OVERRIDE_TTL_MIN", "30"))  # manual override duration

# Mode mutexes - prevent conflicting states
MUTEX = {
    "emergency_mode": {"meeting_mode", "maintenance_mode", "focus_mode", "travel_mode"},
    "maintenance_mode": {"emergency_mode", "meeting_mode", "travel_mode"},
    "meeting_mode": {"emergency_mode", "maintenance_mode"},
}

# Anti-flap: require N consecutive detections before mode change
FLAP_DETECTION_ENABLED = os.getenv("FLAP_DETECTION_ENABLED", "true").lower() == "true"
REQUIRED_CONSECUTIVE_HITS = int(os.getenv("REQUIRED_CONSECUTIVE_HITS", "2"))
FLAP_WINDOW_SECONDS = int(os.getenv("FLAP_WINDOW_SECONDS", "300"))  # 5 min window

# State tracking for flap detection
flap_history = defaultdict(deque)

@dataclass
class Context:
    """Current system context for trigger evaluation"""
    calendar_busy: bool
    location: str           # "home" | "work" | "travel" | "unknown"
    left_work_recently: bool
    now_ts: float
    weekday: int            # 0=Mon .. 6=Sun
    hour: int               # 0..23
    confidence: float       # location confidence 0.0-1.0
    focus_mode: bool
    quiet_hours: bool

    def to_dict(self) -> dict:
        return {
            "calendar_busy": self.calendar_busy,
            "location": self.location,
            "left_work_recently": self.left_work_recently,
            "now_ts": self.now_ts,
            "weekday": self.weekday,
            "hour": self.hour,
            "confidence": self.confidence,
            "focus_mode": self.focus_mode,
            "quiet_hours": self.quiet_hours,
        }

def _cooldown_ok(now_ts: float) -> bool:
    """Check if enough time has passed since last transition"""
    try:
        lt = last_transition_at() or 0
        return (now_ts - lt) >= COOLDOWN_SECONDS
    except:
        # If state helpers don't exist yet, default to OK
        return True

def _automations_paused() -> bool:
    """Check if automations are manually paused"""
    return time.time() < AUTOMATIONS_PAUSED_UNTIL

def _manual_override_active() -> bool:
    """Check if manual override is currently active"""
    try:
        with open("/tmp/athena_manual_override.json", "r") as f:
            data = json.load(f)
            return time.time() < data.get("expires_at", 0)
    except:
        return False

def _blocked_by_mutex(target_macro: str) -> bool:
    """Check if target macro is blocked by mutex with active macros"""
    active = list_active_macros()
    for active_macro in active.keys():
        if active_macro in MUTEX.get(target_macro, set()):
            return True
    return False

def _flap_detection_ok(macro_name: str, condition_met: bool, now_ts: float) -> bool:
    """Anti-flap: require consecutive hits before allowing mode change"""
    if not FLAP_DETECTION_ENABLED:
        return condition_met

    if condition_met:
        # Add hit to history
        flap_history[macro_name].append(now_ts)
    else:
        # Clear history on condition not met
        flap_history[macro_name].clear()
        return False

    # Clean old entries
    cutoff = now_ts - FLAP_WINDOW_SECONDS
    flap_history[macro_name] = deque([t for t in flap_history[macro_name] if t > cutoff])

    # Check if we have enough consecutive hits
    return len(flap_history[macro_name]) >= REQUIRED_CONSECUTIVE_HITS

def activate_manual_override(minutes: int = None):
    """Activate manual override to suppress auto-triggers"""
    if minutes is None:
        minutes = OVERRIDE_TTL_MIN

    expires_at = time.time() + (minutes * 60)
    try:
        with open("/tmp/athena_manual_override.json", "w") as f:
            json.dump({"expires_at": expires_at, "activated_at": time.time()}, f)
        print(f"🔒 Manual override activated for {minutes} minutes")
        return True
    except Exception as e:
        print(f"❌ Failed to activate manual override: {e}")
        return False

def pause_automations(minutes: int):
    """Globally pause all automations for specified minutes"""
    global AUTOMATIONS_PAUSED_UNTIL
    AUTOMATIONS_PAUSED_UNTIL = time.time() + (minutes * 60)
    print(f"⏸️ Automations paused for {minutes} minutes")

def _activate_macro(macro: str, reason: str, ctx: Context):
    """Activate a macro with proper logging"""
    print(f"🎯 Auto-activating macro: {macro}")
    print(f"   Reason: {reason}")
    print(f"   Context: {ctx.to_dict()}")

    success = execute_macro(macro, f"auto:{reason}")
    if success:
        set_last_transition(ctx.now_ts)
        print(f"✅ Macro {macro} activated successfully")
    else:
        print(f"❌ Failed to activate macro {macro}")

    return success

def evaluate_rules(ctx: Context):
    """Evaluate all trigger rules and activate macros as needed"""

    # Priority 1: Check if automations are globally paused
    if _automations_paused():
        print("⏸️ Automations paused - skipping auto-triggers")
        return

    # Priority 2: Manual override active
    if _manual_override_active():
        print("🔒 Manual override active - skipping auto-triggers")
        return

    # Priority 3: Cooldown period
    if not _cooldown_ok(ctx.now_ts):
        print("⏰ Cooldown active - skipping auto-triggers")
        return

    # Priority 4: Hysteresis check
    if not strong_enough_signal(ctx.location, ctx.confidence, threshold=HYSTERESIS_CONFIDENCE):
        print(f"📊 Location confidence too low ({ctx.confidence:.2f} < {HYSTERESIS_CONFIDENCE}) - skipping")
        return

    # ---- Priority-ordered trigger rules ----

    # 1) Calendar Busy → Meeting Mode (highest priority - explicit user intent)
    if _flap_detection_ok("meeting_mode", ctx.calendar_busy and ctx.location in {"work", "home"}, ctx.now_ts):
        if not _blocked_by_mutex("meeting_mode"):
            return _activate_macro("meeting_mode", f"calendar_busy@{ctx.location}", ctx)

    # 2) Travel detection → Travel Mode
    if _flap_detection_ok("travel_mode", ctx.location == "travel", ctx.now_ts):
        if not _blocked_by_mutex("travel_mode"):
            return _activate_macro("travel_mode", "geofence_travel", ctx)

    # 3) Commute (leaving work during work hours) → Commute Mode
    commute_condition = ctx.left_work_recently and 8 <= ctx.hour <= 19 and ctx.weekday < 5
    if _flap_detection_ok("commute_mode", commute_condition, ctx.now_ts):
        if not _blocked_by_mutex("commute_mode"):
            return _activate_macro("commute_mode", "left_work_window", ctx)

    # 4) Maintenance window (02:00–04:00) → Maintenance Mode
    if _flap_detection_ok("maintenance_mode", 2 <= ctx.hour < 4, ctx.now_ts):
        if not _blocked_by_mutex("maintenance_mode"):
            return _activate_macro("maintenance_mode", "night_maintenance", ctx)

    # 5) Default normalization at home outside business hours → Normal Mode
    normal_condition = ctx.location == "home" and (ctx.hour >= 19 or ctx.hour < 8) and not ctx.calendar_busy
    if _flap_detection_ok("normal_mode", normal_condition, ctx.now_ts):
        if not _blocked_by_mutex("normal_mode"):
            return _activate_macro("normal_mode", "home_off_hours", ctx)

    # 6) Emergency Mode - Health Spike Detection (highest priority for safety)
    if alert_spike_detected():
        if not _blocked_by_mutex("emergency_mode"):
            return _activate_macro("emergency_mode", "alert_spike_detected", ctx)

    print("📋 No trigger conditions met - staying in current mode")

def context_from_smart_alerting(raw_ctx: dict) -> Context:
    """Convert smart alerting context to our Context dataclass"""
    import datetime

    now_ts = raw_ctx.get("timestamp", time.time())
    now = datetime.datetime.fromtimestamp(now_ts)

    # Extract location with fallback
    location = raw_ctx.get("location", "unknown")
    if location not in ["home", "work", "travel"]:
        location = "unknown"

    return Context(
        calendar_busy=raw_ctx.get("calendar_busy", False),
        location=location,
        left_work_recently=raw_ctx.get("left_work_recently", False),
        now_ts=now_ts,
        weekday=now.weekday(),
        hour=now.hour,
        confidence=raw_ctx.get("location_confidence", 1.0),
        focus_mode=raw_ctx.get("focus_mode", False),
        quiet_hours=raw_ctx.get("quiet_hours", False),
    )

def run_trigger_engine_forever():
    """Main trigger engine loop"""
    print("🎯 Context Macro Trigger Engine Starting")
    print("=" * 50)
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Cooldown: {COOLDOWN_SECONDS}s")
    print(f"Hysteresis threshold: {HYSTERESIS_CONFIDENCE}")
    print(f"Enabled: {CONTEXT_MACROS_ENABLED}")
    print()

    if not CONTEXT_MACROS_ENABLED:
        print("❌ Context macros disabled via CONTEXT_MACROS_ENABLED=false")
        return

    try:
        while CONTEXT_MACROS_ENABLED:
            try:
                # Get current context from smart alerting system
                raw_ctx = update_smart_alerting()

                # Convert to our context format
                ctx = context_from_smart_alerting(raw_ctx)

                # Show current context (brief)
                print(f"📊 Context: {ctx.location} | {'busy' if ctx.calendar_busy else 'free'} | {ctx.hour:02d}:00 | conf:{ctx.confidence:.2f}")

                # Evaluate rules
                evaluate_rules(ctx)

                # Wait for next check
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                print("\n🛑 Trigger engine stopped by user")
                break
            except Exception as e:
                print(f"❌ Trigger engine error: {e}")
                time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"❌ Fatal trigger engine error: {e}")

def test_trigger_conditions():
    """Test various trigger conditions manually"""
    print("🧪 Testing Trigger Conditions")
    print("=" * 40)

    test_cases = [
        # (description, context_modifications)
        ("Meeting Mode - Calendar busy at work", {"calendar_busy": True, "location": "work"}),
        ("Meeting Mode - Calendar busy at home", {"calendar_busy": True, "location": "home"}),
        ("Travel Mode", {"location": "travel"}),
        ("Commute Mode", {"left_work_recently": True, "hour": 17, "weekday": 1}),
        ("Maintenance Mode", {"hour": 3}),
        ("Normal Mode - Home off-hours", {"location": "home", "hour": 20, "calendar_busy": False}),
        ("No triggers - Home business hours", {"location": "home", "hour": 14, "calendar_busy": False}),
    ]

    for description, mods in test_cases:
        print(f"\n🧪 {description}")

        # Get base context
        raw_ctx = update_smart_alerting()

        # Apply test modifications
        test_ctx = raw_ctx.copy()
        test_ctx.update(mods)
        test_ctx["now"] = time.time()  # Ensure current time

        # Convert and evaluate
        ctx = context_from_smart_alerting(test_ctx)
        print(f"   Context: {ctx.to_dict()}")

        # Test evaluation (without actually activating macros)
        try:
            evaluate_rules(ctx)
        except Exception as e:
            print(f"   Error: {e}")

def get_diagnostics_report() -> str:
    """Generate a voice-friendly diagnostics report"""
    status_parts = []

    # System status
    status_parts.append("Context triggers active" if CONTEXT_MACROS_ENABLED else "Context triggers disabled")

    # Active macros
    active = list_active_macros()
    if active:
        macro_names = list(active.keys())
        status_parts.append(f"Active macros: {', '.join(macro_names)}")
    else:
        status_parts.append("No active macros")

    # Current context
    try:
        raw_ctx = update_smart_alerting()
        ctx = context_from_smart_alerting(raw_ctx)
        location_desc = f"{ctx.location} area"
        time_desc = f"{ctx.hour} {ctx.hour % 12 or 12} {'AM' if ctx.hour < 12 else 'PM'}"
        calendar_desc = "calendar busy" if ctx.calendar_busy else "calendar free"
        status_parts.extend([location_desc, time_desc, calendar_desc])
    except:
        status_parts.append("Context unavailable")

    # Spike status
    spike_info = get_spike_status()
    if spike_info["spike_detected"]:
        status_parts.append("Alert spike detected")
    else:
        status_parts.append(f"{spike_info['alerts_in_window']} recent alerts")

    return ". ".join(status_parts)

def handle_voice_command(command: str) -> str:
    """Handle voice commands related to automation control"""
    cmd = command.lower().strip()

    if "diagnostics" in cmd or "status" in cmd:
        return get_diagnostics_report()

    elif "pause automations" in cmd or "pause automation" in cmd:
        # Extract minutes if specified
        minutes = 60  # default
        if "minutes" in cmd or "minute" in cmd:
            import re
            match = re.search(r'(\d+)\s*minute', cmd)
            if match:
                minutes = int(match.group(1))

        pause_automations(minutes)
        return f"Automations paused for {minutes} minutes"

    elif "resume automations" in cmd or "resume automation" in cmd:
        global AUTOMATIONS_PAUSED_UNTIL
        AUTOMATIONS_PAUSED_UNTIL = 0
        return "Automations resumed"

    elif "manual override" in cmd:
        activate_manual_override()
        return f"Manual override activated for {OVERRIDE_TTL_MIN} minutes"

    return "Unknown automation command"

def show_status():
    """Show current trigger engine status"""
    print("🎯 Context Macro Trigger Status")
    print("=" * 40)

    print(f"Enabled: {CONTEXT_MACROS_ENABLED}")
    print(f"Check Interval: {CHECK_INTERVAL}s")
    print(f"Cooldown: {COOLDOWN_SECONDS}s")
    print(f"Hysteresis: {HYSTERESIS_CONFIDENCE}")
    print(f"Automations Paused: {_automations_paused()}")
    print(f"Manual Override: {_manual_override_active()}")

    # Show active macros
    active = list_active_macros()
    if active:
        print(f"\nActive Macros ({len(active)}):")
        for name, info in active.items():
            if isinstance(info, dict):
                activated = time.strftime("%H:%M:%S", time.localtime(info.get("activated_at", 0)))
                trigger = info.get("trigger_source", "unknown")
                print(f"  📋 {name} (since {activated}, via {trigger})")
    else:
        print("\nNo active macros")

    # Show current context
    try:
        raw_ctx = update_smart_alerting()
        ctx = context_from_smart_alerting(raw_ctx)
        print("\nCurrent Context:")
        print(f"  Location: {ctx.location} (confidence: {ctx.confidence:.2f})")
        print(f"  Calendar: {'busy' if ctx.calendar_busy else 'free'}")
        print(f"  Time: {ctx.weekday} {ctx.hour:02d}:00")
        print(f"  Focus: {'active' if ctx.focus_mode else 'inactive'}")
        print(f"  Quiet Hours: {'active' if ctx.quiet_hours else 'inactive'}")
    except Exception as e:
        print(f"\nContext unavailable: {e}")

    # Show spike status
    spike_info = get_spike_status()
    print("\nSpike Detection:")
    print(f"  Alerts in window: {spike_info['alerts_in_window']}/{spike_info['threshold']}")
    print(f"  Spike detected: {spike_info['spike_detected']}")
    if spike_info['cooldown_remaining'] > 0:
        print(f"  Cooldown: {int(spike_info['cooldown_remaining']/60)}m remaining")

def main():
    parser = argparse.ArgumentParser(description='Context-Triggered Macro System')
    parser.add_argument('--test', action='store_true', help='Test trigger conditions')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--once', action='store_true', help='Run evaluation once and exit')

    args = parser.parse_args()

    if args.test:
        test_trigger_conditions()
    elif args.status:
        show_status()
    elif args.once:
        print("🔄 Running single evaluation...")
        try:
            raw_ctx = update_smart_alerting()
            ctx = context_from_smart_alerting(raw_ctx)
            evaluate_rules(ctx)
            print("✅ Evaluation complete")
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
    else:
        # Default: run forever
        run_trigger_engine_forever()

if __name__ == '__main__':
    main()
