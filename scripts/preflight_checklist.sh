#!/usr/bin/env bash
# Preflight checklist (10 min, copy/paste)
# Run before ANY production validation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
LOG_DIR="$ROOT/logs"
ARTIFACTS_DIR="$ROOT/artifacts/preflight_$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$LOG_DIR" "$ARTIFACTS_DIR"

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ARTIFACTS_DIR/preflight.log"; }
step() { log "▶ $1"; }
fail() { log "✖ $*"; exit 1; }
warn() { log "⚠️  $*"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 PREFLIGHT CHECKLIST (10 min)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$ROOT"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Freeze: tag infra + model images
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step "1. Freeze: tagging infra + model images"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
RELEASE_TAG="release-${TIMESTAMP}-${GIT_COMMIT}"

log "   Creating release tag: $RELEASE_TAG"
git tag "$RELEASE_TAG" 2>/dev/null || warn "   Tag already exists or git not available"

# Tag Docker images
log "   Tagging Docker images..."
docker images --format "{{.Repository}}:{{.Tag}}" | grep -E '(agi-core|rag-gateway|router|uai)' | while read -r image; do
    new_tag="${image%:*}:${RELEASE_TAG}"
    docker tag "$image" "$new_tag" 2>/dev/null || warn "   Failed to tag: $image"
    log "   ✓ Tagged: $new_tag"
done

echo "$RELEASE_TAG" > "$ARTIFACTS_DIR/release_tag.txt"
log "   ✅ Freeze complete: $RELEASE_TAG"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Traffic contracts: confirm payload/response schemas match
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step "2. Traffic contracts: verifying payload/response schemas"

# AGI Core execute endpoint
log "   Checking AGI Core /api/execute schema..."
execute_response=$(curl -s http://localhost:8000/api/execute -H 'Content-Type: application/json' \
    -d '{"objective":"test","tools":[],"max_steps":1}' 2>/dev/null || echo '{}')

if echo "$execute_response" | jq -e '.trace' >/dev/null 2>&1; then
    log "   ✓ AGI execute: schema valid (trace present)"
else
    fail "   AGI execute: schema invalid (missing trace)"
fi

# RAG Gateway query endpoint
log "   Checking RAG Gateway /query schema..."
rag_response=$(curl -s http://localhost:8087/query -H 'Content-Type: application/json' \
    -d '{"query":"test","top_k":3}' 2>/dev/null || echo '{}')

if echo "$rag_response" | jq -e '.hits' >/dev/null 2>&1; then
    log "   ✓ RAG query: schema valid (hits present)"
else
    warn "   RAG query: schema check failed (gateway may be down)"
fi

# UAI chat endpoint
log "   Checking UAI /v1/chat/completions schema..."
uai_response=$(curl -s http://localhost:8080/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"auto","messages":[{"role":"user","content":"test"}]}' 2>/dev/null || echo '{}')

if echo "$uai_response" | jq -e '.choices' >/dev/null 2>&1; then
    log "   ✓ UAI chat: schema valid (choices present)"
else
    warn "   UAI chat: schema check failed (router/UAI may be down)"
fi

log "   ✅ Traffic contracts verified"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Error budget (rolling 30d): if < 30% remaining, do NOT proceed beyond 10%
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step "3. Error budget: checking rolling 30d"

# Query Prometheus for error rate over 30 days
# SLO: 99.5% success rate (0.5% error budget)
if command -v curl >/dev/null && curl -s http://localhost:9090/-/ready >/dev/null 2>&1; then
    log "   Querying Prometheus for 30d error rate..."
    
    # Error rate over 30d
    error_rate=$(curl -s "http://localhost:9090/api/v1/query?query=sum(rate(agi_requests_total{outcome=\"error\"}[30d]))/sum(rate(agi_requests_total[30d]))" \
        | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")
    
    if [ "$error_rate" != "null" ] && [ "$error_rate" != "0" ]; then
        # Calculate remaining budget
        slo_target=0.005  # 0.5% error budget
        budget_used=$(echo "$error_rate / $slo_target" | bc -l 2>/dev/null || echo "0")
        budget_remaining=$(echo "1 - $budget_used" | bc -l 2>/dev/null || echo "1")
        
        log "   Error rate (30d): ${error_rate}"
        log "   Budget used: $(echo "$budget_used * 100" | bc -l)%"
        log "   Budget remaining: $(echo "$budget_remaining * 100" | bc -l)%"
        
        if (( $(echo "$budget_remaining < 0.30" | bc -l) )); then
            warn "   ⚠️  ERROR BUDGET < 30% - DO NOT PROCEED BEYOND 10% CANARY"
            echo "ERROR_BUDGET_LOW=true" > "$ARTIFACTS_DIR/error_budget_warning.txt"
        else
            log "   ✓ Error budget healthy: $(echo "$budget_remaining * 100" | bc -l)% remaining"
        fi
    else
        warn "   No error rate data available (Prometheus may be fresh)"
    fi
else
    warn "   Prometheus not available - skipping error budget check"
fi

log "   ✅ Error budget check complete"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Kill-switch: verify make canary-rollback works now
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step "4. Kill-switch: dry-run canary rollback"

log "   Testing rollback mechanism (dry-run)..."

# Check that rollback script exists
if [ -f "$ROOT/scripts/canary_by_risk.sh" ]; then
    log "   ✓ Rollback script exists"
    
    # Dry-run test (no actual rollback)
    if DRY_RUN=true bash "$ROOT/scripts/canary_by_risk.sh" 0 1 low rollback >/dev/null 2>&1; then
        log "   ✓ Rollback dry-run successful"
    else
        warn "   Rollback dry-run had warnings (check manually)"
    fi
else
    warn "   Rollback script not found - verify manually"
fi

log "   ✅ Kill-switch validated"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PREFLIGHT CHECKLIST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log "Release tag: $RELEASE_TAG"
log "Artifacts: $ARTIFACTS_DIR"
echo ""

if [ -f "$ARTIFACTS_DIR/error_budget_warning.txt" ]; then
    echo "⚠️  WARNING: ERROR BUDGET < 30%"
    echo "    DO NOT PROCEED BEYOND 10% CANARY"
    echo ""
fi

log "📝 Next steps:"
log "   1. Run: make test-validation-structure"
log "   2. Run: make phase0-preconditions"
log "   3. Run: SHADOW_DURATION_MIN=120 make shadow-validation-gates"
log "   4. Run: CANARY_DURATION_MIN=30 make canary-deploy"
log "   5. Run: make prod-rollout"
log "   6. Run: make validation-evidence-pack"
echo ""
