#!/usr/bin/env python3
"""
Demo: Macro Commands for Athena
===============================

Demonstrates complex multi-step commands that execute multiple actions
in sequence, transforming simple voice/text commands into comprehensive
operational workflows.

Features:
- Meeting mode: Quiet alerts + route critical to phone
- Emergency mode: All alerts to phone immediately
- Maintenance mode: Full suppression + slow monitoring
- Normal mode: Return to standard operation

Usage:
    python3 demo_macro_commands.py --basic     # Show macro parsing
    python3 demo_macro_commands.py --meeting   # Test meeting mode
    python3 demo_macro_commands.py --emergency # Test emergency mode
    python3 demo_macro_commands.py --workflow  # Complete workflow demo
"""

import time
import sys
import os

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

from ai_command_routing import AICommandRouter

def demo_macro_parsing():
    """Demonstrate macro command parsing"""
    print("\n🎬 Macro Command Parsing Demo")
    print("=" * 35)

    router = AICommandRouter()

    macro_commands = [
        "meeting mode",
        "emergency mode",
        "maintenance mode",
        "normal mode",
        "start meeting",
        "end meeting"
    ]

    for cmd in macro_commands:
        print(f"\n📝 Command: \"{cmd}\"")
        intent = router.parse_intent(cmd)

        if intent:
            print(f"   ✅ Intent: {intent['intent']}")
            print(f"   🎯 Auth Level: {intent['definition']['auth_level']}")
            print(f"   📋 Description: {intent['definition']['description']}")

            if "macro" in intent["definition"]:
                macro_steps = intent["definition"]["macro"]
                print(f"   🎬 Macro Steps: {len(macro_steps)}")
                for i, step in enumerate(macro_steps, 1):
                    print(f"     {i}. {step['intent']}")
        else:
            print("   ❌ Not recognized")

        time.sleep(0.5)

def demo_meeting_workflow():
    """Demonstrate complete meeting mode workflow"""
    print("\n👥 Meeting Mode Workflow Demo")
    print("=" * 35)

    router = AICommandRouter()

    print("Scenario: You're about to start an important client meeting")
    print()

    # Step 1: Activate meeting mode
    print("1️⃣ Activating Meeting Mode...")
    result = router.route_command("meeting mode")

    if result.get("success"):
        print("   ✅ Meeting mode activated")
        print("   🎬 Executed 2 macro steps:")
        print("     - Quiet alerts for 60 minutes")
        print("     - Route critical alerts to phone")
        print()
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return

    # Simulate meeting time
    print("2️⃣ During Meeting (simulated)...")
    print("   🔕 Non-critical alerts automatically suppressed")
    print("   🚨 Critical alerts routed directly to phone")
    print("   📊 System continues monitoring in background")
    print()

    time.sleep(2)

    # Step 3: Return to normal
    print("3️⃣ Meeting Complete - Returning to Normal...")
    result = router.route_command("normal mode")

    if result.get("success"):
        print("   ✅ Normal mode restored")
        print("   🎬 Executed normalization steps")
        print("   🔔 Alert routing returned to standard")
    else:
        print(f"   ❌ Failed: {result.get('error')}")

def demo_emergency_mode():
    """Demonstrate emergency mode macro"""
    print("\n🚨 Emergency Mode Demo")
    print("=" * 25)

    router = AICommandRouter()

    print("Scenario: Critical system issue detected - need immediate attention")
    print()

    result = router.route_command("emergency mode")

    if result.get("success"):
        print("✅ Emergency mode activated!")
        print("🎬 Executed emergency macro:")
        print("   - Route warning alerts to phone")
        print("   - Route critical alerts to phone")
        print("   - Clear any quiet periods")
        print()
        print("📱 All alerts now going directly to phone")
        print("⚡ Immediate awareness of any issues")
    else:
        print(f"❌ Emergency mode failed: {result.get('error')}")

