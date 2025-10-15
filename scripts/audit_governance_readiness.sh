#!/usr/bin/env bash
set -euo pipefail

# Governance Readiness Audit for universal-ai-tools Repo
# Run this from the repo root to inventory structure, find cruft, and check alignment

AUDIT_DIR="_governance_audit"
REPO_ROOT="${1:-.}"

echo "🔍 Starting Governance Readiness Audit..."
echo "📂 Target repo: $REPO_ROOT"
echo "📊 Output directory: $AUDIT_DIR"
echo ""

cd "$REPO_ROOT"
mkdir -p "$AUDIT_DIR"

# A. Fast tree & size map (excludes node_modules/.venv/venv/.git)
echo "📊 [1/8] Analyzing directory structure and sizes..."
if command -v fd >/dev/null 2>&1; then
  fd -H --type f --exclude ".git" --exclude "node_modules" --exclude ".venv" --exclude "venv" --exclude "__pycache__" . \
    | awk -F/ '{print NF-1 "\t" $0}' | sort -n > "$AUDIT_DIR/depth_map.tsv"
else
  find . -type f \
    ! -path "*/.git/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/.venv/*" \
    ! -path "*/venv/*" \
    ! -path "*/__pycache__/*" \
    | awk -F/ '{print NF-1 "\t" $0}' | sort -n > "$AUDIT_DIR/depth_map.tsv"
fi

du -sh * .[^.]* 2>/dev/null | sort -h > "$AUDIT_DIR/size_by_dir.txt" || true

# B. Stale/duplicate configs (docker, compose, CI, env files)
echo "🐳 [2/8] Finding Docker and configuration files..."
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden -i "dockerfile|docker-compose|compose\.ya?ml|\.github/workflows/|prometheus\.yml|grafana|Makefile|\.env" \
    --type-not lock \
    > "$AUDIT_DIR/config_hits.rg" 2>/dev/null || echo "No config hits found" > "$AUDIT_DIR/config_hits.rg"
else
  grep -r -n -i -E "dockerfile|docker-compose|compose\.ya?ml|\.github/workflows/|prometheus\.yml|grafana|Makefile|\.env" . \
    --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir=".venv" --exclude-dir="venv" \
    > "$AUDIT_DIR/config_hits.rg" 2>/dev/null || echo "No config hits found" > "$AUDIT_DIR/config_hits.rg"
fi

# C. Orphaned Dockerfiles/compose (inventory)
echo "🔍 [3/8] Inventorying Dockerfiles and compose files..."
if command -v rg >/dev/null 2>&1; then
  rg -n "FROM |ENTRYPOINT|CMD" -g "Dockerfile*" > "$AUDIT_DIR/dockerfiles.rg" 2>/dev/null || echo "No Dockerfiles found" > "$AUDIT_DIR/dockerfiles.rg"
  rg -n "services:" -g "*compose*.yml" -g "*compose*.yaml" > "$AUDIT_DIR/compose_files.rg" 2>/dev/null || echo "No compose files found" > "$AUDIT_DIR/compose_files.rg"
else
  find . -name "Dockerfile*" -type f -exec grep -Hn "FROM \|ENTRYPOINT\|CMD" {} \; > "$AUDIT_DIR/dockerfiles.rg" 2>/dev/null || echo "No Dockerfiles found" > "$AUDIT_DIR/dockerfiles.rg"
  find . -name "*compose*.yml" -o -name "*compose*.yaml" -type f -exec grep -Hn "services:" {} \; > "$AUDIT_DIR/compose_files.rg" 2>/dev/null || echo "No compose files found" > "$AUDIT_DIR/compose_files.rg"
fi

# D. Python & JS dependency snapshot
echo "📦 [4/8] Capturing dependency snapshots..."
if [ -f requirements.txt ]; then
  pip freeze > "$AUDIT_DIR/requirements.lock" 2>/dev/null || cp requirements.txt "$AUDIT_DIR/requirements.lock"
elif [ -f pyproject.toml ]; then
  echo "pyproject.toml found (modern)" > "$AUDIT_DIR/requirements.lock"
else
  echo "No Python requirements found" > "$AUDIT_DIR/requirements.lock"
fi

if [ -f package.json ]; then
  jq -r '.dependencies,.devDependencies|keys[]' package.json 2>/dev/null \
    | sort -u > "$AUDIT_DIR/js_deps.txt" || echo "No JS deps" > "$AUDIT_DIR/js_deps.txt"
else
  echo "No package.json found" > "$AUDIT_DIR/js_deps.txt"
fi

# E. Secrets & .env sprawl
echo "🔐 [5/8] Scanning for secrets and environment files..."
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden -i "(api[_-]?key|secret|token|password|private[_-]?key)" \
    --type-not lock --type-not binary \
    > "$AUDIT_DIR/secret_like_hits.rg" 2>/dev/null || echo "No secret patterns found" > "$AUDIT_DIR/secret_like_hits.rg"
else
  grep -r -n -i -E "(api[_-]?key|secret|token|password|private[_-]?key)" . \
    --exclude-dir=".git" --exclude-dir="node_modules" --exclude="*.lock" \
    > "$AUDIT_DIR/secret_like_hits.rg" 2>/dev/null || echo "No secret patterns found" > "$AUDIT_DIR/secret_like_hits.rg"
fi

if command -v fd >/dev/null 2>&1; then
  fd -H ".env" > "$AUDIT_DIR/env_files.txt"
