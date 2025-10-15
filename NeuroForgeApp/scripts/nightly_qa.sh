#!/usr/bin/env bash
# Nightly QA sweep - runs complete validation and archives artifacts
set -euo pipefail

REPO_ROOT="/Users/christianmerrill/Documents/GitHub"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/tmp/neuroforge_qa"
LOG_FILE="$LOG_DIR/qa_${TIMESTAMP}.log"

# Create log directory
mkdir -p "$LOG_DIR"

echo "🌙 Nightly QA Sweep - $TIMESTAMP" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"

# Navigate to NeuroForgeApp
cd "$REPO_ROOT/NeuroForgeApp" || exit 1

# Run complete QA sweep
if make qa 2>&1 | tee -a "$LOG_FILE"; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ Nightly QA PASSED - All green!" | tee -a "$LOG_FILE"

    # Archive artifacts with timestamp
    mkdir -p "$LOG_DIR/artifacts"
    cp -r artifacts/* "$LOG_DIR/artifacts/" 2>/dev/null || true
    cp UITests/Golden/Actual/* "$LOG_DIR/artifacts/" 2>/dev/null || true

    # Create summary
    echo "📊 Summary:" | tee -a "$LOG_FILE"
    echo "  - Timestamp: $TIMESTAMP" | tee -a "$LOG_FILE"
    echo "  - Status: PASSED ✅" | tee -a "$LOG_FILE"
    echo "  - Artifacts: $LOG_DIR/artifacts/" | tee -a "$LOG_FILE"
    echo "  - Log: $LOG_FILE" | tee -a "$LOG_FILE"

    exit 0
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ Nightly QA FAILED" | tee -a "$LOG_FILE"
    echo "Check logs: $LOG_FILE" | tee -a "$LOG_FILE"

    # Preserve failure artifacts
    mkdir -p "$LOG_DIR/failures"
    cp -r artifacts/* "$LOG_DIR/failures/" 2>/dev/null || true
    cp -r UITests/Golden/Diffs/* "$LOG_DIR/failures/" 2>/dev/null || true

    exit 1
fi
