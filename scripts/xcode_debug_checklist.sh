#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Xcode Debug View Hierarchy Checklist"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "📋 Xcode Debug Steps (⌘7 in running app):"
echo ""

echo "1️⃣  Debug View Hierarchy (⌘7)"
echo "   • Navigate to chat screen in running app"
echo "   • Press ⌘7 to open Debug View Hierarchy"
echo "   • Look for layers ABOVE the TextField:"
echo "     - Overlays, full-screen colors, ProgressView"
echo "     - Material backgrounds, .thinMaterial, etc."
echo "     - Any view with .zIndex() higher than input"
echo ""
echo -e "${YELLOW}   🔍 Look for:${NC}"
echo "   • Any view between you and the TextField"
echo "   • Semi-transparent overlays"
echo "   • Progress indicators or loading states"
echo "   • Full-screen background colors"
echo ""

echo "2️⃣  Check Hit Testing"
echo "   • Click around the input area in Debug View"
echo "   • Red highlight should appear on TextField"
echo "   • If highlight appears on parent/overlay: that's blocking"
echo ""

echo "3️⃣  Check Z-Index Order"
echo "   • In Debug View, check layer order"
echo "   • Input should be at top (.zIndex(10))"
echo "   • Overlays should be lower (.zIndex(0))"
echo ""

echo "4️⃣  Check Safe Areas"
echo "   • Look for keyboard insets pushing content"
echo "   • Check if .ignoresSafeArea(.keyboard) is applied"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "🎯 If You Find Blocking Layers:"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Fix A: Add .allowsHitTesting(false) to overlays"
echo "Fix B: Lower .zIndex() on non-interactive layers"
echo "Fix C: Move overlays below input in ZStack"
echo "Fix D: Remove unnecessary full-screen backgrounds"
echo ""

echo -e "${GREEN}🚀 Next: Run the fixes and test again!${NC}"
