#!/bin/bash
# Test voice with console logging

echo "🧪 Testing Athena Voice (with logs)"
echo "===================================="
echo ""

# Kill any running instances
pkill -9 AthenaReporter 2>/dev/null
sleep 0.5

echo "1️⃣  Launching app and capturing logs..."
echo ""

# Launch the app directly (not via open) so we see stdout
build/AthenaReporter.app/Contents/MacOS/AthenaReporter &
APP_PID=$!

# Give it time to initialize
sleep 2

echo "2️⃣  App launched (PID: $APP_PID)"
echo ""

echo "3️⃣  Generating test report..."
ATHENA_VERBOSITY=brief python3 scripts/athena_report.py health 2>&1 | grep -E "(Synopsis|Opening)" | head -2

echo ""
echo "4️⃣  Check the voice above - it should be Samantha, NOT generic!"
echo ""
echo "💡 To see app logs in real-time:"
echo "   tail -f /tmp/athena_reporter.log"
echo ""
echo "   Or open Console.app and filter for 'AthenaReporter'"

