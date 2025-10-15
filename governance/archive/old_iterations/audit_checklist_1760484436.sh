#!/usr/bin/env bash
# AI Republic Audit Smoke - Operator Checklist
# ============================================
#
# Quick checklist for running and triaging audit smoke results
# Run this after any major changes to ensure everything still works

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🧪 AI Republic Audit Smoke - Operator Checklist"
echo "==============================================="
echo ""

# 1. Run the audit
echo "1️⃣  Running comprehensive audit smoke..."
echo "   Command: make audit-smoke"
echo ""

if ! make audit-smoke >/dev/null 2>&1; then
    echo "❌ Audit smoke failed!"
    echo ""
    echo "🔍 Quick triage:"
    echo "   make audit-triage --failures"
    echo "   make audit-triage --step <failing_step>"
    exit 1
fi

echo "✅ Audit smoke completed successfully!"
echo ""

# 2. Find latest artifacts
echo "2️⃣  Finding latest audit artifacts..."
LATEST="$(ls -1dt "$ROOT/artifacts/audit-"* 2>/dev/null | head -1 || true)"

if [[ -z "$LATEST" ]]; then
    echo "❌ No audit artifacts found!"
    echo "   Check that audit_smoke.sh created artifacts/ directory"
    exit 1
fi

echo "   Latest audit: $LATEST"
echo ""

# 3. Check summary
echo "3️⃣  Checking audit summary..."
if [[ -f "$LATEST/audit.log" ]]; then
    SUMMARY_LINE="$(grep -E "SMOKE SUMMARY" "$LATEST/audit.log" || true)"
    if [[ -n "$SUMMARY_LINE" ]]; then
        echo "   $SUMMARY_LINE"
    else
        echo "   ❌ No summary line found in audit.log"
    fi
else
    echo "   ❌ No audit.log found"
    exit 1
fi
echo ""

# 4. Check for failures
echo "4️⃣  Checking for failures..."
FAILURES="$(grep -Hn "❌" "$LATEST/audit.log" || true)"
if [[ -n "$FAILURES" ]]; then
    echo "❌ Failures detected:"
    echo "$FAILURES"
    echo ""
    echo "🔍 Deep dive commands:"
    echo "   make audit-triage --failures"
    echo "   make audit-triage --step <specific_step>"
    exit 1
else
    echo "✅ No failures detected!"
fi
echo ""

# 5. Pinpoint failing steps (if any)
echo "5️⃣  Checking individual step exit codes..."
FAILED_STEPS=""
while read -r rcfile; do
    [[ -f "$rcfile" ]] || continue
    rc="$(cat "$rcfile")"
    if [[ "$rc" != "0" ]]; then
        step="$(basename "$rcfile" .rc)"
        FAILED_STEPS="$FAILED_STEPS$step (rc=$rc) "
    fi
done < <(ls "$LATEST"/*.rc 2>/dev/null || true)

if [[ -n "$FAILED_STEPS" ]]; then
    echo "❌ Failing steps: $FAILED_STEPS"
    echo ""
    echo "🔍 Inspect specific step:"
    echo "   make audit-triage --step <step_name>"
    echo "   cat $LATEST/<step_name>.err"
    exit 1
else
    echo "✅ All steps passed!"
fi
echo ""

# 6. Show key artifacts
echo "6️⃣  Key artifacts available:"
echo "   📄 Master log:    $LATEST/audit.log"
echo "   📊 JUnit XML:     $LATEST/junit.xml"
echo "   🌍 Environment:   $LATEST/env.txt"
echo "   📁 Per-step logs: $LATEST/*.out, *.err, *.rc"
echo ""

echo "🎉 Checklist completed successfully!"
echo ""
echo "💡 Quick commands for ongoing use:"
echo "   make audit-smoke          # Run full audit"
echo "   make audit-triage         # Quick diagnostics"
echo "   make audit-triage --failures  # Only problems"
echo "   grep -E 'SMOKE SUMMARY' artifacts/audit-*/audit.log  # Latest summary"
