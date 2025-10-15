# 🤖 AI REPUBLIC OPERATIONS DASHBOARD

**Interactive CLI Tool for Constitutional AI Governance**

## Overview

The AI Republic Operations Dashboard provides an interactive command-line interface for monitoring and managing your constitutional AI republic. It automates daily health checks, provides real-time monitoring, and handles tribunal alert responses.

## Installation

### Quick Install
```bash
chmod +x install_ai_republic_cli.sh
sudo ./install_ai_republic_cli.sh
```

### Manual Install
```bash
# Copy files
sudo cp ai_republic_cli.py /opt/ai-republic/
sudo cp ai_republic_cli.service /etc/systemd/system/

# Set permissions
sudo chmod +x /opt/ai-republic/ai_republic_cli.py

# Add aliases (optional)
echo "alias ai-republic='python3 /opt/ai-republic/ai_republic_cli.py'" >> ~/.bashrc
echo "alias ai-ops='python3 /opt/ai-republic/ai_republic_cli.py --mode interactive'" >> ~/.bashrc
echo "alias ai-check='python3 /opt/ai-republic/ai_republic_cli.py --mode check'" >> ~/.bashrc
```

## Usage

### Interactive Mode (Default)
```bash
# Launch the main dashboard
python3 /opt/ai-republic/ai_republic_cli.py

# Or use the alias (after installation)
ai-republic
ai-ops
```

**Interactive Commands:**
- `[c]heck` - Run immediate health check
- `[t]ribunal` - Handle tribunal alerts interactively
- `[l]ogs` - View detailed system logs
- `[r]estart` - Restart all AI Republic services
- `[q]uit` - Exit dashboard

### Auto-Monitor Mode
```bash
# Continuous monitoring with 5-minute checks
python3 /opt/ai-republic/ai_republic_cli.py --mode auto

# Custom interval (30 seconds)
python3 /opt/ai-republic/ai_republic_cli.py --mode auto --interval 30
```

### Health Check Mode
```bash
# Quick health check with exit codes
python3 /opt/ai-republic/ai_republic_cli.py --mode check
ai-check

# Exit codes:
# 0 = HEALTHY
# 1 = WARNING
# 2 = CRITICAL
```

## Dashboard Features

### Real-Time Status Display
```
🤖 AI REPUBLIC STATUS DASHBOARD
==================================================
Overall Status: ✅ HEALTHY
Last Check: 2024-12-19 14:30:25

Services:
  Constitutional: ✅ running - Operational
  Judicial: ✅ running - Operational
  Federation: ✅ running - Operational

Key Metrics:
  Compliance Rate: ✅ 99.8%
  Tribunals Today: ✅ 0
  System Uptime: ✅ up 2 days, 4 hours

✅ No tribunal alerts

Recent Activity:
  2024-12-19 14:30:22 - JUDICIAL VERDICT: ALLOW for op_api_call_789
  2024-12-19 14:29:45 - JUDICIAL VERDICT: WARN for op_policy_check_456
  2024-12-19 14:28:12 - JUDICIAL VERDICT: ALLOW for op_user_query_123
```

### Tribunal Alert Handling

When tribunal alerts are detected, the dashboard provides interactive response options:

```
🚨 TRIBUNAL RESPONSE REQUIRED

Alert 1:
  Time: 2024-12-19 14:30:22
  Message: CRITICAL VIOLATION: Sovereignty breach detected in agent-99

Response options:
  1. APPROVE - Allow system to handle automatically
  2. OVERRIDE - Override with human decision
  3. ESCALATE - Send to oversight council
  4. SKIP - Handle later

Choose (1-4): 1
✅ Approved automatic handling
```

### Color-Coded Status
- 🟢 **GREEN**: Healthy/Running/Normal
- 🟡 **YELLOW**: Warning/Degraded/Attention needed
- 🔴 **RED**: Critical/Failed/Action required

## Integration Examples

### Cron Job for Automated Checks
```bash
# Add to crontab for hourly health checks
crontab -e
# Add: 0 * * * * /usr/bin/python3 /opt/ai-republic/ai_republic_cli.py --mode check >> /var/log/ai-republic/cron_health.log 2>&1
```

