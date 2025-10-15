#!/usr/bin/env python3
"""
ATHENA ALERT SYSTEM
Automated notification system for maintenance failures and critical events

Provides multi-channel alerts for:
- Maintenance job failures
- Memory system issues
- Critical conversation errors
- System health alerts
"""

import json
import smtplib
import subprocess
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class AthenaAlertSystem:
    """Multi-channel alert system for Athena operations"""

    def __init__(self, config_file: str = "/etc/ai-republic/athena_alerts.json"):
        self.config_file = Path(config_file)
        # Try standard location, fallback to temp
        try:
            std_path = Path("/var/lib/ai-republic/athena_memory/alert_history.jsonl")
            std_path.parent.mkdir(parents=True, exist_ok=True)
            self.alert_history_file = std_path
        except (OSError, PermissionError):
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "athena_alerts"
            temp_dir.mkdir(exist_ok=True)
            self.alert_history_file = temp_dir / "alert_history.jsonl"
            print(f"Warning: Using fallback alert history location: {self.alert_history_file}")
        self.logger = logging.getLogger('athena_alerts')

        # Default alert configuration
        self.default_config = {
            "enabled": True,
            "channels": {
                "terminal": {
                    "enabled": True,
                    "show_details": True,
                    "sound_alert": False
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "sender_email": "athena@ai-republic.local",
                    "recipient_emails": ["admin@ai-republic.local"],
                    "use_tls": True,
                    "username": "",
                    "password": ""
                },
                "voice": {
                    "enabled": False,
                    "speak_alerts": True,
                    "wake_word_interrupt": True
                },
                "log": {
                    "enabled": True,
                    "log_file": "/var/log/ai-republic/athena_alerts.log",
                    "max_log_size": 10485760  # 10MB
                }
            },
            "alert_levels": {
                "critical": ["maintenance_failure", "memory_corruption", "system_down"],
                "warning": ["maintenance_warning", "memory_high_usage", "conversation_error"],
                "info": ["maintenance_success", "memory_optimized", "backup_created"]
            },
            "throttling": {
                "max_alerts_per_hour": 5,
                "cooldown_minutes": 15,
                "duplicate_suppression": True
            },
            "escalation": {
                "enabled": False,
                "escalate_after_minutes": 60,
                "escalation_recipients": []
            }
        }

        self.config = self._load_config()
        self.alert_history = self._load_alert_history()
        self._setup_logging()

    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    config = self.default_config.copy()
                    self._deep_update(config, loaded)
                    return config
        except Exception as e:
            self.logger.error(f"Failed to load alert config: {e}")

        return self.default_config.copy()

    def _deep_update(self, base: dict, update: dict):
        """Deep update nested dictionaries"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def _load_alert_history(self) -> List[Dict[str, Any]]:
        """Load recent alert history for throttling"""
        history = []
        try:
            if self.alert_history_file.exists():
                with open(self.alert_history_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            history.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Failed to load alert history: {e}")

        # Keep only last 100 alerts
        return history[-100:]

    def _setup_logging(self):
        """Setup alert-specific logging"""
        log_config = self.config['channels']['log']
        if log_config['enabled']:
            log_file = Path(log_config['log_file'])

            # Try to create log directory, fallback to temp if permission denied
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                log_path = log_config['log_file']
            except (OSError, PermissionError):
                # Fallback to temp directory
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "athena_alerts"
                temp_dir.mkdir(exist_ok=True)
                log_path = str(temp_dir / "athena_alerts.log")
                print(f"Warning: Using fallback log location: {log_path}")

            alert_logger = logging.getLogger('athena_alerts')
            alert_logger.setLevel(logging.INFO)

            # File handler with rotation
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                log_path,
                maxBytes=log_config['max_log_size'],
                backupCount=3
            )
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            alert_logger.addHandler(handler)

    def send_alert(self, alert_type: str, message: str,
                  details: Optional[Dict[str, Any]] = None,
                  severity: str = "warning") -> bool:
        """
        Send alert through configured channels

        Args:
            alert_type: Type of alert (maintenance_failure, memory_corruption, etc.)
            message: Alert message
            details: Optional detailed information
            severity: Alert severity (critical, warning, info)

        Returns:
            bool: True if alert was sent successfully
        """
        if not self.config['enabled']:
            return True

        # Check throttling
        if not self._should_send_alert(alert_type, severity):
            self.logger.info(f"Alert throttled: {alert_type}")
            return True

        # Prepare alert data
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'details': details or {},
            'channels_sent': []
        }

        success = True

        # Send through each enabled channel
        for channel_name, channel_config in self.config['channels'].items():
            if channel_config.get('enabled', False):
                try:
                    if channel_name == 'terminal':
                        self._send_terminal_alert(alert_data)
                    elif channel_name == 'email':
                        self._send_email_alert(alert_data)
                    elif channel_name == 'voice' and alert_data['severity'] == 'critical':
                        # Only send voice alerts for critical issues
                        self._send_voice_alert(alert_data)
                    elif channel_name == 'log':
                        self._send_log_alert(alert_data)

                    alert_data['channels_sent'].append(channel_name)

                except Exception as e:
                    self.logger.error(f"Failed to send {channel_name} alert: {e}")
                    success = False

        # Record alert in history
        self._record_alert(alert_data)

        # Check for escalation
        if severity == 'critical' and self.config['escalation']['enabled']:
            self._check_escalation(alert_data)

        return success

    def _should_send_alert(self, alert_type: str, severity: str) -> bool:
        """Check if alert should be sent based on throttling rules"""
        throttling = self.config['throttling']
        now = datetime.now()

        # Count recent alerts
        recent_alerts = [
            alert for alert in self.alert_history
            if (now - datetime.fromisoformat(alert['timestamp'])).total_seconds() < 3600
        ]

        # Check hourly limit
        if len(recent_alerts) >= throttling['max_alerts_per_hour']:
            return False

        # Check cooldown for same alert type
        if throttling['duplicate_suppression']:
            same_type_recent = [
                alert for alert in recent_alerts
                if alert['alert_type'] == alert_type
            ]

            if same_type_recent:
                last_same = datetime.fromisoformat(same_type_recent[-1]['timestamp'])
                cooldown_seconds = throttling['cooldown_minutes'] * 60

                if (now - last_same).total_seconds() < cooldown_seconds:
                    return False

        return True

    def _send_terminal_alert(self, alert_data: Dict[str, Any]):
        """Send alert to terminal with visual formatting"""
        severity_colors = {
            'critical': '\033[91m',  # Red
            'warning': '\033[93m',   # Yellow
            'info': '\033[94m'       # Blue
        }

        color = severity_colors.get(alert_data['severity'], '\033[0m')
        reset = '\033[0m'

        print(f"\n🚨 {color}ATHENA ALERT - {alert_data['severity'].upper()}{reset}")
        print("=" * 50)
        print(f"Type: {alert_data['alert_type']}")
        print(f"Time: {alert_data['timestamp']}")
        print(f"Message: {alert_data['message']}")

        if alert_data.get('details'):
            print("Details:")
            for key, value in alert_data['details'].items():
                print(f"  {key}: {value}")

        # Sound alert if enabled
        if self.config['channels']['terminal'].get('sound_alert', False):
            try:
                # Try to play system beep
                subprocess.run(['tput', 'bel'], check=False)
            except:
                pass

    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send alert via email"""
        email_config = self.config['channels']['email']

        msg = MIMEMultipart()
        msg['From'] = email_config['sender_email']
        msg['To'] = ', '.join(email_config['recipient_emails'])
        msg['Subject'] = f"🤖 Athena Alert - {alert_data['alert_type']} ({alert_data['severity']})"

        # Email body
        body = f"""
Athena Alert Notification
========================

Severity: {alert_data['severity'].upper()}
Type: {alert_data['alert_type']}
Time: {alert_data['timestamp']}

Message:
{alert_data['message']}

"""

        if alert_data.get('details'):
            body += "\nDetails:\n"
            for key, value in alert_data['details'].items():
                body += f"  {key}: {value}\n"

        body += "\n\nThis is an automated alert from the Athena AI Republic system."

        msg.attach(MIMEText(body, 'plain'))

        # Send email
        try:
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config['use_tls']:
                server.starttls()

            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])

            server.send_message(msg)
            server.quit()

        except Exception as e:
            raise Exception(f"Email send failed: {e}")

    def _send_voice_alert(self, alert_data: Dict[str, Any]):
        """Send alert via voice (requires voice integration)"""
        try:
            # Import voice processor
            from athena_voice_integration import VoiceProcessor

            voice_proc = VoiceProcessor()
            if not voice_proc.voice_enabled:
                self.logger.warning("Voice alerts enabled but voice system not available")
                return

            # Create voice message
            voice_message = f"Athena Alert: {alert_data['severity']} priority. {alert_data['message']}"

            # Speak the alert
            voice_proc.speak_response(voice_message)

        except ImportError:
            self.logger.warning("Voice alert requested but voice integration not available")
        except Exception as e:
            raise Exception(f"Voice alert failed: {e}")

    def _send_log_alert(self, alert_data: Dict[str, Any]):
        """Log alert to file"""
        log_message = f"ALERT {alert_data['severity'].upper()}: {alert_data['alert_type']} - {alert_data['message']}"

        if alert_data.get('details'):
            details_str = ", ".join([f"{k}={v}" for k, v in alert_data['details'].items()])
            log_message += f" [{details_str}]"

        self.logger.warning(log_message)

    def _record_alert(self, alert_data: Dict[str, Any]):
        """Record alert in history"""
        self.alert_history.append(alert_data)

        # Write to history file
        try:
            self.alert_history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.alert_history_file, 'a') as f:
                json.dump(alert_data, f)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"Failed to record alert history: {e}")

        # Keep history size manageable
        if len(self.alert_history) > 200:
            self.alert_history = self.alert_history[-100:]

    def _check_escalation(self, alert_data: Dict[str, Any]):
        """Check if alert needs escalation"""
        escalation_config = self.config['escalation']
        if not escalation_config['enabled']:
            return

        # Check if this alert type needs escalation
        escalate_after = timedelta(minutes=escalation_config['escalate_after_minutes'])

        # Look for unresolved critical alerts of same type
        now = datetime.now()
        same_type_alerts = [
            alert for alert in self.alert_history[-20:]  # Check last 20 alerts
            if (alert['alert_type'] == alert_data['alert_type'] and
                alert['severity'] == 'critical' and
                (now - datetime.fromisoformat(alert['timestamp'])) < escalate_after)
        ]

        if len(same_type_alerts) >= 3:  # Escalate after 3+ similar alerts
            self._send_escalation_alert(alert_data, same_type_alerts)

    def _send_escalation_alert(self, alert_data: Dict[str, Any], related_alerts: List[Dict[str, Any]]):
        """Send escalation alert for repeated critical issues"""
        escalation_msg = f"ESCALATION: Multiple {alert_data['alert_type']} alerts detected. " \
                        f"{len(related_alerts)} similar alerts in the last hour."

        escalation_details = {
            'original_alert': alert_data,
            'related_alerts_count': len(related_alerts),
            'escalation_reason': 'multiple_similar_alerts',
            'recommended_action': 'Immediate human intervention required'
        }

        # Send escalation through all channels
        for channel_name in self.config['channels']:
            if channel_name != 'log':  # Log is always sent
                try:
                    escalation_alert = alert_data.copy()
                    escalation_alert['message'] = escalation_msg
                    escalation_alert['details'] = escalation_details
                    escalation_alert['escalation'] = True

                    if channel_name == 'terminal':
                        self._send_terminal_alert(escalation_alert)
                    elif channel_name == 'email':
                        # Send to escalation recipients
                        escalation_recipients = self.config['escalation']['escalation_recipients']
                        if escalation_recipients:
                            self.config['channels']['email']['recipient_emails'] = escalation_recipients
                            self._send_email_alert(escalation_alert)
                    elif channel_name == 'voice':
                        # Escalation alerts are always critical, so voice is appropriate
                        self._send_voice_alert(escalation_alert)

                except Exception as e:
                    self.logger.error(f"Escalation alert failed for {channel_name}: {e}")

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        now = datetime.now()

        # Count alerts by time period
        last_hour = [a for a in self.alert_history if (now - datetime.fromisoformat(a['timestamp'])).total_seconds() < 3600]
        last_day = [a for a in self.alert_history if (now - datetime.fromisoformat(a['timestamp'])).total_seconds() < 86400]
        last_week = [a for a in self.alert_history if (now - datetime.fromisoformat(a['timestamp'])).total_seconds() < 604800]

        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            sev = alert['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Count by type
        type_counts = {}
        for alert in self.alert_history:
            alert_type = alert['alert_type']
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

        return {
            'total_alerts': len(self.alert_history),
            'last_hour': len(last_hour),
            'last_day': len(last_day),
            'last_week': len(last_week),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'channels_enabled': [ch for ch, cfg in self.config['channels'].items() if cfg.get('enabled')]
        }

    def test_alert_system(self) -> Dict[str, bool]:
        """Test all enabled alert channels"""
        test_results = {}

        test_alert = {
            'timestamp': datetime.now().isoformat(),
            'alert_type': 'test_alert',
            'message': 'This is a test alert from Athena Alert System',
            'severity': 'info',
            'details': {'test': True, 'timestamp': datetime.now().isoformat()},
            'channels_sent': []
        }

        print("🧪 Testing Athena Alert System...")

        for channel_name, channel_config in self.config['channels'].items():
            if channel_config.get('enabled', False):
                try:
                    print(f"  Testing {channel_name} channel...")
                    if channel_name == 'terminal':
                        self._send_terminal_alert(test_alert)
                    elif channel_name == 'email':
                        self._send_email_alert(test_alert)
                    elif channel_name == 'voice':
                        self._send_voice_alert(test_alert)
                    elif channel_name == 'log':
                        self._send_log_alert(test_alert)

                    test_results[channel_name] = True
                    print(f"  ✅ {channel_name} test successful")

                except Exception as e:
                    test_results[channel_name] = False
                    print(f"  ❌ {channel_name} test failed: {e}")

        return test_results

def main():
    """Main entry point for alert system management"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Alert System Management')
    parser.add_argument('action', choices=['test', 'stats', 'send', 'configure'],
                       help='Alert system action')
    parser.add_argument('--type', help='Alert type for send action')
    parser.add_argument('--message', help='Alert message for send action')
    parser.add_argument('--severity', choices=['critical', 'warning', 'info'], default='warning',
                       help='Alert severity')
    parser.add_argument('--config', help='Path to alert configuration file')

    args = parser.parse_args()

    # Use custom config if specified
    alert_system = AthenaAlertSystem(args.config) if args.config else AthenaAlertSystem()

    if args.action == 'test':
        results = alert_system.test_alert_system()
        print("\nTest Results Summary:")
        for channel, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {channel}: {status}")

    elif args.action == 'stats':
        stats = alert_system.get_alert_stats()
        print("📊 Athena Alert Statistics")
        print("=" * 30)
        print(f"Total alerts: {stats['total_alerts']}")
        print(f"Last hour: {stats['last_hour']}")
        print(f"Last day: {stats['last_day']}")
        print(f"Last week: {stats['last_week']}")
        print(f"Enabled channels: {', '.join(stats['channels_enabled'])}")

        print("\nBy Severity:")
        for sev, count in stats['by_severity'].items():
            print(f"  {sev}: {count}")

        print("\nBy Type:")
        for alert_type, count in stats['by_type'].items():
            print(f"  {alert_type}: {count}")

    elif args.action == 'send':
        if not args.type or not args.message:
            print("❌ Alert type and message required for send action")
            print("Usage: athena_alert_system.py send --type maintenance_failure --message 'Test alert'")
            return

        success = alert_system.send_alert(args.type, args.message, severity=args.severity)
        if success:
            print("✅ Alert sent successfully")
        else:
            print("❌ Alert send failed")

    elif args.action == 'configure':
        print("📝 Alert System Configuration")
        print("=" * 35)
        print("Edit /etc/ai-republic/athena_alerts.json to configure alerts")
        print("\nCurrent configuration:")
        print(json.dumps(alert_system.config, indent=2))

if __name__ == '__main__':
    main()
