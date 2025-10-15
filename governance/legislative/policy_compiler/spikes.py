#!/usr/bin/env python3
"""
Alert Spike Detection for Emergency Mode Triggers
===============================================

Monitors alert volume and triggers emergency mode when thresholds are exceeded.
"""

import time
from collections import deque
import os
import json

# Configuration
WINDOW_SECONDS = int(os.getenv("SPIKE_WINDOW_SECONDS", "600"))  # 10 minutes
THRESHOLD = int(os.getenv("SPIKE_THRESHOLD", "5"))  # 5 alerts in window
SPIKE_COOLDOWN_SECONDS = int(os.getenv("SPIKE_COOLDOWN_SECONDS", "1800"))  # 30 min cooldown

# State
alert_events = deque()
last_spike_triggered = 0

def record_alert(timestamp=None):
    """Record an alert event for spike detection"""
    ts = timestamp or time.time()
    alert_events.append(ts)

    # Clean old events outside window
    cutoff = ts - WINDOW_SECONDS
    while alert_events and alert_events[0] < cutoff:
        alert_events.popleft()

def alert_spike_detected() -> bool:
    """Check if alert spike threshold is exceeded"""
    global last_spike_triggered
    now = time.time()

    # Clean old events
    cutoff = now - WINDOW_SECONDS
    while alert_events and alert_events[0] < cutoff:
        alert_events.popleft()

    # Check cooldown
    if now - last_spike_triggered < SPIKE_COOLDOWN_SECONDS:
        return False

    # Check threshold
    spike_detected = len(alert_events) >= THRESHOLD

    if spike_detected:
        last_spike_triggered = now

    return spike_detected

def get_spike_status() -> dict:
    """Get current spike detection status"""
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    # Clean old events for status
    clean_events = [t for t in alert_events if t > cutoff]

    return {
        "alerts_in_window": len(clean_events),
        "threshold": THRESHOLD,
        "window_seconds": WINDOW_SECONDS,
        "spike_detected": len(clean_events) >= THRESHOLD,
        "cooldown_remaining": max(0, SPIKE_COOLDOWN_SECONDS - (now - last_spike_triggered)),
        "last_spike": last_spike_triggered
    }

def save_spike_state():
    """Save spike detection state to disk"""
    try:
        state = {
            "alert_events": list(alert_events),
            "last_spike_triggered": last_spike_triggered,
            "saved_at": time.time()
        }
        with open("/tmp/athena_spike_state.json", "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Warning: Could not save spike state: {e}")

def load_spike_state():
    """Load spike detection state from disk"""
    try:
        with open("/tmp/athena_spike_state.json", "r") as f:
            state = json.load(f)

        global alert_events, last_spike_triggered
        alert_events = deque(state.get("alert_events", []))
        last_spike_triggered = state.get("last_spike_triggered", 0)

        # Clean events that are too old
        now = time.time()
        cutoff = now - WINDOW_SECONDS
        alert_events = deque([t for t in alert_events if t > cutoff])

    except:
        # No saved state, start fresh
        pass

# Load state on import
load_spike_state()

# Auto-save state periodically (would be called from main loop)
def periodic_save():
    """Call this periodically to save state"""
    save_spike_state()

if __name__ == "__main__":
    # Test the spike detection
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Testing Spike Detection")
        print("Adding 6 alerts over 5 minutes...")

        base_time = time.time()
        for i in range(6):
            record_alert(base_time + (i * 60))  # One per minute

        print(f"Spike status: {get_spike_status()}")

        # Test cooldown
        print("\nTesting cooldown...")
        status = get_spike_status()
        if status["spike_detected"]:
            print("Spike detected - testing cooldown")
            time.sleep(1)
            status2 = get_spike_status()
            print(f"Immediate re-check: {status2}")

    else:
        print("Spike Detection Module")
        print("Usage: python3 spikes.py test")
        print(f"Current status: {get_spike_status()}")
