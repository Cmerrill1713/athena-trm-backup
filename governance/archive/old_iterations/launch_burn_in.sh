#!/bin/bash
# Athena Context Trigger - One-Liner Burn-In Launcher
# ====================================================
#
# START THE COMPLETE PRODUCTION BURN-IN SEQUENCE
#
# This script launches the fully automated burn-in process that will:
# 1. Run dry-run observation for 2 days
# 2. Enable tiered activation (meeting + travel modes)
# 3. Test emergency spike detection
# 4. Transition to full autonomous operation
#
# The system monitors itself, handles failures, and provides rollback.
#
# Usage: ./launch_burn_in.sh
#
# Control:
#   Status: python3 burn_in_launcher.py --status
#   Stop:   python3 burn_in_launcher.py --stop
#   Report: python3 burn_in_launcher.py --report

set -e

echo "🚀 Athena Context Trigger Burn-In Launcher"
echo "==========================================="
echo ""
echo "This will start the complete automated burn-in sequence:"
echo "• Phase 1: Dry-run observation (2 days)"
echo "• Phase 2: Tiered activation (Day 3)"
echo "• Phase 3: Spike detection testing (Day 4)"
echo "• Phase 4: Full autonomous operation (Day 5+)"
echo ""
echo "🛡️ Safety features:"
echo "• Automatic health monitoring"
echo "• Emergency rollback capability"
echo "• Comprehensive logging and reporting"
echo "• Voice diagnostics available throughout"
echo ""
echo "🎯 Control commands:"
echo "  Check status: python3 burn_in_launcher.py --status"
echo "  Emergency stop: python3 burn_in_launcher.py --stop"
echo "  View reports: python3 burn_in_launcher.py --report"
echo ""

# Confirm before starting
read -p "Start the complete burn-in sequence? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Burn-in cancelled."
    exit 1
fi

echo "🔥 Starting Athena burn-in sequence..."
echo "Process will run in background. Monitor with: python3 burn_in_launcher.py --status"
echo ""

# Launch the burn-in sequence
nohup python3 burn_in_launcher.py > /tmp/athena_burn_in_launcher.log 2>&1 &

# Save the PID for potential cleanup
echo $! > /tmp/athena_burn_in_launcher.pid

echo "✅ Burn-in launcher started (PID: $(cat /tmp/athena_burn_in_launcher.pid))"
echo "📊 Initial status:"
python3 burn_in_launcher.py --status
echo ""
echo "🎉 Burn-in is now running autonomously!"
echo "   Check progress anytime with: python3 burn_in_launcher.py --status"
