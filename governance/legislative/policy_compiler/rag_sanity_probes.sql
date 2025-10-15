-- RAG Reranker Sanity Probes
-- Copy/paste these queries to monitor the rollout

-- 1. Threshold actually updating
SELECT key, value, ts
FROM kv_config
WHERE key = 'RAG_THRESHOLD'
ORDER BY ts DESC
LIMIT 1;

-- 2. Candidates are recorded
SELECT COUNT(*) as total_candidates_recorded
FROM rag_retrieval
WHERE ts > now() - interval '24 hours';

-- 3. Judge improvement (coarse) - Compare avg helpfulness last 6h vs prior 6h
WITH recent AS (
    SELECT
        avg((e.helpfulness + e.factuality + e.clarity) / 3.0) as avg_helpfulness,
        count(*) as sample_count
    FROM rag_retrieval r
    JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '6 hours'
),
prior AS (
    SELECT
        avg((e.helpfulness + e.factuality + e.clarity) / 3.0) as avg_helpfulness,
        count(*) as sample_count
    FROM rag_retrieval r
    JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts BETWEEN now() - interval '12 hours' AND now() - interval '6 hours'
)
SELECT
    recent.avg_helpfulness as last_6h_helpfulness,
    prior.avg_helpfulness as prior_6h_helpfulness,
    recent.avg_helpfulness - prior.avg_helpfulness as improvement,
    recent.sample_count as recent_samples,
    prior.sample_count as prior_samples
FROM recent, prior;

-- 4. RAG tuning data quality check
SELECT
    date_trunc('hour', r.ts) as hour,
    count(*) as queries,
    avg(jsonb_array_length(r.candidates)) as avg_candidates,
    count(DISTINCT e.interaction_id) as evaluated_queries
FROM rag_retrieval r
LEFT JOIN eval_results e ON e.interaction_id = r.interaction_id::text
WHERE r.ts > now() - interval '24 hours'
GROUP BY 1
ORDER BY 1 DESC;

-- 5. Threshold stability check (should not change too frequently)
SELECT
    date_trunc('hour', ts) as hour,
    value as threshold,
    count(*) as changes_in_hour
FROM kv_config
WHERE key = 'RAG_THRESHOLD' AND ts > now() - interval '24 hours'
GROUP BY 1, 2
ORDER BY 1 DESC;

-- 6. Performance regression check
SELECT
    date_trunc('hour', r.ts) as hour,
    avg(jsonb_array_length(r.candidates)) as avg_candidates_before_rerank,
    count(CASE WHEN c->>'used' = 'true' THEN 1 END) * 1.0 / count(*) as rerank_usage_rate
FROM rag_retrieval r,
     jsonb_array_elements(r.candidates) as c
WHERE r.ts > now() - interval '24 hours'
GROUP BY 1
ORDER BY 1 DESC;
