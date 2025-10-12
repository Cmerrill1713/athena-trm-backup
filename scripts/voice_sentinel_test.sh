#!/bin/bash
# Voice Sentinel Verification - Complete diagnostic with proof

echo "🔬 Voice Sentinel Test"
echo "======================"
echo ""

echo "STEP 1: OS-Level Truth Check"
echo "-----------------------------"
echo "Available Samantha:"
say -v '?' | grep -i 'samantha'
echo ""

echo "OS-level test (listen for Samantha):"
say -v "Samantha" "Samantha system voice verification."
echo "Exit code: $?"
echo ""

echo "STEP 2: Kill Old Instances"
echo "---------------------------"
pkill -9 AthenaReporter 2>/dev/null && echo "✅ Killed old instances" || echo "ℹ️  No instances running"
sleep 1
echo ""

echo "STEP 3: Rebuild with Voice Sentinel"
echo "------------------------------------"
make reporter-build 2>&1 | tail -2
echo ""

echo "STEP 4: Launch App with Console Output"
echo "---------------------------------------"
echo "Launching app (check for delegate logs)..."
build/AthenaReporter.app/Contents/MacOS/AthenaReporter > /tmp/athena_voice_log.txt 2>&1 &
APP_PID=$!
echo "App PID: $APP_PID"
echo "Logs: /tmp/athena_voice_log.txt"
sleep 3
echo ""

echo "STEP 5: Trigger Speech"
echo "----------------------"
ATHENA_VERBOSITY=brief python3 scripts/athena_report.py health 2>&1 | head -5
sleep 3
echo ""

echo "STEP 6: Check Logs for Proof"
echo "-----------------------------"
echo "Looking for delegate verification..."
cat /tmp/athena_voice_log.txt | grep -E "(🔎|✅|❌|🔊|🎙️|didStart|didFinish)" || echo "⚠️  No logs captured (app might be sandboxed)"
echo ""

echo "STEP 7: Final Verification Checklist"
echo "-------------------------------------"
echo "Expected log lines:"
echo "  ✅ Found Samantha: ..."
echo "  🔊 Athena: locked by name ..."
echo "  🎙️  Queueing with Samantha [...]"
echo "  ✅ didStart with Samantha [...] matches_preferred=true"
echo ""
echo "🎧 LISTEN TEST: Did you hear Samantha's voice or generic?"
echo "   • Samantha = smooth, natural female voice"
echo "   • Generic = monotone, robotic"
echo ""
echo "💡 If you saw ⚠️ or 'matches_preferred=false', voice mismatch detected!"

