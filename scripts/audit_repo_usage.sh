#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
OUT="${OUT:-audit_report.txt}"
: > "$OUT"

say() { printf "%s\n" "$*" | tee -a "$OUT"; }

say "== Repo Usage Audit =="
say "root: $ROOT"
say "time: $(date)"

# ---- Inventory
say ""
say "[1] Inventory (git)"
git -C "$ROOT" ls-files > /tmp/all_files.txt
wc -l /tmp/all_files.txt | awk '{print "tracked files:",$1}' | tee -a "$OUT"

# ---- Docker wiring (what actually runs & mounts)
say ""
say "[2] Docker compose bindings & entrypoints"
if [ -f "$ROOT/docker-compose.enterprise.yml" ]; then
  say "   Found docker-compose.enterprise.yml"
  grep -E "build:|image:|command:|entrypoint:|volumes:" "$ROOT/docker-compose.enterprise.yml" | tee -a "$OUT" || true
else
  say "   no docker-compose.enterprise.yml found"
fi

# ---- Makefile reachability (what targets touch)
say ""
say "[3] Make targets that reference paths"
if [ -f "$ROOT/Makefile" ]; then
  grep -nE "bridge|athena|kokoro|fastvlm|prometheus|grafana|scripts|dashboards|agents|orchestrator|AI-Projects" Makefile | tee -a "$OUT" || true
fi

# ---- CI pipeline paths (what CI executes)
say ""
say "[4] GitHub Actions paths"
if [ -d "$ROOT/.github/workflows" ]; then
  grep -rnE "bridge|athena|kokoro|fastvlm|prometheus|grafana|scripts|dashboards|tests|AI-Projects" .github/workflows 2>/dev/null | tee -a "$OUT" || true
else
  say "   no .github/workflows directory"
fi

# ---- Runtime imports (Python)
say ""
say "[5] Python import graph (static scan)"
find bridge athena orchestrator agents AI-Projects/universal-ai-tools -name "*.py" -type f 2>/dev/null | while read f; do
  grep -nE "from |import " "$f" 2>/dev/null | head -5 || true
done | tee -a "$OUT" || true

# ---- Tests & coverage hints
say ""
say "[6] Tests referencing modules"
if [ -d tests ]; then
  grep -rnE "bridge|athena|kokoro|fastvlm|orchestrator" tests 2>/dev/null | tee -a "$OUT" || true
fi

# ---- Prometheus/Grafana references
say ""
say "[7] Prometheus rules & dashboards referenced by scripts"
if [ -f Makefile ]; then
  grep -nE "prometheus/|dashboards/|grafana/" scripts/* Makefile 2>/dev/null | tee -a "$OUT" || true
fi

# ---- Hardcoded localhost ports (smoke out stale clients)
say ""
say "[8] Hardcoded localhost:ports (should map to 8014/8090/etc)"
grep -rnE "localhost:[0-9]{3,5}|127\.0\.0\.1:[0-9]{3,5}" \
  --include="*.py" --include="*.swift" --include="*.sh" \
  --exclude-dir="logs" --exclude-dir="build" --exclude-dir=".git" \
  bridge athena orchestrator NeuroForgeApp scripts 2>/dev/null | head -50 | tee -a "$OUT" || true

# ---- Orphans: tracked files never referenced
say ""
say "[9] Likely orphans (heuristic)"

# Find referenced files
{
  grep -rl "bridge\|athena\|kokoro\|fastvlm\|orchestrator\|prometheus\|grafana\|dashboards\|scripts\|agents\|AI-Projects\|NeuroForgeApp\|RUNBOOKS\|releases" \
    --exclude-dir="logs" --exclude-dir="build" --exclude-dir=".git" . 2>/dev/null || true
  find bridge athena orchestrator agents AI-Projects/universal-ai-tools -name "*.py" -type f 2>/dev/null || true
  find scripts -name "*.sh" -type f 2>/dev/null || true
  find NeuroForgeApp -name "*.swift" -type f 2>/dev/null || true
} | sort -u > /tmp/referenced.txt

# Find orphans (files in git but not referenced)
comm -23 <(sort /tmp/all_files.txt) <(sort /tmp/referenced.txt) \
  | grep -vE "(^\.github/|^logs/|^build/|\.md$|\.png$|\.jpg$|\.gif$|\.svg$|\.ico$|\.txt$|LICENSE|README)" \
  | tee -a "$OUT" || true

say ""
say "[10] Summary"
say "Report written to $OUT"
say "Review [9] Likely orphans for cleanup candidates"

