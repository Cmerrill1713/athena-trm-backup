#!/usr/bin/env bash
#
# Generate repository inventory for Cursor/IDE navigation
# This helps Cursor understand the codebase structure
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_FILE="$SCRIPT_DIR/repo_inventory.txt"

cd "$REPO_ROOT"

echo "🔍 Generating repository inventory..."

# Create output file
cat > "$OUT_FILE" << 'HEADER'
# Athena Repository Inventory
# Auto-generated file index for IDE navigation
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

HEADER

# Source files
echo "" >> "$OUT_FILE"
echo "## Python Files" >> "$OUT_FILE"
find . -name "*.py" \
  -not -path "*/.venv/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/build/*" \
  -not -path "*/dist/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/backups/*" \
  -not -path "*/archive/old_iterations/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## YAML/Config Files" >> "$OUT_FILE"
find . \( -name "*.yaml" -o -name "*.yml" \) \
  -not -path "*/.venv/*" \
  -not -path "*/node_modules/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## Shell Scripts" >> "$OUT_FILE"
find . -name "*.sh" \
  -not -path "*/.venv/*" \
  -not -path "*/node_modules/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## Go Files" >> "$OUT_FILE"
find . -name "*.go" \
  -not -path "*/vendor/*" \
  -not -path "*/build/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## Rust Files" >> "$OUT_FILE"
find . -name "*.rs" \
  -not -path "*/target/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## TypeScript/JavaScript Files" >> "$OUT_FILE"
find . \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/dist/*" \
  -not -path "*/build/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## Docker Files" >> "$OUT_FILE"
find . \( -name "Dockerfile*" -o -name "docker-compose*.yml" \) \
  -not -path "*/node_modules/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## Makefile/Build Files" >> "$OUT_FILE"
find . \( -name "Makefile*" -o -name "*.mk" \) \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## Documentation Files" >> "$OUT_FILE"
find . -name "*.md" \
  -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" \
  | sort >> "$OUT_FILE"

echo "" >> "$OUT_FILE"
echo "## JSON Files (Config/Schema)" >> "$OUT_FILE"
find . -name "*.json" \
  -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" \
  -not -path "*/build/*" \
  -not -path "*/dist/*" \
  -not -path "*/backups/*" \
  | grep -E "(config|schema|package)" \
  | sort >> "$OUT_FILE" || true

# Key directories
echo "" >> "$OUT_FILE"
echo "## Key Directories" >> "$OUT_FILE"
for dir in governance orchestrator agi_core workflows monitoring scripts tests config docs; do
  if [ -d "$dir" ]; then
    echo "$dir/" >> "$OUT_FILE"
  fi
done

# Count files
PYTHON_COUNT=$(grep -c "\.py$" "$OUT_FILE" || echo "0")
YAML_COUNT=$(grep -c "\.ya*ml$" "$OUT_FILE" || echo "0")
SCRIPT_COUNT=$(grep -c "\.sh$" "$OUT_FILE" || echo "0")
TOTAL_COUNT=$((PYTHON_COUNT + YAML_COUNT + SCRIPT_COUNT))

echo "" >> "$OUT_FILE"
echo "## Summary" >> "$OUT_FILE"
echo "Python files: $PYTHON_COUNT" >> "$OUT_FILE"
echo "YAML files: $YAML_COUNT" >> "$OUT_FILE"
echo "Shell scripts: $SCRIPT_COUNT" >> "$OUT_FILE"
echo "Total indexed: $TOTAL_COUNT" >> "$OUT_FILE"

echo "✅ Wrote inventory to: $OUT_FILE"
echo "📊 Summary:"
echo "   Python files: $PYTHON_COUNT"
echo "   YAML files: $YAML_COUNT"
echo "   Shell scripts: $SCRIPT_COUNT"
echo "   Total: $TOTAL_COUNT"

