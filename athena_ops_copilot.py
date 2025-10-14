#!/usr/bin/env python3
"""
ATHENA OPS CO-PILOT
Conversational AI Assistant for AI Republic Operations

Provides natural language interface to constitutional AI governance system.
Handles automated monitoring, status briefings, and routine operations.
"""

import json
import time
import datetime
import schedule
import threading
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# Import AI Republic CLI components
try:
    from ai_republic_cli import AIRepublicDashboard, Colors
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False

class OpsPriority(Enum):
    """Operational priority levels"""
    ROUTINE = "routine"
    ATTENTION = "attention"
    URGENT = "urgent"
    CRITICAL = "critical"

@dataclass
class OpsBriefing:
    """Structured operational briefing"""
    timestamp: datetime.datetime
    priority: OpsPriority
    summary: str
    details: Dict[str, Any]
    recommendations: List[str]
    requires_action: bool

class AthenaOpsCopilot:
    """Athena's operational co-pilot for AI Republic governance"""

    def __init__(self):
        self.dashboard = AIRepublicDashboard() if CLI_AVAILABLE else None
        self.last_briefing = None
        self.briefing_history = []
        self.monitoring_active = False
        self.scheduled_briefings = []

        # Load personality and response templates
        self.personality = {
            "greeting": "Good {time_of_day}, {user}. Here's your AI Republic status briefing:",
            "healthy_summary": "Everything's running smoothly. {metrics_summary}",
            "warning_summary": "Minor attention needed. {metrics_summary}",
            "critical_summary": "Immediate action required. {metrics_summary}",
            "tribunal_alert": "Tribunal alert active for {actor}. Severity {severity}. {recommendation}",
            "no_action_needed": "No action needed from you right now.",
            "recommend_approval": "I recommend upholding the tribunal decision.",
            "request_confirmation": "Would you like me to {action}?",
            "confirmation_received": "Confirmed. {action} executed.",
            "status_request": "Current status: {status_summary}"
        }

    def get_time_of_day(self) -> str:
        """Get appropriate time-of-day greeting"""
        hour = datetime.datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"

    def get_user_name(self) -> str:
        """Get user name from environment or default"""
        return "Christian"  # Could be made configurable

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check using CLI dashboard"""
        if not self.dashboard:
            return {"error": "AI Republic CLI not available"}

        try:
            status = self.dashboard.perform_health_check()
            self.last_check = status
            return status
        except Exception as e:
            return {"error": f"Health check failed: {e}"}

    def analyze_status(self, status: Dict[str, Any]) -> OpsBriefing:
        """Analyze system status and generate operational briefing"""

        timestamp = datetime.datetime.now()
        alerts = status.get('alerts', [])
        metrics = status.get('metrics', {})
        services = status.get('services', {})

        # Determine priority
        if status.get('overall_status') == 'CRITICAL' or len(alerts) > 0:
            priority = OpsPriority.CRITICAL
        elif status.get('overall_status') == 'WARNING':
            priority = OpsPriority.ATTENTION
        else:
            priority = OpsPriority.ROUTINE

        # Generate summary
        summary = self._generate_summary(status, alerts, metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(status, alerts)

        # Determine if action required
        requires_action = priority in [OpsPriority.URGENT, OpsPriority.CRITICAL] or len(alerts) > 0

        briefing = OpsBriefing(
            timestamp=timestamp,
            priority=priority,
            summary=summary,
            details={
                'status': status,
                'alerts': alerts,
                'metrics': metrics,
                'services': services
            },
            recommendations=recommendations,
            requires_action=requires_action
        )

        self.briefing_history.append(briefing)
        self.last_briefing = briefing

        return briefing

    def _generate_summary(self, status: Dict, alerts: List, metrics: Dict) -> str:
        """Generate natural language summary of system status"""

        overall = status.get('overall_status', 'UNKNOWN')
        compliance = metrics.get('compliance_rate', 0) * 100
        tribunals_today = metrics.get('tribunals_today', 0)

        if overall == 'HEALTHY':
            metrics_text = f"Compliance at {compliance:.1f}%, {tribunals_today} tribunals today."
            return f"Everything's running smoothly. {metrics_text}"

        elif overall == 'WARNING':
            metrics_text = f"Compliance at {compliance:.1f}%, {tribunals_today} tribunals today."
            return f"Minor attention needed. {metrics_text}"

        elif overall == 'CRITICAL':
            return f"Immediate action required. System status: {overall}"

        else:
            return f"Status check completed. System status: {overall}"

    def _generate_recommendations(self, status: Dict, alerts: List) -> List[str]:
        """Generate operational recommendations"""

        recommendations = []

        if not alerts:
            recommendations.append("Continue normal operations")
        else:
            for alert in alerts:
                severity = alert.get('severity', 'UNKNOWN')
                if severity == 'HIGH':
                    recommendations.append("Review tribunal alert immediately")
                elif severity == 'CRITICAL':
                    recommendations.append("Escalate to oversight council")
                else:
                    recommendations.append("Monitor tribunal situation")

        if status.get('overall_status') == 'WARNING':
            recommendations.append("Schedule detailed performance review")

        return recommendations

    def generate_briefing_message(self, briefing: OpsBriefing) -> str:
        """Generate natural language briefing message"""

        user_name = self.get_user_name()
        time_of_day = self.get_time_of_day()

        greeting = self.personality["greeting"].format(
            time_of_day=time_of_day,
            user=user_name
        )

        message_parts = [greeting, briefing.summary]

        # Add tribunal alerts if any
        alerts = briefing.details.get('alerts', [])
        if alerts:
            tribunal_messages = []
            for alert in alerts:
                actor = alert.get('message', '').split()[-1] if 'agent' in alert.get('message', '') else 'system'
                severity = alert.get('severity', 'UNKNOWN')
                recommendation = self.personality["recommend_approval"]
                tribunal_msg = self.personality["tribunal_alert"].format(
                    actor=actor,
                    severity=severity.lower(),
                    recommendation=recommendation
                )
                tribunal_messages.append(tribunal_msg)

            message_parts.extend(tribunal_messages)

        # Add recommendations
        if briefing.recommendations:
            message_parts.extend(briefing.recommendations)

        # Add action prompt if needed
        if briefing.requires_action:
            message_parts.append("Would you like me to handle any of these items?")
        else:
            message_parts.append(self.personality["no_action_needed"])

        return " ".join(message_parts)

    def schedule_daily_briefing(self, time_str: str = "09:00"):
        """Schedule daily automated briefing"""

        def daily_briefing():
            status = self.perform_health_check()
            if 'error' not in status:
                briefing = self.analyze_status(status)
                message = self.generate_briefing_message(briefing)
                self._deliver_briefing(message, briefing)

        schedule.every().day.at(time_str).do(daily_briefing)
        self.scheduled_briefings.append(f"Daily briefing at {time_str}")

        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()

    def schedule_startup_briefing(self):
        """Schedule briefing on system startup"""

        def startup_briefing():
            time.sleep(30)  # Wait for system to stabilize
            status = self.perform_health_check()
            if 'error' not in status:
                briefing = self.analyze_status(status)
                message = self.generate_briefing_message(briefing)
                self._deliver_briefing(message, briefing, startup=True)

        startup_briefing()  # Run immediately
        self.scheduled_briefings.append("Startup briefing (immediate)")

    def _run_scheduler(self):
        """Run the schedule loop"""
        self.monitoring_active = True
        while self.monitoring_active:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _deliver_briefing(self, message: str, briefing: OpsBriefing, startup: bool = False):
        """Deliver briefing to user (could be console, notification, etc.)"""

        # For now, print to console (could be integrated with messaging platforms)
        print(f"\n🤖 ATHENA OPS BRIEFING {'(STARTUP)' if startup else '(SCHEDULED)'}")
        print("=" * 60)
        print(message)
        print(f"Priority: {briefing.priority.value.upper()}")
        print(f"Timestamp: {briefing.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Log briefing
        self._log_briefing(briefing, message)

    def _log_briefing(self, briefing: OpsBriefing, message: str):
        """Log briefing for audit trail"""
        log_entry = {
            'timestamp': briefing.timestamp.isoformat(),
            'priority': briefing.priority.value,
            'message': message,
            'details': briefing.details,
            'recommendations': briefing.recommendations,
            'action_required': briefing.requires_action
        }

        # Could write to file or database
        log_file = f"/var/log/ai-republic/athena_briefings_{datetime.date.today()}.jsonl"
        try:
            with open(log_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
        except Exception as e:
            print(f"Warning: Could not log briefing: {e}")

    # Command execution methods (for Stage 3)
    def execute_command(self, command: str) -> str:
        """Execute natural language commands"""

        command = command.lower().strip()

        # Parse commands
        if self._matches_command(command, ['check status', 'health check', 'system status']):
            status = self.perform_health_check()
            if 'error' in status:
                return f"Health check failed: {status['error']}"
            briefing = self.analyze_status(status)
            return self.generate_briefing_message(briefing)

        elif self._matches_command(command, ['show logs', 'view logs', 'check logs']):
            if self.dashboard:
                activity = self.dashboard.check_recent_activity()
                return f"Recent activity ({len(activity)} entries):\n" + "\n".join(activity[-5:])
            return "Log access not available"

        elif self._matches_command(command, ['restart services', 'restart all']):
            if self.dashboard:
                # This would need sudo access in real implementation
                return "Service restart initiated (would require sudo in production)"
            return "Service restart not available"

        elif self._matches_command(command, ['clear tribunals', 'approve tribunals']):
            return "Tribunal management requires interactive confirmation for security"

        elif self._matches_command(command, ['show metrics', 'performance metrics']):
            status = self.perform_health_check()
            metrics = status.get('metrics', {})
            return f"Current metrics: Compliance {metrics.get('compliance_rate', 0)*100:.1f}%, " \
                   f"Tribunals today: {metrics.get('tribunals_today', 0)}, " \
                   f"Uptime: {metrics.get('system_uptime', 'Unknown')}"

        else:
            return "Command not recognized. Try: 'check status', 'show logs', 'show metrics'"

    def _matches_command(self, input_text: str, command_patterns: List[str]) -> bool:
        """Check if input matches any command pattern"""
        for pattern in command_patterns:
            if pattern in input_text:
                return True
        return False

    # Interactive conversation mode (for Stage 3)
    def start_conversation(self):
        """Start interactive conversation mode"""
        print("🤖 Athena Ops Co-Pilot activated. Type 'quit' to exit.")

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 Farewell. AI Republic operations continuing autonomously.")
                    break

                elif user_input.lower() in ['help', '?']:
                    print("🤖 Available commands:")
                    print("  - check status / health check")
                    print("  - show logs / view logs")
                    print("  - show metrics / performance metrics")
                    print("  - restart services (requires confirmation)")
                    print("  - quit / exit")

                else:
                    response = self.execute_command(user_input)
                    print(f"🤖 {response}")

            except KeyboardInterrupt:
                print("\n🤖 Conversation ended.")
                break
            except Exception as e:
                print(f"🤖 Error processing command: {e}")

def main():
    """Main entry point for Athena Ops Co-Pilot"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Ops Co-Pilot for AI Republic')
    parser.add_argument('--mode', choices=['briefing', 'conversation', 'schedule', 'startup'],
                       default='briefing', help='Operation mode')
    parser.add_argument('--time', default='09:00', help='Scheduled briefing time (HH:MM)')
    parser.add_argument('--interactive', action='store_true', help='Start interactive conversation')

    args = parser.parse_args()

    copilot = AthenaOpsCopilot()

    if args.mode == 'briefing' or args.interactive:
        # Single briefing
        status = copilot.perform_health_check()
        if 'error' in status:
            print(f"❌ Health check failed: {status['error']}")
        else:
            briefing = copilot.analyze_status(status)
            message = copilot.generate_briefing_message(briefing)
            copilot._deliver_briefing(message, briefing)

    elif args.mode == 'conversation':
        # Interactive mode
        copilot.start_conversation()

    elif args.mode == 'schedule':
        # Scheduled mode
        print(f"🤖 Scheduling daily briefings at {args.time}")
        copilot.schedule_daily_briefing(args.time)
        print("Briefings scheduled. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🤖 Scheduling stopped.")

    elif args.mode == 'startup':
        # Startup mode
        copilot.schedule_startup_briefing()
        print("🤖 Startup briefing delivered.")

if __name__ == '__main__':
    main()
