#!/bin/bash

# AI REPUBLIC CLI DASHBOARD INSTALLATION
# Installs the interactive operations dashboard

set -e

echo "🤖 Installing AI Republic Operations Dashboard..."

# Copy CLI tool
sudo cp ai_republic_cli.py /opt/ai-republic/
sudo chmod +x /opt/ai-republic/ai_republic_cli.py

# Copy systemd service
sudo cp ai_republic_cli.service /etc/systemd/system/

# Create alias for easy access
if ! grep -q "alias ai-republic=" ~/.bashrc 2>/dev/null; then
    echo "alias ai-republic='python3 /opt/ai-republic/ai_republic_cli.py'" >> ~/.bashrc
    echo "alias ai-ops='python3 /opt/ai-republic/ai_republic_cli.py --mode interactive'" >> ~/.bashrc
    echo "alias ai-check='python3 /opt/ai-republic/ai_republic_cli.py --mode check'" >> ~/.bashrc
fi

# Create desktop shortcut (if desktop environment exists)
if [ -d ~/Desktop ]; then
    cat > ~/Desktop/ai-republic-dashboard.desktop << 'EOF'
[Desktop Entry]
Name=AI Republic Dashboard
Comment=Constitutional AI Governance Operations
Exec=python3 /opt/ai-republic/ai_republic_cli.py --mode interactive
Icon=utilities-terminal
Terminal=true
Type=Application
Categories=System;Monitor;
EOF
    chmod +x ~/Desktop/ai-republic-dashboard.desktop
fi

echo "✅ AI Republic CLI Dashboard installed!"
echo ""
echo "Usage:"
echo "  ai-republic                    # Launch interactive dashboard"
echo "  ai-ops                         # Same as above (shorter alias)"
echo "  ai-check                       # Quick health check (exit code based)"
echo "  ai-republic --mode auto        # Auto-monitoring mode"
echo ""
echo "Desktop shortcut created (if desktop environment detected)"
echo "Run 'source ~/.bashrc' to activate aliases"
