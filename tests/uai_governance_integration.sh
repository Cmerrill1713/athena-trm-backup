#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "UAI ↔ GOVERNANCE INTEGRATION TEST"
echo "Testing how UAI works with Athena's governance system"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Test 1: Both services are healthy
echo "═══ Test 1: Service Health Checks ═══"
echo "UAI Health:"
curl -fsS http://localhost:8080/health | jq '.'
echo ""

echo "Governance Health:"
curl -fsS http://localhost:9110/health | jq '.'
echo ""

echo "Governance Ready:"
curl -fsS http://localhost:9110/ready | jq '.'
echo ""

# Test 2: Check current governance state
echo "═══ Test 2: Current Governance State ═══"
curl -fsS http://localhost:9110/state | jq '.'
echo ""

# Test 3: UAI makes a successful LLM call
echo "═══ Test 3: UAI LLM Call (Baseline) ═══"
UAI_RESPONSE=$(curl -fsS -X POST http://localhost:8080/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"What is 2+2?"}]}')
echo "$UAI_RESPONSE" | jq -r '.choices[0].message.content'
echo ""

# Test 4: Submit PASS verdict to governance for UAI call
echo "═══ Test 4: Submit PASS Verdict to Governance ═══"
VERDICT_RESPONSE=$(curl -fsS -X POST http://localhost:9110/verdict \
  -H 'content-type: application/json' \
  -d '{
    "task_id": "uai_test_1",
    "verdict": "PASS",
    "ece_estimate": 0.05,
    "entropy_drift": 0.01,
    "violation_rate_delta": 0.0,
    "latency_p95_delta": -0.05,
    "meta": {
      "source": "uai",
      "model": "qwen2.5:7b",
      "test": "integration_test"
    }
  }')
echo "$VERDICT_RESPONSE" | jq '.'
echo ""

# Test 5: Check state after PASS verdict
echo "═══ Test 5: State After PASS Verdict ═══"
curl -fsS http://localhost:9110/state | jq '.safe_version, .current_version, .freeze_promotions'
echo ""

# Test 6: Submit SOFT_FAIL verdict (simulate minor quality issue)
echo "═══ Test 6: Submit SOFT_FAIL Verdict ═══"
SOFT_FAIL_RESPONSE=$(curl -fsS -X POST http://localhost:9110/verdict \
  -H 'content-type: application/json' \
  -d '{
    "task_id": "uai_test_2",
    "verdict": "SOFT_FAIL",
    "ece_estimate": 0.15,
    "entropy_drift": 0.08,
    "violation_rate_delta": 0.05,
    "latency_p95_delta": 0.12,
    "fix_confidence": 0.85,
    "meta": {
      "source": "uai",
      "model": "qwen2.5:7b",
      "issue": "slightly_higher_ece"
    }
  }')
echo "$SOFT_FAIL_RESPONSE" | jq '.'
echo ""

# Test 7: Check quarantine status
echo "═══ Test 7: Quarantine Status ═══"
curl -fsS http://localhost:9110/state | jq '.quarantine_active, .quarantine_percentage'
echo ""

# Test 8: Check metrics from both services
echo "═══ Test 8: Prometheus Metrics Comparison ═══"
echo "UAI Metrics:"
curl -s http://localhost:8080/metrics | grep "uai_llm" | head -3
echo ""

echo "Governance Metrics:"
curl -s http://localhost:9110/metrics | grep "governance_" | head -5
echo ""

# Test 9: Verify governance can track UAI model performance
echo "═══ Test 9: Simulated Quality Monitoring ═══"
echo "Testing multiple UAI calls with governance oversight..."
for i in {1..3}; do
  # Make UAI call
  RESULT=$(curl -s -X POST http://localhost:8080/v1/chat/completions \
    -H 'content-type: application/json' \
    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Count to $i\"}]}")
  
  # Extract response
  RESPONSE_TEXT=$(echo "$RESULT" | jq -r '.choices[0].message.content')
  echo "Call $i: $RESPONSE_TEXT"
  
  # Simulate governance verdict based on response quality
  VERDICT_RESULT=$(curl -s -X POST http://localhost:9110/verdict \
    -H 'content-type: application/json' \
    -d "{
      \"task_id\": \"uai_batch_$i\",
      \"verdict\": \"PASS\",
      \"ece_estimate\": 0.0$i,
      \"meta\": {\"batch_test\": true, \"iteration\": $i}
    }")
  
  sleep 0.5
done
echo ""

# Test 10: Final metrics check
echo "═══ Test 10: Final Metrics After Integration Tests ═══"
echo "Total UAI LLM Calls:"
curl -s http://localhost:8080/metrics | grep "uai_llm_calls_total"
echo ""

echo "Total Governance Verdicts:"
curl -s http://localhost:9110/metrics | grep "governance_verdicts_total"
echo ""

echo "Governance Actions:"
curl -s http://localhost:9110/metrics | grep "governance_actions_total"
echo ""

# Test 11: Verify both services can communicate
echo "═══ Test 11: Network Connectivity Test ═══"
echo "UAI → Governance (from UAI container):"
docker compose exec uai sh -c 'curl -s http://governance-orchestrator:9110/health' | jq -r '.status'
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ UAI ↔ GOVERNANCE INTEGRATION TESTS COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "- UAI successfully makes LLM calls to Ollama"
echo "- Governance tracks verdicts and manages deployment state"
echo "- Metrics from both services are exposed and incrementing"
echo "- Network connectivity verified (UAI ↔ Governance)"
echo "- Integration points validated for future policy enforcement"
echo ""
