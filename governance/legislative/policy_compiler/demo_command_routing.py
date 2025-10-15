#!/usr/bin/env python3
"""
Demo: AI Command Routing for Athena
===================================

Demonstrates natural language command execution with context awareness,
policy gates, and audit logging.

Features:
- Intent parsing and validation
- Authorization with Touch ID
- Command execution pipeline
- Audit trail logging
- Multi-modal interface demo

Usage:
    python3 demo_command_routing.py --basic     # Basic command parsing
    python3 demo_command_routing.py --execute   # Execute sample commands
    python3 demo_command_routing.py --audit     # Show audit log
    python3 demo_command_routing.py --full      # Full workflow demo
"""

import time
import sys
import os

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

from ai_command_routing import AICommandRouter

def demo_basic_parsing():
    """Demonstrate basic intent parsing"""
    print("\n🧠 Command Parsing Demo")
    print("=" * 30)

    router = AICommandRouter()

    test_commands = [
        "status",
        "quiet for 30 minutes",
        "route critical to phone",
        "ack all",
        "tribunal every 15 minutes",
        "open dashboard",
        "unknown command"
    ]

    for cmd in test_commands:
        print(f"\n📝 Command: \"{cmd}\"")
        intent = router.parse_intent(cmd)

        if intent:
            print(f"   ✅ Intent: {intent['intent']}")
            print(f"   🎯 Slots: {intent['slots']}")
            print(f"   🔐 Auth Level: {intent['definition']['auth_level']}")
            print(f"   📋 Description: {intent['definition']['description']}")
        else:
            print("   ❌ Not recognized")

        time.sleep(0.5)

def demo_command_execution():
    """Demonstrate command execution pipeline"""
    print("\n⚡ Command Execution Demo")
    print("=" * 35)

    router = AICommandRouter()

    # Test commands that don't require high auth
    test_commands = [
        "status",
        "quiet for 15 minutes",  # This will require approval
        "open dashboard"
    ]

    for cmd in test_commands:
        print(f"\n🚀 Executing: \"{cmd}\"")
        result = router.route_command(cmd)

        if result.get("success"):
            print(f"   ✅ {result.get('message', 'Success')}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ {error}")

        time.sleep(1)

def demo_audit_trail():
    """Demonstrate audit logging"""
    print("\n📋 Audit Trail Demo")
    print("=" * 25)

    router = AICommandRouter()

    print(f"Total audit entries: {len(router.audit_log)}")

    if router.audit_log:
        print("\nRecent entries:")
        for entry in router.audit_log[-3:]:  # Last 3
            ts = entry['timestamp'][:19]
            intent = entry['intent']
            outcome = entry['outcome']
            print(f"   {ts} | {intent} | {outcome}")
    else:
        print("No audit entries yet - execute some commands first")

def demo_cli_interface():
    """Demonstrate CLI interface"""
    print("\n💻 CLI Interface Demo")
    print("=" * 25)

    print("Testing athena CLI commands:")
    print()

    # Test basic commands
    test_commands = [
        ["python3", "athena_cli.py", "status"],
        ["python3", "athena_cli.py", "help"]
    ]

    for cmd_args in test_commands:
        print(f"💻 {' '.join(cmd_args)}")
        try:
            result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Show first few lines of output
                lines = result.stdout.strip().split('\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                if len(result.stdout.strip().split('\n')) > 3:
                    print("   ...")
            else:
                print(f"   ❌ Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        time.sleep(1)

def demo_full_workflow():
    """Demonstrate complete command routing workflow"""
    print("\n🔄 Complete Command Routing Workflow")
    print("=" * 45)

    router = AICommandRouter()

    print("1️⃣ Service Check")
    services_ok = router.check_athena_services()
    print(f"   Athena Services: {'✅ Running' if services_ok else '❌ Not Available'}")
    print()

    print("2️⃣ Intent Parsing")
    command = "quiet for 30 minutes"
    intent = router.parse_intent(command)
    if intent:
        print(f"   ✅ Parsed: {intent['intent']} (auth level {intent['definition']['auth_level']})")
    else:
        print("   ❌ Parsing failed")
    print()

    print("3️⃣ Context Validation")
    context_ok = router.validate_context(intent) if intent else False
    print(f"   Context Valid: {'✅ Yes' if context_ok else '❌ No'}")
    print()

    print("4️⃣ Authorization Check")
    auth_ok = router.check_authorization(intent) if intent else False
    print(f"   Authorized: {'✅ Yes' if auth_ok else '❌ No (requires approval)'}")
    print()

    print("5️⃣ Command Execution")
    if intent and context_ok and auth_ok:
        result = router.execute_command(intent)
        if result.get("success"):
            print(f"   ✅ Executed: {result.get('message')}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    else:
        print("   ⏭️ Skipped (prerequisites not met)")
    print()

    print("6️⃣ Audit Logging")
    if router.audit_log:
        last_entry = router.audit_log[-1]
        print(f"   📝 Logged: {last_entry['intent']} → {last_entry['outcome']}")
    else:
        print("   📝 No audit entries")

def main():
    print("🎯 Athena AI Command Routing Demo")
    print("=" * 45)
    print()

    if len(sys.argv) < 2:
        print("Complete AI command routing system with natural language processing.")
        print()
        print("Commands:")
        print("  --basic     Demonstrate intent parsing")
        print("  --execute   Execute sample commands")
        print("  --audit     Show audit trail")
        print("  --cli       Test CLI interface")
        print("  --full      Complete workflow demonstration")
        print()
        print("Features:")
        print("  • Natural language intent parsing")
        print("  • Context-aware command validation")
        print("  • Policy-based authorization")
        print("  • Comprehensive audit logging")
        print("  • Multi-modal interfaces")
        print()
        print("Example: python3 demo_command_routing.py --basic")

        return

    command = sys.argv[1]

    if command == "--basic":
        demo_basic_parsing()

    elif command == "--execute":
        demo_command_execution()

    elif command == "--audit":
        demo_audit_trail()

    elif command == "--cli":
        demo_cli_interface()

    elif command == "--full":
        demo_full_workflow()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