def demo_maintenance_mode():
    """Demonstrate maintenance mode macro"""
    print("\n🔧 Maintenance Mode Demo")
    print("=" * 30)

    router = AICommandRouter()

    print("Scenario: Performing system maintenance - need quiet environment")
    print()

    result = router.route_command("maintenance mode")

    if result.get("success"):
        print("✅ Maintenance mode activated!")
        print("🎬 Executed maintenance macro:")
        print("   - Suppress alerts for 2 hours")
        print("   - Slow tribunal monitoring to 60 minutes")
        print("   - Route critical alerts to phone")
        print()
        print("🔇 System operating quietly for maintenance")
        print("⏰ Monitoring cadence reduced to prevent noise")
        print("📞 Critical issues still get through immediately")
    else:
        print(f"❌ Maintenance mode failed: {result.get('error')}")

def demo_complete_workflow():
    """Demonstrate complete operational workflow with macros"""
    print("\n🔄 Complete Operational Workflow")
    print("=" * 40)

    router = AICommandRouter()

    workflow = [
        ("normal mode", "Start day in standard mode"),
        ("meeting mode", "Client presentation starting"),
        ("emergency mode", "Urgent system alert during meeting"),
        ("maintenance mode", "Post-meeting system updates"),
        ("normal mode", "Return to standard operations")
    ]

    for cmd, description in workflow:
        print(f"\n🎯 {description}")
        print(f"   Command: \"{cmd}\"")

        result = router.route_command(cmd)

        if result.get("success"):
            print("   ✅ Success")
            if "steps_executed" in result:
                print(f"   🎬 {result['steps_executed']} macro steps executed")
        else:
            print(f"   ❌ Failed: {result.get('error')}")

        time.sleep(1.5)

    print("\n🏆 Workflow Complete!")
    print("   • 5 macro commands executed")
    print("   • System state managed through modes")
    print("   • All transitions handled automatically")

def show_macro_benefits():
    """Show the benefits of macro commands"""
    print("\n💡 Macro Command Benefits")
    print("=" * 30)

    benefits = [
        ("🎯 One Command, Multiple Actions", "meeting mode = quiet + route in one step"),
        ("⚡ Operational Speed", "Complex workflows in seconds, not minutes"),
        ("🛡️ Consistency", "Standardized responses to common scenarios"),
        ("📝 Audit Trail", "Complete record of multi-step operations"),
        ("🎚️ Progressive Complexity", "Start simple, add complexity as needed"),
        ("🔄 Reversible", "Easy rollback with normal/emergency modes"),
        ("📊 Observable", "Clear status indicators for active modes"),
        ("🎨 Extensible", "Easy to add new macro combinations")
    ]

    for title, description in benefits:
        print(f"   {title}")
        print(f"      {description}")
        print()

def main():
    print("🎬 Athena Macro Commands Demo")
    print("=" * 35)
    print()

    if len(sys.argv) < 2:
        print("Complete macro command system with multi-step operations.")
        print()
        print("Commands:")
        print("  --basic      Show macro parsing and recognition")
        print("  --meeting    Demonstrate meeting mode workflow")
        print("  --emergency  Test emergency mode macro")
        print("  --workflow   Complete operational workflow")
        print("  --benefits   Show macro command advantages")
        print()
        print("Macro Commands Available:")
        print("  • meeting mode     - Quiet + critical alerts to phone")
        print("  • emergency mode   - All alerts to phone immediately")
        print("  • maintenance mode - Full suppression + slow monitoring")
        print("  • normal mode      - Return to standard operation")
        print()
        print("Example: python3 demo_macro_commands.py --meeting")

        return

    command = sys.argv[1]

    if command == "--basic":
        demo_macro_parsing()

    elif command == "--meeting":
        demo_meeting_workflow()

    elif command == "--emergency":
        demo_emergency_mode()

    elif command == "--workflow":
        demo_complete_workflow()

    elif command == "--benefits":
        show_macro_benefits()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
