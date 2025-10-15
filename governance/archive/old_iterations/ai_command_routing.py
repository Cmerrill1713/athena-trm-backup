#!/usr/bin/env python3
"""
AI Command Routing for Athena
============================

Natural language command interface for Athena's AI Republic.
Provides context-aware command execution with policy gates and audit logging.

Features:
- Natural language intent parsing
- Context-aware command validation
- Policy-based authorization
- Comprehensive audit logging
- Multi-modal interfaces (CLI, voice, dashboard)

Usage:
    python3 ai_command_routing.py --parse "quiet for 30 minutes"
    python3 ai_command_routing.py --execute "route critical to phone"
    python3 ai_command_routing.py --audit
    python3 ai_command_routing.py --status
"""

import json
import os
import sys
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class AICommandRouter:
    """Natural language command routing for Athena"""

    def __init__(self):
        self.intents = self.load_intents()
        self.audit_log = self.load_audit_log()
        self.athena_api_url = "http://localhost:8009"
        self.context_cache = {}

    def load_intents(self) -> Dict[str, Dict]:
        """Load intent definitions with slots, auth levels, and handlers"""
        return {
            "status": {
                "patterns": [
                    r"status",
                    r"how are you",
                    r"system status",
                    r"show status",
                    r"health check"
                ],
                "slots": [],
                "auth_level": 1,  # Basic read-only
                "side_effects": ["read"],
                "description": "Get system status overview",
                "handler": self.handle_status
            },

            "quiet": {
                "patterns": [
                    r"quiet(?: for)? (\d+) ?(min|minutes?|hour|hours?)",
                    r"be quiet for (\d+) ?(min|minutes?|hour|hours?)",
                    r"silence for (\d+) ?(min|minutes?|hour|hours?)"
                ],
                "slots": ["duration", "unit"],
                "auth_level": 2,  # Requires approval
                "side_effects": ["alert_suppression"],
                "description": "Temporarily suppress non-critical alerts",
                "handler": self.handle_quiet
            },

            "route": {
                "patterns": [
                    r"route (\w+) (?:alerts? )?to (\w+)",
                    r"send (\w+) (?:alerts? )?to (\w+)",
                    r"(\w+) alerts? to (\w+)"
                ],
                "slots": ["severity", "channel"],
                "auth_level": 2,  # Requires approval
                "side_effects": ["routing_change"],
                "description": "Route alerts of specific severity to target channel",
                "handler": self.handle_route
            },

            "acknowledge": {
                "patterns": [
                    r"ack(?:nowledge)? (?:all|\w+)",
                    r"clear (?:all|\w+)",
                    r"dismiss (?:all|\w+)"
                ],
                "slots": ["target"],
                "auth_level": 2,  # Requires approval
                "side_effects": ["alert_acknowledgment"],
                "description": "Acknowledge/clear alerts",
                "handler": self.handle_acknowledge
            },

            "set_cadence": {
                "patterns": [
                    r"set (\w+) cadence to (\d+) ?(min|minutes?|hour|hours?)",
                    r"change (\w+) to every (\d+) ?(min|minutes?|hour|hours?)",
                    r"(\w+) every (\d+) ?(min|minutes?|hour|hours?)"
                ],
                "slots": ["component", "interval", "unit"],
                "auth_level": 3,  # High-risk configuration
                "side_effects": ["system_configuration"],
                "description": "Change monitoring cadence for system components",
                "handler": self.handle_set_cadence
            },

                "open_dashboard": {
                "patterns": [
                    r"open dashboard",
                    r"show dashboard",
                    r"dashboard",
                    r"view status"
                ],
                "slots": [],
                "auth_level": 1,  # Basic
                "side_effects": ["ui_action"],
                "description": "Open the NeuroForge dashboard",
                "handler": self.handle_open_dashboard
            },

            "meeting_mode": {
                "patterns": [
                    r"meeting mode",
                    r"start meeting",
                    r"meeting prep",
                    r"focus mode",
                    r"deep work mode"
                ],
                "slots": [],
                "auth_level": 2,  # Requires approval
                "side_effects": ["alert_suppression", "routing_change"],
                "description": "Activate meeting mode: quiet alerts + route critical to phone",
                "handler": self.handle_meeting_mode,
                "macro": [
                    {"intent": "quiet", "slots": {"duration": "60", "unit": "minutes"}},
                    {"intent": "route", "slots": {"severity": "critical", "channel": "phone"}}
                ]
            },

            "normal_mode": {
                "patterns": [
                    r"normal mode",
                    r"end meeting",
                    r"resume normal",
                    r"back to normal",
                    r"standard alerts"
                ],
                "slots": [],
                "auth_level": 1,  # Basic
                "side_effects": ["alert_suppression"],
                "description": "Return to normal alert mode",
                "handler": self.handle_normal_mode,
                "macro": [
                    {"intent": "quiet", "slots": {"duration": "0", "unit": "minutes"}},  # Clear quiet mode
                    {"intent": "route", "slots": {"severity": "critical", "channel": "dashboard"}}  # Default routing
                ]
            },

            "emergency_mode": {
                "patterns": [
                    r"emergency mode",
                    r"emergency alerts",
                    r"critical override",
                    r"all alerts to phone"
                ],
                "slots": [],
                "auth_level": 2,  # Requires approval
                "side_effects": ["routing_change"],
                "description": "Emergency mode: route all alerts to phone immediately",
                "handler": self.handle_emergency_mode,
                "macro": [
                    {"intent": "route", "slots": {"severity": "warning", "channel": "phone"}},
                    {"intent": "route", "slots": {"severity": "critical", "channel": "phone"}},
                    {"intent": "quiet", "slots": {"duration": "0", "unit": "minutes"}}  # Ensure no suppression
                ]
            },

            "maintenance_mode": {
                "patterns": [
                    r"maintenance mode",
                    r"system maintenance",
                    r"quiet system",
                    r"silence everything"
                ],
                "slots": [],
                "auth_level": 3,  # High-risk, requires Touch ID
                "side_effects": ["alert_suppression", "system_configuration"],
                "description": "Maintenance mode: suppress all alerts + slow monitoring",
                "handler": self.handle_maintenance_mode,
                "macro": [
                    {"intent": "quiet", "slots": {"duration": "120", "unit": "minutes"}},
                    {"intent": "set_cadence", "slots": {"component": "tribunal", "interval": "60", "unit": "minutes"}},
                    {"intent": "route", "slots": {"severity": "critical", "channel": "phone"}}
                ]
            }
        }

    def load_audit_log(self) -> List[Dict]:
        """Load command audit log"""
        audit_file = os.path.expanduser("~/.athena_behavioral/command_audit.json")
        try:
            if os.path.exists(audit_file):
                with open(audit_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_audit_log(self):
        """Save audit log to disk"""
        audit_file = os.path.expanduser("~/.athena_behavioral/command_audit.json")
        os.makedirs(os.path.dirname(audit_file), exist_ok=True)
        with open(audit_file, 'w') as f:
            json.dump(self.audit_log[-1000:], f, indent=2, default=str)  # Keep last 1000

    def parse_intent(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse natural language command into structured intent"""
        command = command.lower().strip()

        for intent_name, intent_def in self.intents.items():
            for pattern in intent_def["patterns"]:
                match = re.search(pattern, command)
                if match:
                    # Extract slots from regex groups
                    slots = {}
                    if intent_def["slots"]:
                        groups = match.groups()
                        for i, slot_name in enumerate(intent_def["slots"]):
                            if i < len(groups):
                                slots[slot_name] = groups[i]

                    return {
                        "intent": intent_name,
                        "slots": slots,
                        "confidence": 0.9,  # Could be improved with ML
                        "raw_command": command,
                        "definition": intent_def
                    }

        return None

    def validate_context(self, intent: Dict) -> bool:
        """Validate command against current context"""
        # Check if Athena services are running
        if not self.check_athena_services():
            return False

        # Check timing (no commands during critical operations)
        # Check location context if needed
        # Add more context validation as needed

        return True

    def check_authorization(self, intent: Dict) -> bool:
        """Check if command is authorized"""
        auth_level = intent["definition"]["auth_level"]

        if auth_level >= 3:
            # High-risk commands require explicit approval
            return self.request_touch_id_approval(intent)

        # Lower auth levels auto-approve for now
        # Could add role-based access control here
        return True

    def request_touch_id_approval(self, intent: Dict) -> bool:
        """Request Touch ID approval for high-risk commands"""
        try:
            # Use macOS security command for Touch ID
            description = intent["definition"]["description"]
            cmd = f'security authorize -u -P "Athena Command: {description}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)

            return result.returncode == 0

        except:
            # Fallback to console approval
            response = input(f"Authorize command '{intent['raw_command']}'? (y/N): ")
            return response.lower() in ['y', 'yes']

    def execute_command(self, intent: Dict) -> Dict[str, Any]:
        """Execute parsed and validated command"""
        start_time = datetime.now()

        try:
            # Check if this is a macro command
            if "macro" in intent["definition"]:
                return self.execute_macro(intent, start_time)
            else:
                # Execute single command
                result = intent["definition"]["handler"](intent)

            # Log to audit
            audit_entry = {
                "timestamp": start_time.isoformat(),
                "intent": intent["intent"],
                "raw_command": intent["raw_command"],
                "slots": intent["slots"],
                "auth_level": intent["definition"]["auth_level"],
                "outcome": "success" if result.get("success", False) else "failure",
                "result": result,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "is_macro": "macro" in intent["definition"]
            }

            self.audit_log.append(audit_entry)
            self.save_audit_log()

            return result

        except Exception as e:
            # Log failure
            audit_entry = {
                "timestamp": start_time.isoformat(),
                "intent": intent["intent"],
                "raw_command": intent["raw_command"],
                "outcome": "error",
                "error": str(e),
                "is_macro": "macro" in intent.get("definition", {})
            }
            self.audit_log.append(audit_entry)
            self.save_audit_log()

            return {"success": False, "error": str(e)}

    def execute_macro(self, intent: Dict, start_time: datetime) -> Dict[str, Any]:
        """Execute a macro command (multiple sub-commands)"""
        macro_steps = intent["definition"]["macro"]
        results = []

        print(f"🎬 Executing macro: {intent['intent']} ({len(macro_steps)} steps)")

        for i, step in enumerate(macro_steps, 1):
            step_intent = {
                "intent": step["intent"],
                "definition": self.intents[step["intent"]],
                "slots": step.get("slots", {}),
                "raw_command": f"[MACRO] {step['intent']}"
            }

            print(f"  {i}. {step['intent']}")
            result = step_intent["definition"]["handler"](step_intent)
            results.append(result)

            if not result.get("success", False):
                return {
                    "success": False,
                    "error": f"Macro failed at step {i}: {result.get('error', 'Unknown error')}",
                    "completed_steps": i - 1,
                    "total_steps": len(macro_steps)
                }

        return {
            "success": True,
            "message": f"Macro '{intent['intent']}' completed successfully ({len(macro_steps)} steps)",
            "steps_executed": len(macro_steps),
            "results": results
        }

    def route_command(self, command: str) -> Dict[str, Any]:
        """Main command routing pipeline"""
        # 1. Parse intent
        intent = self.parse_intent(command)
        if not intent:
            return {
                "success": False,
                "error": "Command not recognized",
                "suggestion": "Try: status, 'quiet for 30 minutes', 'route critical to phone'"
            }

        # 2. Validate context
        if not self.validate_context(intent):
            return {
                "success": False,
                "error": "Command not allowed in current context"
            }

        # 3. Check authorization
        if not self.check_authorization(intent):
            return {
                "success": False,
                "error": "Command not authorized"
            }

        # 4. Execute
        return self.execute_command(intent)

    # Command Handlers

    def handle_status(self, intent: Dict) -> Dict[str, Any]:
        """Handle status command"""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(f"{self.athena_api_url}/health", timeout=5)
                if response.status_code == 200:
                    health = response.json()
                    return {
                        "success": True,
                        "message": "System healthy",
                        "details": health
                    }

            return {
                "success": True,
                "message": "Status check completed",
                "services": ["API", "Monitor", "Learning"]  # Mock
            }
        except:
            return {"success": False, "error": "Cannot reach Athena services"}

    def handle_quiet(self, intent: Dict) -> Dict[str, Any]:
        """Handle quiet command"""
        duration = intent["slots"].get("duration", "30")
        unit = intent["slots"].get("unit", "minutes")

        # Convert to minutes
        if unit.startswith('h'):
            duration_minutes = int(duration) * 60
        else:
            duration_minutes = int(duration)

        try:
            # Set temporary quiet hours
            if REQUESTS_AVAILABLE:
                # This would integrate with the alerting system
                pass

            return {
                "success": True,
                "message": f"Quiet mode enabled for {duration_minutes} minutes",
                "duration_minutes": duration_minutes
            }
        except:
            return {"success": False, "error": "Cannot enable quiet mode"}

    def handle_route(self, intent: Dict) -> Dict[str, Any]:
        """Handle route command"""
        severity = intent["slots"].get("severity", "critical")
        channel = intent["slots"].get("channel", "phone")

        try:
            # Update routing configuration
            if REQUESTS_AVAILABLE:
                # This would integrate with notification routing
                pass

            return {
                "success": True,
                "message": f"Routing {severity} alerts to {channel}",
                "severity": severity,
                "channel": channel
            }
        except:
            return {"success": False, "error": "Cannot update routing"}

    def handle_acknowledge(self, intent: Dict) -> Dict[str, Any]:
        """Handle acknowledge command"""
        target = intent["slots"].get("target", "all")

        try:
            # Clear alerts
            if REQUESTS_AVAILABLE:
                # This would integrate with alert management
                pass

            return {
                "success": True,
                "message": f"Acknowledged {target} alerts",
                "target": target
            }
        except:
            return {"success": False, "error": "Cannot acknowledge alerts"}

    def handle_set_cadence(self, intent: Dict) -> Dict[str, Any]:
        """Handle set cadence command"""
        component = intent["slots"].get("component", "tribunal")
        interval = intent["slots"].get("interval", "15")
        unit = intent["slots"].get("unit", "minutes")

        # Convert to seconds
        if unit.startswith('h'):
            interval_seconds = int(interval) * 3600
        else:
            interval_seconds = int(interval) * 60

        try:
            # Update component cadence
            # This would integrate with launchd/service management
            return {
                "success": True,
                "message": f"Set {component} cadence to {interval} {unit}",
                "component": component,
                "interval_seconds": interval_seconds
            }
        except:
            return {"success": False, "error": "Cannot update cadence"}

    def handle_open_dashboard(self, intent: Dict) -> Dict[str, Any]:
        """Handle open dashboard command"""
        try:
            # Open NeuroForge app
            subprocess.run(["open", "-a", "NeuroForge"], check=True)
            return {
                "success": True,
                "message": "Opening NeuroForge dashboard"
            }
        except:
            return {"success": False, "error": "Cannot open dashboard"}

    # Macro Command Handlers

    def handle_meeting_mode(self, intent: Dict) -> Dict[str, Any]:
        """Handle meeting mode macro"""
        # This is handled by the macro execution system
        # Individual steps are executed by their respective handlers
        return {
            "success": True,
            "message": "Meeting mode activated: quiet alerts + critical alerts routed to phone"
        }

    def handle_normal_mode(self, intent: Dict) -> Dict[str, Any]:
        """Handle normal mode macro"""
        return {
            "success": True,
            "message": "Returned to normal alert mode"
        }

    def handle_emergency_mode(self, intent: Dict) -> Dict[str, Any]:
        """Handle emergency mode macro"""
        return {
            "success": True,
            "message": "Emergency mode activated: all alerts routed to phone"
        }

    def handle_maintenance_mode(self, intent: Dict) -> Dict[str, Any]:
        """Handle maintenance mode macro"""
        return {
            "success": True,
            "message": "Maintenance mode activated: alerts suppressed + monitoring slowed"
        }

    def check_athena_services(self) -> bool:
        """Check if Athena services are running"""
        if not REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.get(f"{self.athena_api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

def main():
    if len(sys.argv) < 2:
        print("🧠 Athena AI Command Routing")
        print("=" * 35)
        print()
        print("Natural language command interface for Athena.")
        print()
        print("Commands:")
        print("  --parse \"<command>\"     Parse and show intent")
        print("  --execute \"<command>\"   Execute command")
        print("  --audit                  Show audit log")
        print("  --status                 Show routing status")
        print()
        print("Example Commands:")
        print("  \"status\"")
        print("  \"quiet for 30 minutes\"")
        print("  \"route critical to phone\"")
        print("  \"ack all\"")
        print("  \"tribunal every 15 minutes\"")
        print("  \"open dashboard\"")
        print()
        print("Example: python3 ai_command_routing.py --execute \"status\"")

        return

    router = AICommandRouter()
    command = sys.argv[1]

    if command == "--parse":
        if len(sys.argv) < 3:
            print("❌ Please provide a command to parse")
            return

        cmd_text = " ".join(sys.argv[2:])
        intent = router.parse_intent(cmd_text)

        if intent:
            print("✅ Parsed Intent:")
            print(f"  Intent: {intent['intent']}")
            print(f"  Confidence: {intent['confidence']}")
            print(f"  Slots: {intent['slots']}")
            print(f"  Auth Level: {intent['definition']['auth_level']}")
            print(f"  Description: {intent['definition']['description']}")
        else:
            print("❌ Command not recognized")

    elif command == "--execute":
        if len(sys.argv) < 3:
            print("❌ Please provide a command to execute")
            return

        cmd_text = " ".join(sys.argv[2:])
        result = router.route_command(cmd_text)

        if result.get("success"):
            print(f"✅ {result.get('message', 'Command executed')}")
        else:
            print(f"❌ {result.get('error', 'Command failed')}")

    elif command == "--audit":
        audit_log = router.audit_log[-10:]  # Last 10 entries

        print("📋 Command Audit Log (Last 10)")
        print("=" * 35)

        if not audit_log:
            print("No commands executed yet")
            return

        for entry in audit_log:
            ts = entry['timestamp'][:19]  # YYYY-MM-DDTHH:MM:SS
            intent = entry['intent']
            outcome = entry['outcome']
            print(f"{ts} | {intent} | {outcome}")

    elif command == "--status":
        services_ok = router.check_athena_services()

        print("🔄 Command Routing Status")
        print("=" * 30)
        print(f"Athena Services: {'✅ Running' if services_ok else '❌ Not Available'}")
        print(f"Intents Loaded: {len(router.intents)}")
        print(f"Audit Entries: {len(router.audit_log)}")
        print(f"Context Cache: {len(router.context_cache)} items")

        print("\n📋 Available Commands:")
        for name, intent in router.intents.items():
            auth_icon = "🔒" if intent['auth_level'] >= 3 else "✅" if intent['auth_level'] >= 2 else "🆓"
            print(f"  {auth_icon} {name}: {intent['description']}")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
