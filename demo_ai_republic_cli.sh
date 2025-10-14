#!/bin/bash

# AI REPUBLIC CLI DASHBOARD DEMO
# Demonstrates the interactive operations dashboard

echo "🤖 AI REPUBLIC CLI DASHBOARD DEMO"
echo "=================================="
echo ""

# Check if CLI is installed
if [ ! -f "/opt/ai-republic/ai_republic_cli.py" ]; then
    echo "❌ AI Republic CLI not found. Please run installation first:"
    echo "   sudo ./install_ai_republic_cli.sh"
    exit 1
fi

echo "✅ AI Republic CLI detected"
echo ""

# Demo 1: Health Check Mode
echo "📊 DEMO 1: Health Check Mode"
echo "----------------------------"
echo "Command: python3 /opt/ai-republic/ai_republic_cli.py --mode check"
echo ""
echo "Output:"
python3 /opt/ai-republic/ai_republic_cli.py --mode check 2>/dev/null || echo "(System not fully deployed - showing demo output)"
echo ""

# Demo 2: Auto-Monitor Mode (brief)
echo "📈 DEMO 2: Auto-Monitor Mode (5-second demo)"
echo "---------------------------------------------"
echo "Command: timeout 8 python3 /opt/ai-republic/ai_republic_cli.py --mode auto --interval 2"
echo ""
echo "Starting auto-monitor for 8 seconds..."
timeout 8 python3 /opt/ai-republic/ai_republic_cli.py --mode auto --interval 2 2>/dev/null || echo "(System not deployed - auto-monitor would show real-time status updates)"
echo ""

# Demo 3: Interactive Mode Help
echo "🎮 DEMO 3: Interactive Mode Commands"
echo "------------------------------------"
echo "Available commands in interactive mode:"
echo "  [c]heck   - Run immediate health check"
echo "  [t]ribunal- Handle tribunal alerts interactively"
echo "  [l]ogs    - View detailed system logs"
echo "  [r]estart - Restart all AI Republic services"
echo "  [q]uit    - Exit dashboard"
echo ""

# Demo 4: Installation Verification
echo "✅ DEMO 4: Installation Verification"
echo "------------------------------------"
echo "Checking installed components:"

check_file() {
    if [ -f "$1" ]; then
        echo "  ✅ $2"
    else
        echo "  ❌ $2 (missing: $1)"
    fi
}

check_file "/opt/ai-republic/ai_republic_cli.py" "CLI Dashboard"
check_file "/etc/systemd/system/ai-republic-cli.service" "Systemd Service"
check_file "/opt/ai-republic/phase1_constitutional_runtime.py" "Constitutional Runtime"
check_file "/opt/ai-republic/phase2/phase2_judicial_runtime.py" "Judicial System"
check_file "AI_REPUBLIC_CLI_README.md" "Documentation"

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Deploy AI Republic core system (Phase 1 + 2)"
echo "2. Install CLI dashboard: sudo ./install_ai_republic_cli.sh"
echo "3. Run interactive dashboard: ai-ops"
echo "4. Optional: Enable federation (Phase 3)"
echo ""

echo "📖 For full documentation, see:"
echo "   AI_REPUBLIC_CLI_README.md - Complete CLI guide"
echo "   AI_REPUBLIC_FINAL_REFERENCE.md - Full operations reference"
echo "   AI_REPUBLIC_CHEAT_SHEET.md - Quick daily operations"
echo ""

echo "🏛️ AI Republic CLI Dashboard Demo Complete! 🤖⚖️"
