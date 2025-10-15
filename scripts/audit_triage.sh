#!/usr/bin/env bash
# Audit Smoke Triage Helper
# =========================
#
# Quick diagnostic tool for audit smoke results
#
# Usage:
#   ./scripts/audit_triage.sh                # Check latest audit
#   ./scripts/audit_triage.sh --help         # Show help
#   ./scripts/audit_triage.sh --failures     # Show only failures
#   ./scripts/audit_triage.sh --step <name>  # Inspect specific step

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
  cat << 'EOF'
Audit Smoke Triage Helper
=========================

Quick diagnostic tool for audit smoke results.

USAGE:
  ./scripts/audit_triage.sh [OPTIONS]

OPTIONS:
  --help, -h          Show this help
  --latest, -l        Show latest audit directory
  --failures, -f      Show only failing steps
  --step <name>       Inspect specific step (show .err, .out, .rc)
  --summary, -s       Show overall summary
  --env               Show environment from latest audit
  --all               Show all steps with status

EXAMPLES:
  ./scripts/audit_triage.sh                    # Quick overview
  ./scripts/audit_triage.sh --failures         # Only problems
  ./scripts/audit_triage.sh --step burnin_import_sanity  # Deep dive
  ./scripts/audit_triage.sh --env              # Environment check

QUICK TRIAGE BY COMPONENT:
  Burn-in:     Check PYTHONPATH and user-space paths
  Governance:  Verify dry-run hooks don't need DB/Prometheus
  Validation:  May need test DB; consider nightly-only
  Hardening:   Install yq/psql or skip in smoke
  Self-learning: Ensure analyzer has fallback input
  Frontend:    Set SCHEME=NeuroForgeApp if needed
  Container:   Ensure Dockerfile has deterministic exit
  Security:    Non-blocking; advisory results

EOF
}

find_latest_audit() {
  local latest
  latest="$(ls -1dt "$ROOT/artifacts/audit-"* 2>/dev/null | head -1 || true)"
  if [[ -z "$latest" ]]; then
    echo "❌ No audit artifacts found in $ROOT/artifacts/" >&2
    echo "Run 'make audit-smoke' first." >&2
    exit 1
  fi
  echo "$latest"
}

show_summary() {
  local audit_dir="$1"
  local audit_log="$audit_dir/audit.log"

  if [[ ! -f "$audit_log" ]]; then
    echo "❌ No audit.log found in $audit_dir" >&2
    return 1
  fi

  echo "📊 Audit Summary: $(basename "$audit_dir")"
  echo "========================================"

  # Extract summary line
  grep "SMOKE SUMMARY:" "$audit_log" || echo "No summary found"

  # Count failures
  local fails
  fails="$(grep -c "❌" "$audit_log" || true)"
  if [[ "$fails" -gt 0 ]]; then
    echo "❌ Failures found: $fails"
    echo ""
    echo "🔍 Failing steps:"
    grep -Hn "❌" "$audit_log" | sed 's/.*— RUN: //' | sed 's/ (rc=.*//' || true
  else
    echo "✅ No failures detected"
  fi

  echo ""
  echo "📁 Full artifacts: $audit_dir"
}

show_failures() {
  local audit_dir="$1"

  echo "❌ Failing Steps in $(basename "$audit_dir")"
  echo "==========================================="

  local found=0
  for rcfile in "$audit_dir"/*.rc; do
    [[ -f "$rcfile" ]] || continue
    local rc
    rc="$(cat "$rcfile")"
    if [[ "$rc" != "0" ]]; then
      local step
      step="$(basename "$rcfile" .rc)"
      echo "• $step (rc=$rc)"
      found=$((found + 1))
    fi
  done

  if [[ $found -eq 0 ]]; then
    echo "✅ No failures found!"
  else
    echo ""
    echo "💡 Run './scripts/audit_triage.sh --step <name>' for details"
  fi
}

inspect_step() {
  local audit_dir="$1"
  local step="$2"

  echo "🔍 Inspecting step: $step"
  echo "========================"

  local rcfile="$audit_dir/${step}.rc"
  local outfile="$audit_dir/${step}.out"
  local errfile="$audit_dir/${step}.err"

  if [[ ! -f "$rcfile" ]]; then
    echo "❌ Step '$step' not found in audit" >&2
    echo "Available steps:" >&2
    ls -1 "$audit_dir"/*.rc | sed 's/.rc$//' | xargs basename -a | sort >&2
    return 1
  fi

  local rc
  rc="$(cat "$rcfile")"
  echo "Exit code: $rc"

  if [[ -f "$errfile" ]] && [[ -s "$errfile" ]]; then
    echo ""
    echo "📄 stderr (first 200 lines):"
    echo "---"
    head -n 200 "$errfile"
    echo "---"
    if [[ "$(wc -l < "$errfile")" -gt 200 ]]; then
      echo "... ($(($(wc -l < "$errfile") - 200))) more lines"
    fi
  fi

  if [[ -f "$outfile" ]] && [[ -s "$outfile" ]]; then
    echo ""
    echo "📄 stdout (first 50 lines):"
    echo "---"
    head -n 50 "$outfile"
    echo "---"
    if [[ "$(wc -l < "$outfile")" -gt 50 ]]; then
      echo "... ($(($(wc -l < "$outfile") - 50))) more lines"
    fi
  fi
}

show_all_steps() {
  local audit_dir="$1"

  echo "📋 All Steps in $(basename "$audit_dir")"
  echo "======================================"

  for rcfile in "$audit_dir"/*.rc; do
    [[ -f "$rcfile" ]] || continue
    local step
    step="$(basename "$rcfile" .rc)"
    local rc
    rc="$(cat "$rcfile")"
    local status="✅"
    [[ "$rc" != "0" ]] && status="❌"
    printf "%-30s %s (rc=%s)\n" "$step" "$status" "$rc"
  done
}

show_env() {
  local audit_dir="$1"
  local envfile="$audit_dir/env.txt"

  if [[ -f "$envfile" ]]; then
    echo "🌍 Environment from $(basename "$audit_dir")"
    echo "=========================================="
    cat "$envfile"
  else
    echo "❌ No environment file found" >&2
  fi
}

main() {
  local audit_dir=""
  local command="summary"

  while [[ $# -gt 0 ]]; do
    case $1 in
      --help|-h)
        show_help
        exit 0
        ;;
      --latest|-l)
        audit_dir="$(find_latest_audit)"
        echo "📁 Latest audit: $audit_dir"
        exit 0
        ;;
      --failures|-f)
        command="failures"
        shift
        ;;
      --step)
        command="step"
        local step="$2"
        shift 2
        ;;
      --summary|-s)
        command="summary"
        shift
        ;;
      --all)
        command="all"
        shift
        ;;
      --env)
        command="env"
        shift
        ;;
      *)
        echo "Unknown option: $1" >&2
        echo "Use --help for usage" >&2
        exit 1
        ;;
    esac
  done

  # Find latest audit if not specified
  if [[ -z "$audit_dir" ]]; then
    audit_dir="$(find_latest_audit)"
  fi

  case "$command" in
    summary)
      show_summary "$audit_dir"
      ;;
    failures)
      show_failures "$audit_dir"
      ;;
    step)
      inspect_step "$audit_dir" "$step"
      ;;
    all)
      show_all_steps "$audit_dir"
      ;;
    env)
      show_env "$audit_dir"
      ;;
  esac
}

main "$@"
