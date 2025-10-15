#!/usr/bin/env bash
# Smoke Test for Autonomous Evolution System
# Verifies all components work without breaking production

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Autonomous Evolution - Smoke Test                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

FAIL_COUNT=0

# Check DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo "❌ DATABASE_URL not set"
    echo "   Export it or set in .env"
    ((FAIL_COUNT++))
else
    echo "✅ DATABASE_URL configured"
fi

# Check if tables exist
echo ""
echo "━━━ Database Schema ━━━"
if psql "$DATABASE_URL" -c "\dt routing_outcomes" >/dev/null 2>&1; then
    echo "✅ routing_outcomes table exists"
else
    echo "❌ routing_outcomes table missing"
    echo "   Run: psql \"\$DATABASE_URL\" -f db/migrations/20251012_routing_outcomes.sql"
    ((FAIL_COUNT++))
fi

if psql "$DATABASE_URL" -c "\dt trm_training_runs" >/dev/null 2>&1; then
    echo "✅ trm_training_runs table exists"
else
    echo "⚠️  trm_training_runs table missing (will be created)"
fi

# Check scripts
echo ""
echo "━━━ Scripts ━━━"
for script in train_trm_lora.py eval_trm.py promote.py outcome_logger.py; do
    if [ -x "scripts/learn/$script" ]; then
        echo "✅ $script executable"
    else
        echo "❌ $script missing or not executable"
        ((FAIL_COUNT++))
    fi
done

# Check TinyRecursiveModels
echo ""
echo "━━━ TRM Infrastructure ━━━"
if [ -f "TinyRecursiveModels/infer.py" ]; then
    echo "✅ TRM infer.py present"
else
    echo "❌ TRM infer.py missing"
    ((FAIL_COUNT++))
fi

if [ -d "TinyRecursiveModels/.venv" ]; then
    echo "✅ TRM venv exists"
else
    echo "⚠️  TRM venv missing (run: cd TinyRecursiveModels && make venv)"
fi

# Test outcome logger
echo ""
echo "━━━ Testing Outcome Logger ━━━"
if python3 scripts/learn/outcome_logger.py 2>&1 | grep -q "✅"; then
    echo "✅ Outcome logger works"
else
    echo "❌ Outcome logger failed"
    ((FAIL_COUNT++))
fi

# Dry-run training
echo ""
echo "━━━ Dry-Run Training ━━━"
echo "Running dry-run training (creates structure only)..."
if python3 scripts/learn/train_trm_lora.py --from-outcomes --days 30 --dry-run 2>&1 | grep -q "wrote"; then
    echo "✅ Training script works (dry-run)"
else
    echo "❌ Training script failed"
    ((FAIL_COUNT++))
fi

# Check for candidate
CANDIDATE=$(ls -dt artifacts/trm/* 2>/dev/null | head -1 || echo "")
if [ -n "$CANDIDATE" ]; then
    echo "✅ Candidate artifacts created: $CANDIDATE"
    
    # Test eval
    echo ""
    echo "━━━ Testing Evaluation ━━━"
    if python3 scripts/learn/eval_trm.py --candidate "$CANDIDATE" --baseline models/trm/current 2>&1 | grep -q "Evaluation complete"; then
        echo "✅ Evaluation works"
    else
        echo "⚠️  Evaluation had issues (may be expected if no baseline)"
    fi
    
    # Test promote (with safeguards)
    echo ""
    echo "━━━ Testing Promotion ━━━"
    echo "Note: Promotion may fail if no improvement (expected behavior)"
    python3 scripts/learn/promote.py --candidate "$CANDIDATE" 2>&1 | head -5 || true
    
else
    echo "⚠️  No candidate artifacts (run train first)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ All smoke tests passed!"
    echo ""
    echo "Next steps:"
    echo "  1. Start logging outcomes in production"
    echo "  2. Let data accumulate"
    echo "  3. Run: make learn"
    exit 0
else
    echo "⚠️  $FAIL_COUNT issue(s) found"
    echo ""
    echo "Fix issues above, then re-run this test"
    exit 1
fi

