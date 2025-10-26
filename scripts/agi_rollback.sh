#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🔄 AGI Fix Rollback"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp

# Check if on fix branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"
echo ""

if [ "$BRANCH" = "feat/agi-fix-frontend" ]; then
    echo "⚠️  You are on the AGI fix branch"
    echo ""
    echo "Rollback options:"
    echo "  1. Keep changes, return to main"
    echo "  2. Discard changes, return to main"
    echo "  3. Cancel"
    echo ""
    read -p "Choose (1/2/3): " CHOICE
    
    case "$CHOICE" in
        1)
            echo "Switching to main, keeping changes..."
            git checkout main
            echo "✅ On main branch, fix branch preserved"
            ;;
        2)
            echo "Discarding changes and returning to main..."
            git checkout main
            git reset --hard origin/main
            git branch -D feat/agi-fix-frontend || true
            echo "✅ Rolled back to clean main"
            ;;
        3)
            echo "Cancelled"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo "Not on AGI fix branch, nothing to rollback"
fi

# Check for stash
STASH_COUNT=$(git stash list | grep "AGI fix savepoint" | wc -l)
if [ "$STASH_COUNT" -gt 0 ]; then
    echo ""
    echo "📦 Found $STASH_COUNT AGI fix stash(es)"
    echo ""
    git stash list | grep "AGI fix savepoint"
    echo ""
    read -p "Pop latest stash? (y/N): " POP
    if [ "$POP" = "y" ]; then
        git stash pop
        echo "✅ Stash popped"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Rollback Complete"
echo "════════════════════════════════════════════════════════════════"
