#!/usr/bin/env bash
# Setup Auto-Promotion - Install cron job for automatic canary promotion

set -euo pipefail

WORKSPACE="/Users/christianmerrill/Documents/GitHub"
CRON_TIME="0 */6 * * *"  # Every 6 hours
LOG_DIR="$WORKSPACE/logs"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Setup Auto-Promotion (Cron Job)                       ║"
echo "║           Stat-Sig Canary → Control Every 6 Hours              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Create logs directory
mkdir -p "$LOG_DIR"

# Build cron command
CRON_CMD="cd $WORKSPACE && make canary-auto-promote >> $LOG_DIR/auto_promotion.log 2>&1"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "canary-auto-promote"; then
    echo "⚠️  Auto-promotion cron job already exists"
    echo ""
    echo "Current entry:"
    crontab -l | grep "canary-auto-promote"
    echo ""
    read -p "Replace it? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing entry"
        exit 0
    fi
    
    # Remove old entry
    crontab -l | grep -v "canary-auto-promote" | crontab -
fi

# Add new entry
(crontab -l 2>/dev/null; echo "$CRON_TIME $CRON_CMD") | crontab -

echo "✅ Auto-promotion installed!"
echo ""
echo "📅 Schedule: Every 6 hours"
echo "📁 Logs:     $LOG_DIR/auto_promotion.log"
echo "🔧 Command:  make canary-auto-promote"
echo ""
echo "🎯 Promotion Criteria:"
echo "   • Canary statistically better (p<0.05)"
echo "   • Improvement >3%"
echo "   • Sustained for 48 hours"
echo "   • Sample size ≥50 each"
echo ""
echo "Verify installation:"
echo "  crontab -l | grep canary"
echo ""
echo "View logs:"
echo "  tail -f $LOG_DIR/auto_promotion.log"
echo ""
echo "Remove:"
echo "  crontab -l | grep -v 'canary-auto-promote' | crontab -"
echo ""

