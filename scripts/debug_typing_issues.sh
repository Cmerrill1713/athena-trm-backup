#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Athena SwiftUI Typing Issues Debugger"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "📋 Debugging Steps:"
echo ""

# 1. Test basic SwiftUI input capability
echo "1️⃣  Testing basic SwiftUI TextField functionality..."
echo ""

cat > /tmp/test_input.swift << 'EOF'
import SwiftUI

struct TestInput: View {
    @State private var text = ""
    @FocusState private var focused: Bool

    var body: some View {
        VStack(spacing: 20) {
            Text("🧪 Basic Input Test")
                .font(.title)

            TextField("Type here...", text: $text)
                .focused($focused)
                .textFieldStyle(.roundedBorder)
                .padding()
                .onAppear {
                    DispatchQueue.main.async { focused = true }
                }

            Text("Text: '\(text)'")
                .font(.system(.body, design: .monospaced))
        }
        .padding()
        .frame(width: 400, height: 300)
    }
}

@main
struct TestApp: App {
    var body: some Scene {
        WindowGroup {
            TestInput()
        }
        .windowStyle(.automatic)
        .windowToolbarStyle(.automatic)
    }
}
EOF

echo "   ✅ Created basic test input"

# 2. Check if Athena services are running
echo ""
echo "2️⃣  Checking Athena backend services..."

services=("9110" "8000" "9090" "3001" "9109" "9111")
backend_ok=true

for port in "${services[@]}"; do
    if curl -sf --max-time 2 "http://localhost:${port}/health" >/dev/null 2>&1; then
        echo -e "   ${GREEN}✅${NC} Service on port ${port}"
    else
        echo -e "   ${RED}❌${NC} Service on port ${port} not responding"
        backend_ok=false
    fi
done

if [ "$backend_ok" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Backend services not all running. Run:${NC}"
    echo "   make start"
    echo ""
fi

# 3. Check Swift build
echo ""
echo "3️⃣  Checking Swift build..."

cd NeuroForgeApp
if swift build >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅${NC} Swift build successful"
else
    echo -e "   ${RED}❌${NC} Swift build failed"
    echo "   Check Xcode console for errors"
fi
cd ..

# 4. Check if MCP server is running
echo ""
echo "4️⃣  Checking MCP server..."

if curl -sf --max-time 2 "http://localhost:3335/health" >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅${NC} MCP server running on port 3335"
else
    echo -e "   ${RED}❌${NC} MCP server not running"
    echo "   Run: cd SwiftUI_MCP_Modernization && python3 simple_crawl_server.py --port 3335 &"
fi

# 5. Create debugging checklist
echo ""
echo "🔧 Debugging Checklist:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ STEP 1: Test Basic Input"
echo "   • Open Xcode and run NeuroForgeApp"
echo "   • Navigate to chat view"
echo "   • Try typing in the input field"
echo ""
echo "❓ If typing doesn't work:"
echo "   • Uncomment 'ChatInputBar.knownGoodInput()' in NeuroForgeChatView.swift"
echo "   • Rebuild and run - does basic input work?"
echo ""
echo "❓ If basic input works but chat input doesn't:"
echo "   • The issue is in ChatInputBar implementation"
echo "   • Check overlays, ZStack, or gesture conflicts"
echo ""
echo "✅ STEP 2: UIKit Fallback Test"
echo "   • Uncomment the FirstResponderField in ChatInputBar.swift"
echo "   • Comment out the SwiftUI TextField"
echo "   • Rebuild and test - guaranteed focus should work"
echo ""
echo "✅ STEP 3: Hit Testing Debug"
echo "   • Uncomment .modifier(HitTestProbe()) in NeuroForgeChatView.swift"
echo "   • Run app and check console for tap messages"
echo "   • Red border should appear around input area"
echo ""
echo "✅ STEP 4: NavigationSplitView Issues"
echo "   • Check if input loses focus when switching tabs"
echo "   • Try stable .id() for input field"
echo "   • Add re-focus after selection changes"
echo ""
echo "✅ STEP 5: Common Culprits"
echo "   • Check for .disabled(true) on parent containers"
echo "   • Remove any full-screen overlays"
echo "   • Check .zIndex() values"
echo "   • Look for conflicting gestures"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "🎯 Quick Fix Options:"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Option A: Use UIKit fallback (guaranteed to work)"
echo "   • Uncomment FirstResponderField in ChatInputBar.swift"
echo "   • Comment out SwiftUI TextField"
echo ""
echo "Option B: Fix SwiftUI focus management"
echo "   • Ensure .focused() is directly on TextField"
echo "   • Remove any overlays that might block taps"
echo "   • Check for NavigationSplitView rebuild issues"
echo ""
echo "Option C: Debug step by step"
echo "   • Start with known-good input test"
echo "   • Add hit testing visualization"
echo "   • Isolate focus management"
echo ""

echo -e "${GREEN}🚀 Ready for debugging! Run Xcode and test the input field.${NC}"
