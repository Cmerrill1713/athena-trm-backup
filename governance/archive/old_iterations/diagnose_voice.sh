#!/bin/bash
# Full voice diagnostic with console output

echo "🔬 Athena Voice Diagnostic"
echo "=========================="
echo ""

# Kill any running instances
echo "1️⃣  Killing any running Athena Reporter..."
pkill -9 AthenaReporter 2>/dev/null
sleep 1

# Test OS-level voice
echo ""
echo "2️⃣  Testing OS-level Samantha voice..."
say -v "Samantha" "This is Athena using Samantha at the OS level."
echo "   Exit code: $?"

# Launch app with output
echo ""
echo "3️⃣  Launching app with console output..."
echo "============================================================"
build/AthenaReporter.app/Contents/MacOS/AthenaReporter 2>&1 &
APP_PID=$!
echo "   App PID: $APP_PID"

# Wait for init
sleep 3

# Trigger a report
echo ""
echo "4️⃣  Generating health report..."
echo "============================================================"
ATHENA_VERBOSITY=brief python3 scripts/athena_report.py health 2>&1 | head -5

echo ""
echo "5️⃣  Waiting for speech..."
sleep 5

echo ""
echo "============================================================"
echo "✅ Diagnostic complete"
echo ""
echo "💡 Check the output above for:"
echo "   • ✅ VoiceDoctor: Samantha found..."
echo "   • 🔊 Athena: locked exact Samantha..."
echo "   • 🔊 Speaking with: Samantha..."
echo ""
echo "   If you see ❌ or any 'generic' mentions, Samantha isn't properly locked."

