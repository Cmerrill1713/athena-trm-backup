#!/usr/bin/env bash
# Creates encrypted snapshot of bandit + telemetry
# Requires BACKUP_PASSPHRASE in env
# Produces ./releases/backups/backup-YYYYmmdd-HHMM.tar.gz.enc
set -euo pipefail

PASS="${BACKUP_PASSPHRASE:?Set BACKUP_PASSPHRASE environment variable}"
OUT_DIR="${OUT_DIR:-./releases/backups}"
mkdir -p "$OUT_DIR"
STAMP=$(date +%Y%m%d-%H%M)
TMP="backup-$STAMP.tar.gz"
ENC="$OUT_DIR/$TMP.enc"

echo "🔐 Creating encrypted snapshot..."
echo "   Timestamp: $STAMP"

cd "$(dirname "$0")/.."

# Create tar (include both files if they exist)
if [ -f "state/telemetry.sqlite" ]; then
    tar -czf "$TMP" -C state bandit.json telemetry.sqlite 2>/dev/null || \
    tar -czf "$TMP" -C state bandit.json 2>/dev/null
else
    tar -czf "$TMP" -C state bandit.json 2>/dev/null || {
        echo "❌ No state files to backup"
        exit 1
    }
fi

# Encrypt with AES-256
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$TMP" -out "$ENC" -pass env:BACKUP_PASSPHRASE

# Cleanup temp tar
rm -f "$TMP"

echo "✅ Encrypted backup created: $ENC"
echo "   Size: $(du -h "$ENC" | awk '{print $1}')"