else
  find . -name ".env*" -type f > "$AUDIT_DIR/env_files.txt"
fi

# F. Tests & coverage signals
echo "🧪 [6/8] Finding test files and coverage..."
if command -v rg >/dev/null 2>&1; then
  rg -n "(pytest|unittest|vitest|jest|playwright|test_|_test\.)" \
    > "$AUDIT_DIR/test_signals.rg" 2>/dev/null || echo "No test signals found" > "$AUDIT_DIR/test_signals.rg"
else
  grep -r -n -E "(pytest|unittest|vitest|jest|playwright|test_|_test\.)" . \
    --exclude-dir=".git" --exclude-dir="node_modules" \
    > "$AUDIT_DIR/test_signals.rg" 2>/dev/null || echo "No test signals found" > "$AUDIT_DIR/test_signals.rg"
fi

# G. Dead code quick pass (files not touched in 180 days)
echo "🗑️  [7/8] Identifying stale files (>180 days)..."
if git rev-parse --git-dir > /dev/null 2>&1; then
  git ls-files | while read file; do
    if [ -f "$file" ]; then
      last_mod=$(git log -1 --format=%ct -- "$file" 2>/dev/null || echo "0")
      cutoff=$(date -v-180d +%s 2>/dev/null || date -d "180 days ago" +%s 2>/dev/null || echo "0")
      if [ "$last_mod" -lt "$cutoff" ] && [ "$last_mod" != "0" ]; then
        echo "$file"
      fi
    fi
  done > "$AUDIT_DIR/stale_files.txt"
else
  echo "Not a git repository - skipping stale file analysis" > "$AUDIT_DIR/stale_files.txt"
fi

# H. Governance alignment check
echo "⚖️  [8/8] Checking governance component alignment..."
{
  echo "=== Governance Components Inventory ==="
  echo ""
  
  for f in \
    docker-compose.athena-governance.yml \
    monitoring/prometheus/prometheus.yml \
    monitoring/grafana/dashboards/governance-overview.json \
    monitoring/grafana/dashboards/governance-predictive.json \
    scripts/gov_predeploy_gate.py \
    scripts/gov_canary_decider.py \
    scripts/gov_rollback.sh \
    scripts/gov_deploy.sh \
    scripts/gov_promote.sh \
    scripts/gov_adaptive_thresholds.py \
    scripts/gov_window_tuner.py \
    scripts/gov_predictor.py \
    scripts/gov_incident_reporter.py \
    scripts/gov_promotion_chain.py \
    exec/playbook_executor.py \
    exec/verdict_actions.py \
    exec/playbooks/ece_spike_remediation.yaml \
    policy/governance_policy.yaml \
    policy/god_judge_verdict_mapping.yaml \
    policy/bundles/dev.yaml \
    policy/bundles/staging.yaml \
    policy/bundles/prod.yaml \
    .github/workflows/governance-deploy.yml \
    .github/workflows/governance-canary-watch.yml \
    .github/workflows/governance-adaptive-learning.yml ; do
    
    if [ -f "$f" ]; then
      echo "✅ FOUND: $f"
    else
      echo "❌ MISSING: $f"
    fi
  done
  
  echo ""
  echo "=== Summary ==="
  found_count=$(for f in docker-compose.athena-governance.yml monitoring/prometheus/prometheus.yml scripts/gov_*.py exec/playbook_executor.py policy/governance_policy.yaml .github/workflows/governance-*.yml; do test -f "$f" && echo "1"; done 2>/dev/null | wc -l | tr -d ' ')
  echo "Governance components found: $found_count"
  
} > "$AUDIT_DIR/governance_gaps.txt"

# Generate summary report
{
  echo "# Governance Readiness Audit Report"
  echo "Generated: $(date)"
  echo ""
  echo "## Repository Statistics"
  echo "- Total files analyzed: $(wc -l < "$AUDIT_DIR/depth_map.tsv" | tr -d ' ')"
  echo "- Dockerfiles found: $(wc -l < "$AUDIT_DIR/dockerfiles.rg" | tr -d ' ')"
  echo "- Compose files found: $(wc -l < "$AUDIT_DIR/compose_files.rg" | tr -d ' ')"
  echo "- Environment files found: $(wc -l < "$AUDIT_DIR/env_files.txt" | tr -d ' ')"
  echo "- Stale files (>180 days): $(wc -l < "$AUDIT_DIR/stale_files.txt" | tr -d ' ')"
  echo ""
  echo "## Top 10 Largest Directories"
  head -10 "$AUDIT_DIR/size_by_dir.txt"
  echo ""
  echo "## Governance Alignment"
  echo "See: $AUDIT_DIR/governance_gaps.txt"
  echo ""
  echo "## Recommendations"
  echo "1. Review stale_files.txt and archive/delete unused code"
  echo "2. Consolidate Dockerfiles found in dockerfiles.rg"
  echo "3. Merge compose files found in compose_files.rg"
  echo "4. Review secret_like_hits.rg for hardcoded secrets"
  echo "5. Check governance_gaps.txt for missing components"
  echo ""
  echo "## Next Steps"
  echo "Run: cat $AUDIT_DIR/governance_gaps.txt"
  echo "Then: Review and implement consolidation plan"
} > "$AUDIT_DIR/REPORT.md"

echo ""
echo "✅ Audit complete!"
echo "📊 Results in: $AUDIT_DIR/"
echo ""
echo "📋 Quick summary:"
cat "$AUDIT_DIR/REPORT.md"


