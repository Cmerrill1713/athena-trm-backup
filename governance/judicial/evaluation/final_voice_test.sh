#!/bin/bash
# Final Voice Sentinel Test - Definitive proof

echo "🎯 FINAL VOICE SENTINEL TEST"
echo "============================="
echo ""

echo "STEP 1: OS-Level Check"
echo "----------------------"
say -v '?' | grep -i 'samantha'
echo ""
echo "Testing OS-level Samantha:"
say -v "Samantha" "OS level Samantha verification."
echo "✅ Complete (listen - should be natural female voice)"
echo ""

echo "STEP 2: Isolated Swift Test"
echo "---------------------------"
echo "Testing Samantha outside the app:"
./VoiceProof
echo ""

echo "STEP 3: Kill & Rebuild"
echo "----------------------"
pkill -9 AthenaReporter 2>/dev/null && echo "Killed old instances" || echo "No instances running"
make reporter-build 2>&1 | tail -1
echo ""

echo "STEP 4: Launch with Logging"
echo "---------------------------"
rm -f /tmp/athena_voice_log.txt
build/AthenaReporter.app/Contents/MacOS/AthenaReporter > /tmp/athena_voice_log.txt 2>&1 &
APP_PID=$!
echo "App PID: $APP_PID"
sleep 3
echo ""

echo "STEP 5: Trigger Speech"
echo "---------------------"
ATHENA_VERBOSITY=brief python3 scripts/athena_report.py health 2>&1 | head -4
sleep 3
echo ""

echo "STEP 6: Check Logs for PROOF"
echo "-----------------------------"
echo "Looking for Voice Sentinel logs..."
cat /tmp/athena_voice_log.txt | grep -E "(🔊 Locked|🎙️|didStart|MATCH|MISMATCH|🚨)"
echo ""

echo "STEP 7: Verification"
echo "--------------------"
echo "✅ Expected logs:"
echo "   • 🔊 Locked voice by name: Samantha [...] q=1"
echo "   • 🎙️  Queueing with Samantha [...]"
echo "   • ✅ didStart with Samantha [...] MATCH"
echo ""
echo "❌ If you see:"
echo "   • ⚠️  didStart with [OTHER] [...] MISMATCH"
echo "   • 🚨 VOICE MISMATCH – stopped playback."
echo "   Then the voice mismatch detection is working!"
echo ""
echo "🎧 LISTEN TEST:"
echo "   Did you hear Samantha (natural female) or generic (robotic)?"

