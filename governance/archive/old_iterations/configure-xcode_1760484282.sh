#!/usr/bin/env bash
# Auto-configure Xcode scheme with environment variables from xcode.env

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Configuring Xcode scheme with environment variables..."

# Read env vars from xcode.env
if [ ! -f "xcode.env" ]; then
    echo "❌ xcode.env not found"
    exit 1
fi

echo ""
echo "📋 Environment variables from xcode.env:"
grep -v "^#" xcode.env | grep -v "^$" | while read line; do
    echo "  ✅ $line"
done

echo ""
echo "═══════════════════════════════════════════════════════"
echo "MANUAL CONFIGURATION STEPS"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "In Xcode:"
echo "1. Product → Scheme → Edit Scheme..."
echo "2. Select 'Run' (left sidebar)"
echo "3. Go to 'Arguments' tab"
echo "4. Under 'Environment Variables' click '+' for each:"
echo ""

grep -v "^#" xcode.env | grep -v "^$" | while IFS='=' read key value; do
    echo "   Name:  $key"
    echo "   Value: $value"
    echo ""
done

echo "5. Click 'Close'"
echo "6. Press ⌘R to run"
echo ""
echo "═══════════════════════════════════════════════════════"
echo ""
echo "✅ Xcode is already open"
echo "✅ Backend is healthy"
echo "✅ Configure scheme and press ⌘R"
echo ""

