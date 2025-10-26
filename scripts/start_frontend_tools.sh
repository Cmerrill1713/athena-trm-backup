#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🔧 Starting MCP Frontend Tools"
echo "════════════════════════════════════════════════════════════════"

# Check dependencies
echo -n "Checking Python dependencies... "
python3 -c "import fastapi, uvicorn, pydantic, prometheus_client" 2>/dev/null || {
    echo "❌ MISSING"
    echo ""
    echo "Install with:"
    echo "  pip3 install fastapi uvicorn pydantic prometheus-client"
    exit 1
}
echo "✅"

# Check Xcode
echo -n "Checking Xcode... "
if command -v xcodebuild >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌ MISSING"
    echo "Install Xcode from App Store"
    exit 1
fi

# Check NeuroForgeApp
echo -n "Checking NeuroForgeApp... "
if [ -d "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp" ]; then
    echo "✅"
else
    echo "❌ NOT FOUND"
    exit 1
fi

echo ""
echo "Starting frontend tools on port 8413..."
echo ""
echo "Press Ctrl+C to stop"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /Users/christianmerrill/Documents/GitHub
python3 services/mcp_frontend_tools.py
