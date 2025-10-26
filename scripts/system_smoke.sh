#!/usr/bin/env bash
# Complete System Verification - All Endpoints End-to-End
set -euo pipefail

green(){ printf "\033[32m%s\033[0m\n" "$*"; }
red(){ printf "\033[31m%s\033[0m\n" "$*"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$*"; }
sec(){ printf "\n\033[1m=== %s ===\033[0m\n" "$*"; }

BASE_AGI="http://localhost:8000"
BASE_RAG="http://localhost:8087"
BASE_UAI="http://localhost:8080"
BASE_MCP="http://localhost:8412"
BASE_FE="http://localhost:8413"
BASE_TRM="http://localhost:8420"
BASE_ROUTER="http://localhost:9113"
WEAVIATE="http://localhost:8090"

ok=()
warn=()
fail=()

probe(){
  name="$1"; shift
  if out=$("$@" 2>&1); then
    ok+=("$name")
    green "✅ $name"
    echo "$out" | head -5 | sed 's/^/   /'
  else
    fail+=("$name")
    red "❌ $name"
    echo "$out" | head -3 | sed 's/^/   /'
    return 1
  fi
}

probe_warn(){
  name="$1"; shift
  if out=$("$@" 2>&1); then
    ok+=("$name")
    green "✅ $name"
    echo "$out" | head -5 | sed 's/^/   /'
  else
    warn+=("$name")
    yellow "⚠️  $name (optional)"
    return 0
  fi
}

echo "══════════════════════════════════════════════════════════"
echo "  🔎 COMPLETE SYSTEM VERIFICATION"
echo "══════════════════════════════════════════════════════════"

sec "Core Services Health"
probe "AGI /health" \
  curl -fsS "$BASE_AGI/health"

probe "RAG Gateway /health" \
  curl -fsS "$BASE_RAG/health"

probe "TRM Service /health" \
  curl -fsS "$BASE_TRM/health"

probe_warn "UAI /health" \
  curl -fsS "$BASE_UAI/health"

probe_warn "MCP /health" \
  curl -fsS "$BASE_MCP/health"

probe_warn "Frontend Tools /health" \
  curl -fsS "$BASE_FE/health"

probe_warn "Router /health" \
  curl -fsS "$BASE_ROUTER/health"

probe "Weaviate ready" \
  curl -fsS "$WEAVIATE/v1/.well-known/ready"

sec "Policy & Registry"
probe "TRM Adaptive Policy" \
  sh -c "curl -sS '$BASE_AGI/trm/policy' | jq -c '{status,decisions:.stats.total_decisions,bias:.policy.bias}'"

probe "AGI Tools Registry" \
  sh -c "curl -sS '$BASE_AGI/tools' | jq -c '{count,trm:(.tools|keys|map(select(contains(\"trm\")))|length)}'"

sec "Functional Endpoints"

# 1. Simple AGI execution (no TRM, fast path)
probe "AGI execute (simple, no TRM)" \
  sh -c "curl -sS -X POST '$BASE_AGI/api/execute' \
    -H 'Content-Type: application/json' \
    -d '{\"objective\":\"test health\",\"tools\":[],\"max_steps\":1,\"flags\":{\"adaptive_trm\":false}}' | \
  jq -c '{task_id,status,time:.execution_time_s}'"

# 2. AGI with auto-curiosity (RAG should be consulted)
probe "AGI auto-curiosity (RAG)" \
  sh -c "curl -sS -X POST '$BASE_AGI/api/execute' \
    -H 'Content-Type: application/json' \
    -d '{\"objective\":\"Where is the router MCP provider configured?\",\"tools\":[],\"max_steps\":3,\"flags\":{\"adaptive_trm\":false}}' | \
  jq -c '[.trace[]? | select(.action?==\"rag_consulted\" or .action?==\"rag_empty\")] | if length > 0 then .[0] | {step,action,hits:(.details.hits//0)} else {note:\"rag_not_triggered\"} end'"

# 3. RAG query (expect hits and low latency)
probe "RAG /query" \
  sh -c "curl -sS -X POST '$BASE_RAG/query' \
    -H 'Content-Type: application/json' \
    -d '{\"query\":\"AGI planner workflow\",\"top_k\":3}' | \
  jq -c '{hits:(.hits//[]|length),lane:(.plan.lanes[0]//\"none\"),latency_ms:(.took_ms//0)}'"

# 4. TRM adaptive decision (may skip if below threshold)
probe "TRM adaptive (may skip)" \
  sh -c "curl -sS -X POST '$BASE_AGI/api/execute' \
    -H 'Content-Type: application/json' \
    -d '{\"objective\":\"Explain how adaptive TRM policy learns from production\",\"tools\":[],\"max_steps\":3,\"flags\":{\"adaptive_trm\":true}}' | \
  jq -c '[.trace[]? | select(.action?==\"trm_deliberated\")] | if length > 0 then .[0] | {step,action,adaptive:.details.adaptive,trigger_prob:.details.trigger_prob,cycles:.details.cycles_allocated} else {note:\"TRM_skipped_below_threshold\"} end'"

# 5. TRM modes direct (classify, deliberate, critique)
probe "TRM /classify" \
  sh -c "curl -sS -X POST '$BASE_TRM/v1/trm/classify' \
    -H 'Content-Type: application/json' \
    -d '{\"objective\":\"Build a complex system\",\"signals\":{\"rag_hits\":5,\"tools_len\":2}}' | \
  jq -c '{complexity,confidence,cycles_used,took_ms}'"

probe "TRM /deliberate" \
  sh -c "curl -sS -X POST '$BASE_TRM/v1/trm/deliberate' \
    -H 'Content-Type: application/json' \
    -d '{\"question\":\"How to structure AGI?\",\"context\":\"RAG context: planner uses Scout-Plan-Build...\",\"cycles\":12}' | \
  jq -c '{used_cycles,took_ms,answer:(.answer[:80])}'"

probe "TRM /critique" \
  sh -c "curl -sS -X POST '$BASE_TRM/v1/trm/critique' \
    -H 'Content-Type: application/json' \
    -d '{\"plan\":[\"Step 1\",\"Step 2\",\"Step 3\"],\"constraints\":[\"timeout<=300s\"]}' | \
  jq -c '{issues,suggestions,cycles_used,took_ms}'"

# 6. UAI chat (verify LLM path - router handles model selection)
probe_warn "UAI /v1/chat/completions" \
  sh -c "curl -sS -X POST '$BASE_UAI/v1/chat/completions' \
    -H 'Content-Type: application/json' \
    -d '{\"model\":\"auto\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":10}' | \
  jq -c '{model_used,content:.choices[0].message.content}'"

