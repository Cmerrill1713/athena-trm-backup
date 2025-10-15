-- CE Precision Mode Monitoring Dashboard
-- Execute these queries to track CE performance and ROI

-- 1. CE vs Cosine Performance Comparison (Last 24h)
SELECT
    CASE
        WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 'CE'
        ELSE 'Cosine'
    END as reranker_type,
    round(avg((e.helpfulness + e.factuality + e.clarity)/3.0)::numeric, 2) as avg_judge_score,
    round(avg(extract(epoch from (e.completed_at - e.started_at)) * 1000)::numeric, 0) as avg_latency_ms,
    count(*) as query_count,
    round(avg(jsonb_array_length(r.candidates))::numeric, 1) as avg_candidates
FROM rag_retrieval r
JOIN eval_results e ON e.interaction_id = r.interaction_id::text
WHERE r.ts > now() - interval '24 hours'
  AND jsonb_array_length(r.candidates) > 0
GROUP BY 1
ORDER BY 1;

-- 2. Intent-Stratified CE Performance (Last 24h)
SELECT
    COALESCE(NULLIF(e.intent, ''), 'unknown') as intent,
    CASE
        WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 'CE'
        ELSE 'Cosine'
    END as reranker_used,
    round(avg((e.helpfulness + e.factuality + e.clarity)/3.0)::numeric, 2) as avg_helpfulness,
    round(avg(extract(epoch from (e.completed_at - e.started_at)) * 1000)::numeric, 0) as p95_latency,
    count(*) as n_queries
FROM rag_retrieval r
JOIN eval_results e ON e.interaction_id = r.interaction_id::text
WHERE r.ts > now() - interval '24 hours'
GROUP BY 1, 2
ORDER BY 1, 2;

-- 3. CE Routing Ratio (What % of queries use CE?)
SELECT
    date_trunc('hour', r.ts) as hour,
    count(*) as total_queries,
    count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END) as ce_queries,
    round(
        count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END)::numeric
        / count(*)::numeric * 100, 1
    ) as ce_percentage
FROM rag_retrieval r
WHERE r.ts > now() - interval '24 hours'
GROUP BY 1
ORDER BY 1 DESC
LIMIT 10;

-- 4. CE Threshold Evolution (How CE tuning adapts)
SELECT
    date_trunc('hour', ts) as hour,
    value::numeric as threshold,
    lag(value::numeric) OVER (ORDER BY ts) as prev_threshold,
    round((value::numeric - lag(value::numeric) OVER (ORDER BY ts))::numeric, 3) as change
FROM kv_config
WHERE key = 'RAG_THRESHOLD'
  AND ts > now() - interval '7 days'
ORDER BY ts DESC
LIMIT 20;

-- 5. CE Guardrail Violations (Alert Triggers)
SELECT
    date_trunc('hour', r.ts) as hour,
    -- CE latency violations (>500ms p95)
    CASE WHEN percentile_cont(0.95) WITHIN GROUP (
        ORDER BY extract(epoch from (e.completed_at - e.started_at)) * 1000
    ) > 500 THEN 'LATENCY_VIOLATION' END as ce_latency_alert,

    -- Docs used violations (<3 median)
    CASE WHEN percentile_cont(0.5) WITHIN GROUP (
        ORDER BY jsonb_array_length(r.candidates)
    ) < 3 THEN 'OVERFILTER_VIOLATION' END as docs_used_alert,

    -- Quality violations (<5.0 helpfulness)
    CASE WHEN avg((e.helpfulness + e.factuality + e.clarity)/3.0) < 5.0
         THEN 'QUALITY_VIOLATION' END as quality_alert,

    count(*) as ce_query_count
FROM rag_retrieval r
JOIN eval_results e ON e.interaction_id = r.interaction_id::text
WHERE r.ts > now() - interval '24 hours'
  AND r.candidates::jsonb->0->>'reranker_type' = 'crossencoder'
GROUP BY 1
ORDER BY 1 DESC;

-- 6. CE Learning Progress (Samples for tuning)
SELECT
    date_trunc('day', r.ts) as day,
    count(*) as total_rag_queries,
    count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END) as ce_queries,
    count(e.interaction_id) as evaluated_queries,
    count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END) as ce_evaluated
FROM rag_retrieval r
LEFT JOIN eval_results e ON e.interaction_id = r.interaction_id::text
WHERE r.ts > now() - interval '7 days'
GROUP BY 1
ORDER BY 1 DESC;
