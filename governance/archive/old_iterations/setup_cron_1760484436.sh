#!/bin/bash
# Setup Athena Automation Cron Jobs

echo "🔄 Setting up Athena automation cron jobs"
echo "=========================================="
echo ""

GITHUB_DIR="$HOME/Documents/GitHub"

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Create new crontab entries
CRON_ENTRIES="
# Athena Automation
# Generated: $(date)

# Auto-rollback check (every 5 min)
*/5 * * * * cd $GITHUB_DIR && make auto-rollback >> logs/rollback.log 2>&1

# Nightly evolution (2 AM)
0 2 * * * cd $GITHUB_DIR && make learn DAYS=7 >> logs/evolution.log 2>&1

# Daily backup (3 AM)
0 3 * * * cd $GITHUB_DIR && make pg-backup >> logs/backup.log 2>&1

# Weekly autopilot report (Monday 9 AM)
0 9 * * 1 cd $GITHUB_DIR && make weekly-autopilot >> logs/weekly.log 2>&1

# Daily health report (Weekdays 9 AM)
0 9 * * 1-5 cd $GITHUB_DIR && make report-health >> logs/daily_health.log 2>&1
"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "# Athena Automation" | grep -v "auto-rollback" | grep -v "weekly-autopilot" | grep -v "pg-backup"; echo "$CRON_ENTRIES") | crontab -

echo "✅ Cron jobs installed"
echo ""
echo "📋 Installed jobs:"
crontab -l | grep -A 20 "# Athena Automation"
echo ""
echo "📁 Create log directories:"
mkdir -p logs
echo "✅ logs/ directory ready"
echo ""
echo "🔍 Verify cron with:"
echo "   crontab -l | grep Athena"
echo ""
echo "📊 Monitor logs:"
echo "   tail -f logs/rollback.log"
echo "   tail -f logs/evolution.log"
echo "   tail -f logs/backup.log"
echo "   tail -f logs/weekly.log"

