#!/bin/bash
#
# Quick Setup for Athena Frontend Demo
#

set -e

echo "🚀 Quick Athena Frontend Setup"

# Create Python venv if needed
if [ ! -d ".venv" ]; then
    echo "🐍 Setting up Python environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install psutil
else
    source .venv/bin/activate
fi

# Change to NeuroForgeApp directory
cd NeuroForgeApp

echo "🏗️ Building SwiftUI app..."
xcodebuild -project NeuroForgeApp.xcodeproj -scheme NeuroForgeApp -configuration Release -destination 'platform=macOS' build

echo "📱 Finding built app..."
APP_PATH=$(find build -name "*.app" -type d | head -1)
if [ -z "$APP_PATH" ]; then
    echo "❌ Could not find built app"
    exit 1
fi

echo "✅ App built at: $APP_PATH"

echo "🚀 Launching app with pop-out windows..."
POPUPS_ENABLED=1 AUTOEXEC_GUARD=1 open -n "$APP_PATH"

echo "🧪 Running pop-out window demo..."
sleep 2
cd ..
python demo_athena_popouts.py --smoke

echo "🎉 Setup complete!"
echo ""
echo "You should see three pop-out windows with the demo!"
