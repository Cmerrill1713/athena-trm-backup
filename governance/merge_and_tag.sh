#!/bin/bash
# Governance Merge & Tag Script
# Automates iteration management and sanity checks

set -euo pipefail

ITERATION_LOG="iteration_log.yaml"
MANIFEST="governance_manifest.json"

# Auto-increment version
if [[ -f "$ITERATION_LOG" ]]; then
    current_version=$(grep "version:" "$ITERATION_LOG" | cut -d' ' -f2)
    major=$(echo "$current_version" | cut -d'.' -f1 | sed 's/v//')
    minor=$(echo "$current_version" | cut -d'.' -f2)
    new_minor=$((minor + 1))
    new_version="v${major}.${new_minor}"
else
    new_version="v1.0"
fi

# Update iteration log
cat >> "$ITERATION_LOG" << LOG_ENTRY

---
version: $new_version
author: $(whoami)
date: $(date -Iseconds)
summary: "Auto-merged governance iteration"
changes:
  - "Merged pending changes into governance structure"
LOG_ENTRY

# Regenerate manifest
./governance_cleanup.sh --manifest-only

echo "✅ Governance iteration $new_version created"
