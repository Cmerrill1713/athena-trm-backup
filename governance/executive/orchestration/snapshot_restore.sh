#!/usr/bin/env bash
# Restore from an encrypted backup file into orchestrator/state
# Usage: BACKUP_PASSPHRASE=... snapshot_restore.sh ./releases/backups/backup-*.tar.gz.enc
set -euo pipefail

PASS="${BACKUP_PASSPHRASE:?Set BACKUP_PASSPHRASE environment variable}"
ENC="${1:?Provide encrypted backup path}"
TMP="restore-$(date +%s).tar.gz"

echo "🔓 Restoring from encrypted snapshot..."
echo "   Source: $ENC"

cd "$(dirname "$0")/.."

# Decrypt
openssl enc -d -aes-256-cbc -pbkdf2 -in "$ENC" -out "$TMP" -pass env:BACKUP_PASSPHRASE

# Extract
mkdir -p state
tar -xzf "$TMP" -C state || {
    echo "❌ Failed to extract backup"
    rm -f "$TMP"
    exit 1
}

# Cleanup temp tar
rm -f "$TMP"

echo "✅ Snapshot restored to orchestrator/state/"
ls -lh state/bandit.json state/telemetry.sqlite 2>/dev/null || true
