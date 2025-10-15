-- Personalization v1 Monitoring Dashboard
-- Track user preference learning and personalization impact

-- 1. User Profile Statistics
SELECT
    count(*) as total_profiles,
    avg(interaction_count) as avg_interactions,
    count(CASE WHEN interaction_count > 5 THEN 1 END) as active_profiles,
    count(CASE WHEN last_updated > now() - interval '7 days' THEN 1 END) as recently_active
FROM user_profiles;

-- 2. Preference Distribution (Last 30 days)
SELECT
    preferred_length,
    preferred_tone,
    evidence_appetite,
    count(*) as user_count
FROM user_profiles
WHERE last_updated > now() - interval '30 days'
GROUP BY 1, 2, 3
ORDER BY user_count DESC;

-- 3. Learning Signals by Type (Last 7 days)
SELECT
    signal_type,
    signal_value,
    count(*) as signal_count,
    round(avg(confidence)::numeric, 2) as avg_confidence
FROM preference_signals
WHERE ts > now() - interval '7 days'
GROUP BY 1, 2
ORDER BY 1, signal_count DESC;

-- 4. Personalization Impact on Judge Scores
SELECT
    CASE WHEN up.user_id IS NOT NULL THEN 'personalized' ELSE 'non_personalized' END as personalization_status,
    round(avg((e.helpfulness + e.factuality + e.clarity)/3.0)::numeric, 2) as avg_helpfulness,
    round(avg(extract(epoch from (e.completed_at - e.started_at)) * 1000)::numeric, 0) as avg_latency,
    count(*) as query_count
FROM eval_results e
LEFT JOIN user_profiles up ON up.user_id = e.user_id  -- Assuming eval_results has user_id
WHERE e.ts > now() - interval '7 days'
GROUP BY 1
ORDER BY 1;

-- 5. Preference Evolution Over Time
SELECT
    date_trunc('day', ps.ts) as day,
    ps.signal_type,
    mode() WITHIN GROUP (ORDER BY ps.signal_value) as most_common_preference,
    count(*) as signals_learned
FROM preference_signals ps
WHERE ps.ts > now() - interval '30 days'
GROUP BY 1, 2
ORDER BY 1, 2;

-- 6. User Engagement with Personalization
SELECT
    up.interaction_count as profile_interactions,
    count(DISTINCT e.interaction_id) as evaluated_interactions,
    round(avg((e.helpfulness + e.factuality + e.clarity)/3.0)::numeric, 2) as avg_helpfulness
FROM user_profiles up
LEFT JOIN eval_results e ON e.user_id = up.user_id  -- Assuming eval_results has user_id
    AND e.ts > now() - interval '30 days'
WHERE up.last_updated > now() - interval '30 days'
GROUP BY up.user_id, up.interaction_count
ORDER BY up.interaction_count DESC
LIMIT 20;

-- 7. Personalization Effectiveness by Preference Type
WITH user_perf AS (
    SELECT
        up.user_id,
        up.preferred_length,
        up.preferred_tone,
        up.evidence_appetite,
        avg((e.helpfulness + e.factuality + e.clarity)/3.0) as avg_helpfulness,
        count(e.interaction_id) as eval_count
    FROM user_profiles up
    JOIN eval_results e ON e.user_id = up.user_id
    WHERE e.ts > now() - interval '14 days'
      AND up.interaction_count > 3  -- Users with established preferences
    GROUP BY 1, 2, 3, 4
)
SELECT
    preferred_length,
    round(avg(avg_helpfulness)::numeric, 2) as avg_helpfulness,
    round(avg(eval_count)::numeric, 1) as avg_evaluations,
    count(*) as user_count
FROM user_perf
GROUP BY 1
ORDER BY avg_helpfulness DESC;

-- 8. Freshness of User Profiles
SELECT
    case
        when last_updated > now() - interval '1 day' then 'very_recent'
        when last_updated > now() - interval '7 days' then 'recent'
        when last_updated > now() - interval '30 days' then 'stale'
        else 'very_stale'
    end as profile_freshness,
    count(*) as profile_count,
    round(avg(interaction_count)::numeric, 1) as avg_interactions
FROM user_profiles
GROUP BY 1
ORDER BY
    case when profile_freshness = 'very_recent' then 1
         when profile_freshness = 'recent' then 2
         when profile_freshness = 'stale' then 3
         else 4 end;
