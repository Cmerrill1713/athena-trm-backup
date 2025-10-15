#!/usr/bin/env bash
# PostgreSQL Backup Script

set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL}"

STAMP=$(date +%Y%m%d-%H%M%S)
OUT="backups/pg-${STAMP}.sql.zst"

echo "📦 Backing up PostgreSQL database..."
echo "   Timestamp: $STAMP"

# Create backups directory
mkdir -p backups

# Dump using Docker container's pg_dump (version-matched)
docker exec athena-postgres pg_dump -U postgres athena_db | zstd -q -T0 -o "$OUT"

SIZE=$(du -h "$OUT" | cut -f1)
echo "✅ Wrote $OUT ($SIZE)"

# Keep only last 30 backups
echo "🗑️  Cleaning old backups (keeping last 30)..."
ls -t backups/pg-*.sql.zst | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "✅ Backup complete"

