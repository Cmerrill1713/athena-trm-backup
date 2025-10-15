#!/bin/bash

# ATHENA CONVERSATIONAL DEMO
# Demonstrates natural language AI Republic operations

echo "🤖 ATHENA CONVERSATIONAL DEMO"
echo "=============================="
echo ""

# Check if Athena is installed
if [ ! -f "/opt/ai-republic/athena_conversation_engine.py" ]; then
    echo "❌ Athena not found. Please run installation first:"
    echo "   sudo ./install_athena_copilot.sh"
    exit 1
fi

echo "✅ Athena Conversational Engine detected"
echo ""

# Demo 1: Text Conversation Mode
echo "💬 DEMO 1: Text Conversation Mode"
echo "----------------------------------"
echo "Command: python3 /opt/ai-republic/athena_conversation_engine.py --mode single --input 'check status'"
echo ""
echo "Simulated Response (would show real status if AI Republic deployed):"
echo "🤖 Everything's running smoothly. Compliance at 99.8%, 0 tribunals today."
echo ""

# Demo 2: Various Natural Language Commands
echo "🗣️ DEMO 2: Natural Language Commands"
echo "-------------------------------------"
echo "Athena understands plain English commands:"
echo ""

commands=(
    "how is the system running?"
    "show me the logs"
    "what are the metrics?"
    "check tribunal alerts"
    "restart services"
    "do that again"
    "help"
)

for cmd in "${commands[@]}"; do
    echo "You: $cmd"
    # In a real demo, this would call the actual engine
    case $cmd in
        "how is the system running?")
            echo "🤖 Everything's running smoothly. Compliance at 99.8%, 0 tribunals today."
            ;;
        "show me the logs")
            echo "🤖 Recent activity (5 entries):"
            echo "  • JUDICIAL VERDICT: ALLOW for op_user_query_123"
            echo "  • JUDICIAL VERDICT: WARN for op_policy_check_456"
            echo "  • [additional log entries...]"
            ;;
        "what are the metrics?")
            echo "🤖 Current metrics: Compliance 99.7%, Tribunals today: 0, Uptime: up 2 days"
            ;;
        "check tribunal alerts")
            echo "🤖 No tribunal alerts currently active. System is operating within normal parameters."
            ;;
        "restart services")
            echo "🤖 Are you sure you want to restart AI Republic services? This will temporarily interrupt system operations."
            ;;
        "do that again")
            echo "🤖 Referring to your previous request: 'check tribunal alerts' which resulted in: No tribunal alerts currently active..."
            ;;
        "help")
            echo "🤖 I can help you with AI Republic operations. Try asking about:"
            echo "     • Status & Health: 'how is the system running?'"
            echo "     • Logs & Activity: 'show me the logs'"
            echo "     • Metrics: 'what are the metrics?'"
            echo "     • Tribunals: 'check tribunal alerts'"
            echo "     • Services: 'restart services'"
            ;;
    esac
    echo ""
done

# Demo 3: Confirmation Workflows
echo "✅ DEMO 3: Confirmation Workflows"
echo "----------------------------------"
echo "For sensitive operations, Athena requires confirmation:"
echo ""
echo "You: restart services"
echo "🤖 Are you sure you want to restart AI Republic services? This will temporarily interrupt system operations."
echo ""
echo "Available responses:"
echo "  • 'yes' or 'confirm' → Executes the action"
echo "  • 'no' or 'cancel' → Cancels the action"
echo "  • 'tell me more' → Gets additional details"
echo ""
echo "You: tell me more"
echo "🤖 Pending action: restart all AI Republic services. This will:"
echo "     • Stop current operations temporarily"
echo "     • Restart all constitutional services"
echo "     • Perform health checks after restart"
echo "     • Generate restart confirmation report"
echo ""

# Demo 4: Context Awareness
echo "🧠 DEMO 4: Context Awareness"
echo "-----------------------------"
echo "Athena remembers conversation context:"
echo ""
echo "You: show metrics"
echo "🤖 Current metrics: Compliance 99.7%, Tribunals today: 0, Uptime: up 2 days"
echo ""
echo "You: do that again"
echo "🤖 Referring to your previous request: 'show metrics' which resulted in: Current metrics: Compliance 99.7%..."
echo ""
echo "You: what was the compliance rate?"
echo "🤖 Based on your recent metrics request: Compliance is currently at 99.7%"
echo ""

# Demo 5: Voice Capabilities (if available)
echo "🎤 DEMO 5: Voice Capabilities"
echo "-----------------------------"
if python3 -c "import speech_recognition, pyttsx3" 2>/dev/null; then
    echo "✅ Voice libraries detected - full voice capabilities available"
    echo ""
    echo "Voice Commands:"
    echo "  • athena-voice --mode voice        # Voice-only conversation"
    echo "  • athena-voice --mode continuous   # Always listening ('Hey Athena')"
    echo "  • athena-voice --mode hybrid       # Mix text and voice"
    echo ""
    echo "Wake Words: 'Athena', 'Hey Athena', 'AI Republic', 'System'"
else
    echo "❌ Voice libraries not installed"
    echo ""
    echo "To enable voice capabilities:"
    echo "  pip install SpeechRecognition pyttsx3 pyaudio"
    echo "  sudo apt install portaudio19-dev python3-pyaudio  # Ubuntu/Debian"
    echo "  athena-setup  # Test voice environment"
fi
echo ""

# Demo 6: Scheduled Operations
echo "📅 DEMO 6: Scheduled Operations"
echo "-------------------------------"
echo "Athena provides automated briefings:"
echo ""
echo "• Daily Briefing: 9:00 AM weekdays"
echo "  🤖 'Good morning Christian — everything's green. Compliance at 99.8%. No tribunals overnight.'"
echo ""
echo "• Startup Briefing: 60 seconds after boot"
echo "  🤖 'System initialized successfully. All services operational.'"
echo ""
echo "• Health Monitoring: Hourly checks"
echo "  🤖 Only alerts when status changes to WARNING/CRITICAL"
echo ""

# Demo 7: Error Handling
echo "🔧 DEMO 7: Error Handling & Suggestions"
echo "----------------------------------------"
echo "Athena handles errors gracefully with helpful suggestions:"
echo ""
echo "You: show me the login"
echo "🤖 I'm not sure I understand that command. Did you mean: 'show me the logs', 'show metrics', 'check tribunals'?"
echo ""
echo "You: system helth"
echo "🤖 I'm not sure I understand that command. Did you mean: 'system health', 'system status', 'check status'?"
echo ""

echo "🎯 ATHENA CONVERSATIONAL SUMMARY:"
echo "• Natural language understanding for all AI Republic operations"
echo "• Context-aware conversations with memory"
echo "• Safe confirmation workflows for sensitive actions"
echo "• Voice capabilities (optional) for hands-free operation"
echo "• Automated briefings and monitoring"
echo "• Intelligent error handling with suggestions"
echo ""

echo "🚀 NEXT STEPS:"
echo "1. Install Athena: sudo ./install_athena_copilot.sh"
echo "2. Test conversation: athena-chat"
echo "3. Enable voice (optional): pip install SpeechRecognition pyttsx3"
echo "4. Enable scheduling: sudo systemctl enable athena-scheduler"
echo "5. Say 'Athena, check system status' - she understands!"
echo ""

echo "📖 For full documentation, see:"
echo "   ATHENA_CONVERSATIONAL_GUIDE.md - Complete conversational guide"
echo "   athena_conversation_engine.py - Source code and customization"
echo ""

echo "🎉 Athena Conversational Demo Complete!"
echo "Your AI Republic now speaks your language! 🫡🤖💬"
