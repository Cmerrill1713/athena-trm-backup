# 🤖 ATHENA OPS CO-PILOT INTEGRATION

**Conversational AI Assistant for Constitutional Governance**

## Overview

Athena serves as your intelligent operations co-pilot, transforming manual CLI commands into natural conversation while maintaining full constitutional governance capabilities.

### Key Features
- **Conversational Interface**: Speak naturally about AI Republic operations
- **Automated Monitoring**: Scheduled health checks and status briefings
- **Intelligent Analysis**: Parses complex system data into actionable insights
- **Proactive Alerts**: Escalates only critical issues requiring human judgment
- **Audit Trail**: All interactions logged for compliance

## Architecture

### Core Components
- `athena_ops_copilot.py` - Main conversational interface
- `athena_copilot_scheduler.py` - Automated briefing scheduler
- `ai_republic_cli.py` - Underlying operations engine (integrated)

### Integration Flow
```
User Request → Athena Parser → CLI Commands → System Actions → Natural Response
```

## Installation

### One-Command Install
```bash
chmod +x install_athena_copilot.sh
sudo ./install_athena_copilot.sh
```

### Manual Setup
```bash
# Install dependencies
pip3 install schedule

# Copy components
sudo cp athena_*.py /opt/ai-republic/
sudo cp athena_scheduler.service /etc/systemd/system/

# Enable scheduler
sudo systemctl enable athena-scheduler
sudo systemctl start athena-scheduler
```

## Usage Modes

### 1. Immediate Briefing
```bash
# Get current status briefing
athena-brief

# Output:
🤖 ATHENA OPS BRIEFING
============================================================
Good morning Christian — everything's green. Compliance at 99.8%, 0 tribunals today.
No action needed from you right now.
Priority: ROUTINE
============================================================
```

### 2. Conversational Mode
```bash
# Interactive chat interface
athena-chat

# Output:
🤖 Athena Ops Co-Pilot activated. Type 'quit' to exit.
You: how are things running?
🤖 Current status: All services operational, compliance at 99.7%, no active alerts.
You: show me recent logs
🤖 Recent activity (5 entries):
  JUDICIAL VERDICT: ALLOW for op_user_query_123
  JUDICIAL VERDICT: WARN for op_policy_check_456
  ...
```

### 3. Scheduled Briefings
Athena automatically provides briefings:
- **Startup**: 60 seconds after system boot
- **Daily**: 9:00 AM weekdays
- **Health Checks**: Every hour (alerts only on issues)

### 4. Command Execution
Athena understands natural language commands:

```
"check system status"     → Performs health check
"show me the logs"        → Displays recent activity
"what's the compliance"   → Shows performance metrics
"restart services"        → Initiates service restart (with confirmation)
"clear low tribunals"     → Auto-resolves minor violations
```

## Configuration

### Schedule Configuration
Edit `/etc/ai-republic/athena_schedule.json`:
```json
{
  "daily_briefing": "09:00",
  "startup_delay": 60,
  "health_check_interval": 3600,
  "briefing_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "timezone": "UTC"
}
```

### Personality Customization
Modify personality strings in `athena_ops_copilot.py` for different communication styles.

## Command Reference

### Status & Monitoring
- "check status" / "health check" / "system status"
- "show metrics" / "performance metrics"
- "show logs" / "view logs" / "recent activity"

### Tribunal Management
- "handle tribunals" / "check alerts"
- "approve tribunals" / "clear tribunals"
- "escalate tribunal" / "review tribunal [id]"

### Service Management
- "restart services" / "restart all"
- "check services" / "service status"

### Information Requests
- "what happened overnight"
- "any issues today"
- "compliance report"
- "tribunal summary"

## Integration Examples

### With Existing Scripts
```bash
#!/bin/bash
# Deployment script with Athena integration

echo "Starting deployment..."
# ... deployment steps ...

# Check system health via Athena
if python3 /opt/ai-republic/athena_ops_copilot.py --mode briefing | grep -q "everything's running smoothly"; then
    echo "✅ Deployment successful - system healthy"
else
    echo "⚠️ Deployment completed but health check flagged issues"
fi
```

