#!/bin/bash
# Phase 2: Move remaining stragglers

echo "🧹 Phase 2: Moving remaining files..."

# Move to archive
mv AUTONOMOUS_EVOLUTION_FOUNDATION.md docs/archive/ 2>/dev/null
mv BRIDGE_SHIP_IT.md docs/archive/ 2>/dev/null
mv DEV_NOTES.md docs/archive/ 2>/dev/null
mv FINAL_DELIVERY.md docs/complete/ 2>/dev/null
mv FULL_VALIDATION_REPORT.md docs/complete/ 2>/dev/null
mv GRADING_SYSTEM_REFINED.md docs/archive/ 2>/dev/null
mv INDYDEVDAN_INFO.md docs/archive/ 2>/dev/null
mv INTERNAL_ANNOUNCEMENT.md docs/archive/ 2>/dev/null
mv NEXT_TIER_ROADMAP.md docs/archive/ 2>/dev/null
mv SHIPLOG.md docs/archive/ 2>/dev/null
mv SHIPPED_*.md docs/complete/ 2>/dev/null
mv VICTORY_LAP.txt docs/archive/ 2>/dev/null

# Move to operations
mv GHOST_BUSTING_PROTOCOL.md docs/operations/ 2>/dev/null
mv PRODUCTION_AUTONOMOUS_SYSTEM.md docs/operations/ 2>/dev/null
mv RUNBOOK.md docs/operations/ 2>/dev/null

# Move to reference
mv METAPROMPT_QUICKSTART.md docs/reference/ 2>/dev/null
mv README_PRODUCTION.md docs/reference/ 2>/dev/null
mv README_STACK_TOOLS.md docs/reference/ 2>/dev/null
mv README_STACK.md docs/reference/ 2>/dev/null
mv REAL_MODE_QUICK_REF.md docs/reference/ 2>/dev/null

# Move to launch
mv DO_THIS_NOW.md docs/launch/ 2>/dev/null
mv FRONTEND_GO_LIVE.md docs/launch/ 2>/dev/null

# Move to complete
mv READY_TO_SHIP.md docs/complete/ 2>/dev/null
mv READY_TO_TAG.md docs/complete/ 2>/dev/null

# Move to athena
mv FIX_GENERIC_VOICE.md docs/athena/ 2>/dev/null
mv TIER_5_ATHENA_GITOPS.md docs/athena/ 2>/dev/null

# Move to setup
mv CODE_INVENTORY.md docs/setup/ 2>/dev/null

# Move to archive (strategics)
mv STRATEGIC_DECISION.md docs/archive/ 2>/dev/null

echo "✅ Phase 2 complete!"
echo ""
echo "Remaining in root:"
ls -1 *.md 2>/dev/null | grep -v "^README.md$\|^START_HERE.md$\|^INDEX.md$\|^CHANGELOG" | wc -l
