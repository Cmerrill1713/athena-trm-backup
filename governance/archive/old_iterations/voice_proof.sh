#!/bin/bash
# Get definitive proof of which voice is being used

echo "🔬 Voice Proof Test"
echo "==================="
echo ""

echo "📋 What macOS says is available:"
say -v '?' | grep -i 'samantha'
echo ""

echo "🗣️  OS-level test (this MUST sound like Samantha):"
say -v "Samantha" "This is Athena using the Samantha voice at the OS level." && echo "✅ OS test complete"
echo ""

echo "📱 Checking what Swift sees..."
swift test_voice.swift 2>&1 | grep -E "(Found|Using|Speaking)" | head -5
echo ""

echo "🎯 Quick app test:"
echo "   1. Kill old instances"
pkill -9 AthenaReporter 2>/dev/null
sleep 0.5

echo "   2. Build fresh"
make reporter-build 2>&1 | tail -1

echo "   3. Launch and trigger"
make test-voice 2>&1 | head -10

echo ""
echo "💡 Listen carefully to the voice quality"
echo "   • Generic voice = monotone, robotic"
echo "   • Samantha = smooth, natural, female"

