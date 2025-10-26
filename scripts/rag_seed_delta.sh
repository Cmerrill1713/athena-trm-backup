#!/bin/bash
# Nightly RAG seed delta job (mtime-based incremental updates)
# Run via cron: 0 2 * * * /Users/christianmerrill/Documents/GitHub/scripts/rag_seed_delta.sh

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
DELTA_LOG="$LOG_DIR/rag_delta.log"
STATE_FILE="$SCRIPT_DIR/.rag_seed_state.json"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y91-%m-%d %H:%M:%S UTC') - Starting nightly RAG delta seed" >> "$DELTA_LOG"

cd "$SCRIPT_DIR"

# Check if Weaviate is ready
if ! curl -sf http://localhost:8090/v1/.well-known/ready >/dev/null 2>&1; then
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ❌ Weaviate not ready, skipping delta seed" >> "$DELTA_LOG"
    exit 0
fi

# Run incremental seed (only changed files since last run)
if make rag-seed >> "$DELTA_LOG" 2>&1; then
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ✅ RAG delta seed completed" >> "$DELTA_LOG"
    
    # Update state file timestamp
    echo '{"last_seed": "'$(date -u '+%Y-%m-%d %H:%M:%S')' UTC", "type": "delta"}' > "$STATE_FILE"
    
    # Run golden test to validate quality
    if make rag-golden >> "$DELTA_LOG" 2>&1; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ✅ Golden test passed after delta seed" >> "$DELTA_LOG"
    else
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ⚠️ Golden test failed after delta seed" >> "$DELTA_LOG"
    fi
else
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ❌ RAG delta seed failed" >> "$DELTA_LOG"
    exit 1
fi
