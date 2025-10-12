#!/bin/bash
set -e

echo "📦 Backing up UAT traces..."
echo "============================"
echo ""

BACKUP_DIR="data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/uat_traces_$TIMESTAMP.json"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Fetch traces from UAT
echo "Fetching traces from UAT..."
curl -s -H "Authorization: Bearer ${UAT_TOKEN:-supersecret}" \
  http://127.0.0.1:8181/traces > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    TRACE_COUNT=$(jq '.traces | length' "$BACKUP_FILE" 2>/dev/null || echo "0")
    echo "✅ Backed up $TRACE_COUNT traces to $BACKUP_FILE"

    # Create symlink to latest
    ln -sf "$(basename $BACKUP_FILE)" "$BACKUP_DIR/latest.json"
    echo "✅ Updated latest backup symlink"

    # Clean up old backups (keep last 10)
    ls -t "$BACKUP_DIR"/uat_traces_*.json | tail -n +11 | xargs -r rm
    echo "✅ Cleaned up old backups (keeping last 10)"
else
    echo "❌ Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo ""
echo "📊 Backup Summary:"
echo "   File: $BACKUP_FILE"
echo "   Traces: $TRACE_COUNT"
echo "   Size: $(du -h $BACKUP_FILE | cut -f1)"
echo ""
