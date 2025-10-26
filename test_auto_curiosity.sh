#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🧠 Testing Automatic Curiosity (RAG Auto-Query)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "== Baseline: Check metrics before query =="
BEFORE_RAG=$(curl -s http://localhost:8000/metrics | grep 'agi_rag_queries_total{outcome="ok"}' | awk '{print $2}' || echo "0")
BEFORE_CURIOSITY=$(curl -s http://localhost:8000/metrics | grep 'agi_curiosity_actions_total{kind="rag_query"}' | awk '{print $2}' || echo "0")

echo "Before: RAG queries = ${BEFORE_RAG}, Curiosity actions (rag_query) = ${BEFORE_CURIOSITY}"
echo ""

echo "== Test 1: Uncertain objective (should trigger RAG) =="
echo "Objective: 'Where is the router MCP provider configured?'"
echo ""

RESPONSE=$(curl -sS -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Where is the router MCP provider configured?",
    "context": {},
    "tools": [],
    "max_steps": 5
  }')

echo "$RESPONSE" | jq '{
  task_id,
  status,
  trace: .trace | map({step, agent, action, details: (.details | if type == "object" then keys else . end)})
}'
echo ""

echo "== Check: Did RAG get consulted? =="
TRACE_HAS_RAG=$(echo "$RESPONSE" | jq '.trace[] | select(.action == "rag_consulted" or .action == "rag_empty" or .action == "rag_failed")' | wc -l)
if [ "$TRACE_HAS_RAG" -gt 0 ]; then
  echo "✅ RAG was consulted (found $TRACE_HAS_RAG trace entries)"
else
  echo "⚠️  RAG was NOT consulted (trace has no rag_* actions)"
fi
echo ""

echo "== Check: Did metrics increment? =="
AFTER_RAG=$(curl -s http://localhost:8000/metrics | grep 'agi_rag_queries_total{outcome="ok"}' | awk '{print $2}' || echo "0")
AFTER_CURIOSITY=$(curl -s http://localhost:8000/metrics | grep 'agi_curiosity_actions_total{kind="rag_query"}' | awk '{print $2}' || echo "0")

echo "After: RAG queries = ${AFTER_RAG}, Curiosity actions (rag_query) = ${AFTER_CURIOSITY}"

RAG_DELTA=$(echo "${AFTER_RAG} - ${BEFORE_RAG}" | bc)
CURIOSITY_DELTA=$(echo "${AFTER_CURIOSITY} - ${BEFORE_CURIOSITY}" | bc)

if [ "$RAG_DELTA" -gt 0 ] || [ "$CURIOSITY_DELTA" -gt 0 ]; then
  echo "✅ Metrics incremented! (RAG +${RAG_DELTA}, Curiosity +${CURIOSITY_DELTA})"
else
  echo "⚠️  Metrics did NOT increment (RAG +${RAG_DELTA}, Curiosity +${CURIOSITY_DELTA})"
fi
echo ""

echo "== Test 2: Empty tool list (should trigger doctor + auto-expand) =="
echo "Objective: 'Simple task' with tools: []"
echo ""

RESPONSE2=$(curl -sS -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Simple task",
    "context": {},
    "tools": [],
    "max_steps": 3
  }')

TRACE_HAS_GUARDIAN=$(echo "$RESPONSE2" | jq '.trace[] | select(.agent == "guardian")' | wc -l)
TRACE_HAS_DOCTOR=$(echo "$RESPONSE2" | jq '.trace[] | select(.action == "doctor_consulted")' | wc -l)

if [ "$TRACE_HAS_GUARDIAN" -gt 0 ]; then
  echo "✅ Guardian expanded empty tool list"
else
  echo "⚠️  Guardian did NOT expand empty tool list"
fi

if [ "$TRACE_HAS_DOCTOR" -gt 0 ]; then
  echo "✅ Doctor was consulted (few tools)"
else
  echo "⚠️  Doctor was NOT consulted"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "Summary:"
echo "  • RAG auto-query on uncertainty: $([ "$TRACE_HAS_RAG" -gt 0 ] && echo "✅" || echo "⚠️ ")"
echo "  • Metrics tracking RAG usage:    $([ "$RAG_DELTA" -gt 0 ] && echo "✅" || echo "⚠️ ")"
echo "  • Empty tool list protection:    $([ "$TRACE_HAS_GUARDIAN" -gt 0 ] && echo "✅" || echo "⚠️ ")"
echo "  • Doctor consultation (sparse):  $([ "$TRACE_HAS_DOCTOR" -gt 0 ] && echo "✅" || echo "⚠️ ")"
echo ""
echo "Athena is now $([ "$TRACE_HAS_RAG" -gt 0 ] && [ "$RAG_DELTA" -gt 0 ] && echo "AUTOMATICALLY CURIOUS!" || echo "still passive (check logs)")"
echo "════════════════════════════════════════════════════════════════"


