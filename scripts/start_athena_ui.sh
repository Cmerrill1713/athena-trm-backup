#!/usr/bin/env bash
set -euo pipefail

echo "🎨 Starting Athena Swift UI..."
echo ""

# Check if backend is running
echo "🔍 Checking backend services..."
if ! curl -sf http://localhost:9110/health >/dev/null 2>&1; then
    echo "❌ Backend not running!"
    echo ""
    echo "Starting backend first..."
    ./scripts/start_athena.sh
    echo ""
fi

echo "✅ Backend running"
echo ""

# Open in Xcode
echo "🚀 Opening NeuroForgeApp in Xcode..."
cd NeuroForgeApp
open -a Xcode Package.swift || open -a Xcode .

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Wait for Xcode indexing (~30 seconds)"
echo "2. Select 'My Mac' target (top toolbar)"
echo "3. Press ⌘R or click ▶️  Play button"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 WHAT YOU'LL SEE:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Live Governance Dashboard"
echo "   • ECE gauge (current: real-time)"
echo "   • Entropy monitor"
echo "   • Verdict counters (5m window)"
echo "   • Active alerts"
echo ""
echo "✅ Mode Switcher"
echo "   • Shadow (current)"
echo "   • Canary"
echo "   • Enforce"
echo ""
echo "✅ Verdict Form"
echo "   • Submit test verdicts"
echo "   • See immediate response"
echo ""
echo "✅ Recent Receipts"
echo "   • Live traffic feed"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 TIP: Keep Xcode open for hot reload during development"
echo ""

