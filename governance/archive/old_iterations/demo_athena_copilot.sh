#!/bin/bash

# ATHENA OPS CO-PILOT DEMO
# Demonstrates conversational AI Republic operations

echo "🤖 ATHENA OPS CO-PILOT DEMO"
echo "==========================="
echo ""

# Check if Athena is installed
if [ ! -f "/opt/ai-republic/athena_ops_copilot.py" ]; then
    echo "❌ Athena not found. Please run installation first:"
    echo "   sudo ./install_athena_copilot.sh"
    exit 1
fi

echo "✅ Athena Ops Co-Pilot detected"
echo ""

# Demo 1: Briefing Mode
echo "📋 DEMO 1: Status Briefing"
echo "--------------------------"
echo "Command: python3 /opt/ai-republic/athena_ops_copilot.py --mode briefing"
echo ""
echo "Simulated Output (would show real status if AI Republic deployed):"
echo "🤖 ATHENA OPS BRIEFING"
echo "=============================================================="
echo "Good morning Christian — everything's running smoothly. Compliance at 99.8%, 0 tribunals today."
echo "No action needed from you right now."
echo "Priority: ROUTINE"
echo "=============================================================="
echo ""

# Demo 2: Scheduled Briefings
echo "📅 DEMO 2: Scheduled Operations"
echo "-------------------------------"
echo "Athena automatically provides:"
echo "  • Startup briefing: 60 seconds after system boot"
echo "  • Daily briefing: 9:00 AM on weekdays"
echo "  • Health monitoring: Hourly checks with alerts only"
echo ""
echo "Configuration in: /etc/ai-republic/athena_schedule.json"
echo ""

# Demo 3: Conversational Commands
echo "💬 DEMO 3: Conversational Interface"
echo "-----------------------------------"
echo "Athena understands natural language commands:"
echo ""
echo "You: check status"
echo "🤖 Current status: All services operational, compliance at 99.7%, no active alerts."
echo ""
echo "You: show me the logs"
echo "🤖 Recent activity (5 entries):"
echo "  JUDICIAL VERDICT: ALLOW for op_user_query_123"
echo "  JUDICIAL VERDICT: WARN for op_policy_check_456"
echo "  [additional log entries...]"
echo ""
echo "You: what's the compliance"
echo "🤖 Current metrics: Compliance 99.7%, Tribunals today: 0, Uptime: up 2 days"
echo ""

# Demo 4: Tribunal Handling
echo "⚖️ DEMO 4: Tribunal Management"
echo "------------------------------"
echo "When tribunal alerts occur:"
echo ""
echo "🤖 P0 alert triggered on sandbox_agent_14 — severity 0.86, tribunal verdict issued."
echo "   Recommend uphold. Would you like me to handle it?"
echo ""
echo "Available responses:"
echo "  • 'approve' - Uphold tribunal decision"
echo "  • 'override' - Override with human reasoning"
echo "  • 'escalate' - Send to oversight council"
echo "  • 'details' - Get full tribunal information"
echo ""

# Demo 5: Installation Verification
echo "✅ DEMO 5: Installation Status"
echo "------------------------------"
echo "Checking installed components:"

check_file() {
    if [ -f "$1" ]; then
        echo "  ✅ $2"
    else
        echo "  ❌ $2 (missing: $1)"
    fi
}

check_file "/opt/ai-republic/athena_ops_copilot.py" "Athena Co-Pilot"
check_file "/opt/ai-republic/athena_copilot_scheduler.py" "Scheduler"
check_file "/etc/systemd/system/athena-scheduler.service" "Systemd Service"
check_file "/etc/ai-republic/athena_schedule.json" "Schedule Config"
check_file "ATHENA_OPS_INTEGRATION.md" "Documentation"

echo ""
echo "🎯 ATHENA INTEGRATION SUMMARY:"
echo "• Conversational interface for all AI Republic operations"
echo "• Automated daily briefings with natural language"
echo "• Proactive escalation of critical issues only"
echo "• Full audit trail of all human-AI interactions"
echo "• Extensible command system for custom operations"
echo ""

echo "🚀 NEXT STEPS:"
echo "1. Deploy AI Republic core (Phase 1 + 2)"
echo "2. Install Athena: sudo ./install_athena_copilot.sh"
echo "3. Enable scheduler: sudo systemctl enable athena-scheduler"
echo "4. Test conversation: athena-chat"
echo "5. Wait for automated morning briefing at 9 AM"
echo ""

echo "📖 For full documentation, see:"
echo "   ATHENA_OPS_INTEGRATION.md - Complete integration guide"
echo "   athena_ops_copilot.py - Source code and customization"
echo ""

echo "🏛️ Athena Ops Co-Pilot Demo Complete!"
echo "Your AI Republic now has an intelligent operations assistant! 🫡✨"
