#!/usr/bin/env bash
#
# Generate a tractable "hot set" of files for Cursor to index
# This creates a smaller active set (1-3k files) for fast IDE performance
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT="$SCRIPT_DIR/hotset.txt"

cd "$REPO_ROOT"

echo "🔥 Generating HOT set (recent + critical paths)..."

{
  # Recent work (last 30 days)
  echo "# Recent changes (30 days)" >&2
  git log --since="30 days ago" --name-only --pretty=format: 2>/dev/null | grep -v '^\s*$' || true
  
  # Critical governance paths
  echo "# Critical paths: governance" >&2
  find governance \
    -type f \
    \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" \) \
    -not -path "*/archive/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/.venv/*" 2>/dev/null || true
  
  # Orchestrator
  echo "# Critical paths: orchestrator" >&2
  find orchestrator -type f \( -name "*.py" -o -name "*.yaml" \) 2>/dev/null || true
  
  # AGI Core
  echo "# Critical paths: agi_core" >&2
  find agi_core -type f -name "*.py" 2>/dev/null || true
  
  # Workflows
  echo "# Critical paths: workflows" >&2
  find workflows -type f -name "*.py" 2>/dev/null || true
  
  # Monitoring & Observability
  echo "# Critical paths: monitoring" >&2
  find monitoring -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) 2>/dev/null || true
  find governance/observability -type f -name "*.py" 2>/dev/null || true
  
  # Scripts (governance & dgm)
  echo "# Critical paths: scripts" >&2
  find scripts -type f -name "gov_*.sh" -o -name "dgm_*.sh" -o -name "verify_*.sh" 2>/dev/null || true
  
  # Tests
  echo "# Critical paths: tests" >&2
  find tests -type f -name "test_*.py" 2>/dev/null || true
  
  # Config files
  echo "# Critical paths: config" >&2
  find config -type f \( -name "*.yaml" -o -name "*.yml" \) 2>/dev/null || true
  
  # Root-level critical files
  echo "# Critical paths: root" >&2
  ls -1 *.py 2>/dev/null || true
  ls -1 *.md 2>/dev/null | grep -E "^(SYSTEM|WIRING|GOVERNANCE|DGM|CURSOR|COMPLETE)" || true
  
  # Makefile & docker-compose
  ls -1 Makefile* docker-compose*.yml 2>/dev/null || true
  
  # VS Code config
  find .vscode -type f 2>/dev/null || true
  echo ".cursorrules"
  
} | grep -v -E '(^\.git/|/node_modules/|/dist/|/build/|/target/|/\.venv/|/backups/|/archive/old_iterations/)' \
  | sort -u \
  | head -n 3000 > "$OUT"

# Count by type
PYTHON_COUNT=$(grep -c "\.py$" "$OUT" || echo "0")
YAML_COUNT=$(grep -c "\.ya*ml$" "$OUT" || echo "0")
SCRIPT_COUNT=$(grep -c "\.sh$" "$OUT" || echo "0")
MD_COUNT=$(grep -c "\.md$" "$OUT" || echo "0")
TOTAL=$(wc -l < "$OUT" | tr -d ' ')

echo ""
echo "✅ HOT set generated: $OUT"
echo "📊 Summary:"
echo "   Python files: $PYTHON_COUNT"
echo "   YAML files: $YAML_COUNT"
echo "   Shell scripts: $SCRIPT_COUNT"
echo "   Documentation: $MD_COUNT"
echo "   Total: $TOTAL files (max 3000)"
echo ""
echo "💡 This is your active working set for Cursor."
echo "   Full inventory: tools/index/repo_inventory.txt"

