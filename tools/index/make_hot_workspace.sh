#!/usr/bin/env bash
#
# Generate a "hot" workspace with only the active set of files
# This makes Cursor fast by only indexing ~1-3k relevant files
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOT="$SCRIPT_DIR/hotset.txt"
OUT="$REPO_ROOT/athena-hot.code-workspace"

cd "$REPO_ROOT"

if [ ! -s "$HOT" ]; then
  echo "❌ Missing or empty $HOT"
  echo "   Run: bash tools/index/generate_hotset.sh first"
  exit 1
fi

echo "🔥 Creating hot workspace from hotset..."

# Start workspace JSON
cat > "$OUT" << 'EOF'
{
  "folders": [
    { "path": ".", "name": "🏠 Root (Hot Set)" },
    { "path": "governance", "name": "⚖️ Governance" },
    { "path": "orchestrator", "name": "🎯 Orchestrator" },
    { "path": "agi_core", "name": "🧠 AGI Core" },
    { "path": "workflows", "name": "🔄 Workflows" },
    { "path": "monitoring", "name": "📊 Monitoring" },
    { "path": "scripts", "name": "🛠️ Scripts" },
    { "path": "tests", "name": "🧪 Tests" }
  ],
  "settings": {
    "files.exclude": {
      "**/.git": true,
      "**/.DS_Store": true,
      "**/node_modules": true,
      "**/dist": true,
      "**/build": true,
      "**/target": true,
      "**/.venv": true,
      "**/__pycache__": true,
      "**/*.pyc": true,
      "**/backups": true,
      "**/archive/old_iterations": true
    },
    "search.exclude": {
      "**/node_modules": true,
      "**/dist": true,
      "**/build": true,
      "**/target": true,
      "**/.venv": true,
      "**/backups": true,
      "**/archive/old_iterations": true,
      "**/*.log": true
    },
    "files.watcherExclude": {
      "**/node_modules/**": true,
      "**/.venv/**": true,
      "**/backups/**": true,
      "**/archive/**": true
    },
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.analysis.extraPaths": [
      ".",
      "governance",
      "orchestrator",
      "agi_core",
      "workflows",
      "common"
    ],
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.indexing": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
      "tests",
      "-v"
    ],
    "go.toolsManagement.autoUpdate": true,
    "gopls": {
      "directoryFilters": [
        "-**/dist",
        "-**/build",
        "-**/target",
        "-**/.venv",
        "-**/node_modules",
        "-**/archive"
      ]
    },
    "rust-analyzer.checkOnSave.command": "clippy",
    "rust-analyzer.cargo.allFeatures": false,
    "search.useIgnoreFiles": true,
    "search.followSymlinks": false,
    "editor.formatOnSave": true
  }
}
EOF

FILE_COUNT=$(wc -l < "$HOT" | tr -d ' ')

echo "✅ Created hot workspace: $OUT"
echo "📊 Indexed paths: $FILE_COUNT"
echo ""
echo "🚀 To use:"
echo "   1. Open in Cursor: code $OUT"
echo "   2. Or: File → Open Workspace → athena-hot.code-workspace"
echo ""
echo "💡 This workspace focuses on:"
echo "   • Recent changes (30 days)"
echo "   • Governance system"
echo "   • Orchestrator & AGI Core"
echo "   • Workflows & Monitoring"
echo "   • Critical scripts & tests"
echo ""
echo "📚 For full codebase access, use: athena.code-workspace"

