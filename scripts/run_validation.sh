#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS="${ROOT}/artifacts/validation_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ARTIFACTS/logs" "$ARTIFACTS/reports"

log(){ echo "[$(date -u +%H:%M:%S)] $*"; }
step(){ log "▶ $1"; }
fail(){ log "✖ $*"; exit 1; }

# --- Fast rollback wiring (safe default)
trap 'ec=$?; if [[ $ec -ne 0 ]]; then
  echo "[!] Gate failed, invoking rollback..."; make canary-rollback || true
  echo "[!] Collecting evidence..."; make validation-evidence-pack || true
fi; exit $ec' EXIT

# --- Prechecks
step "Prechecks"
command -v make >/dev/null || fail "make not found"
: "${ENV_STAGE:=prod}"               # override in CI if needed
: "${CANARY_DURATION_MIN:=30}"
: "${SHADOW_DURATION_MIN:=120}"

# helpful echo for audit trail
env | sort | sed -n '1,120p' > "$ARTIFACTS/env.dump"

# --- Phase 0
step "Phase-0 freeze & baselines"
(make phase0-preconditions) 2>&1 | tee "$ARTIFACTS/logs/phase0.log"
(make ops-status)            2>&1 | tee "$ARTIFACTS/logs/ops-status.log"
(make grafana-open || true)  >/dev/null 2>&1 || true

# --- Shadow validation (no user impact)
step "Shadow: start + monitor ($SHADOW_DURATION_MIN min)"
(make shadow-validation-gates) 2>&1 | tee "$ARTIFACTS/logs/shadow-start.log"
end=$((SECONDS + 60*SHADOW_DURATION_MIN))
while [ $SECONDS -lt $end ]; do
  (make traffic-shadow-stats) 2>&1 | tee -a "$ARTIFACTS/logs/shadow-stats.log"
  sleep 60
done

# --- Tiny canary 1% → 5% → 10% with gates
promote() {
  local pct="$1"
  local min="$2"
  step "Canary to ${pct}% for ${min} min"
  CANARY_PERCENT="$pct" make canary-deploy 2>&1 | tee "$ARTIFACTS/logs/canary-${pct}.log"
  end=$((SECONDS + 60*min))
  while [ $SECONDS -lt $end ]; do
    make ops-status 2>&1 | tee -a "$ARTIFACTS/logs/canary-${pct}-status.log"
    sleep 60
  done
  # Gate check: rely on your Make targets to nonzero on failure
  make prod-rollout-status 2>&1 | tee -a "$ARTIFACTS/logs/canary-${pct}-gate.log"
}

promote 1  "$CANARY_DURATION_MIN"
promote 5  "$CANARY_DURATION_MIN"
promote 10 "$CANARY_DURATION_MIN"

# --- Staged rollout 10→25→50→100
step "Staged rollout"
(make prod-rollout) 2>&1 | tee "$ARTIFACTS/logs/rollout.log"

# --- Smoke probes (best-effort, non-blocking unless you want strict)
step "Smoke probes"
set +e
make smoke-health     2>&1 | tee "$ARTIFACTS/logs/smoke-health.log"
make smoke-rag        2>&1 | tee "$ARTIFACTS/logs/smoke-rag.log"
make smoke-router-uai 2>&1 | tee "$ARTIFACTS/logs/smoke-router.log"
make smoke-e2e-agi    2>&1 | tee "$ARTIFACTS/logs/smoke-e2e.log"
set -e

# --- Minimal chaos test (optional)
if [[ "${CHAOS:=false}" == "true" ]]; then
  step "Minimal chaos"
  (make playbook-minimal-chaos) 2>&1 | tee "$ARTIFACTS/logs/chaos.log"
fi

# --- Evidence pack
step "Evidence pack"
(make validation-evidence-pack ARTIFACTS_DIR="$ARTIFACTS") 2>&1 | tee "$ARTIFACTS/logs/evidence.log"

log "✅ Validation completed. Artifacts at: $ARTIFACTS"