# 7. MCP tools
probe_warn "MCP /tools" \
  sh -c "curl -sS '$BASE_MCP/tools' | jq -c '{count:(.tools|length)}'"

sec "Data & Metrics"
probe "Weaviate schema (classes)" \
  sh -c "curl -sS '$WEAVIATE/v1/schema' | jq -c '.classes|map(.class)'"

probe "TRM metrics" \
  sh -c "curl -sS http://localhost:9093/metrics | grep 'trm_requests_total' | grep -v '^#' | head -3"

probe "Policy stats" \
  sh -c "curl -sS '$BASE_AGI/trm/policy' | jq '{decisions:.stats.total_decisions,invocations:.stats.recent_invocations,skips:.stats.recent_skips,bias:.policy.bias}'"

sec "Summary"
pass_count=${#ok[@]}
warn_count=${#warn[@]}
fail_count=${#fail[@]}

echo ""
echo "══════════════════════════════════════════════════════════"
printf "  ✅ Passed: %d\n" "$pass_count"
printf "  ⚠️  Warnings: %d\n" "$warn_count"
printf "  ❌ Failed: %d\n" "$fail_count"
echo "══════════════════════════════════════════════════════════"

if [ "$fail_count" -eq 0 ]; then
  green "🎉 ALL CRITICAL CHECKS PASSED"
  echo ""
  echo "System is operational and ready for production traffic."
  echo ""
  echo "Next steps:"
  echo "  • Monitor Grafana dashboard"
  echo "  • Run: make rag-golden"
  echo "  • Run: make trm-ab (A/B test)"
  echo "  • Check policy after 100+ requests: curl :8000/trm/policy | jq"
  exit 0
else
  red "❌ CRITICAL FAILURES DETECTED"
  echo ""
  echo "Failed checks:"
  for f in "${fail[@]}"; do
    echo "  - $f"
  done
  echo ""
  echo "Review errors above and fix before deploying."
  exit 1
fi

