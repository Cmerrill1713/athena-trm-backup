#!/bin/bash
set -euo pipefail
ROOT="${1:-./governance_data}"
RECEIPTS_DAYS="${RECEIPTS_DAYS:-14}"
LOGS_DAYS="${LOGS_DAYS:-7}"
SNAPSHOTS_DAYS="${SNAPSHOTS_DAYS:-5}"
MAX_HOT_RECEIPTS_GB="${MAX_HOT_RECEIPTS_GB:-50}"

mkdir -p "$ROOT"/{receipts,logs,snapshots,archive}

find "$ROOT/receipts" -type f -mtime +$RECEIPTS_DAYS -print -delete 2>/dev/null || true
find "$ROOT/logs" -type f -mtime +$LOGS_DAYS -print -delete 2>/dev/null || true
find "$ROOT/snapshots" -type f -mtime +$SNAPSHOTS_DAYS -print -delete 2>/dev/null || true

# compress older receipts
find "$ROOT/receipts" -type f -mtime +2 -name "*.json" -exec zstd -T0 -f --rm "{}" \; 2>/dev/null || true

size_gb=$(du -s "$ROOT/receipts" 2>/dev/null | awk '{print $1/1024/1024}'); size_gb=${size_gb:-0}
echo "[retention] receipts hot size ≈ ${size_gb} GB (cap ${MAX_HOT_RECEIPTS_GB})"
if (( ${size_gb%.*} > MAX_HOT_RECEIPTS_GB )); then
  find "$ROOT/receipts" -type f -printf "%T@ %p\n" | sort -n | head -n 500 | awk "{print \$2}" | \
    while read -r f; do zstd -T0 -f --rm "$f" -o "$ROOT/archive/$(basename "$f").zst"; done
fi
echo "[retention] done."