### Cron Job Integration
```bash
# Add to crontab for automated monitoring
crontab -e
# Add: 0 * * * * /usr/bin/python3 /opt/ai-republic/athena_ops_copilot.py --mode briefing >> /var/log/ai-republic/athena_cron.log 2>&1
```

### Alert Integration
```python
# Integrate with notification systems
from athena_ops_copilot import AthenaOpsCopilot

def send_alert(message, priority):
    # Send to Slack, email, etc.
    if priority == 'CRITICAL':
        # Immediate notification
        pass
    elif priority == 'WARNING':
        # Scheduled summary
        pass

# In monitoring loop
copilot = AthenaOpsCopilot()
status = copilot.perform_health_check()
briefing = copilot.analyze_status(status)

if briefing.requires_action:
    send_alert(copilot.generate_briefing_message(briefing), briefing.priority.value)
```

## Advanced Features

### Custom Commands
Extend Athena by adding new command patterns in `execute_command()`:

```python
def execute_command(self, command: str) -> str:
    if self._matches_command(command, ['custom action']):
        # Implement custom logic
        return "Custom action executed"
    # ... existing commands
```

### Briefing Templates
Customize briefing messages by modifying the personality dictionary:

```python
self.personality = {
    "greeting": "Hello {user}, here's your AI Republic update:",
    "healthy_summary": "All systems nominal. {metrics_summary}",
    # ... customize as needed
}
```

### Escalation Rules
Modify `analyze_status()` to customize when Athena escalates to human attention.

## Security Considerations

### Access Control
- Athena runs with ai-republic user permissions
- All operations logged for audit trail
- Sensitive operations require explicit confirmation

### Data Privacy
- Briefings contain aggregated, non-sensitive information
- Detailed logs accessible only to authorized users
- No raw system data exposed in conversations

### Operational Boundaries
- Athena cannot override constitutional decisions
- Tribunal approvals require explicit human confirmation
- Service restarts are logged and auditable

## Troubleshooting

### Athena Not Responding
```bash
# Check if service is running
systemctl status athena-scheduler

# Test manual execution
python3 /opt/ai-republic/athena_ops_copilot.py --mode briefing

# Check logs
journalctl -u athena-scheduler --since "1 hour ago"
```

### Briefings Not Delivered
```bash
# Check schedule configuration
cat /etc/ai-republic/athena_schedule.json

# Test manual briefing
python3 /opt/ai-republic/athena_copilot_scheduler.py --mode test-daily

# Verify timezone settings
date
```

### Command Not Recognized
```bash
# Check available commands
athena-chat
# Type "help" or "?" for command list

# Update command patterns in athena_ops_copilot.py
# Look for _matches_command() method
```

## Performance Tuning

### Briefing Frequency
- **High Activity**: Reduce startup delay, increase health check frequency
- **Normal Operations**: Default schedule (daily + hourly checks)
- **Low Activity**: Extend intervals, focus on daily briefings

### Resource Usage
- **Memory**: ~50MB baseline, spikes during health checks
- **CPU**: Minimal background usage, <5% during briefings
- **Storage**: ~10MB/month for briefing logs

## Future Enhancements

### Planned Features
- **Multi-Modal Output**: Voice briefings, dashboard visualizations
- **Advanced Analytics**: Trend analysis, predictive alerts
- **Team Collaboration**: Multi-user briefing coordination
- **Integration APIs**: REST endpoints for external systems

### Extension Points
- **Plugin System**: Custom command modules
- **Notification Channels**: SMS, voice, desktop notifications
- **Custom Briefings**: Domain-specific status reports
- **Learning System**: Adaptive briefing content based on user preferences

---

**Athena transforms complex AI Republic operations into natural conversation, making constitutional governance accessible while maintaining full operational integrity.**
