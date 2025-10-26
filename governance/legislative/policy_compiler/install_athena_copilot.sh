#!/bin/bash

# ATHENA OPS CO-PILOT INSTALLATION
# Installs Athena as your AI Republic operations assistant

set -e

echo "🤖 Installing Athena Ops Co-Pilot..."

# Check dependencies
if ! python3 -c "import schedule, json" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip3 install schedule
fi

# Copy Athena components
sudo cp athena_ops_copilot.py /opt/ai-republic/
sudo cp athena_copilot_scheduler.py /opt/ai-republic/
sudo cp athena_conversation_engine.py /opt/ai-republic/
sudo cp athena_voice_integration.py /opt/ai-republic/
sudo cp athena_memory_system.py /opt/ai-republic/
sudo cp athena_memory_maintenance.py /opt/ai-republic/
sudo cp athena_alert_system.py /opt/ai-republic/
sudo chmod +x /opt/ai-republic/athena_ops_copilot.py
sudo chmod +x /opt/ai-republic/athena_copilot_scheduler.py
sudo chmod +x /opt/ai-republic/athena_conversation_engine.py
sudo chmod +x /opt/ai-republic/athena_voice_integration.py
sudo chmod +x /opt/ai-republic/athena_memory_system.py
sudo chmod +x /opt/ai-republic/athena_memory_maintenance.py
sudo chmod +x /opt/ai-republic/athena_alert_system.py

# Copy systemd services and timers
sudo cp athena_memory_maintenance.service /etc/systemd/system/
sudo cp athena_memory_maintenance.timer /etc/systemd/system/

# Create memory directories
sudo mkdir -p /var/lib/ai-republic/athena_memory/conversations
sudo mkdir -p /var/lib/ai-republic/athena_memory/backups
sudo chown -R ai-republic:ai-republic /var/lib/ai-republic/athena_memory

# Create default alert configuration
sudo tee /etc/ai-republic/athena_alerts.json > /dev/null << 'EOF'
{
  "enabled": true,
  "channels": {
    "terminal": {
      "enabled": true,
      "show_details": true,
      "sound_alert": false
    },
    "email": {
      "enabled": false,
      "smtp_server": "localhost",
      "smtp_port": 587,
      "sender_email": "athena@ai-republic.local",
      "recipient_emails": ["admin@ai-republic.local"],
      "use_tls": true,
      "username": "",
      "password": ""
    },
    "voice": {
      "enabled": true,
      "speak_alerts": true,
      "wake_word_interrupt": true
    },
    "log": {
      "enabled": true,
      "log_file": "/var/log/ai-republic/athena_alerts.log",
      "max_log_size": 10485760
    }
  },
  "alert_levels": {
    "critical": ["maintenance_failure", "memory_corruption", "system_down", "backup_system_failure"],
    "warning": ["maintenance_warning", "memory_high_usage", "backup_failure", "memory_compaction_failure"],
    "info": ["maintenance_success", "memory_optimized", "backup_created"]
  },
  "throttling": {
    "max_alerts_per_hour": 5,
    "cooldown_minutes": 15,
    "duplicate_suppression": true
  },
  "escalation": {
    "enabled": false,
    "escalate_after_minutes": 60,
    "escalation_recipients": []
  }
}
EOF

# Copy systemd service
sudo cp athena_scheduler.service /etc/systemd/system/

# Create configuration
sudo mkdir -p /etc/ai-republic
sudo tee /etc/ai-republic/athena_schedule.json > /dev/null << 'EOF'
{
  "daily_briefing": "09:00",
  "startup_delay": 60,
  "health_check_interval": 3600,
  "briefing_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "timezone": "UTC"
}
EOF

# Add aliases
if ! grep -q "alias athena=" ~/.bashrc 2>/dev/null; then
    echo "alias athena='python3 /opt/ai-republic/athena_conversation_engine.py'" >> ~/.bashrc
    echo "alias athena-chat='python3 /opt/ai-republic/athena_conversation_engine.py'" >> ~/.bashrc
    echo "alias athena-brief='python3 /opt/ai-republic/athena_ops_copilot.py --mode briefing'" >> ~/.bashrc
    echo "alias athena-voice='python3 /opt/ai-republic/athena_voice_integration.py'" >> ~/.bashrc
    echo "alias athena-setup='python3 /opt/ai-republic/athena_voice_integration.py --setup'" >> ~/.bashrc
    echo "alias athena-maintenance='python3 /opt/ai-republic/athena_memory_maintenance.py'" >> ~/.bashrc
    echo "alias athena-alerts='python3 /opt/ai-republic/athena_alert_system.py'" >> ~/.bashrc
fi

# Create desktop integration (optional)
if [ -d ~/Desktop ] && [ ! -f ~/Desktop/athena-copilot.desktop ]; then
    cat > ~/Desktop/athena-copilot.desktop << 'EOF'
[Desktop Entry]
Name=Athena Ops Co-Pilot
Comment=AI Republic Operations Assistant
Exec=gnome-terminal -- python3 /opt/ai-republic/athena_ops_copilot.py --mode conversation
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;Monitor;
EOF
    chmod +x ~/Desktop/athena-copilot.desktop
fi

# Test installation
echo "Testing Athena installation..."
python3 /opt/ai-republic/athena_ops_copilot.py --mode briefing > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Athena installation successful"
else
    echo "⚠️ Athena installation completed but testing failed (this is normal if AI Republic is not deployed yet)"
fi

echo ""
echo "🎉 Athena Ops Co-Pilot installed!"
echo ""
echo "🎉 Athena Conversational Co-Pilot with Automated Memory Maintenance Ready!"
echo ""
echo "Usage:"
echo "  athena                # Conversational mode (text)"
echo "  athena-brief          # Get immediate status briefing"
echo "  athena-voice          # Voice-enabled assistant"
echo "  athena-setup          # Setup voice environment"
echo ""
echo "Conversational Commands:"
echo "  • 'How is the system running?'"
echo "  • 'Show me the logs'"
echo "  • 'Check tribunal alerts'"
echo "  • 'What are the metrics?'"
echo "  • 'Restart services' (requires confirmation)"
echo ""
echo "Voice Features (if enabled):"
echo "  • athena-voice --mode voice        # Voice-only conversation"
echo "  • athena-voice --mode continuous   # Wake word: 'Athena'"
echo "  • athena-voice --mode hybrid       # Text + voice mixed"
echo ""
echo "Scheduled Operations:"
echo "  - Daily briefing at 9:00 AM (weekdays)"
echo "  - Startup briefing 60 seconds after boot"
echo "  - Hourly health checks with alerts"
echo ""
echo "To enable scheduled briefings:"
echo "  sudo systemctl enable athena-scheduler"
echo "  sudo systemctl start athena-scheduler"
echo ""
echo "To enable weekly memory maintenance:"
echo "  sudo systemctl enable athena-memory-maintenance.timer"
echo "  sudo systemctl start athena-memory-maintenance.timer"
echo ""
echo "To enable alert notifications:"
echo "  athena-alerts test  # Test all alert channels"
echo ""
echo "To test immediately:"
echo "  athena-chat  # Type: 'check status' then 'quit'"
echo ""
echo "Run 'source ~/.bashrc' to activate aliases"
