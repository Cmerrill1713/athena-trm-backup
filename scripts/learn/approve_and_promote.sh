#!/usr/bin/env bash
set -euo pipefail
CAND="${1:-$(ls -dt artifacts/trm/* 2>/dev/null | head -1)}"
[ -z "${CAND}" ] && { echo "No candidate found in artifacts/trm/"; exit 2; }

MAX_DELTA="${TRM_MAX_DELTA:-0.15}"

jq -e \
  --argjson maxd "$MAX_DELTA" \
  '(.safety_regressions == 0)
   and (.route_accuracy > (.baseline_route_accuracy // 0))
   and ((.route_accuracy - (.baseline_route_accuracy // 0)) <= $maxd)' \
  "$CAND/metrics.json" >/dev/null \
  || { echo "❌ Gate failed (safety/accuracy/delta)"; cat "$CAND/metrics.json"; exit 3; }

python3 scripts/learn/promote.py --candidate "$CAND"
echo "✅ promoted $CAND"

