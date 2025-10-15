-- CE Bandit Router Monitoring Dashboard
-- Track explore/exploit performance and routing optimization

-- 1. Bandit Arm Performance (Last 24h)
SELECT
    date_trunc('hour', timestamp::timestamp) as hour,
    arm_used,
    count(*) as decisions,
    count(CASE WHEN exploration_used THEN 1 END) as explorations,
    avg(judge_improvement) as avg_judge_improvement,
    count(CASE WHEN judge_improvement > 1.0 THEN 1 END)::float / count(*) as win_rate
FROM (
    SELECT
        (routing_history->>'timestamp') as timestamp,
        routing_history->>'arm_used' as arm_used,
        (routing_history->>'exploration_used')::boolean as exploration_used,
        (routing_history->>'judge_improvement')::float as judge_improvement
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1  -- Assuming single row table for state
    ) t
) routing_data
WHERE timestamp::timestamp > now() - interval '24 hours'
GROUP BY 1, 2
ORDER BY 1, 2;

-- 2. Exploration vs Exploitation Effectiveness (Last 7 days)
SELECT
    exploration_used,
    count(*) as decisions,
    avg(judge_improvement) as avg_improvement,
    stddev(judge_improvement) as improvement_stddev,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY judge_improvement) as median_improvement,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY judge_improvement) as p95_improvement,
    count(CASE WHEN judge_improvement > 1.0 THEN 1 END)::float / count(*) as win_rate
FROM (
    SELECT
        (routing_history->>'exploration_used')::boolean as exploration_used,
        (routing_history->>'judge_improvement')::float as judge_improvement
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
) routing_data
WHERE (routing_history->>'timestamp')::timestamp > now() - interval '7 days'
GROUP BY 1
ORDER BY 1;

-- 3. Query Type Performance by Bandit Arm
SELECT
    arm_used,
    intent,
    count(*) as queries,
    avg(judge_improvement) as avg_improvement,
    count(CASE WHEN exploration_used THEN 1 END) as explorations,
    count(CASE WHEN judge_improvement > 1.0 THEN 1 END)::float / count(*) as win_rate
FROM (
    SELECT
        routing_history->>'arm_used' as arm_used,
        routing_history->>'intent' as intent,
        (routing_history->>'exploration_used')::boolean as exploration_used,
        (routing_history->>'judge_improvement')::float as judge_improvement
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
) routing_data
WHERE (routing_history->>'timestamp')::timestamp > now() - interval '7 days'
GROUP BY 1, 2
ORDER BY 1, 3 DESC;

-- 4. Bandit Learning Progress (Win Rate Trends)
SELECT
    date_trunc('day', timestamp::timestamp) as day,
    arm_used,
    count(*) as daily_decisions,
    count(CASE WHEN judge_improvement > 1.0 THEN 1 END)::float / count(*) as daily_win_rate,
    avg(judge_improvement) as daily_avg_improvement
FROM (
    SELECT
        (routing_history->>'timestamp') as timestamp,
        routing_history->>'arm_used' as arm_used,
        (routing_history->>'judge_improvement')::float as judge_improvement
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
) routing_data
WHERE timestamp::timestamp > now() - interval '30 days'
GROUP BY 1, 2
ORDER BY 1, 2;

-- 5. Exploration Efficiency (When Exploration Pays Off)
SELECT
    exploration_used,
    arm_used,
    count(*) as decisions,
    avg(judge_improvement) as avg_improvement,
    -- Exploration premium: how much better exploration performs
    avg(CASE WHEN exploration_used THEN judge_improvement END) -
    avg(CASE WHEN NOT exploration_used THEN judge_improvement END) as exploration_premium,
    -- Exploration hit rate: % of explorations that improve scores
    count(CASE WHEN exploration_used AND judge_improvement > 1.0 THEN 1 END)::float /
    nullif(count(CASE WHEN exploration_used THEN 1 END), 0) as exploration_hit_rate
FROM (
    SELECT
        (routing_history->>'exploration_used')::boolean as exploration_used,
        routing_history->>'arm_used' as arm_used,
        (routing_history->>'judge_improvement')::float as judge_improvement
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
) routing_data
WHERE (routing_history->>'timestamp')::timestamp > now() - interval '14 days'
GROUP BY 1, 2
ORDER BY 1, 3 DESC;

-- 6. Neural Context vs Bandit Decisions (Agreement Analysis)
SELECT
    CASE
        WHEN neural_ce_decision = final_ce_decision THEN 'agreement'
        ELSE 'disagreement'
    END as neural_bandit_agreement,
    count(*) as decisions,
    avg(judge_improvement) as avg_improvement,
    count(CASE WHEN exploration_used THEN 1 END) as explorations_in_group
FROM (
    SELECT
        (routing_history->>'neural_prediction'->>'use_ce')::boolean as neural_ce_decision,
        (routing_history->>'final_ce_decision')::boolean as final_ce_decision,
        (routing_history->>'exploration_used')::boolean as exploration_used,
        (routing_history->>'judge_improvement')::float as judge_improvement
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
) routing_data
WHERE (routing_history->>'timestamp')::timestamp > now() - interval '7 days'
  AND routing_history->>'neural_prediction' IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- 7. Confidence Bucket Analysis
SELECT
    CASE
        WHEN (routing_history->'neural_prediction'->>'confidence')::float >= 0.8 THEN 'high_confidence'
        WHEN (routing_history->'neural_prediction'->>'confidence')::float >= 0.6 THEN 'medium_confidence'
        ELSE 'low_confidence'
    END as confidence_bucket,
    count(*) as decisions,
    avg(judge_improvement) as avg_improvement,
    count(CASE WHEN exploration_used THEN 1 END) as explorations,
    count(CASE WHEN exploration_used THEN 1 END)::float / count(*) as exploration_rate
FROM (
    SELECT
        (routing_history->>'exploration_used')::boolean as exploration_used,
        (routing_history->>'judge_improvement')::float as judge_improvement,
        routing_history
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
) routing_data
WHERE (routing_history->>'timestamp')::timestamp > now() - interval '14 days'
GROUP BY 1
ORDER BY
    CASE confidence_bucket
        WHEN 'high_confidence' THEN 1
        WHEN 'medium_confidence' THEN 2
        ELSE 3
    END;

-- 8. Bandit Arm Evolution (Learning Over Time)
WITH arm_performance_over_time AS (
    SELECT
        date_trunc('day', (routing_history->>'timestamp')::timestamp) as day,
        routing_history->>'arm_used' as arm,
        count(*) as decisions,
        count(CASE WHEN (routing_history->>'judge_improvement')::float > 1.0 THEN 1 END)::float / count(*) as win_rate
    FROM (
        SELECT jsonb_array_elements(
            CASE WHEN routing_history IS NOT NULL
                 THEN routing_history
                 ELSE '[]'::jsonb
            END
        ) as routing_history
        FROM bandit_router_state
        WHERE id = 1
    ) t
    WHERE (routing_history->>'timestamp')::timestamp > now() - interval '30 days'
    GROUP BY 1, 2
),
arm_rankings AS (
    SELECT
        day,
        arm,
        win_rate,
        rank() OVER (PARTITION BY day ORDER BY win_rate DESC) as daily_rank
    FROM arm_performance_over_time
)
SELECT
    day,
    arm,
    win_rate,
    daily_rank
FROM arm_rankings
WHERE daily_rank <= 2  -- Top 2 arms per day
ORDER BY day, daily_rank;

-- Note: This assumes a bandit_router_state table exists with routing history.
-- In practice, you'd need to create this table or modify the router to persist state.
