#!/usr/bin/env python3
"""
Athena CLI Interface
====================

Command-line interface for Athena's AI Republic.
Provides natural language command execution with context awareness.

Usage:
    python3 athena_cli.py do "status"
    python3 athena_cli.py do "quiet for 30 minutes"
    python3 athena_cli.py do "route critical to phone"
    python3 athena_cli.py voice  # Start voice interface
"""

import sys
from ai_command_routing import AICommandRouter

def main():
    if len(sys.argv) < 2:
        print("🧠 Athena CLI - AI Republic Command Interface")
        print("=" * 50)
        print()
        print("Natural language commands for your AI Republic.")
        print()
        print("Usage:")
        print("  athena do \"<command>\"     Execute natural language command")
        print("  athena voice               Start voice interface")
        print("  athena help                Show available commands")
        print()
        print("Example Commands:")
        print("  athena do \"status\"")
        print("  athena do \"quiet for 30 minutes\"")
        print("  athena do \"route critical to phone\"")
        print("  athena do \"meeting mode\"")
        print("  athena do \"emergency mode\"")
        print("  athena do \"maintenance mode\"")
        print()
        print("Quick Commands:")
        print("  athena status          # System health")
        print("  athena quiet           # Quick 30min quiet")
        print("  athena meeting         # Meeting mode macro")
        print("  athena normal          # Return to normal")
        print("  athena emergency       # Emergency routing")
        print("  athena dashboard       # Open NeuroForge")
        return

    command = sys.argv[1]

    if command == "do":
        if len(sys.argv) < 3:
            print("❌ Please provide a command: athena do \"<command>\"")
            return

        cmd_text = " ".join(sys.argv[2:])
        router = AICommandRouter()
        result = router.route_command(cmd_text)

        if result.get("success"):
            print(f"✅ {result.get('message', 'Command executed')}")
        else:
            print(f"❌ {result.get('error', 'Command failed')}")

    elif command == "status":
        # Quick status command
        router = AICommandRouter()
        result = router.route_command("status")

        if result.get("success"):
            print("🧠 Athena Status: Healthy")
            if "details" in result:
                details = result["details"]
                print(f"   Version: {details.get('version', 'Unknown')}")
                print(f"   Timestamp: {details.get('timestamp', 'Unknown')[:19]}")
        else:
            print(f"❌ Status check failed: {result.get('error')}")

    elif command == "quiet":
        # Quick quiet command
        router = AICommandRouter()
        result = router.route_command("quiet for 30 minutes")

        if result.get("success"):
            print(f"🔕 {result.get('message')}")
        else:
            print(f"❌ Quiet command failed: {result.get('error')}")

    elif command == "dashboard":
        # Quick dashboard command
        router = AICommandRouter()
        result = router.route_command("open dashboard")

        if result.get("success"):
            print(f"📊 {result.get('message')}")
        else:
            print(f"❌ Dashboard command failed: {result.get('error')}")

    elif command == "meeting":
        # Quick meeting mode command
        router = AICommandRouter()
        result = router.route_command("meeting mode")

        if result.get("success"):
            print(f"👥 {result.get('message')}")
        else:
            print(f"❌ Meeting mode failed: {result.get('error')}")

    elif command == "normal":
        # Quick normal mode command
        router = AICommandRouter()
        result = router.route_command("normal mode")

        if result.get("success"):
            print(f"🔄 {result.get('message')}")
        else:
            print(f"❌ Normal mode failed: {result.get('error')}")

    elif command == "emergency":
        # Quick emergency mode command
        router = AICommandRouter()
        result = router.route_command("emergency mode")

        if result.get("success"):
            print(f"🚨 {result.get('message')}")
        else:
            print(f"❌ Emergency mode failed: {result.get('error')}")

    elif command == "voice":
        print("🎤 Voice interface not yet implemented")
        print("💡 For now, use: athena do \"<command>\"")

    elif command == "help":
        print("🧠 Athena Available Commands")
        print("=" * 35)
        print()
        router = AICommandRouter()
        for name, intent in router.intents.items():
            auth_icon = "🔒" if intent['auth_level'] >= 3 else "✅" if intent['auth_level'] >= 2 else "🆓"
            print(f"{auth_icon} {name}")
            print(f"   {intent['description']}")
            examples = [p.replace(r'(\w+)', '<word>').replace(r'(\d+)', '<number>') for p in intent['patterns'][:2]]
            print(f"   Examples: {' | '.join(examples)}")
            print()

    else:
        print(f"❌ Unknown command: {command}")
        print("💡 Try: athena help")

if __name__ == "__main__":
    main()
