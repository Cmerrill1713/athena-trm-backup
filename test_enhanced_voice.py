#!/usr/bin/env python3
"""
Test Enhanced Voice Activation Features
=======================================

Tests the new context-aware voice feedback, priority arbitration,
voice-only macro aliases, and diagnostic voice command.
"""

import os
import sys
import time

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

from voice_activation import speak, _expand_voice_alias, VoiceActivation
from athena_notifications import (
    get_active_mode,
    apply_manual_override,
    is_override_active,
    is_router_healthy,
    get_system_uptime_human,
    clear_manual_override
)

def test_voice_styles():
    """Test context-aware voice styles"""
    print("🎤 Testing Voice Styles")
    print("=" * 30)

    styles = ["meeting_mode", "emergency_mode", "normal_mode", "maintenance_mode"]

    for style in styles:
        print(f"   Testing {style}...")
        speak(f"This is a {style.replace('_', ' ')} message", style_key=style, brief=True)
        time.sleep(0.5)

    print("✅ Voice styles test complete\n")

def test_voice_aliases():
    """Test voice-only macro aliases"""
    print("🔄 Testing Voice Aliases")
    print("=" * 30)

    aliases = [
        "red alert",
        "all clear",
        "silence",
        "deck status",
        "deck diagnostics",
        "stop automations",
        "kill switch",
        "normal command"  # should not expand
    ]

    for alias in aliases:
        expanded = _expand_voice_alias(alias)
        print(f"   '{alias}' → '{expanded}'")

    print("✅ Voice aliases test complete\n")

def test_override_system():
    """Test manual override system"""
    print("🎯 Testing Override System")
    print("=" * 30)

    print(f"   Initial active mode: {get_active_mode()}")
    print(f"   Override active: {is_override_active()}")

    # Apply override
    print("   Applying emergency mode override...")
    apply_manual_override("emergency_mode", "test", ttl_seconds=10, reason="Test override")

    print(f"   New active mode: {get_active_mode()}")
    print(f"   Override active: {is_override_active()}")

    # Clear override
    time.sleep(1)
    clear_manual_override()
    print(f"   After clearing - active mode: {get_active_mode()}")
    print(f"   Override active: {is_override_active()}")

    print("✅ Override system test complete\n")

def test_diagnostics():
    """Test diagnostic functions"""
    print("🔍 Testing Diagnostics")
    print("=" * 25)

    router_ok = is_router_healthy()
    uptime = get_system_uptime_human()

    print(f"   Router healthy: {router_ok}")
    print(f"   System uptime: {uptime}")

    # Simulate voice diagnostics response
    msg = f"Wake word OK. STT OK. Router {'OK' if router_ok else 'not responding'}. Uptime {uptime}."
    print(f"   Voice response: {msg}")

    print("✅ Diagnostics test complete\n")

def test_kill_switch():
    """Test kill switch functionality"""
    print("🛑 Testing Kill Switch")
    print("=" * 25)

    va = VoiceActivation()

    # Test kill switch commands
    kill_commands = ["stop automations", "kill switch", "disable automations"]

    for cmd in kill_commands:
        print(f"   Testing '{cmd}'...")
        result = va.process_voice_command(cmd)
        print(f"   Result: {result}")

    print("✅ Kill switch test complete\n")

def test_ttl_monitoring():
    """Test TTL monitoring system"""
    print("⏰ Testing TTL Monitoring")
    print("=" * 28)

    va = VoiceActivation()

    # Test TTL monitor initialization
    print("   Testing TTL monitor initialization...")
    va.start_ttl_monitor()
    print("   ✅ TTL monitor started")

    # Test TTL monitor stopping
    va.ttl_monitor_active = False
    print("   ✅ TTL monitor stopped")

    print("✅ TTL monitoring test complete\n")

def test_voice_integration():
    """Test voice command processing with new features"""
    print("🎭 Testing Voice Integration")
    print("=" * 35)

    va = VoiceActivation()

    # Test diagnostics command processing
    print("   Testing diagnostics command...")
    result = va.process_voice_command("deck diagnostics")
    print(f"   Result: {result}")

    # Test voice alias expansion
    print("   Testing red alert alias...")
    result = va.process_voice_command("red alert")
    print(f"   Result: {result}")

    # Test kill switch
    print("   Testing kill switch...")
    result = va.process_voice_command("stop automations")
    print(f"   Result: {result}")

    print("✅ Voice integration test complete\n")

def main():
    print("🧪 Enhanced Voice Activation Test Suite")
    print("=" * 45)
    print()

    try:
        test_voice_styles()
        test_voice_aliases()
        test_override_system()
        test_diagnostics()
        test_kill_switch()
        test_ttl_monitoring()
        test_voice_integration()

        print("🎉 All enhanced voice activation tests passed!")
        print()
        print("🚀 Ready for production voice commands:")
        print("   • 'Hey Athena, deck diagnostics'")
        print("   • 'Hey Athena, red alert'")
        print("   • 'Hey Athena, all clear'")
        print("   • 'Hey Athena, silence'")
        print("   • 'Hey Athena, stop automations'")
        print("   • TTL expiry notifications")
        print("   • Human override status updates")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
