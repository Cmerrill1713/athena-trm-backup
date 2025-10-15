#!/usr/bin/env bash
set -euo pipefail

# ---------- Config ----------
FAST_TIMEOUT="${FAST_TIMEOUT:-900}"             # 15 min hard cap per job when applicable
PY=python3
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ART_DIR="$ROOT/artifacts/audit-$(date +%Y%m%d-%H%M%S)"
LOG="$ART_DIR/audit.log"
ENVFILE="$ART_DIR/env.txt"
JUNIT="$ART_DIR/junit.xml"
mkdir -p "$ART_DIR"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
ok()  { log "✅ $*"; }
ko()  { log "❌ $*"; }

# make sure we never invoke sudo in smoke
export NO_SUDO=1
export DRY_RUN=1
export POPUPS_ENABLED=0
export AUTOEXEC_GUARD=1
export PYTHONUNBUFFERED=1

# Capture environment snapshot
{
  echo "DATE: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "PWD:  $PWD"
  echo "ROOT: $ROOT"
  echo "PY:   $(command -v $PY 2>/dev/null || echo 'not found')"
  echo "XCODE: $(xcodebuild -version 2>/dev/null | head -1 || echo 'not found')"
  echo "SCHEME: ${SCHEME:-NeuroForgeApp}"
} > "$ENVFILE"

# Helper: run step with soft timeout & capture exit
run_step() {
  local name="$1"; shift
  log "— RUN: $name"
  set +e
  # Use timeout if available, otherwise run without timeout
  if command -v timeout >/dev/null 2>&1; then
    timeout "$FAST_TIMEOUT" "$@" >"$ART_DIR/${name}.out" 2>"$ART_DIR/${name}.err"
  else
    # macOS doesn't have timeout, run with background process and kill after timeout
    "$@" >"$ART_DIR/${name}.out" 2>"$ART_DIR/${name}.err" &
    local pid=$!
    local count=0
    while kill -0 $pid 2>/dev/null && [ $count -lt $FAST_TIMEOUT ]; do
      sleep 1
      ((count++))
    done
    if kill -0 $pid 2>/dev/null; then
      kill $pid 2>/dev/null || true
      echo "TIMEOUT after ${FAST_TIMEOUT}s" >>"$ART_DIR/${name}.err"
    fi
    wait $pid 2>/dev/null || true
  fi
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then ok "$name"; else ko "$name (rc=$rc)"; fi
  echo "$rc" > "$ART_DIR/${name}.rc"
  return 0
}

# ---------- 1) Env sanity ----------
log "Starting Comprehensive Evaluation Audit (Smoke)"
command -v $PY >/dev/null || { ko "python3 not found"; exit 1; }

# Optional venv activate if present
[[ -d "$ROOT/.venv" ]] && source "$ROOT/.venv/bin/activate" || true

# ---------- 2) Burn-in core smoke ----------
# Uses user-space install (no sudo), runs both tests
if [[ -d "$HOME/.local/share/ai-republic" ]]; then
  run_step burnin_import_sanity           $PY -c "import sys; sys.path.insert(0, '$HOME/.local/share/ai-republic'); import importlib; importlib.import_module('triggers'); importlib.import_module('spikes'); print('✅ All imports OK')"
  run_step burnin_maintenance_smoke       env MAINTENANCE_MODE=1 DRY_RUN=1 PYTHONPATH="$HOME/.local/share/ai-republic" $PY "$HOME/.local/share/ai-republic/burn_in_test.py" --health-check
  run_step burnin_emergency_spike_smoke   env EMERGENCY_SPIKE_TEST=1 DRY_RUN=1 PYTHONPATH="$HOME/.local/share/ai-republic" $PY "$HOME/.local/share/ai-republic/burn_in_launcher.py" --test emergency_spike
else
  log "⚠️  User-space burn-in not found, skipping burn-in tests"
fi

# ---------- 3) Governance drift smoke ----------
if [[ -f "$ROOT/scripts/test_governance_drift_detection.py" ]]; then
  run_step governance_drift_unit        $PY "$ROOT/scripts/test_governance_drift_detection.py" -q 2>/dev/null || true
fi
if [[ -f "$ROOT/scripts/integrate_governance_drift_detection.py" ]]; then
  run_step governance_drift_integrate   $PY "$ROOT/scripts/integrate_governance_drift_detection.py" --dry-run 2>/dev/null || true
fi

# ---------- 4) Production validation (fast) ----------
# Prefer the fast runner if present; otherwise run SQL suite quickly.
if [[ -f "$ROOT/scripts/run_production_validation.sh" ]]; then
  run_step production_validation_fast   bash "$ROOT/scripts/run_production_validation.sh" --fast 2>/dev/null || true
elif [[ -f "$ROOT/scripts/production_validation_suite.sql" ]]; then
  command -v psql >/dev/null 2>&1 && run_step production_validation_sql psql -f "$ROOT/scripts/production_validation_suite.sql" 2>/dev/null || true
fi

# ---------- 5) Constitutional hardening checks ----------
# SQL schema + Prometheus rule lint if available
if [[ -f "$ROOT/constitutional_hardening_bundle.sql" ]]; then
  command -v psql >/dev/null 2>&1 && run_step hardening_sql psql -f "$ROOT/constitutional_hardening_bundle.sql" 2>/dev/null || true
