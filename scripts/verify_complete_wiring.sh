#!/bin/bash
# Complete System Wiring Verification
# Proves all integrations are connected and functional

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ATHENA COMPLETE WIRING VERIFICATION                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/.."
PASS=0
TOTAL=0

function test_check() {
    TOTAL=$((TOTAL + 1))
    if eval "$1" > /dev/null 2>&1; then
        echo "✅ $2"
        PASS=$((PASS + 1))
        return 0
    else
        echo "❌ $2"
        return 1
    fi
}

function test_check_output() {
    TOTAL=$((TOTAL + 1))
    OUTPUT=$(eval "$1" 2>&1)
    if echo "$OUTPUT" | grep -q "$2"; then
        echo "✅ $3"
        PASS=$((PASS + 1))
        return 0
    else
        echo "❌ $3"
        echo "   Expected: $2"
        echo "   Got: $(echo $OUTPUT | head -c 50)..."
        return 1
    fi
}

echo "━━━ 1. CODE IMPORTS (Integration Layer) ━━━"
test_check "python3 -c 'from athena_master_orchestrator import AthenaMasterOrchestrator'" \
    "Master Orchestrator imports"

test_check "python3 -c 'from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter'" \
    "DGM Governance Adapter imports"

test_check "python3 -c 'from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator'" \
    "Verdict Validator imports"

test_check "python3 -c 'from governance.research.dgm.dgm_agi_bridge import DGMAGIBridge'" \
    "DGM-AGI Bridge imports"

test_check "python3 -c 'from workflows.end_to_end_integration import run_workflow'" \
    "End-to-End Workflows import"

echo ""
echo "━━━ 2. SYSTEM INITIALIZATION ━━━"
test_check_output "python3 athena_master_orchestrator.py status 2>&1" \
    "governance.*true" \
    "Master Orchestrator initializes with Governance active"

test_check_output "python3 athena_master_orchestrator.py status 2>&1" \
    "dgm.*true" \
    "Master Orchestrator initializes with DGM active"

echo ""
echo "━━━ 3. RUNNING SERVICES ━━━"
test_check "curl -fsS http://localhost:8888/health" \
    "Athena API responding (8888)"

test_check "curl -fsS http://localhost:9109/metrics" \
    "Governance Metrics Exporter (9109)"

test_check "curl -fsS http://localhost:9110/health" \
    "Governance Orchestrator (9110)"

test_check "curl -fsS http://localhost:9111/health" \
    "Governance Canary Monitor (9111)"

test_check "curl -fsS http://localhost:9090/-/healthy" \
    "Prometheus (9090)"

echo ""
echo "━━━ 4. VERDICT ENDPOINT (End-to-End Flow) ━━━"

# Test verdict submission
TASK_ID="wire-verify-$(date +%s)"
VERDICT_RESPONSE=$(curl -s -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\",\"verdict\":\"PASS\",\"ece_post\":0.95,\"entropy\":0.05,\"actions\":[\"PROMOTE\"],\"ts\":\"$(date -u +%FT%TZ)\"}")

test_check_output "echo '$VERDICT_RESPONSE'" \
    "applied" \
    "Verdict POST returns 'applied' status"

test_check_output "echo '$VERDICT_RESPONSE'" \
    "$TASK_ID" \
    "Verdict echoes back task_id"

echo ""
echo "━━━ 5. METRICS EXPORT ━━━"
test_check "curl -s http://localhost:9110/metrics | grep -q 'governance_verdicts_total'" \
    "Governance verdicts metric exists"

test_check "curl -s http://localhost:9110/metrics | grep -q 'governance_actions_total'" \
    "Governance actions metric exists"

test_check "curl -s http://localhost:9110/metrics | grep -q 'governance_ece_post'" \
    "Governance ECE metric exists"

echo ""
echo "━━━ 6. IDEMPOTENCE CHECK ━━━"
# Re-post same verdict
IDEM_RESPONSE=$(curl -s -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\",\"verdict\":\"PASS\",\"ece_post\":0.95,\"entropy\":0.05,\"actions\":[\"PROMOTE\"],\"ts\":\"$(date -u +%FT%TZ)\"}")

test_check_output "echo '$IDEM_RESPONSE'" \
    "idempotent_skip" \
    "Duplicate verdict returns idempotent_skip"

echo ""
echo "━━━ 7. STATE PERSISTENCE ━━━"
test_check "test -f exec_state.json" \
    "State file exists (exec_state.json)"

test_check "test -f exec_action_ledger.jsonl" \
    "Action ledger exists (exec_action_ledger.jsonl)"

test_check "grep -q '$TASK_ID' exec_action_ledger.jsonl" \
    "Test verdict logged to ledger"

echo ""
echo "━━━ 8. DGM INTEGRATION ━━━"
test_check "test -f governance/research/dgm/dgm_governance_adapter.py" \
    "DGM Governance Adapter file exists"

test_check "test -f governance/judicial/evaluation/dgm_verdict_validator.py" \
    "DGM Verdict Validator file exists"

test_check "test -f governance/executive/orchestration/dgm_orchestrator.py" \
    "DGM Executive Orchestrator file exists"

test_check "test -f governance/research/dgm/dgm_agi_bridge.py" \
    "DGM-AGI Bridge file exists"

echo ""
echo "━━━ 9. CONFIGURATION ━━━"
test_check "test -f config/athena_master_config.yaml" \
    "Master config exists"

test_check "test -f governance/research/dgm/config/dgm_config.yaml" \
    "DGM config exists"

test_check "test -f governance/legislative/self_modification_policy.yaml" \
    "Constitutional policy exists"

echo ""
echo "━━━ 10. WORKFLOWS & AUTOMATION ━━━"
test_check "test -f workflows/end_to_end_integration.py" \
    "End-to-end workflows file exists"

test_check "test -f .github/workflows/dgm-experiment.yml" \
    "DGM experiment workflow exists"

test_check "test -f .github/workflows/game-day-drill.yml" \
    "Game day drill workflow exists"

test_check "test -f .github/workflows/security-scan.yml" \
    "Security scan workflow exists"

echo ""
echo "━━━ 11. MONITORING ━━━"
test_check "test -f monitoring/grafana/dashboards/athena-unified.json" \
    "Athena unified dashboard exists"

test_check "test -f monitoring/grafana/dashboards/dgm-evolution.json" \
    "DGM evolution dashboard exists"

test_check "test -f governance/observability/dgm_metrics.py" \
    "DGM metrics collector exists"

echo ""
echo "━━━ 12. DOCUMENTATION ━━━"
test_check "test -f SYSTEM_ARCHITECTURE.md" \
    "System Architecture doc exists"

test_check "test -f DGM_INTEGRATION_SUMMARY.md" \
    "DGM Integration Summary exists"

test_check "test -f WIRING_DEFINITION.md" \
    "Wiring Definition exists"

test_check "test -f RUNBOOKS/DGM_OPERATOR_RUNBOOK.md" \
    "Operator Runbook exists"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  VERIFICATION RESULTS                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Tests Passed: $PASS/$TOTAL"
echo ""

if [ $PASS -eq $TOTAL ]; then
    echo "🎉 ✅ ALL WIRING VERIFIED - SYSTEM FULLY INTEGRATED"
    echo ""
    echo "Next Steps:"
    echo "  1. Set API key: export ANTHROPIC_API_KEY='your-key'"
    echo "  2. Run pilot: ./scripts/dgm_quickstart.sh"
    echo "  3. View dashboards: open http://localhost:3000"
    exit 0
else
    echo "⚠️  Some checks failed. Review output above."
    exit 1
fi

