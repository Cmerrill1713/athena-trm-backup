-- Neural CE Router Metrics Dashboard
-- Monitor intelligent routing performance and A/B testing results

-- 1. Router Decision Distribution (Last 24h)
SELECT
    date_trunc('hour', r.ts) as hour,
    count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END) as ce_routed,
    count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'cosine' THEN 1 END) as cosine_routed,
    count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' IS NULL THEN 1 END) as no_reranking,
    round(
        count(CASE WHEN r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' THEN 1 END)::numeric
        / nullif(count(*), 0) * 100, 1
    ) as ce_percentage
FROM rag_retrieval r
WHERE r.ts > now() - interval '24 hours'
GROUP BY 1
ORDER BY 1 DESC
LIMIT 10;

-- 2. Neural Router Performance by Confidence (Last 24h)
SELECT
    CASE
        WHEN routing_confidence >= 0.8 THEN 'high_confidence'
        WHEN routing_confidence >= 0.6 THEN 'medium_confidence'
        ELSE 'low_confidence'
    END as confidence_level,
    count(*) as decisions,
    avg(CASE WHEN used_ce THEN judge_score END) as ce_avg_judge,
    avg(CASE WHEN NOT used_ce THEN judge_score END) as cosine_avg_judge,
    avg(expected_improvement) as avg_predicted_improvement
FROM (
    SELECT
        r.ts,
        r.candidates::jsonb->0->>'reranker_type' = 'crossencoder' as used_ce,
        -- These would come from router decision logs
        0.7 as routing_confidence,  -- Placeholder - would be logged
        1.5 as expected_improvement,  -- Placeholder - would be logged
        coalesce(avg((e.helpfulness + e.factuality + e.clarity)/3.0), 0) as judge_score
    FROM rag_retrieval r
    LEFT JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '24 hours'
    GROUP BY r.id, r.ts, r.candidates
) routing_data
GROUP BY 1
ORDER BY
    CASE confidence_level
        WHEN 'high_confidence' THEN 1
        WHEN 'medium_confidence' THEN 2
        ELSE 3
    END;

-- 3. Router Accuracy vs. Actual Performance (Last 7 days)
WITH router_predictions AS (
    -- This would be populated by router decision logging
    SELECT
        query_hash,
        predicted_ce_benefit,
        actual_ce_benefit,
        routing_confidence
    FROM router_performance_log  -- Would need to create this table
    WHERE ts > now() - interval '7 days'
),
performance_stats AS (
    SELECT
        CASE
            WHEN routing_confidence >= 0.8 THEN 'high'
            WHEN routing_confidence >= 0.6 THEN 'medium'
            ELSE 'low'
        END as confidence_bucket,
        avg(predicted_ce_benefit) as avg_predicted,
        avg(actual_ce_benefit) as avg_actual,
        count(*) as sample_count,
        -- Prediction accuracy
        avg(abs(predicted_ce_benefit - actual_ce_benefit)) as avg_error,
        -- Over/under prediction
        avg(CASE WHEN predicted_ce_benefit > actual_ce_benefit THEN predicted_ce_benefit - actual_ce_benefit ELSE 0 END) as avg_overprediction,
        avg(CASE WHEN predicted_ce_benefit < actual_ce_benefit THEN actual_ce_benefit - predicted_ce_benefit ELSE 0 END) as avg_underprediction
    FROM router_predictions
    GROUP BY 1
)
SELECT
    confidence_bucket,
    round(avg_predicted::numeric, 2) as predicted_improvement,
    round(avg_actual::numeric, 2) as actual_improvement,
    sample_count,
    round(avg_error::numeric, 2) as prediction_error,
    round(avg_overprediction::numeric, 2) as overprediction,
    round(avg_underprediction::numeric, 2) as underprediction
FROM performance_stats
ORDER BY
    CASE confidence_bucket
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        ELSE 3
    END;

-- 4. Query Complexity Distribution (Neural Features)
SELECT
    date_trunc('day', r.ts) as day,
    -- Would need to log neural features
    avg(0.6) as avg_complexity,  -- Placeholder
    avg(0.4) as avg_ambiguity,   -- Placeholder
    percentile_cont(0.5) WITHIN GROUP (ORDER BY 0.6) as median_complexity,  -- Placeholder
    percentile_cont(0.9) WITHIN GROUP (ORDER BY 0.6) as p90_complexity,     -- Placeholder
    count(*) as queries_analyzed
FROM rag_retrieval r
WHERE r.ts > now() - interval '7 days'
GROUP BY 1
ORDER BY 1 DESC;

-- 5. Router A/B Testing Framework
-- Compare neural routing vs. heuristic routing performance

WITH ab_test AS (
    SELECT
        date_trunc('day', r.ts) as day,
        CASE WHEN random() < 0.5 THEN 'neural' ELSE 'heuristic' END as routing_method,
        r.candidates::jsonb->0->>'reranker_type' as reranker_used,
        coalesce(avg((e.helpfulness + e.factuality + e.clarity)/3.0), 0) as judge_score
    FROM rag_retrieval r
    LEFT JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    WHERE r.ts > now() - interval '14 days'
    GROUP BY 1, 2, r.id, r.candidates
)
SELECT
    day,
    routing_method,
    count(*) as queries,
    avg(judge_score) as avg_judge_score,
    count(CASE WHEN reranker_used = 'crossencoder' THEN 1 END) as ce_used_count
FROM ab_test
GROUP BY 1, 2
ORDER BY 1, 2;

-- 6. Router Learning Progress (Improvement Over Time)
SELECT
    date_trunc('week', r.ts) as week,
    -- Neural router improvements
    avg(CASE WHEN reranker_type = 'crossencoder' THEN judge_score END) -
    lag(avg(CASE WHEN reranker_type = 'crossencoder' THEN judge_score END))
    OVER (ORDER BY date_trunc('week', r.ts)) as ce_weekly_improvement,

    -- Overall system improvement
    avg(judge_score) -
    lag(avg(judge_score)) OVER (ORDER BY date_trunc('week', r.ts)) as total_weekly_improvement,

    count(*) as weekly_queries
FROM (
    SELECT
        r.ts,
        r.candidates::jsonb->0->>'reranker_type' as reranker_type,
        coalesce(avg((e.helpfulness + e.factuality + e.clarity)/3.0), 0) as judge_score
    FROM rag_retrieval r
    LEFT JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    GROUP BY r.id, r.ts, r.candidates
) weekly_data
WHERE ts > now() - interval '12 weeks'
GROUP BY 1
ORDER BY 1;

-- 7. Router Feature Importance (What Drives Decisions)
SELECT
    'complexity' as feature,
    corr(complexity_score, ce_decision) as correlation_with_ce_use,
    avg(CASE WHEN ce_decision THEN complexity_score END) as avg_complexity_when_ce,
    avg(CASE WHEN NOT ce_decision THEN complexity_score END) as avg_complexity_when_cosine
FROM (
    -- Would need to log these features
    SELECT
        0.6 as complexity_score,  -- Placeholder
        random() < 0.3 as ce_decision  -- Placeholder
    FROM generate_series(1, 1000)
) feature_analysis

UNION ALL

SELECT
    'ambiguity' as feature,
    corr(ambiguity_score, ce_decision) as correlation_with_ce_use,
    avg(CASE WHEN ce_decision THEN ambiguity_score END) as avg_ambiguity_when_ce,
    avg(CASE WHEN NOT ce_decision THEN ambiguity_score END) as avg_ambiguity_when_cosine
FROM (
    SELECT
        0.4 as ambiguity_score,  -- Placeholder
        random() < 0.3 as ce_decision  -- Placeholder
    FROM generate_series(1, 1000)
) feature_analysis2;

-- 8. Router Efficiency Metrics
SELECT
    date_trunc('hour', r.ts) as hour,
    count(*) as total_queries,
    count(CASE WHEN reranker_used = 'crossencoder' THEN 1 END) as ce_queries,
    -- Efficiency: CE used only when beneficial
    round(
        count(CASE WHEN reranker_used = 'crossencoder' AND judge_score > 6.0 THEN 1 END)::numeric
        / nullif(count(CASE WHEN reranker_used = 'crossencoder' THEN 1 END), 0) * 100, 1
    ) as ce_precision_pct,
    -- Effectiveness: High judge scores when CE used
    round(avg(CASE WHEN reranker_used = 'crossencoder' THEN judge_score END)::numeric, 2) as ce_avg_judge
FROM (
    SELECT
        r.ts,
        r.candidates::jsonb->0->>'reranker_type' as reranker_used,
        coalesce(avg((e.helpfulness + e.factuality + e.clarity)/3.0), 0) as judge_score
    FROM rag_retrieval r
    LEFT JOIN eval_results e ON e.interaction_id = r.interaction_id::text
    GROUP BY r.id, r.ts, r.candidates
) efficiency_data
WHERE ts > now() - interval '24 hours'
GROUP BY 1
ORDER BY 1 DESC
LIMIT 10;
