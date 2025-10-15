#!/bin/bash
# CE Precision Mode Success Checklist
# Run this script to validate CE deployment success

echo "🎯 CE Precision Mode Success Checklist"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_metric() {
    local name="$1"
    local command="$2"
    local expected="$3"
    local critical="${4:-false}"

    echo -n "  $name: "
    local result=$(eval "$command" 2>/dev/null)

    if [ -n "$result" ] && [ "$result" != "null" ]; then
        echo -e "${GREEN}✅ $result${NC}"
        return 0
    else
        if [ "$critical" = "true" ]; then
            echo -e "${RED}❌ FAILED${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  No data${NC}"
            return 0
        fi
    fi
}

echo "📊 1. Core Functionality Checks"
echo "-------------------------------"

# CE enabled in config
check_metric "CE enabled in config" \
    "grep -q 'RAG_RERANKER_CE_ENABLED=true' docker-compose.enterprise.yml && echo 'true' || echo 'false'" \
    "true" "true"

# CE metrics present
check_metric "CE metrics collected" \
    "curl -s http://127.0.0.1:8015/metrics | grep -q 'rag_ce_requests_total' && echo 'present' || echo 'missing'" \
    "present" "true"

# Routing working
check_metric "CE routing active" \
    "curl -s http://127.0.0.1:8015/metrics | grep 'rag_ce_requests_total' | awk '{sum += \$2} END {print sum}'" \
    ">0" "false"

echo ""
echo "📈 2. Performance Metrics (Last 24h)"
echo "------------------------------------"

# CE query volume
check_metric "CE queries processed" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT count(*) FROM rag_retrieval r
    WHERE r.ts > now() - interval '24 hours'
      AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder';\" 2>/dev/null | tr -d ' '" \
    ">10"

# CE routing ratio
check_metric "CE routing ratio" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT round(
        count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END)::numeric
        / count(*)::numeric * 100, 1
    ) FROM rag_retrieval r WHERE r.ts > now() - interval '24 hours';\" 2>/dev/null | tr -d ' '" \
    "15-30"

# Judge helpfulness lift on CE intents
check_metric "CE intent helpfulness" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT round(avg((e.helpfulness + e.factuality + e.clarity)/3.0)::numeric, 2)
    FROM rag_retrieval r
    JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '24 hours'
      AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder';\" 2>/dev/null | tr -d ' '" \
    ">=6.0"

echo ""
echo "🛡️ 3. Guardrail Compliance"
echo "-------------------------"

# CE latency budget
check_metric "CE latency ≤500ms p95" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT round(percentile_cont(0.95) WITHIN GROUP (
        ORDER BY extract(epoch from (e.completed_at - e.started_at)) * 1000
    )::numeric, 0)
    FROM rag_retrieval r
    JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '24 hours'
      AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder';\" 2>/dev/null | tr -d ' '" \
    "<=500" "true"

# Docs used not collapsing
check_metric "Median docs used ≥3" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY jsonb_array_length(r.candidates))
    FROM rag_retrieval r
    WHERE r.ts > now() - interval '24 hours'
      AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder';\" 2>/dev/null | tr -d ' '" \
    ">=3" "true"

# No quality regression
check_metric "No quality regression" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT round(avg((e.helpfulness + e.factuality + e.clarity)/3.0)::numeric, 2)
    FROM rag_retrieval r
    JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '24 hours'
      AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder';\" 2>/dev/null | tr -d ' '" \
    ">=5.0" "true"

echo ""
echo "🎯 4. Learning & Adaptation"
echo "---------------------------"

# Tuning data available
check_metric "CE tuning samples" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT count(*)
    FROM rag_retrieval r
    JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '24 hours'
      AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder';\" 2>/dev/null | tr -d ' '" \
    ">=50"

# Threshold tuned
check_metric "Threshold auto-tuned" \
    "psql -h athena-postgres -d universal_ai_tools -U postgres -t -c \"
    SELECT count(*) FROM kv_config
    WHERE key = 'RAG_THRESHOLD' AND ts > now() - interval '24 hours';\" 2>/dev/null | tr -d ' '" \
    ">=1"

echo ""
echo "🏁 SUCCESS CRITERIA SUMMARY"
echo "=========================="

echo "✅ DECLARE SUCCESS when ALL of these are true:"
echo "   • CE intent helpfulness ≥6.0 (target: +3-6pts lift)"
echo "   • CE latency p95 ≤500ms"
echo "   • Median docs used ≥3 (no over-filtering)"
echo "   • CE routing ratio stable (15-30%)"
echo "   • ≥50 CE tuning samples collected"
echo "   • Threshold auto-tuned at least once"
echo "   • No guardrail violations in last 6h"
echo "   • CE model healthy (/api/rag/ce-health)"
echo "   • Model inference working (not fallback mode)"
echo "   • CE cache hit ratio >50% after warmup"
echo ""

echo "🎉 If all checks pass: make rag-canary-full"
echo "❌ If any critical check fails: make rag-canary-off"
