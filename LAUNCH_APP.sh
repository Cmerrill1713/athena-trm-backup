#!/bin/bash
# Launch NeuroForge Modern UI

set -e

echo "🚀 Launching NeuroForge with Modern UI"
echo "======================================"
echo ""

# Check if Xcode is available
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode not found. Please run from Xcode:"
    echo "   1. Open NeuroForgeApp/Package.swift in Xcode"
    echo "   2. Product → Scheme → Edit Scheme"
    echo "   3. Add FEATURE_MODERN_UI=1 to Environment Variables"
    echo "   4. Press ⌘R"
    exit 1
fi

cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp

echo "📦 Building app..."
xcodebuild -scheme NeuroForgeApp -configuration Debug build

echo ""
echo "✅ Build complete!"
echo ""
echo "🎯 To launch with Modern UI:"
echo "   1. Open in Xcode: open Package.swift"
echo "   2. Product → Scheme → Edit Scheme"
echo "   3. Run → Environment Variables → Add:"
echo "      FEATURE_MODERN_UI = 1"
echo "   4. Press ⌘R"
echo ""
echo "Or just press ⌘R if you already set the environment variable!"

