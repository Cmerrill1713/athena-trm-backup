#!/usr/bin/env bash
#
# Complete Wiring Verification
# Checks code imports, services, endpoints, metrics, state, and Prometheus
#

set -euo pipefail

cd "$(dirname "$0")/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}✅ $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; return 1; }
info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }

PASS_COUNT=0
FAIL_COUNT=0
INFO_COUNT=0

check_pass() {
  if eval "$1" > /dev/null 2>&1; then
    pass "$2"
    ((PASS_COUNT++))
    return 0
  else
    warn "$2 (not critical)"
    ((INFO_COUNT++))
    return 1
  fi
}

check_required() {
  if eval "$1" > /dev/null 2>&1; then
    pass "$2"
    ((PASS_COUNT++))
    return 0
  else
    fail "$2"
    ((FAIL_COUNT++))
    return 1
  fi
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ATHENA COMPLETE WIRING VERIFICATION                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ═══════════════════════════════════════════════════════════════
echo "━━━ 1. CODE IMPORTS (Integration Layer) ━━━"
# ═══════════════════════════════════════════════════════════════

check_required "python3 -c 'from athena_master_orchestrator import AthenaMasterOrchestrator'" \
  "athena_master_orchestrator imports"

check_required "python3 -c 'from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter'" \
  "DGM Governance Adapter imports"

check_required "python3 -c 'from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator'" \
  "Verdict Validator imports"

check_required "python3 -c 'from governance.research.dgm.dgm_agi_bridge import DGMAGIBridge'" \
  "DGM-AGI Bridge imports"

check_required "python3 -c 'from workflows.end_to_end_integration import run_workflow'" \
  "End-to-End Workflows import"

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 2. SYSTEM INITIALIZATION ━━━"
# ═══════════════════════════════════════════════════════════════

if python3 athena_master_orchestrator.py status 2>&1 | grep -q '"governance".*true'; then
  pass "Master Orchestrator - Governance active"
  ((PASS_COUNT++))
else
  warn "Master Orchestrator - Governance status unknown"
  ((INFO_COUNT++))
fi

if python3 athena_master_orchestrator.py status 2>&1 | grep -q '"dgm".*true'; then
  pass "Master Orchestrator - DGM active"
  ((PASS_COUNT++))
else
  warn "Master Orchestrator - DGM status unknown"
  ((INFO_COUNT++))
fi

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 3. RUNNING SERVICES ━━━"
# ═══════════════════════════════════════════════════════════════

check_pass "curl -fsS http://localhost:8888/health" \
  "Athena API (8888)"

check_pass "curl -fsS http://localhost:9109/metrics" \
  "Governance Metrics Exporter (9109)"

check_required "curl -fsS http://localhost:9110/health" \
  "Governance Orchestrator (9110)"

check_pass "curl -fsS http://localhost:9111/health" \
  "Governance Canary Monitor (9111)"

check_pass "curl -fsS http://localhost:9090/-/healthy" \
  "Prometheus (9090)"

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 4. VERDICT ENDPOINT (Critical Path) ━━━"
# ═══════════════════════════════════════════════════════════════

TASK_ID="verify-$(date +%s)"
VERDICT_RESP=$(curl -s -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\",\"verdict\":\"PASS\",\"ece_post\":0.95,\"entropy\":0.05,\"actions\":[\"PROMOTE\"],\"ts\":\"$(date -u +%FT%TZ)\"}" 2>/dev/null || echo '{}')

if echo "$VERDICT_RESP" | grep -q '"status".*"applied"'; then
  pass "POST /verdict returns 'applied'"
  ((PASS_COUNT++))
else
  fail "POST /verdict failed or returned unexpected response"
  ((FAIL_COUNT++))
fi

if echo "$VERDICT_RESP" | grep -q "$TASK_ID"; then
  pass "Verdict echoes back task_id"
  ((PASS_COUNT++))
else
  warn "Verdict response doesn't contain task_id"
  ((INFO_COUNT++))
fi

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 5. METRICS EXPORT ━━━"
# ═══════════════════════════════════════════════════════════════

check_required "curl -s http://localhost:9110/metrics | grep -q 'governance_verdicts_total'" \
  "governance_verdicts_total metric exists"

check_required "curl -s http://localhost:9110/metrics | grep -q 'governance_actions_total'" \
  "governance_actions_total metric exists"

check_required "curl -s http://localhost:9110/metrics | grep -q 'governance_ece_post'" \
  "governance_ece_post metric exists"

check_required "curl -s http://localhost:9110/metrics | grep -q 'governance_orchestrator_up'" \
  "governance_orchestrator_up metric exists"

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 6. PROMETHEUS SCRAPING ━━━"
# ═══════════════════════════════════════════════════════════════

if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
  # Check if Prometheus has governance targets
  if curl -s http://localhost:9090/api/v1/targets | grep -q 'governance'; then
    pass "Prometheus has governance targets configured"
    ((PASS_COUNT++))
  else
    warn "Prometheus running but no governance targets"
    ((INFO_COUNT++))
  fi
  
  # Check if metrics are queryable
  sleep 2  # Give Prometheus time to scrape
  if curl -s "http://localhost:9090/api/v1/query?query=governance_verdicts_total" | grep -q '"result":\['; then
    pass "Governance metrics queryable in Prometheus"
    ((PASS_COUNT++))
  else
    warn "Metrics not yet scraped (may need more time)"
    ((INFO_COUNT++))
  fi
else
  warn "Prometheus not running (scraping verification skipped)"
  ((INFO_COUNT++))
fi

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 7. STATE PERSISTENCE ━━━"
# ═══════════════════════════════════════════════════════════════

check_required "test -f exec_state.json" \
  "State file exists (exec_state.json)"

check_required "test -f exec_action_ledger.jsonl" \
  "Action ledger exists (exec_action_ledger.jsonl)"

if grep -q "$TASK_ID" exec_action_ledger.jsonl 2>/dev/null; then
  pass "Test verdict logged to ledger"
  ((PASS_COUNT++))
else
  warn "Test verdict not found in ledger"
  ((INFO_COUNT++))
fi

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 8. DGM INTEGRATION FILES ━━━"
# ═══════════════════════════════════════════════════════════════

check_required "test -f governance/research/dgm/dgm_governance_adapter.py" \
  "DGM Governance Adapter file"

check_required "test -f governance/judicial/evaluation/dgm_verdict_validator.py" \
  "DGM Verdict Validator file"

check_required "test -f governance/executive/orchestration/dgm_orchestrator.py" \
  "DGM Executive Orchestrator file"

check_required "test -f governance/research/dgm/dgm_agi_bridge.py" \
  "DGM-AGI Bridge file"

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 9. CONFIGURATION FILES ━━━"
# ═══════════════════════════════════════════════════════════════

check_required "test -f config/athena_master_config.yaml" \
  "Master config exists"

check_required "test -f governance/research/dgm/config/dgm_config.yaml" \
  "DGM config exists"

check_required "test -f governance/legislative/self_modification_policy.yaml" \
  "Constitutional policy exists"

check_required "test -f monitoring/prometheus/prometheus.yml" \
  "Prometheus config exists"

echo ""
# ═══════════════════════════════════════════════════════════════
echo "━━━ 10. DOCUMENTATION ━━━"
# ═══════════════════════════════════════════════════════════════

check_pass "test -f SYSTEM_ARCHITECTURE.md" \
  "System Architecture doc"

check_pass "test -f WIRING_DEFINITION.md" \
  "Wiring Definition doc"

check_pass "test -f COMPLETE_SYSTEM_STATUS.md" \
  "Complete System Status doc"

check_pass "test -f RUNBOOKS/DGM_OPERATOR_RUNBOOK.md" \
  "DGM Operator Runbook"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  VERIFICATION RESULTS                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

TOTAL=$((PASS_COUNT + FAIL_COUNT + INFO_COUNT))
PASS_PCT=$((PASS_COUNT * 100 / TOTAL))

echo "Tests Passed:  $PASS_COUNT"
echo "Tests Failed:  $FAIL_COUNT"
echo "Informational: $INFO_COUNT"
echo "Total Tests:   $TOTAL"
echo ""
echo "Pass Rate: $PASS_PCT%"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
  echo -e "${GREEN}🎉 ✅ ALL CRITICAL CHECKS PASSED - SYSTEM FULLY WIRED${NC}"
  echo ""
  info "Next Steps:"
  echo "  • Set API key: export ANTHROPIC_API_KEY='your-key'"
  echo "  • Run pilot: ./scripts/dgm_quickstart.sh"
  echo "  • View dashboards: open http://localhost:3000"
  exit 0
else
  echo -e "${RED}⚠️  Some critical checks failed. Review output above.${NC}"
  exit 1
fi

