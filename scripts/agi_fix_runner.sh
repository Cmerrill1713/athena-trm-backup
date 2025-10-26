#!/usr/bin/env bash
set -euo pipefail

# Idempotency lock (macOS compatible - using directory)
LOCKDIR="/tmp/agi_frontend_fix.lock"
if mkdir "$LOCKDIR" 2>/dev/null; then
    trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT
else
    echo "❌ Another AGI fix run is active"
    exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "  🧠 AGI Autonomous Fix - Starting"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check for dry-run mode
DRY_RUN=${AGI_DRY_RUN:-0}
if [ "$DRY_RUN" = "1" ]; then
    echo "🔍 DRY-RUN MODE: Will generate diff/PR draft without pushing"
    echo ""
fi

# Git stash savepoint (safety)
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
if [ -n "$(git status --porcelain)" ]; then
    echo "📦 Creating git stash savepoint..."
    git stash push -m "AGI fix savepoint $(date +%Y%m%d-%H%M%S)"
fi

# Execute AGI task
echo "🚀 Launching AGI Core execution..."
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/execute \
    -H 'Content-Type: application/json' \
    -d @/Users/christianmerrill/Documents/GitHub/agi_frontend_fix_payload.json)

# Parse response
TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id // "unknown"')
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')
EXEC_TIME=$(echo "$RESPONSE" | jq -r '.execution_time_s // 0')

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📊 Execution Result"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Task ID:       $TASK_ID"
echo "Status:        $STATUS"
echo "Execution:     ${EXEC_TIME}s"
echo ""

# Show trace
echo "Trace:"
echo "$RESPONSE" | jq -C '.trace[]' 2>/dev/null || echo "No trace available"
echo ""

# Show result
echo "Result:"
echo "$RESPONSE" | jq -C '.result' 2>/dev/null || echo "No result available"
echo ""

# Check contract tests
if [ "$STATUS" = "completed" ]; then
    echo "✅ AGI task completed successfully"
    
    # Run contract tests
    echo ""
    echo "🧪 Running contract tests..."
    if bash /Users/christianmerrill/Documents/GitHub/tests/frontend_contract.sh; then
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo "  ✅ AUTONOMOUS FIX SUCCESSFUL"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Next steps:"
        echo "  1. Review PR: $(echo "$RESPONSE" | jq -r '.result.pr_url // "Check GitHub"')"
        echo "  2. Manual smoke test: cd NeuroForgeApp && xcodebuild"
        echo "  3. Merge when satisfied"
        echo ""
    else
        echo ""
        echo "⚠️  Contract tests failed - PR may need triage"
    fi
elif [ "$STATUS" = "failed" ]; then
    echo "❌ AGI task failed"
    echo ""
    echo "Failure details:"
    echo "$RESPONSE" | jq -C '.result.error // "No error details"'
    echo ""
    echo "Check logs: docker compose logs agi-core --tail=100"
    exit 1
else
    echo "⚠️  Unexpected status: $STATUS"
    exit 1
fi

# Lock auto-released by trap on EXIT