fi
if [[ -f "$ROOT/constitutional_hardening_alerts.yml" ]]; then
  command -v yq >/dev/null 2>&1 && run_step hardening_alerts_lint yq e '.' "$ROOT/constitutional_hardening_alerts.yml" >/dev/null 2>/dev/null || true
fi

# ---------- 6) Self-learning audit ----------
if [[ -f "$ROOT/scripts/run_self_learning_audit.sh" ]]; then
  run_step self_learning_prompt         bash "$ROOT/scripts/run_self_learning_audit.sh" cursor 2>/dev/null || true
  run_step self_learning_analyze        bash "$ROOT/scripts/run_self_learning_audit.sh" analyze 2>/dev/null || true
fi

# ---------- 7) Frontend headless build ----------
# Headless compile only (no app open)
if ls "$ROOT"/*.xcodeproj >/dev/null 2>&1 || ls "$ROOT"/*.xcworkspace >/dev/null 2>&1; then
  SCHEME="${SCHEME:-NeuroForgeApp}"
  run_step swiftpm_resolve              xcodebuild -resolvePackageDependencies
  run_step frontend_build_release       xcodebuild -scheme "$SCHEME" -configuration Release -quiet build
fi

# ---------- 8) Container build + smoke ----------
if [[ -f "$ROOT/Dockerfile.ai-republic" ]] && command -v docker >/dev/null 2>&1; then
  run_step docker_build                 docker build -f "$ROOT/Dockerfile.ai-republic" -t ai-republic:smoke "$ROOT" 2>/dev/null || true
  run_step docker_smoke                 docker run --rm ai-republic:smoke /bin/true 2>/dev/null || true
fi

# ---------- 9) Security quick scan ----------
# Bandit (python) + simple secrets grep
if command -v bandit >/dev/null 2>&1; then
  run_step bandit_quick bandit -q -r "$ROOT" -lll 2>/dev/null || true
else
  log "⚠️  Bandit not installed, skipping security scan"
fi
run_step secrets_grep  grep -RIEsn --exclude-dir=.git --exclude-dir=node_modules --exclude='*.png' --exclude='*.jpg' 'API_KEY|SECRET_KEY|BEGIN RSA|password=' "$ROOT" 2>/dev/null || echo "No secrets found"

# ---------- 10) Final summary ----------
log "Collating results…"
FAILS=0
PASSES=0
while read -r rcfile; do
  name="$(basename "$rcfile" .rc)"
  rc="$(cat "$rcfile")"
  if [[ "$rc" -eq 0 ]]; then PASSES=$((PASSES+1)); else FAILS=$((FAILS+1)); fi
done < <(ls "$ART_DIR"/*.rc 2>/dev/null || true)

echo "----------------------------------------" | tee -a "$LOG"
echo "SMOKE SUMMARY: PASSES=$PASSES FAILS=$FAILS" | tee -a "$LOG"
echo "Artifacts: $ART_DIR" | tee -a "$LOG"

# ---------- 11) Generate JUnit XML for CI integration ----------
log "Generating JUnit XML..."
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<testsuite name="audit_smoke" tests="'$((PASSES + FAILS))'" failures="'$FAILS'" time="0">'
  for rcfile in "$ART_DIR"/*.rc; do
    [[ -f "$rcfile" ]] || continue
    step="$(basename "$rcfile" .rc)"
    rc="$(cat "$rcfile")"
    out="$ART_DIR/$step.out"
    err="$ART_DIR/$step.err"

    if [[ "$rc" -eq 0 ]]; then
      echo "  <testcase name=\"$step\"/>"
    else
      echo "  <testcase name=\"$step\">"
      echo "    <failure message=\"Exit code: $rc\">"
      echo "      <![CDATA[$(head -n 50 "$err" 2>/dev/null || echo "No stderr available")]]>"
      echo "    </failure>"
      echo "  </testcase>"
    fi
  done
  echo '</testsuite>'
} > "$JUNIT"

# --- iPhone notification hook (optional) ---
DEST="${IPHONE_DEST:-}"   # set IPHONE_DEST="+15551234567" in env or Makefile
if [[ -n "${DEST}" ]]; then
  if [[ ${FAILS:-0} -eq 0 ]]; then
    scripts/notify_iphone.sh "$DEST" "✅ Audit Smoke PASSED on $(hostname). All checks green."
  else
    scripts/notify_iphone.sh "$DEST" "❌ Audit Smoke FAILED on $(hostname). Check artifacts: $(ls -1dt artifacts/audit-* | head -1)"
  fi
fi

# --- Local Mac notification (optional) ---
if command -v terminal-notifier >/dev/null 2>&1; then
  if [[ ${FAILS:-0} -eq 0 ]]; then
    terminal-notifier -title "Audit Smoke" -message "✅ Passed" -sound default >/dev/null 2>&1 || true
  else
    terminal-notifier -title "Audit Smoke" -message "❌ Failed – see artifacts" -sound Basso >/dev/null 2>&1 || true
  fi
fi

# gate
if [[ $FAILS -gt 0 ]]; then
  ko "Comprehensive Audit Smoke: FAILED ($FAILS failing step(s))"
  echo "📁 Check artifacts: $ART_DIR" >&2
  echo "🔍 Quick failures: grep -Hn '❌' '$ART_DIR/audit.log'" >&2
  exit 1
else
  ok "Comprehensive Audit Smoke: PASSED"
  exit 0
fi
