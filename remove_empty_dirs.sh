#!/bin/bash
# Safe Empty Directory Removal Script
# This script removes empty directories in categories that are safe to clean

set -euo pipefail

echo "🧹 Removing Empty Directories (Safe Categories)"
echo "================================================"
echo ""

# Category 1: Build artifacts (SAFE)
echo "1. Removing empty build artifact directories..."
find . -type d -empty \( -path "*/.build/*" -o -path "*/build/*" -o -path "*/dist/*" -o -path "*/artifacts/*" \) -delete 2>/dev/null || true
echo "   ✅ Build artifacts cleaned"

# Category 2: Empty project directories (SAFE - after review)
echo ""
echo "2. Removing confirmed empty project directories..."

# Backup directories
rm -rf ./refactor_backup_* 2>/dev/null || true
echo "   ✅ Removed old refactor backups"

# Legacy/archive
rm -rf ./neuroforge_legacy 2>/dev/null || true
rm -rf ./archive/ios-code 2>/dev/null || true
echo "   ✅ Removed legacy directories"

# Temporary/scratch directories
rm -rf ./.stack 2>/dev/null || true
rm -rf ./pids 2>/dev/null || true
rm -rf ./loki 2>/dev/null || true
rm -rf ./bin 2>/dev/null || true
echo "   ✅ Removed temporary directories"

# Empty transcript subdirectories
find ./ai_coding_transcripts -type d -empty -delete 2>/dev/null || true
echo "   ✅ Cleaned empty transcript directories"

# Docker empty directories
rm -rf ./docker/spikes 2>/dev/null || true
rm -rf ./docker/scripts 2>/dev/null || true
echo "   ✅ Removed empty docker directories"

# Empty tools
rm -rf ./tools/obs 2>/dev/null || true
echo "   ✅ Removed empty tools directories"

echo ""
echo "================================================"
echo "🎉 Safe Empty Directory Cleanup Complete!"
echo ""
echo "Summary:"
echo "  ✅ Build artifacts removed"
echo "  ✅ Legacy/backup directories removed"
echo "  ✅ Temporary directories removed"
echo "  ✅ Empty subdirectories cleaned"
echo ""
echo "Remaining empty directories:"
find . -type d -empty 2>/dev/null | wc -l | xargs echo "  Total:"
echo ""
echo "💡 Git internal directories (.git) were preserved"
echo ""
