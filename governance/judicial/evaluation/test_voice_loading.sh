#!/bin/bash
# Test voice loading in Athena Reporter

echo "🎤 Testing Athena Voice Loading"
echo "================================"
echo ""

echo "1️⃣  Voice ID file:"
if [ -f ~/.athena/voice.id ]; then
    cat ~/.athena/voice.id
else
    echo "   ❌ Not found"
fi
echo ""

echo "2️⃣  Voice name file:"
if [ -f ~/.athena/voice.name ]; then
    cat ~/.athena/voice.name
else
    echo "   ❌ Not found"
fi
echo ""

echo "3️⃣  Testing voice with 'say' command:"
if [ -f ~/.athena/voice.name ]; then
    VOICE=$(cat ~/.athena/voice.name)
    echo "   Testing: $VOICE"
    say -v "$VOICE" "This is Athena. Testing voice quality."
else
    echo "   ❌ Cannot test - no voice.name file"
fi
echo ""

echo "4️⃣  Generating a test report to trigger the app:"
echo "   (Listen for the voice and check Console.app for logs)"
ATHENA_VERBOSITY=brief python3 scripts/athena_report.py health

