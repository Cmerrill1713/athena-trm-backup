#!/usr/bin/env bash
# Setup Nightly Learning - Install cron job for autonomous evolution

set -euo pipefail

WORKSPACE="/Users/christianmerrill/Documents/GitHub"
CRON_TIME="0 2 * * *"  # 2:00 AM daily
LOG_DIR="$WORKSPACE/logs"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Setup Nightly Learning (Cron Job)                     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Create logs directory
mkdir -p "$LOG_DIR"

# Build cron command
CRON_CMD="cd $WORKSPACE && make learn DAYS=7 >> $LOG_DIR/evolution.log 2>&1"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "make learn"; then
    echo "⚠️  Nightly learning cron job already exists"
    echo ""
    echo "Current entry:"
    crontab -l | grep "make learn"
    echo ""
    read -p "Replace it? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing entry"
        exit 0
    fi
    
    # Remove old entry
    crontab -l | grep -v "make learn" | crontab -
fi

# Add new entry
(crontab -l 2>/dev/null; echo "$CRON_TIME $CRON_CMD") | crontab -

echo "✅ Nightly learning installed!"
echo ""
echo "📅 Schedule: Every day at 2:00 AM"
echo "📁 Logs:     $LOG_DIR/evolution.log"
echo "🔧 Command:  make learn DAYS=7"
echo ""
echo "Verify installation:"
echo "  crontab -l | grep learn"
echo ""
echo "View logs:"
echo "  tail -f $LOG_DIR/evolution.log"
echo ""
echo "Remove:"
echo "  crontab -l | grep -v 'make learn' | crontab -"
echo ""

