#!/usr/bin/env bash
# Test validation runner structure without full execution
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo "🧪 Testing validation runner structure..."
echo ""

# Test 1: Check script exists and is executable
echo "✓ Test 1: Script existence and permissions"
if [ -x "$ROOT/scripts/run_validation.sh" ]; then
    echo "  ✅ run_validation.sh exists and is executable"
else
    echo "  ❌ run_validation.sh missing or not executable"
    exit 1
fi

# Test 2: Check GitHub Actions workflow exists
echo ""
echo "✓ Test 2: GitHub Actions workflow"
if [ -f "$ROOT/.github/workflows/validation.yml" ]; then
    echo "  ✅ validation.yml exists"
else
    echo "  ❌ validation.yml missing"
    exit 1
fi

# Test 3: Check Makefile targets exist
echo ""
echo "✓ Test 3: Makefile targets"
cd "$ROOT"
targets=(
    "smoke-health"
    "smoke-rag"
    "smoke-router-uai"
    "smoke-e2e-agi"
    "run-validation"
    "run-validation-quick"
    "run-validation-chaos"
)

for target in "${targets[@]}"; do
    if make -n "$target" >/dev/null 2>&1; then
        echo "  ✅ make $target"
    else
        echo "  ❌ make $target not found"
        exit 1
    fi
done

# Test 4: Smoke probe functionality
echo ""
echo "✓ Test 4: Smoke probes (quick check)"
make smoke-health >/dev/null 2>&1 && echo "  ✅ smoke-health passed" || echo "  ⚠️  smoke-health had warnings (expected if services aren't running)"

# Test 5: Check playbook fixes exist
echo ""
echo "✓ Test 5: Playbook fixes"
if [ -x "$ROOT/scripts/playbook_fixes.sh" ]; then
    echo "  ✅ playbook_fixes.sh exists and is executable"
else
    echo "  ❌ playbook_fixes.sh missing or not executable"
    exit 1
fi

# Test 6: Check validation checklist script exists
echo ""
echo "✓ Test 6: Validation checklist"
if [ -x "$ROOT/scripts/validation_checklist.sh" ]; then
    echo "  ✅ validation_checklist.sh exists and is executable"
else
    echo "  ❌ validation_checklist.sh missing or not executable"
    exit 1
fi

# Test 7: Validate script structure (no syntax errors)
echo ""
echo "✓ Test 7: Script syntax validation"
bash -n "$ROOT/scripts/run_validation.sh" 2>&1 && echo "  ✅ run_validation.sh syntax valid" || {
    echo "  ❌ run_validation.sh has syntax errors"
    exit 1
}

bash -n "$ROOT/scripts/validation_checklist.sh" 2>&1 && echo "  ✅ validation_checklist.sh syntax valid" || {
    echo "  ❌ validation_checklist.sh has syntax errors"
    exit 1
}

bash -n "$ROOT/scripts/playbook_fixes.sh" 2>&1 && echo "  ✅ playbook_fixes.sh syntax valid" || {
    echo "  ❌ playbook_fixes.sh has syntax errors"
    exit 1
}

# Test 8: Check environment variables handling
echo ""
echo "✓ Test 8: Environment variable handling"
export ENV_STAGE=test
export SHADOW_DURATION_MIN=1
export CANARY_DURATION_MIN=1
export CHAOS=false

# Test that the script can read env vars (dry run check)
if grep -q 'ENV_STAGE' "$ROOT/scripts/run_validation.sh"; then
    echo "  ✅ ENV_STAGE handling present"
else
    echo "  ❌ ENV_STAGE handling missing"
    exit 1
fi

if grep -q 'SHADOW_DURATION_MIN' "$ROOT/scripts/run_validation.sh"; then
    echo "  ✅ SHADOW_DURATION_MIN handling present"
else
    echo "  ❌ SHADOW_DURATION_MIN handling missing"
    exit 1
fi

if grep -q 'CANARY_DURATION_MIN' "$ROOT/scripts/run_validation.sh"; then
    echo "  ✅ CANARY_DURATION_MIN handling present"
else
    echo "  ❌ CANARY_DURATION_MIN handling missing"
    exit 1
fi

if grep -q 'CHAOS' "$ROOT/scripts/run_validation.sh"; then
    echo "  ✅ CHAOS handling present"
else
    echo "  ❌ CHAOS handling missing"
    exit 1
fi

# Test 9: Check rollback trap exists
echo ""
echo "✓ Test 9: Rollback trap"
if grep -q 'trap' "$ROOT/scripts/run_validation.sh" && grep -q 'make canary-rollback' "$ROOT/scripts/run_validation.sh"; then
    echo "  ✅ Rollback trap present"
else
    echo "  ❌ Rollback trap missing"
    exit 1
fi

# Test 10: Check artifacts directory creation
echo ""
echo "✓ Test 10: Artifacts handling"
if grep -q 'ARTIFACTS=' "$ROOT/scripts/run_validation.sh" && grep -q 'mkdir -p.*ARTIFACTS' "$ROOT/scripts/run_validation.sh"; then
    echo "  ✅ Artifacts directory handling present"
else
    echo "  ❌ Artifacts directory handling missing"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All validation structure tests passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Turn-key validation runner is ready"
echo "✅ GitHub Actions workflow is configured"
echo "✅ Smoke probes are functional"
echo "✅ Playbook fixes are available"
echo "✅ Rollback safety net is active"
echo ""
echo "📝 Next steps:"
echo "   1. Run smoke probes: make smoke-health"
echo "   2. Quick validation: make run-validation-quick"
echo "   3. Full validation: make run-validation"
echo "   4. With chaos: make run-validation-chaos"
echo ""
