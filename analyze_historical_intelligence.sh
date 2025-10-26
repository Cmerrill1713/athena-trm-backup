#!/bin/bash

echo "🧠 ANALYZING HISTORICAL SYSTEM INTELLIGENCE"
echo "============================================"
echo ""

echo "1️⃣ Routing Patterns Analysis (50 Historical Decisions)"
echo "-------------------------------------------------------"

docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT 
  selected_model,
  COUNT(*) as usage_count,
  ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
  ROUND((COUNT(*) FILTER (WHERE success = true)::float / COUNT(*)) * 100, 1) as success_rate_pct
FROM routing_outcomes
GROUP BY selected_model
ORDER BY usage_count DESC;
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Query Pattern Recognition"
echo "------------------------------"

docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT 
  CASE 
    WHEN prompt LIKE '%weather%' THEN 'Weather Queries'
    WHEN prompt LIKE '%Debug%' OR prompt LIKE '%code%' THEN 'Code Analysis'
    WHEN prompt LIKE '%Summarize%' OR prompt LIKE '%paper%' THEN 'Research'
    WHEN prompt LIKE '%image%' OR prompt LIKE '%Analyze%' THEN 'Vision'
    ELSE 'Other'
  END as query_category,
  COUNT(*) as count,
  selected_model as preferred_model
FROM routing_outcomes
GROUP BY query_category, selected_model
ORDER BY count DESC
LIMIT 10;
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Most Recent Routing Decisions"
echo "----------------------------------"

docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT 
  id,
  LEFT(prompt, 40) as prompt_preview,
  selected_model,
  latency_ms,
  success
FROM routing_outcomes
ORDER BY created_at DESC
LIMIT 5;
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Can We Use This for Adaptive Learning?"
echo "-------------------------------------------"

echo "Querying routing success patterns:"
docker exec athena-postgres psql -U postgres -d athena_db -c "
SELECT 
  selected_model,
  ROUND(AVG(latency_ms)::numeric, 2) as avg_latency,
  COUNT(*) FILTER (WHERE success = true) as successes,
  COUNT(*) as total,
  ROUND((COUNT(*) FILTER (WHERE success = true)::float / COUNT(*)) * 100, 1) || '%' as success_rate
FROM routing_outcomes
WHERE selected_model IS NOT NULL
GROUP BY selected_model
HAVING COUNT(*) > 2
ORDER BY success_rate DESC;
" 2>/dev/null

echo ""
echo "💡 These patterns can feed into Adaptive TRM learning!"
echo ""

echo "============================================"
echo "✅ Historical Intelligence Analysis Complete"

