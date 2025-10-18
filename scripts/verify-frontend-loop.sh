#!/bin/bash
# Frontend Verification Loop - Automated Build→Launch→Test
# Uses MCP Frontend Tools for repeatable verification

set -e

MCP_URL="http://localhost:8413"
PROJECT_PATH="/Users/christianmerrill/Documents/GitHub/NeuroForgeApp"
SCHEME="NeuroForgeApp"
BUNDLE_ID="com.neuroforge.NeuroForgeApp"

echo "🔄 Frontend Verification Loop"
echo "============================="
echo ""

# Check if MCP Frontend Tools is running
echo "📡 Checking MCP Frontend Tools..."
if ! curl -sf "$MCP_URL/health" > /dev/null 2>&1; then
    echo "⚠️  MCP Frontend Tools not running on port 8413"
    echo "   Starting service..."
    python3 services/mcp_frontend_tools.py > /tmp/mcp-frontend.log 2>&1 &
    sleep 3
    if ! curl -sf "$MCP_URL/health" > /dev/null 2>&1; then
        echo "❌ Failed to start MCP Frontend Tools"
        exit 1
    fi
fi
echo "✅ MCP Frontend Tools ready"
echo ""

# Run full verification
echo "🔨 Running frontend_verify..."
echo "   This will: build → launch → test typing"
echo ""

response=$(curl -sf -X POST "$MCP_URL/tool/frontend_verify" \
    -H 'Content-Type: application/json' \
    -d "{
        \"project_path\": \"$PROJECT_PATH\",
        \"scheme\": \"$SCHEME\",
        \"bundle_id\": \"$BUNDLE_ID\"
    }")

# Parse results
echo "$response" | jq .

build_ok=$(echo "$response" | jq -r '.build.success // false')
probe_ok=$(echo "$response" | jq -r '.probe.pass // false')
overall_ok=$(echo "$response" | jq -r '.overall // false')

echo ""
echo "================================"
echo "📊 Verification Results"
echo "================================"
echo "Build:  $([ "$build_ok" = "true" ] && echo "✅" || echo "❌")"
echo "Launch: $(echo "$response" | jq -r '.launch.success // false' | sed 's/true/✅/;s/false/❌/')"
echo "Probe:  $([ "$probe_ok" = "true" ] && echo "✅" || echo "❌")"
echo "Overall: $([ "$overall_ok" = "true" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "================================"
echo ""

if [ "$overall_ok" = "true" ]; then
    echo "✅ Frontend verification PASSED"
    echo "   Focus persists across sends"
    echo "   Typing is stable"
    echo "   Ready for production"
    exit 0
else
    echo "❌ Frontend verification FAILED"
    echo ""
    echo "Failure details:"
    echo "$response" | jq '.probe.iterations'
    echo ""
    echo "Next steps:"
    echo "  1. Check app behavior manually"
    echo "  2. Run: open -a Console (filter: com.neuroforge.athena)"
    echo "  3. Apply auto-fix: curl -X POST $MCP_URL/tool/swift_frontend_reflex"
    exit 1
fi

