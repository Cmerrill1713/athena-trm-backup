-- Federated Bandit Learning Monitoring Dashboard
-- Track collective intelligence across deployments

-- 1. Federation Health Overview (Last 24h)
SELECT
    date_trunc('hour', now()) as current_hour,
    (SELECT count(*) FROM federation_contributions WHERE ts > now() - interval '24 hours') as recent_contributions,
    (SELECT count(*) FROM federation_updates WHERE ts > now() - interval '24 hours') as recent_updates,
    (SELECT count(distinct deployment_id) FROM federation_contributions WHERE ts > now() - interval '24 hours') as active_deployments,
    (SELECT avg(privacy_budget) FROM federation_contributions WHERE ts > now() - interval '24 hours') as avg_privacy_budget,
    (SELECT count(distinct arm_name) FROM federated_priors WHERE last_updated > now() - interval '24 hours') as arms_with_updates
FROM federation_health;

-- 2. Federated Arm Performance (Global vs Local)
SELECT
    fp.arm_name,
    fp.global_alpha,
    fp.global_beta,
    fp.global_alpha / (fp.global_alpha + fp.global_beta) as global_win_rate,
    -- Compare with local performance (would need local priors table)
    CASE
        WHEN fp.arm_name = 'conservative_ce' THEN 0.75
        WHEN fp.arm_name = 'aggressive_ce' THEN 0.70
        WHEN fp.arm_name = 'exploratory' THEN 0.55
        ELSE 0.50
    END as local_win_rate_estimate,
    fp.sample_count as contributing_samples,
    fp.last_updated
FROM federated_priors fp
ORDER BY fp.global_alpha / (fp.global_alpha + fp.global_beta) DESC;

-- 3. Deployment Contribution Patterns
SELECT
    fc.deployment_id,
    count(*) as total_contributions,
    avg(fc.sample_count) as avg_samples_per_contribution,
    avg(fc.privacy_budget) as avg_privacy_budget,
    max(fc.ts) as last_contribution,
    extract(epoch from (now() - max(fc.ts)))/3600 as hours_since_last_contribution,
    count(distinct fc.arm_name) as arms_contributed
FROM federation_contributions fc
WHERE fc.ts > now() - interval '7 days'
GROUP BY fc.deployment_id
ORDER BY total_contributions DESC
LIMIT 10;

-- 4. Privacy vs Utility Analysis
SELECT
    date_trunc('day', fc.ts) as day,
    avg(fc.privacy_budget) as avg_privacy_epsilon,
    -- Utility proxy: how much federated knowledge differs from local
    avg(
        CASE
            WHEN fc.arm_name = 'conservative_ce' THEN abs(0.75 - (fc.alpha::float / (fc.alpha + fc.beta)))
            WHEN fc.arm_name = 'aggressive_ce' THEN abs(0.70 - (fc.alpha::float / (fc.alpha + fc.beta)))
            WHEN fc.arm_name = 'exploratory' THEN abs(0.55 - (fc.alpha::float / (fc.alpha + fc.beta)))
            ELSE 0.0
        END
    ) as avg_utility_divergence,
    count(*) as contributions
FROM federation_contributions fc
WHERE fc.ts > now() - interval '30 days'
GROUP BY 1
ORDER BY 1 DESC;

-- 5. Federation Learning Effectiveness
WITH learning_progress AS (
    SELECT
        date_trunc('day', fu.ts) as day,
        count(*) as updates_received,
        avg(fu.learning_rate) as avg_learning_rate,
        count(distinct fu.arm_name) as arms_updated
    FROM federation_updates fu
    WHERE fu.ts > now() - interval '30 days'
    GROUP BY 1
),
performance_impact AS (
    SELECT
        date_trunc('day', r.ts) as day,
        avg(r.judge_improvement) as avg_judge_improvement,
        count(CASE WHEN r.exploration_used THEN 1 END)::float / count(*) as exploration_rate,
        count(*) as total_decisions
    FROM routing_history r
    WHERE r.ts > now() - interval '30 days'
    GROUP BY 1
)
SELECT
    lp.day,
    lp.updates_received,
    lp.avg_learning_rate,
    lp.arms_updated,
    pi.avg_judge_improvement,
    pi.exploration_rate,
    pi.total_decisions
FROM learning_progress lp
LEFT JOIN performance_impact pi ON lp.day = pi.day
ORDER BY lp.day DESC;

-- 6. Cross-Deployment Knowledge Transfer
SELECT
    source_deployment,
    target_deployment,
    arm_name,
    knowledge_transfer_impact,
    transfer_timestamp
FROM knowledge_transfers kt
WHERE kt.transfer_timestamp > now() - interval '7 days'
ORDER BY kt.transfer_timestamp DESC
LIMIT 20;

-- 7. Federation Security & Compliance
SELECT
    event_type,
    count(*) as events,
    max(timestamp) as last_event,
    avg(severity_score) as avg_severity
FROM federation_security_events
WHERE timestamp > now() - interval '30 days'
GROUP BY event_type
ORDER BY events DESC;

-- 8. Deployment Reputation & Trust
SELECT
    deployment_id,
    reputation_score,
    total_contributions,
    successful_contributions,
    successful_contributions::float / nullif(total_contributions, 0) as contribution_quality,
    last_activity,
    extract(epoch from (now() - last_activity))/3600 as hours_since_active,
    trust_level
FROM deployment_reputation dr
ORDER BY reputation_score DESC
LIMIT 20;

-- 9. Federated Learning ROI Analysis
SELECT
    date_trunc('month', r.ts) as month,
    count(*) as total_queries,
    avg(r.judge_improvement) as avg_improvement,
    -- Federation contribution proxy
    count(CASE WHEN r.federation_influence THEN 1 END) as federation_influenced_decisions,
    count(CASE WHEN r.federation_influence THEN 1 END)::float / count(*) as federation_influence_rate,
    -- Performance comparison
    avg(CASE WHEN r.federation_influence THEN r.judge_improvement END) as federated_avg_improvement,
    avg(CASE WHEN NOT r.federation_influence THEN r.judge_improvement END) as local_only_avg_improvement
FROM routing_history r
WHERE r.ts > now() - interval '6 months'
GROUP BY 1
ORDER BY 1 DESC;

-- 10. Privacy Budget Consumption
SELECT
    deployment_id,
    date_trunc('week', fc.ts) as week,
    sum(fc.privacy_budget * fc.sample_count) as total_privacy_spend,
    avg(fc.privacy_budget) as avg_privacy_budget,
    count(*) as contributions,
    sum(fc.sample_count) as total_samples_shared
FROM federation_contributions fc
WHERE fc.ts > now() - interval '12 weeks'
GROUP BY 1, 2
ORDER BY 1, 2 DESC;

-- Note: These queries assume tables exist for federation tracking.
-- In a real implementation, you'd create:
-- - federation_contributions (deployment contributions)
-- - federated_priors (global aggregated priors)
-- - federation_updates (knowledge updates received)
-- - deployment_reputation (trust scores)
-- - federation_security_events (security monitoring)
-- - knowledge_transfers (cross-deployment learning)
