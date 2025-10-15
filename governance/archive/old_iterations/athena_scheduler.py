#!/usr/bin/env python3
"""
Athena Daily Briefing Scheduler
==============================

Automated conversational daily briefings for AI Republic operations.
Runs scheduled health checks and delivers natural language status reports.

Features:
- Scheduled daily briefings (configurable time)
- Automated CLI health checks
- Natural language status summaries
- Proactive issue detection and recommendations
- Integration with existing CLI dashboard

Usage:
    python3 athena_scheduler.py --start    # Start scheduled briefings
    python3 athena_scheduler.py --briefing # Run immediate briefing
    python3 athena_scheduler.py --status   # Check scheduler status
"""

import schedule
import time
import os
from datetime import datetime, timedelta
from typing import Dict
import subprocess
import argparse
import sys

# Add paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

from ai_republic_cli import AIRepublicDashboard, Colors
from athena_notifications import AthenaNotifications

class AthenaBriefingSystem:
    """Conversational daily briefing system for AI Republic operations"""

    def __init__(self, briefing_time: str = "09:00"):
        self.briefing_time = briefing_time
        self.dashboard = AIRepublicDashboard()
        self.notifications = AthenaNotifications()
        self.last_briefing = None
        self.scheduler_running = False
        self.briefing_thread = None

        # Briefing configuration
        self.personality = "professional"  # Options: professional, casual, detailed
        self.include_recommendations = True
        self.alert_on_issues = True

        # Logging
        log_dir = '/var/log/ai-republic' if os.path.exists('/var/log/ai-republic') else './logs'
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, 'athena_briefings.log')

    def log_briefing(self, message: str):
        """Log briefing activity"""
        timestamp = datetime.now().isoformat()
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} - {message}\n")

    def run_health_check(self) -> Dict:
        """Run comprehensive health check via CLI dashboard"""
        try:
            # Run the CLI check command
            result = subprocess.run(
                [sys.executable, 'ai_republic_cli.py', '--mode', 'check'],
                capture_output=True, text=True, timeout=30
            )

            # Parse the output (simplified - in reality would parse JSON)
            status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'UNKNOWN',
                'services': {},
                'alerts': [],
                'metrics': {},
                'activity': [],
                'raw_output': result.stdout,
                'errors': result.stderr
            }

            # Try to parse actual status from CLI
            try:
                # This would be more sophisticated in production
                if 'HEALTHY' in result.stdout:
                    status['overall_status'] = 'HEALTHY'
                elif 'WARNING' in result.stdout:
                    status['overall_status'] = 'WARNING'
                elif 'CRITICAL' in result.stdout:
                    status['overall_status'] = 'CRITICAL'

                # Extract service status
                if 'constitutional:' in result.stdout:
                    status['services']['constitutional'] = {'status': 'running' if 'ACTIVE' in result.stdout else 'stopped'}
                if 'judicial:' in result.stdout:
                    status['services']['judicial'] = {'status': 'running' if 'ACTIVE' in result.stdout else 'stopped'}

            except Exception as e:
                self.log_briefing(f"Error parsing CLI output: {e}")

            return status

        except subprocess.TimeoutExpired:
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'ERROR',
                'error': 'Health check timed out'
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'ERROR',
                'error': str(e)
            }

    def generate_conversational_briefing(self, status: Dict) -> str:
        """Generate natural language briefing from status data"""

        # Determine greeting based on time
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good morning"
        elif current_hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        # Get user name (could be from config)
        user_name = os.getenv('USER', 'Christian')

        # Start building briefing
        briefing_parts = [
            f"🤖 {greeting}, {user_name}! Here's your AI Republic status briefing:",
            ""
        ]

        # Overall status with personality
        overall = status.get('overall_status', 'UNKNOWN')

        if overall == 'HEALTHY':
            if self.personality == 'casual':
                briefing_parts.append("✅ **All systems green** - Everything's running smoothly!")
            else:
                briefing_parts.append("✅ **Overall Status: HEALTHY** - All systems operating normally")

        elif overall == 'WARNING':
            briefing_parts.append("⚠️ **Overall Status: WARNING** - Minor issues detected, monitoring closely")

        elif overall == 'CRITICAL':
            briefing_parts.append("🚨 **Overall Status: CRITICAL** - Immediate attention required")

        else:
            briefing_parts.append("❓ **Status: UNCLEAR** - Unable to determine system health")

        briefing_parts.append("")

        # Services section
        services = status.get('services', {})
        if services:
            briefing_parts.append("🔧 **Services:**")

            for name, info in services.items():
                status_icon = "✅" if info.get('status') == 'running' else "❌"
                display_name = name.capitalize()
                briefing_parts.append(f"   {status_icon} {display_name}: {info.get('status', 'unknown')}")

            briefing_parts.append("")

        # Metrics section
        metrics = status.get('metrics', {})
        if metrics:
            briefing_parts.append("📊 **Key Metrics:**")

            if 'compliance_rate' in metrics and metrics['compliance_rate']:
                rate = metrics['compliance_rate'] * 100
                color_icon = "🟢" if rate > 99.5 else "🟡" if rate > 99 else "🔴"
                briefing_parts.append(f"   {color_icon} Compliance Rate: {rate:.1f}%")

            if 'tribunals_today' in metrics:
                tribunals = metrics['tribunals_today']
                if tribunals == 0:
                    briefing_parts.append(f"   ✅ Tribunals Today: {tribunals} (clean day!)")
                else:
                    briefing_parts.append(f"   ⚖️ Tribunals Today: {tribunals}")

            if 'system_uptime' in metrics:
                briefing_parts.append(f"   ⏱️ System Uptime: {metrics['system_uptime']}")

            briefing_parts.append("")

        # Alerts section
        alerts = status.get('alerts', [])
        if alerts:
            briefing_parts.append("🚨 **Active Alerts:**")
            for alert in alerts[:3]:  # Show up to 3 alerts
                severity = alert.get('severity', 'UNKNOWN')
                emoji = "🔴" if severity == 'CRITICAL' else "🟡" if severity == 'HIGH' else "🟢"
                briefing_parts.append(f"   {emoji} {alert.get('timestamp', 'Unknown')}: {alert.get('message', 'No details')[:60]}...")

            if len(alerts) > 3:
                briefing_parts.append(f"   ...and {len(alerts) - 3} more alerts")

            briefing_parts.append("")
            briefing_parts.append("💡 **Action Required:** Run tribunal response mode for these alerts")

        else:
            if overall == 'HEALTHY':
                briefing_parts.append("✅ **No active alerts** - Everything under control!")

        # Recent activity (if available)
        activity = status.get('activity', [])
        if activity and len(activity) > 0:
            briefing_parts.append("")
            briefing_parts.append("📋 **Recent Activity:**")
            for line in activity[-2:]:  # Show last 2 activities
                if line.strip():
                    briefing_parts.append(f"   • {line}")

        # Recommendations
        if self.include_recommendations:
            briefing_parts.append("")
            briefing_parts.append("🎯 **Recommendations:**")

            if overall == 'HEALTHY' and not alerts:
                briefing_parts.append("   • No action needed - have a great day!")
            elif alerts:
                briefing_parts.append("   • Address alerts promptly")
                briefing_parts.append("   • Review tribunal cases in detail")
            elif overall == 'WARNING':
                briefing_parts.append("   • Monitor service stability")
                briefing_parts.append("   • Check logs for emerging issues")

            # Weekly tasks reminder
            if datetime.now().weekday() == 0:  # Monday
                briefing_parts.append("   • Weekly: Review reputation trends and quarantine backlog")

        # Sign off
        briefing_parts.append("")
        briefing_parts.append("🤖 Athena - Your AI Republic Operations Partner")
        briefing_parts.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(briefing_parts)

    def deliver_briefing(self, briefing_text: str):
        """Deliver briefing to user (console, file, notification, etc.)"""

        # Print to console with formatting
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}🤖 ATHENA DAILY BRIEFING{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

        print(briefing_text)

        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")

        # Log the briefing
        self.log_briefing("BRIEFING DELIVERED")

        # Save to daily briefing file
        log_dir = '/var/log/ai-republic' if os.path.exists('/var/log/ai-republic') else './logs'
        os.makedirs(log_dir, exist_ok=True)

        date_str = datetime.now().strftime('%Y%m%d')
        briefing_file = os.path.join(log_dir, f'daily_briefing_{date_str}.md')

        with open(briefing_file, 'w') as f:
            f.write(briefing_text)

        print(f"\n{Colors.GREEN}Briefing saved to: {briefing_file}{Colors.END}")

        # Send briefing via configured notification channels
        try:
            self.notifications.send_daily_briefing(briefing_text)
            print(f"{Colors.GREEN}📧 Briefing sent via configured notification channels{Colors.END}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Could not send notification: {e}{Colors.END}")
            self.log_briefing(f"NOTIFICATION FAILED: {e}")

    def run_daily_briefing(self):
        """Run the complete daily briefing process"""
        try:
            self.log_briefing("STARTING DAILY BRIEFING")

            # Run health check
            print(f"{Colors.BLUE}🤖 Athena: Running health check...{Colors.END}")
            status = self.run_health_check()

            # Generate conversational briefing
            print(f"{Colors.BLUE}🤖 Athena: Analyzing results...{Colors.END}")
            briefing = self.generate_conversational_briefing(status)

            # Deliver briefing
            self.deliver_briefing(briefing)

            # Update last briefing time
            self.last_briefing = datetime.now()

            self.log_briefing("DAILY BRIEFING COMPLETED")

        except Exception as e:
            error_msg = f"BRIEFING ERROR: {e}"
            print(f"{Colors.RED}❌ {error_msg}{Colors.END}")
            self.log_briefing(error_msg)

    def start_scheduler(self):
        """Start the daily briefing scheduler"""
        def scheduled_briefing():
            print(f"\n{Colors.BLUE}🤖 Scheduled briefing time reached{Colors.END}")
            self.run_daily_briefing()

        # Schedule daily briefing
        schedule.every().day.at(self.briefing_time).do(scheduled_briefing)

        print(f"{Colors.GREEN}✅ Daily briefing scheduler started{Colors.END}")
        print(f"Briefings scheduled for: {self.briefing_time} daily")
        print(f"{Colors.BLUE}Press Ctrl+C to stop...{Colors.END}")

        self.scheduler_running = True

        try:
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print(f"\n{Colors.BLUE}🤖 Scheduler stopped by user{Colors.END}")
            self.scheduler_running = False

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        print(f"{Colors.BLUE}🤖 Scheduler stopping...{Colors.END}")

def main():
    parser = argparse.ArgumentParser(description='Athena Daily Briefing Scheduler')
    parser.add_argument('--start', action='store_true', help='Start scheduled daily briefings')
    parser.add_argument('--briefing', action='store_true', help='Run immediate briefing')
    parser.add_argument('--status', action='store_true', help='Check scheduler status')
    parser.add_argument('--time', default='09:00', help='Briefing time (HH:MM)')

    args = parser.parse_args()

    scheduler = AthenaBriefingSystem(briefing_time=args.time)

    if args.start:
        # Start scheduled briefings
        try:
            scheduler.start_scheduler()
        except KeyboardInterrupt:
            scheduler.stop_scheduler()

    elif args.briefing:
        # Run immediate briefing
        print(f"{Colors.BLUE}🤖 Athena: Running immediate briefing...{Colors.END}")
        scheduler.run_daily_briefing()

    elif args.status:
        # Check status
        print(f"{Colors.BLUE}🤖 Athena Briefing System Status:{Colors.END}")
        print(f"  Scheduled Time: {args.time}")
        print(f"  Last Briefing: {scheduler.last_briefing or 'Never'}")
        print(f"  Scheduler Running: {scheduler.scheduler_running}")

        # Check upcoming briefing
        now = datetime.now()
        briefing_hour, briefing_minute = map(int, args.time.split(':'))
        briefing_time = now.replace(hour=briefing_hour, minute=briefing_minute, second=0, microsecond=0)

        if briefing_time < now:
            briefing_time += timedelta(days=1)

        time_until = briefing_time - now
        hours, remainder = divmod(time_until.seconds, 3600)
        minutes = remainder // 60

        print(f"  Next Briefing: {briefing_time.strftime('%Y-%m-%d %H:%M')} (in {hours}h {minutes}m)")

    else:
        # Interactive mode
        print(f"{Colors.BOLD}{Colors.BLUE}🤖 Athena Daily Briefing System{Colors.END}")
        print("Commands:")
        print("  --start          Start scheduled daily briefings")
        print("  --briefing       Run immediate briefing")
        print("  --status         Check system status")
        print("  --time HH:MM     Set briefing time (default: 09:00)")

        print(f"\n{Colors.GREEN}Example: python3 athena_scheduler.py --start{Colors.END}")

if __name__ == '__main__':
    main()
