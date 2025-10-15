#!/bin/bash
# Clean up root directory - organize documentation

set -e

echo "🧹 Cleaning up root directory..."
cd /Users/christianmerrill/Documents/GitHub

# Create organized doc structure
mkdir -p docs/guides
mkdir -p docs/complete
mkdir -p docs/reference
mkdir -p docs/setup
mkdir -p docs/athena
mkdir -p docs/fastvlm
mkdir -p docs/tier4
mkdir -p docs/operations
mkdir -p docs/launch
mkdir -p docs/archive

# Move completion status docs
echo "📦 Moving completion docs..."
mv *_COMPLETE.md docs/complete/ 2>/dev/null || true
mv *_READY.md docs/complete/ 2>/dev/null || true
mv *_SHIPPED.md docs/complete/ 2>/dev/null || true
mv VALIDATION_*.md docs/complete/ 2>/dev/null || true
mv VERIFICATION_*.md docs/complete/ 2>/dev/null || true

# Move guides
echo "📚 Moving guides..."
mv *_GUIDE.md docs/guides/ 2>/dev/null || true
mv *_PLAYBOOK.md docs/guides/ 2>/dev/null || true
mv *_REFERENCE.md docs/guides/ 2>/dev/null || true

# Move reference cards
echo "🗂️  Moving reference cards..."
mv *_CARD.md docs/reference/ 2>/dev/null || true
mv QUICK_*.md docs/reference/ 2>/dev/null || true
mv COMMAND_*.md docs/reference/ 2>/dev/null || true

# Move setup docs
echo "⚙️  Moving setup docs..."
mv *_SETUP*.md docs/setup/ 2>/dev/null || true
mv LOCAL_*.md docs/setup/ 2>/dev/null || true

# Move Athena docs
echo "🧠 Moving Athena docs..."
mv ATHENA_*.md docs/athena/ 2>/dev/null || true

# Move FastVLM docs
echo "👁️  Moving FastVLM docs..."
mv FASTVLM_*.md docs/fastvlm/ 2>/dev/null || true
mv README_FASTVLM.md docs/fastvlm/ 2>/dev/null || true
mv START_HERE_FASTVLM.md docs/fastvlm/ 2>/dev/null || true

# Move Tier 4 docs
echo "📊 Moving Tier 4 docs..."
mv TIER4_*.md docs/tier4/ 2>/dev/null || true
mv TIER_4_*.md docs/tier4/ 2>/dev/null || true
mv OBSERVABILITY_*.md docs/tier4/ 2>/dev/null || true
mv MONITORING_*.md docs/tier4/ 2>/dev/null || true

# Move operations docs
echo "🔧 Moving operations docs..."
mv OPERATIONAL_*.md docs/operations/ 2>/dev/null || true
mv OPERATOR_*.md docs/operations/ 2>/dev/null || true
mv AUTO_*.md docs/operations/ 2>/dev/null || true
mv SELF_HEALING_*.md docs/operations/ 2>/dev/null || true
mv STACK_*.md docs/operations/ 2>/dev/null || true
mv DAY2_*.md docs/operations/ 2>/dev/null || true
mv POST_*.md docs/operations/ 2>/dev/null || true

# Move launch docs
echo "🚀 Moving launch docs..."
mv GO_*.md docs/launch/ 2>/dev/null || true
mv LAUNCH_*.md docs/launch/ 2>/dev/null || true
mv SHIP_*.md docs/launch/ 2>/dev/null || true
mv EXECUTE_*.md docs/launch/ 2>/dev/null || true
mv PREFLIGHT_*.sh docs/launch/ 2>/dev/null || true
mv MISSION_*.md docs/launch/ 2>/dev/null || true
mv GREEN_LIGHTS.sh docs/launch/ 2>/dev/null || true
mv INSTANT_FIXES.md docs/launch/ 2>/dev/null || true

# Move voice docs
echo "🎙️  Moving voice docs..."
mv VOICE_*.md docs/athena/ 2>/dev/null || true

# Move archive/legacy docs
echo "📂 Moving archive docs..."
mv SESSION_*.md docs/archive/ 2>/dev/null || true
mv VICTORY_*.md docs/archive/ 2>/dev/null || true
mv ULTIMATE_*.md docs/archive/ 2>/dev/null || true
mv FROM_CHAOS_*.md docs/archive/ 2>/dev/null || true
mv THE_ENDGAME.md docs/archive/ 2>/dev/null || true
mv FILES_CREATED.md docs/archive/ 2>/dev/null || true
mv TODAYS_*.md docs/archive/ 2>/dev/null || true
mv WEEK_*.md docs/archive/ 2>/dev/null || true

# Move integration/summary docs
echo "📋 Moving summary docs..."
mv *_SUMMARY.md docs/archive/ 2>/dev/null || true
mv *_INTEGRATION*.md docs/archive/ 2>/dev/null || true
mv COMPLETE_*.md docs/archive/ 2>/dev/null || true

# Keep important root docs
echo "✅ Keeping essential root docs..."
# These stay in root:
# - README.md
# - START_HERE.md
# - INDEX.md
# - CHANGELOG.md
# - Makefile
# - VERSION

# Create new organized INDEX
echo "📝 Creating new index..."
cat > docs/INDEX.md << 'EOF'
# 📚 Documentation Index

## 🚀 Quick Start
- [Main README](../README.md)
- [Start Here](../START_HERE.md)
- [Quick Reference](reference/)

## 📖 By Category

### Launch & Deployment
- [launch/](launch/) - Launch procedures and checklists

### Operations
- [operations/](operations/) - Day 2 ops, monitoring, self-healing

### Guides
- [guides/](guides/) - How-to guides and playbooks

### Reference
- [reference/](reference/) - Quick reference cards and commands

### Setup
- [setup/](setup/) - Initial setup and configuration

### Athena
- [athena/](athena/) - Athena AI system documentation

### FastVLM
- [fastvlm/](fastvlm/) - FastVLM integration

### Tier 4 Observability
- [tier4/](tier4/) - Observability and monitoring

### Completion Status
- [complete/](complete/) - Project completion status

### Archive
- [archive/](archive/) - Legacy and historical docs

## 🔍 Find What You Need

**I want to:**
- Deploy the system → [launch/](launch/)
- Operate the system → [operations/](operations/)
- Understand Athena → [athena/](athena/)
- Monitor the system → [tier4/](tier4/)
- Troubleshoot issues → [guides/](guides/)
- Quick commands → [reference/](reference/)

EOF

echo ""
echo "✅ Root cleanup complete!"
echo ""
echo "📁 New structure:"
echo "   docs/launch/        - Launch procedures"
echo "   docs/operations/    - Operations guides"
echo "   docs/guides/        - How-to guides"
echo "   docs/reference/     - Quick references"
echo "   docs/athena/        - Athena documentation"
echo "   docs/fastvlm/       - FastVLM docs"
echo "   docs/tier4/         - Observability"
echo "   docs/complete/      - Completion status"
echo "   docs/archive/       - Legacy docs"
echo ""
echo "📝 See docs/INDEX.md for navigation"
echo ""

