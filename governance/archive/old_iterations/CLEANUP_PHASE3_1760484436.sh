#!/bin/bash
# Phase 3: Organize scripts and test files

echo "🧹 Phase 3: Organizing scripts and tests..."

# Move CHANGELOGs to docs
mkdir -p docs/changelog
mv CHANGELOG*.md docs/changelog/ 2>/dev/null && echo "  ✅ Moved CHANGELOGs"

# Move test files to tests/
mv test_*.py tests/ 2>/dev/null
mv test_*.swift tests/ 2>/dev/null
mv VoiceProof* tests/ 2>/dev/null
echo "  ✅ Moved test files"

# Move launch/ship scripts to scripts/
mv GO_LIVE_NOW.sh scripts/ 2>/dev/null
mv GO_NO_GO_CHECKLIST.sh scripts/ 2>/dev/null
mv SHIP_IT_NOW.sh scripts/ 2>/dev/null
mv SHIP_NOW.sh scripts/ 2>/dev/null
mv ROLLBACK_PLAYBOOK.sh scripts/ 2>/dev/null
echo "  ✅ Moved launch scripts"

# Move utility scripts to scripts/
mv run-full-evaluation.sh scripts/ 2>/dev/null
mv import_dashboard_simple.sh scripts/ 2>/dev/null
mv fix_docker.sh scripts/ 2>/dev/null
mv bootstrap_broker.sh scripts/ 2>/dev/null
mv embed_all_transcripts.py scripts/ 2>/dev/null
echo "  ✅ Moved utility scripts"

# Move cleanup scripts to scripts/
mv CLEANUP_*.sh scripts/ 2>/dev/null
echo "  ✅ Moved cleanup scripts"

# Move config examples
mkdir -p config/examples
mv .env.stack.example config/examples/ 2>/dev/null
mv crontab.example config/examples/ 2>/dev/null
echo "  ✅ Moved config examples"

echo ""
echo "✅ Phase 3 complete!"
echo ""
echo "Essential files remaining in root:"
ls -1 | grep -v "^\." | head -20
