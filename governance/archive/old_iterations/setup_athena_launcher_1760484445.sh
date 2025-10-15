#!/bin/bash
#
# Athena Desktop Launcher Setup
# =============================
#
# Sets up desktop icons and taskbar shortcuts for Athena control
# Compatible with macOS
#

set -e

echo "🎯 Setting up Athena Desktop Launcher"
echo "===================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This setup script is for macOS only"
    exit 1
fi

# Function to check command success
check_command() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Working directory: $SCRIPT_DIR"

# 1. Make launcher script executable
echo
echo "1️⃣ Setting up launcher script..."
chmod +x "$SCRIPT_DIR/athena_launcher.sh"
check_command "Launcher script permissions"

# Test launcher script
echo "   Testing launcher script..."
"$SCRIPT_DIR/athena_launcher.sh" status > /dev/null 2>&1
check_command "Launcher script functionality"

# 2. Create AppleScript application
echo
echo "2️⃣ Creating AppleScript application..."

# Convert .scpt to .app using osacompile
if [ -f "$SCRIPT_DIR/Athena_Launcher.scpt" ]; then
    osacompile -o "$SCRIPT_DIR/Athena Launcher.app" "$SCRIPT_DIR/Athena_Launcher.scpt"
    check_command "AppleScript application creation"

    echo "   📍 Created: $SCRIPT_DIR/Athena Launcher.app"
else
    echo "⚠️ Athena_Launcher.scpt not found, skipping .app creation"
    echo "   You can create it manually in Script Editor"
fi

# 3. Install Quick Actions
echo
echo "3️⃣ Installing Quick Actions..."

QUICK_ACTIONS_DIR="$HOME/Library/Services"

# Create services directory if it doesn't exist
mkdir -p "$QUICK_ACTIONS_DIR"

# Install each Quick Action
quick_actions=("Start Athena Frontend" "Start Athena Backend" "Restart Athena" "Stop Athena")

for action in "${quick_actions[@]}"; do
    workflow_file="QuickAction_${action// /_}.workflow"
    if [ -d "$SCRIPT_DIR/$workflow_file" ]; then
        echo "   Installing: $action"
        cp -r "$SCRIPT_DIR/$workflow_file" "$QUICK_ACTIONS_DIR/"
        check_command "$action Quick Action installation"
    else
        echo "   ⚠️ $workflow_file not found, skipping $action"
    fi
done

# 4. Create desktop and dock shortcuts
echo
echo "4️⃣ Setting up desktop and dock shortcuts..."

DESKTOP_DIR="$HOME/Desktop"
DOCK_APP_PATH="$SCRIPT_DIR/Athena Launcher.app"

if [ -d "$DOCK_APP_PATH" ]; then
    # Create desktop alias
    if [ ! -e "$DESKTOP_DIR/Athena Launcher.app" ]; then
        ln -s "$DOCK_APP_PATH" "$DESKTOP_DIR/"
        echo "   ✅ Desktop shortcut created"
    else
        echo "   ℹ️ Desktop shortcut already exists"
    fi

    # Instructions for dock
    echo "   📌 To add to Dock: Drag '$DOCK_APP_PATH' to your Dock"
else
    echo "   ⚠️ Athena Launcher.app not found"
    echo "   Create it manually in Script Editor → File → Export → Application"
fi

# 5. Create custom icon (optional)
echo
echo "5️⃣ Custom icon setup (optional)..."

# Check if there's an icon file
if [ -f "$SCRIPT_DIR/athena_icon.icns" ] || [ -f "$SCRIPT_DIR/athena_icon.png" ]; then
    echo "   🎨 Custom icon found"
    if [ -d "$DOCK_APP_PATH" ]; then
        echo "   💡 To apply custom icon:"
        echo "      1. Right-click '$DOCK_APP_PATH'"
        echo "      2. Select 'Get Info'"
        echo "      3. Drag icon to the app icon in the top-left"
    fi
else
    echo "   ℹ️ No custom icon found (athena_icon.icns or athena_icon.png)"
    echo "   Add one to customize the launcher appearance"
fi

# 6. Final instructions
echo
echo "🎉 Athena Desktop Launcher Setup Complete!"
echo
echo "🚀 How to use:"
echo "   • Double-click desktop icon or dock icon for full restart"
echo "   • Right-click desktop icon or dock icon → Quick Actions:"
echo "     - Start Athena Frontend"
echo "     - Start Athena Backend"
echo "     - Restart Athena (full restart)"
echo "     - Stop Athena (safe shutdown)"
echo
echo "📊 Check status:"
echo "   ./athena_launcher.sh status"
echo
echo "🛠️ Manual commands:"
echo "   ./athena_launcher.sh frontend   # Start just UI"
echo "   ./athena_launcher.sh backend    # Start just services"
echo "   ./athena_launcher.sh restart    # Full restart"
echo "   ./athena_launcher.sh stop       # Stop all"
echo
echo "🎯 Everything is ready - zero terminal needed! 🎯"

# Final check
echo
echo "🔍 Running final verification..."
"$SCRIPT_DIR/athena_launcher.sh" status
echo
echo "✅ Setup verification complete!"
