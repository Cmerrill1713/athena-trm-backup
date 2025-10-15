#!/usr/bin/env python3
"""
AI REPUBLIC OPERATIONS DASHBOARD
CLI Tool for Daily Operations and Tribunal Management

This interactive dashboard provides:
- Automated daily health checks
- Real-time system monitoring
- Tribunal alert management
- Emergency response tools
- System status overview
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# Add system paths
sys.path.insert(0, '/opt/ai-republic')

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class AIRepublicDashboard:
    """Main dashboard class for AI Republic operations"""

    def __init__(self):
        self.last_check = None
        self.system_status = {}
        self.tribunal_alerts = []
        self.check_interval = 300  # 5 minutes

    def run_command(self, cmd: str, timeout: int = 10) -> Tuple[str, str, int]:
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", f"Error: {e}", -1

    def check_service_status(self) -> Dict[str, Dict]:
        """Check status of all AI Republic services"""
        services = {
            'constitutional': 'ai-republic-constitutional',
            'judicial': 'ai-republic-judicial',
            'federation': 'ai-republic-fop'
        }

        status = {}
        for name, service in services.items():
            stdout, stderr, code = self.run_command(f'systemctl status {service} --no-pager -l')

            if 'Active: active (running)' in stdout:
                status[name] = {'status': 'running', 'details': 'Operational'}
            elif 'Active: inactive' in stdout or 'could not be found' in stdout:
                status[name] = {'status': 'stopped', 'details': 'Service not running'}
            elif 'Active: failed' in stdout:
                status[name] = {'status': 'failed', 'details': 'Service failed'}
            else:
                status[name] = {'status': 'unknown', 'details': 'Unable to determine'}

        return status

    def check_recent_activity(self) -> List[str]:
        """Get recent constitutional activity"""
        stdout, stderr, code = self.run_command('tail -10 /var/log/ai-republic/constitutional_audit.log')
        if code == 0:
            return stdout.split('\n') if stdout else []
        return []

    def check_tribunal_alerts(self) -> List[Dict]:
        """Check for active tribunal alerts"""
        stdout, stderr, code = self.run_command('grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log | tail -5')
        alerts = []

        if code == 0 and stdout:
            for line in stdout.split('\n'):
                if line.strip():
                    alerts.append({
                        'timestamp': line.split(' - ')[0] if ' - ' in line else 'Unknown',
                        'message': line,
                        'severity': 'CRITICAL' if 'EMERGENCY' in line else 'HIGH'
                    })

        return alerts

    def get_system_metrics(self) -> Dict:
        """Get key system performance metrics"""
        metrics = {}

        # Compliance rate
        stdout, stderr, code = self.run_command(
            'grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -20 | '
            'awk \'{sum+=$NF; count++} END {if(count>0) print sum/count; else print "N/A"}\''
        )
        metrics['compliance_rate'] = float(stdout) if stdout and stdout != 'N/A' else None

        # Tribunal count (last 24h)
        stdout, stderr, code = self.run_command(
            'grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | grep "$(date +%Y-%m-%d)" | wc -l'
        )
        metrics['tribunals_today'] = int(stdout) if stdout else 0

        # System uptime
        stdout, stderr, code = self.run_command('uptime -p')
        metrics['system_uptime'] = stdout if stdout else 'Unknown'

        return metrics

    def perform_health_check(self) -> Dict:
        """Perform complete health check"""
        self.last_check = datetime.now()

        result = {
            'timestamp': self.last_check.isoformat(),
            'services': self.check_service_status(),
            'activity': self.check_recent_activity(),
            'alerts': self.check_tribunal_alerts(),
            'metrics': self.get_system_metrics(),
            'overall_status': 'UNKNOWN'
        }

        # Determine overall status
        services_running = sum(1 for s in result['services'].values() if s['status'] == 'running')
        total_services = len(result['services'])

        if services_running == total_services and len(result['alerts']) == 0:
            result['overall_status'] = 'HEALTHY'
        elif services_running >= total_services - 1 and len(result['alerts']) <= 1:
            result['overall_status'] = 'WARNING'
        else:
            result['overall_status'] = 'CRITICAL'

        self.system_status = result
        return result

    def display_status(self, status: Dict):
        """Display system status with colors"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🤖 AI REPUBLIC STATUS DASHBOARD{Colors.END}")
        print(f"{Colors.BLUE}{'='*50}{Colors.END}")

        # Overall status
        overall = status['overall_status']
        if overall == 'HEALTHY':
            color = Colors.GREEN
        elif overall == 'WARNING':
            color = Colors.YELLOW
        else:
            color = Colors.RED

        print(f"Overall Status: {color}{Colors.BOLD}{overall}{Colors.END}")
        print(f"Last Check: {status['timestamp'][:19]}")

        # Services
        print(f"\n{Colors.BOLD}Services:{Colors.END}")
        for name, info in status['services'].items():
            status_color = Colors.GREEN if info['status'] == 'running' else Colors.RED
            print(f"  {name.capitalize()}: {status_color}{info['status']}{Colors.END} - {info['details']}")

        # Metrics
        metrics = status.get('metrics', {})
        if metrics:
            print(f"\n{Colors.BOLD}Key Metrics:{Colors.END}")
            if metrics.get('compliance_rate'):
                rate = metrics['compliance_rate'] * 100
                color = Colors.GREEN if rate > 99.5 else Colors.YELLOW if rate > 99 else Colors.RED
                print(f"  Compliance Rate: {color}{rate:.1f}%{Colors.END}")
            if metrics.get('tribunals_today') is not None:
                tribunals = metrics['tribunals_today']
                color = Colors.GREEN if tribunals == 0 else Colors.YELLOW if tribunals <= 2 else Colors.RED
                print(f"  Tribunals Today: {color}{tribunals}{Colors.END}")
            if metrics.get('system_uptime'):
                print(f"  System Uptime: {Colors.BLUE}{metrics['system_uptime']}{Colors.END}")

        # Alerts
        alerts = status.get('alerts', [])
        if alerts:
            print(f"\n{Colors.BOLD}{Colors.RED}🚨 TRIBUNAL ALERTS:{Colors.END}")
            for alert in alerts:
                print(f"  {Colors.RED}{alert['timestamp']}: {alert['message']}{Colors.END}")
        else:
            print(f"\n{Colors.GREEN}✅ No tribunal alerts{Colors.END}")

        # Recent activity
        activity = status.get('activity', [])
        if activity:
            print(f"\n{Colors.BOLD}Recent Activity:{Colors.END}")
            for line in activity[-3:]:  # Show last 3 entries
                if line.strip():
                    print(f"  {Colors.BLUE}{line}{Colors.END}")

    def handle_tribunal_response(self):
        """Interactive tribunal alert response"""
        if not self.tribunal_alerts:
            print(f"{Colors.GREEN}No tribunal alerts to handle.{Colors.END}")
            return

        print(f"\n{Colors.BOLD}{Colors.RED}🚨 TRIBUNAL RESPONSE REQUIRED{Colors.END}")
        print("Choose response for each alert:")

        for i, alert in enumerate(self.tribunal_alerts, 1):
            print(f"\n{Colors.YELLOW}Alert {i}:{Colors.END}")
            print(f"  Time: {alert['timestamp']}")
            print(f"  Message: {alert['message']}")

            while True:
                print("\nResponse options:")
                print("  1. APPROVE - Allow system to handle automatically")
                print("  2. OVERRIDE - Override with human decision")
                print("  3. ESCALATE - Send to oversight council")
                print("  4. SKIP - Handle later")

                choice = input("Choose (1-4): ").strip()

                if choice == '1':
                    print(f"{Colors.GREEN}✅ Approved automatic handling{Colors.END}")
                    # Log approval
                    with open('/var/log/ai-republic/human_interventions.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - APPROVED: {alert['message'][:100]}...\n")
                    break
                elif choice == '2':
                    reason = input("Override reason: ").strip()
                    print(f"{Colors.YELLOW}⚠️ Override logged: {reason}{Colors.END}")
                    with open('/var/log/ai-republic/human_interventions.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - OVERRIDE: {reason} - {alert['message'][:100]}...\n")
                    break
                elif choice == '3':
                    print(f"{Colors.RED}🚨 Escalated to oversight council{Colors.END}")
                    with open('/var/log/ai-republic/human_interventions.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - ESCALATED: {alert['message'][:100]}...\n")
                    break
                elif choice == '4':
                    print(f"{Colors.BLUE}⏭️ Skipped for now{Colors.END}")
                    break
                else:
                    print("Invalid choice. Please enter 1-4.")

    def run_interactive_mode(self):
        """Run interactive dashboard mode"""
        try:
            while True:
                os.system('clear')
                status = self.perform_health_check()
                self.display_status(status)

                # Check for tribunal alerts
                self.tribunal_alerts = status.get('alerts', [])
                if self.tribunal_alerts:
                    print(f"\n{Colors.BOLD}{Colors.RED}⚠️ Tribunal alerts detected!{Colors.END}")

                print(f"\n{Colors.BOLD}Commands:{Colors.END}")
                print("  [c]heck - Run health check")
                print("  [t]ribunal - Handle tribunal alerts")
                print("  [l]ogs - View detailed logs")
                print("  [r]estart - Restart services")
                print("  [q]uit - Exit dashboard")

                try:
                    cmd = input(f"\n{Colors.BLUE}Command>{Colors.END} ").strip().lower()

                    if cmd == 'q' or cmd == 'quit':
                        break
                    elif cmd == 'c' or cmd == 'check':
                        continue  # Already did check above
                    elif cmd == 't' or cmd == 'tribunal':
                        self.handle_tribunal_response()
                        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")
                    elif cmd == 'l' or cmd == 'logs':
                        os.system('tail -20 /var/log/ai-republic/constitutional_audit.log')
                        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")
                    elif cmd == 'r' or cmd == 'restart':
                        print("Restarting all services...")
                        os.system('sudo systemctl restart ai-republic-constitutional ai-republic-judicial ai-republic-fop 2>/dev/null')
                        time.sleep(3)
                        print("Services restarted.")
                        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")
                    else:
                        print(f"{Colors.YELLOW}Unknown command. Type 'q' to quit.{Colors.END}")
                        time.sleep(1)

                except KeyboardInterrupt:
                    break

        except Exception as e:
            print(f"{Colors.RED}Error in interactive mode: {e}{Colors.END}")

    def run_auto_mode(self, interval: int = 300):
        """Run automated monitoring mode"""
        print(f"{Colors.BLUE}🤖 AI Republic Auto-Monitor Mode{Colors.END}")
        print(f"Checking every {interval} seconds... (Ctrl+C to stop)")

        try:
            while True:
                status = self.perform_health_check()

                # Display status
                timestamp = status['timestamp'][:19]
                overall = status['overall_status']

                if overall == 'HEALTHY':
                    color = Colors.GREEN
                elif overall == 'WARNING':
                    color = Colors.YELLOW
                else:
                    color = Colors.RED

                alerts = len(status.get('alerts', []))
                alert_str = f" ({alerts} alerts)" if alerts > 0 else ""

                print(f"[{timestamp}] {color}{overall}{Colors.END}{alert_str}")

                # Alert on tribunal events
                if alerts > 0:
                    print(f"{Colors.RED}🚨 TRIBUNAL ALERTS DETECTED! Run interactive mode to respond.{Colors.END}")

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n{Colors.BLUE}Auto-monitor stopped.{Colors.END}")

def main():
    parser = argparse.ArgumentParser(description='AI Republic Operations Dashboard')
    parser.add_argument('--mode', choices=['interactive', 'auto', 'check'],
                       default='interactive', help='Dashboard mode')
    parser.add_argument('--interval', type=int, default=300,
                       help='Auto-check interval in seconds')
    parser.add_argument('--quiet', action='store_true',
                       help='Quiet mode (less output)')

    args = parser.parse_args()

    dashboard = AIRepublicDashboard()

    if args.mode == 'check':
        # Single health check
        status = dashboard.perform_health_check()
        dashboard.display_status(status)

        # Exit with appropriate code
        if status['overall_status'] == 'HEALTHY':
            sys.exit(0)
        elif status['overall_status'] == 'WARNING':
            sys.exit(1)
        else:
            sys.exit(2)

    elif args.mode == 'auto':
        # Automated monitoring
        dashboard.run_auto_mode(args.interval)

    else:
        # Interactive mode (default)
        dashboard.run_interactive_mode()

if __name__ == '__main__':
    main()
