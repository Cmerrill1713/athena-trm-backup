#!/bin/bash
# Cache Cleanup Script for GitHub Repository
# Run this regularly to maintain optimal performance

set -euo pipefail

echo "🧹 Starting Cache Cleanup..."
echo ""

# Python caches
echo "Cleaning Python caches..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# Testing artifacts
echo "Cleaning test artifacts..."
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".coverage" -delete 2>/dev/null || true
find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true

# Build artifacts
echo "Cleaning build artifacts..."
find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Node.js artifacts (if needed)
echo "Cleaning Node.js artifacts..."
find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".next" -type d -exec rm -rf {} + 2>/dev/null || true

# IDE caches
echo "Cleaning IDE caches..."
rm -rf .vscode/.cache 2>/dev/null || true
rm -rf .cursor 2>/dev/null || true

# Logs and metadata
echo "Cleaning logs and metadata..."
find . -name "*.log" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

# Docker cleanup (optional - uncomment if needed)
# echo "Cleaning Docker cache..."
# docker system prune -f 2>/dev/null || true

echo ""
echo "✅ Cache cleanup completed!"
echo ""
echo "Verification:"
echo "  __pycache__: $(find . -name "__pycache__" -type d | wc -l | xargs echo) remaining"
echo "  .pyc files: $(find . -name "*.pyc" | wc -l | xargs echo) remaining"
echo "  node_modules: $(find . -name "node_modules" -type d | wc -l | xargs echo) remaining"
echo ""
