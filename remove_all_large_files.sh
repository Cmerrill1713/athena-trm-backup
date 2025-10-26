#!/bin/bash

echo "🗑️  REMOVING ALL REMAINING LARGE FILES"
echo "======================================="

# Remove all large tar files
git rm --cached governance/judicial/evaluation/*.tar 2>/dev/null || true
git rm --cached governance/executive/orchestration/*.tar 2>/dev/null || true

# Remove large zip files
git rm --cached governance/judicial/evaluation/UITestArtifacts*.zip 2>/dev/null || true
git rm --cached archive/**/*.tar.gz 2>/dev/null || true

# More specific removals
find governance/judicial/evaluation -name "*.tar" -o -name "UITestArtifacts*.zip" | while read file; do
    git rm --cached "$file" 2>/dev/null || true
done

echo "✅ All large files removed"

