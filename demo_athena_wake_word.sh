#!/bin/bash

# ATHENA WAKE-WORD DEMO
# Demonstrates hands-free "Hey Athena" voice control

echo "🎤 ATHENA WAKE-WORD DEMO - HANDS-FREE CONTROL"
echo "=============================================="
echo ""

# Check if voice integration is available
if [ ! -f "/opt/ai-republic/athena_voice_integration.py" ]; then
    echo "❌ Athena voice integration not found. Please install Athena first:"
    echo "   sudo ./install_athena_copilot.sh"
    exit 1
fi

if ! python3 -c "import speech_recognition, pyttsx3" 2>/dev/null; then
    echo "❌ Voice libraries not available. To enable wake-word control:"
    echo "   ./athena_wake_word_activation.sh"
    exit 1
fi

echo "✅ Athena wake-word capabilities detected"
echo ""

# Demo 1: Wake Word Activation
echo "🎯 DEMO 1: WAKE-WORD ACTIVATION"
echo "-------------------------------"
echo "Athena listens continuously for wake words:"
echo ""
echo "🎤 Listening for command..."
echo "🗣️ You say: 'Hey Athena'"
echo "🎯 Wake word detected!"
echo "🗣️ Athena responds: 'Yes?'"
echo ""
echo "🎤 Listening for command..."
echo "🗣️ You say: 'Check system status'"
echo "🤖 Processing: check system status"
echo "🤖 System status: All services operational, compliance at 99.7%, no active alerts."
echo "🗣️ Speaking response..."
echo ""

# Demo 2: Natural Conversation Flow
echo "💬 DEMO 2: NATURAL CONVERSATION FLOW"
echo "-------------------------------------"
echo "Just like you described - full conversational control:"
echo ""

conversations=(
    "Hey Athena, show me the system status."
    "Good. Check quarantines."
    "Restart judicial."
    "Do that again."
    "What was the compliance earlier?"
    "Stop listening."
)

for i in "${!conversations[@]}"; do
    if [ $i -eq 0 ]; then
        echo "🎤 You say: '${conversations[$i]}'"
        echo "🎯 Wake word 'Athena' detected!"
        echo "🤖 Athena: All services operational. Compliance 99.8%. No tribunals active."
        echo "🗣️ Speaking response..."
    elif [ $i -eq 1 ]; then
        echo ""
        echo "🎤 You say: '${conversations[$i]}'"
        echo "🤖 Athena: No quarantines currently active."
        echo "🗣️ Speaking response..."
    elif [ $i -eq 2 ]; then
        echo ""
        echo "🎤 You say: '${conversations[$i]}'"
        echo "🤖 Athena: Confirming — restart the judicial service? (yes/no)"
        echo "🗣️ Speaking confirmation request..."
    elif [ $i -eq 3 ]; then
        echo ""
        echo "🎤 You say: 'Yes'"
        echo "🤖 Athena: Confirmed. Judicial service restarted successfully."
        echo "🗣️ Speaking confirmation..."
        echo ""
        echo "🎤 You say: '${conversations[$i]}'"
        echo "🤖 Athena: Repeating last action — restarting judicial service."
        echo "🗣️ Speaking response..."
    elif [ $i -eq 4 ]; then
        echo ""
        echo "🎤 You say: '${conversations[$i]}'"
        echo "🤖 Athena: 99.8% during your last status check."
        echo "🗣️ Speaking response..."
    elif [ $i -eq 5 ]; then
        echo ""
        echo "🎤 You say: '${conversations[$i]}'"
        echo "🤖 Athena: Deactivating wake-word control. Goodbye!"
        echo "🗣️ Speaking farewell..."
    fi
done

echo ""
echo ""

# Demo 3: Multiple Wake Words
echo "🎤 DEMO 3: MULTIPLE WAKE WORDS"
echo "------------------------------"
echo "Athena responds to various wake words:"
echo ""

wake_words=(
    "Hey Athena"
    "Athena"
    "AI Republic"
    "System"
)

for wake_word in "${wake_words[@]}"; do
    echo "🗣️ You say: '$wake_word, what are the metrics?'"
    echo "🎯 Wake word '$wake_word' detected!"
    echo "🤖 Athena: Current metrics: Compliance 99.7%, Tribunals today: 0, Uptime: up 2 days"
    echo "🗣️ Speaking response..."
    echo ""
done

# Demo 4: Background Operation
echo "🔄 DEMO 4: BACKGROUND OPERATION"
echo "--------------------------------"
echo "Run as a background service for always-on control:"
echo ""
echo "Commands:"
echo "  sudo systemctl enable athena-wake-word    # Auto-start on boot"
echo "  sudo systemctl start athena-wake-word     # Start now"
echo "  sudo systemctl stop athena-wake-word      # Stop"
echo "  athena-voice-on                           # Quick start alias"
echo "  athena-voice-off                          # Quick stop alias"
echo ""
echo "Benefits:"
echo "  ✅ Always listening (no app to open)"
echo "  ✅ Hands-free operation"
echo "  ✅ Background monitoring"
echo "  ✅ Instant response to wake words"
echo ""

# Demo 5: Error Handling
echo "🛠️ DEMO 5: ERROR HANDLING"
echo "-------------------------"
echo "Athena handles voice recognition gracefully:"
echo ""
echo "🎤 Listening..."
echo "🗣️ You say: (unclear audio or background noise)"
echo "❌ Athena: Could not understand audio. Please try again."
echo "🗣️ Speaking error message..."
echo ""
echo "🎤 Listening..."
echo "🗣️ You say: 'Show me the login' (unrecognized command)"
echo "🤖 Athena: I'm not sure I understand that command. Did you mean: 'show me the logs', 'show metrics'?"
echo "🗣️ Speaking suggestions..."
echo ""

echo "🎯 WAKE-WORD CONTROL SUMMARY:"
echo "• 🎤 Always listening for wake words: 'Hey Athena', 'Athena', 'AI Republic', 'System'"
echo "• 🗣️ Natural speech commands with voice responses"
echo "• 🧠 Full conversation memory and context"
echo "• ✅ Confirmation workflows for sensitive operations"
echo "• 🔄 Background service operation"
echo "• 🛠️ Intelligent error handling and suggestions"
echo ""

echo "🚀 ACTIVATION:"
echo "1. Run: ./athena_wake_word_activation.sh"
echo "2. Start: athena-wake (manual) or sudo systemctl start athena-wake-word (service)"
echo "3. Say: 'Hey Athena, check system status'"
echo "4. Enjoy hands-free AI Republic control!"
echo ""

echo "📖 For full documentation:"
echo "   ATHENA_CONVERSATIONAL_GUIDE.md - Complete voice guide"
echo "   athena_voice_integration.py - Voice implementation"
echo ""

echo "🎉 Athena Wake-Word Demo Complete!"
echo "You now command your AI Republic with your voice! 🫡🎤🤖"