### Scripting Integration
```bash
#!/bin/bash
# Check AI Republic health in deployment scripts

if python3 /opt/ai-republic/ai_republic_cli.py --mode check; then
    echo "✅ AI Republic healthy - proceeding with deployment"
else
    echo "❌ AI Republic issues detected - aborting deployment"
    exit 1
fi
```

### Monitoring Integration
```bash
# Nagios/Icinga compatible check
EXIT_CODE=$(python3 /opt/ai-republic/ai_republic_cli.py --mode check; echo $?)
if [ $EXIT_CODE -eq 0 ]; then
    echo "OK - AI Republic healthy"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "WARNING - AI Republic needs attention"
else
    echo "CRITICAL - AI Republic has critical issues"
fi
```

## Service Management

### Enable Auto-Monitor Service
```bash
# Install systemd service
sudo cp ai_republic_cli.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-republic-cli
sudo systemctl start ai-republic-cli

# Check status
sudo systemctl status ai-republic-cli
```

### View Service Logs
```bash
# Systemd logs
sudo journalctl -u ai-republic-cli -f

# Application logs
tail -f /var/log/ai-republic/cli_monitor.log
```

## Troubleshooting

### Common Issues

#### "Command not found"
```bash
# Ensure Python path is correct
which python3
ls -la /opt/ai-republic/ai_republic_cli.py

# Check permissions
sudo chmod +x /opt/ai-republic/ai_republic_cli.py
```

#### "Permission denied"
```bash
# Run as appropriate user or with sudo
sudo python3 /opt/ai-republic/ai_republic_cli.py

# Or add user to ai-republic group
sudo usermod -a -G ai-republic $USER
```

#### "Services not detected"
```bash
# Check if AI Republic is deployed
systemctl list-units | grep ai-republic

# Verify deployment
ls -la /opt/ai-republic/
ls -la /var/log/ai-republic/
```

#### Interactive mode not working
```bash
# Ensure terminal supports ANSI colors
export TERM=xterm-256color

# Try with simpler terminal
python3 /opt/ai-republic/ai_republic_cli.py --mode check
```

## Advanced Configuration

### Custom Check Intervals
```bash
# Modify the check_interval in the script
# Default: 300 seconds (5 minutes)
sed -i 's/self.check_interval = 300/self.check_interval = 60/' /opt/ai-republic/ai_republic_cli.py
```

### Custom Metrics
Add custom metrics by modifying the `get_system_metrics()` method in the dashboard class.

### Alert Integration
Modify the `check_tribunal_alerts()` method to integrate with external alerting systems (email, Slack, etc.).

## API Reference

### Exit Codes
- `0`: HEALTHY - All systems operational
- `1`: WARNING - Attention needed but not critical
- `2`: CRITICAL - Immediate action required

### Command Line Options
```
usage: ai_republic_cli.py [-h] [--mode {interactive,auto,check}]
                         [--interval INTERVAL] [--quiet]

AI Republic Operations Dashboard

optional arguments:
  -h, --help           show this help message and exit
  --mode {interactive,auto,check}
                       Dashboard mode (default: interactive)
  --interval INTERVAL  Auto-check interval in seconds (default: 300)
  --quiet              Quiet mode (less output)
```

## Security Notes

- The dashboard reads system logs and service status only
- No write operations are performed automatically
- Interactive tribunal responses are logged for audit trails
- All actions require appropriate system permissions

## Support

### Documentation
- Main Operations Reference: `AI_REPUBLIC_FINAL_REFERENCE.md`
- Executive Summary: `AI_REPUBLIC_EXECUTIVE_SUMMARY.md`
- Cheat Sheet: `AI_REPUBLIC_CHEAT_SHEET.md`

### Emergency Contacts
- System Administration: admin@ai-republic.org
- Security Incidents: security@ai-republic.org
- Constitutional Oversight: oversight@ai-republic.org

---

**The AI Republic Operations Dashboard transforms constitutional AI governance from manual processes to automated, interactive management.**
