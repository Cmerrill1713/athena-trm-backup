-- Advanced Optimization Monitoring Queries
-- ========================================

-- Latest RAG threshold & its history
-- Shows current threshold and recent changes
SELECT
    value::float as tau,
    ts,
    LAG(value::float) OVER (ORDER BY ts) as prev_tau,
    (value::float - LAG(value::float) OVER (ORDER BY ts)) as delta_tau
FROM kv_config
WHERE key='RAG_THRESHOLD'
ORDER BY ts DESC
LIMIT 10;

-- Judge helpfulness last 6h vs previous 6h
-- Measures recent quality performance
WITH s AS (
    SELECT
        ts,
        (helpfulness + factuality + clarity) / 3.0 as score
    FROM eval_results
    WHERE ts > NOW() - INTERVAL '12 hours'
)
SELECT
    ROUND(AVG(CASE WHEN ts > NOW() - INTERVAL '6 hours' THEN score END)::numeric, 3) as last6h,
    ROUND(AVG(CASE WHEN ts BETWEEN NOW() - INTERVAL '12 hours' AND NOW() - INTERVAL '6 hours' THEN score END)::numeric, 3) as prev6h,
    ROUND(
        (AVG(CASE WHEN ts > NOW() - INTERVAL '6 hours' THEN score END) -
         AVG(CASE WHEN ts BETWEEN NOW() - INTERVAL '12 hours' AND NOW() - INTERVAL '6 hours' THEN score END)
        )::numeric, 3
    ) as delta_score
FROM s;

-- Docs used distribution (24h)
-- Monitors RAG effectiveness and over-filtering
SELECT
    ROUND(PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY docs_used)::numeric, 2) as p50,
    ROUND(PERCENTILE_DISC(0.95) WITHIN GROUP (ORDER BY docs_used)::numeric, 2) as p95,
    ROUND(AVG(docs_used)::numeric, 2) as mean,
    COUNT(*) as total_queries
FROM (
    SELECT
        JSONB_ARRAY_LENGTH(
            JSONB_PATH_QUERY_ARRAY(candidates, '$ ? (@.used == true)')
        ) as docs_used
    FROM rag_retrieval
    WHERE ts > NOW() - INTERVAL '24 hours'
) t;

-- Bandit algorithm performance
-- Shows variant selection distribution and promotion status
WITH variant_stats AS (
    SELECT
        variant_name,
        COUNT(*) as selections,
        ROUND(AVG(reward)::numeric, 3) as avg_reward,
        ROUND(STDDEV(reward)::numeric, 3) as reward_std,
        MAX(last_updated) as last_selected
    FROM bandit_selections
    WHERE ts > NOW() - INTERVAL '24 hours'
    GROUP BY variant_name
),
promotion_info AS (
    SELECT
        variant_name,
        is_promoted,
        promotion_score,
        alpha, beta,
        ROUND(alpha / (alpha + beta)::numeric, 3) as theta_hat
    FROM bandit_variants
)
SELECT
    v.variant_name,
    v.selections,
    v.avg_reward,
    v.reward_std,
    p.is_promoted,
    p.promotion_score,
    p.theta_hat,
    p.alpha,
    p.beta,
    v.last_selected
FROM variant_stats v
LEFT JOIN promotion_info p ON v.variant_name = p.variant_name
ORDER BY p.is_promoted DESC, p.theta_hat DESC;

-- Reward shaper drift correction stats
-- Monitors judge score stability across domains
WITH domain_stats AS (
    SELECT
        domain,
        COUNT(*) as samples,
        ROUND(AVG(judge_score)::numeric, 3) as mean_score,
        ROUND(STDDEV(judge_score)::numeric, 3) as std_score,
        ROUND(MIN(judge_score)::numeric, 3) as min_score,
        ROUND(MAX(judge_score)::numeric, 3) as max_score
    FROM reward_shaper_history
    WHERE ts > NOW() - INTERVAL '7 days'
    GROUP BY domain
    HAVING COUNT(*) >= 10
)
SELECT
    domain,
    samples,
    mean_score,
    std_score,
    ROUND((std_score / NULLIF(mean_score, 0))::numeric, 3) as cv, -- coefficient of variation
    min_score,
    max_score,
    CASE
        WHEN std_score > 0.5 THEN 'HIGH_VARIANCE'
        WHEN std_score > 0.3 THEN 'MODERATE_VARIANCE'
        ELSE 'STABLE'
    END as drift_status
FROM domain_stats
ORDER BY std_score DESC;

-- Experiment uplift analysis
-- Measures improvement from optimization features
WITH baseline_period AS (
    SELECT
        (helpfulness + factuality + clarity) / 3.0 as score,
        'baseline' as period
    FROM eval_results
    WHERE ts BETWEEN NOW() - INTERVAL '14 days' AND NOW() - INTERVAL '7 days'
),
optimization_period AS (
    SELECT
        (helpfulness + factuality + clarity) / 3.0 as score,
        'optimization' as period
    FROM eval_results
    WHERE ts > NOW() - INTERVAL '7 days'
)
SELECT
    period,
    COUNT(*) as samples,
    ROUND(AVG(score)::numeric, 3) as avg_score,
    ROUND(STDDEV(score)::numeric, 3) as std_score
FROM (
    SELECT * FROM baseline_period
    UNION ALL
    SELECT * FROM optimization_period
) combined
GROUP BY period
ORDER BY period;

-- Latency impact analysis
-- Measures performance impact of optimization features
SELECT
    DATE_TRUNC('hour', ts) as hour,
    COUNT(*) as requests,
    ROUND(AVG(latency_ms)::numeric, 0) as avg_latency,
    ROUND(PERCENTILE_DISC(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 0) as p95_latency,
    ROUND(AVG(docs_used)::numeric, 2) as avg_docs_used,
    ROUND(AVG(judge_score)::numeric, 3) as avg_judge_score,
    COUNT(CASE WHEN rerank_enabled THEN 1 END) as rerank_requests,
    COUNT(CASE WHEN cross_encoder_used THEN 1 END) as ce_requests
FROM request_logs
WHERE ts > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', ts)
ORDER BY hour DESC;

-- Error rate analysis by component
-- Identifies optimization-related errors
SELECT
    component,
    error_type,
    COUNT(*) as occurrences,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()::numeric, 2) as pct_total,
    ROUND(AVG(CASE WHEN rerank_enabled THEN 1.0 ELSE 0.0 END)::numeric, 3) as rerank_pct,
    ROUND(AVG(CASE WHEN bandit_variant IS NOT NULL THEN 1.0 ELSE 0.0 END)::numeric, 3) as bandit_pct
FROM error_logs
WHERE ts > NOW() - INTERVAL '7 days'
GROUP BY component, error_type
HAVING COUNT(*) >= 5
ORDER BY occurrences DESC;

-- A/B test results (if running experiment)
-- Statistical significance testing
WITH experiment_data AS (
    SELECT
        variant_name,
        COUNT(*) as n,
        ROUND(AVG(judge_score)::numeric, 3) as mean_score,
        ROUND(STDDEV(judge_score)::numeric, 3) as std_score
    FROM experiment_results
    WHERE experiment_id = 'current_test'
    GROUP BY variant_name
    HAVING COUNT(*) >= 30
),
stats_calc AS (
    SELECT
        a.variant_name as variant_a,
        b.variant_name as variant_b,
        a.mean_score as mean_a,
        b.mean_score as mean_b,
        a.std_score as std_a,
        b.std_score as std_b,
        a.n as n_a,
        b.n as n_b,
        -- Two-sample t-test statistic
        ROUND(
            ((a.mean_score - b.mean_score) /
             SQRT((a.std_score*a.std_score/a.n) + (b.std_score*b.std_score/b.n))
            )::numeric, 3
        ) as t_stat,
        -- Degrees of freedom approximation
        ROUND((a.n + b.n - 2)::numeric, 0) as df
    FROM experiment_data a
    CROSS JOIN experiment_data b
    WHERE a.variant_name < b.variant_name
)
SELECT
    variant_a,
    variant_b,
    mean_a,
    mean_b,
    ROUND((mean_a - mean_b)::numeric, 3) as diff,
    t_stat,
    df,
    CASE
        WHEN ABS(t_stat) > 2.576 THEN 'p < 0.01 (99% CI)'
        WHEN ABS(t_stat) > 1.96 THEN 'p < 0.05 (95% CI)'
        WHEN ABS(t_stat) > 1.645 THEN 'p < 0.10 (90% CI)'
        ELSE 'not significant'
    END as significance
FROM stats_calc
ORDER BY ABS(t_stat) DESC;

-- Hierarchical bandit performance
-- Shows meta-bandit strategy selection and performance
SELECT
    strategy,
    COUNT(*) as selections,
    ROUND(AVG(meta_confidence)::numeric, 3) as avg_meta_confidence,
    ROUND(AVG(strategy_confidence)::numeric, 3) as avg_strategy_confidence,
    ROUND(AVG(expected_improvement)::numeric, 3) as avg_expected_improvement,
    ROUND(AVG(reward)::numeric, 3) as avg_reward
FROM hierarchical_decisions hd
LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
WHERE hd.ts > NOW() - INTERVAL '24 hours'
GROUP BY strategy
ORDER BY selections DESC;

-- Strategy effectiveness by intent category
-- Shows which strategies work best for different query types
SELECT
    intent_category,
    strategy,
    COUNT(*) as queries,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(AVG(expected_improvement)::numeric, 3) as avg_expected_improvement,
    ROUND(AVG(latency_used_ms)::numeric, 0) as avg_latency_ms
FROM hierarchical_decisions hd
JOIN optimization_requests req ON hd.request_id = req.request_id
LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
WHERE hd.ts > NOW() - INTERVAL '7 days'
GROUP BY intent_category, strategy
ORDER BY intent_category, avg_reward DESC;

-- Meta-bandit learning progress
-- Shows how meta-bandit performance evolves over time
SELECT
    DATE_TRUNC('hour', hd.ts) as hour,
    COUNT(*) as decisions,
    ROUND(AVG(meta_confidence)::numeric, 3) as avg_meta_confidence,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    COUNT(DISTINCT strategy) as strategies_used
FROM hierarchical_decisions hd
LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
WHERE hd.ts > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', hd.ts)
ORDER BY hour DESC;

-- Strategy variant performance within strategies
-- Shows which variants are working best per strategy
SELECT
    strategy,
    variant,
    COUNT(*) as selections,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(AVG(strategy_confidence)::numeric, 3) as avg_confidence,
    ROUND(STDDEV(reward)::numeric, 3) as reward_std,
    MAX(is_promoted::int) as currently_promoted
FROM hierarchical_decisions hd
LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
WHERE hd.ts > NOW() - INTERVAL '24 hours'
GROUP BY strategy, variant
ORDER BY strategy, avg_reward DESC;

-- Personalization effectiveness
-- Shows how personalization impacts outcomes
SELECT
    personalization_applied,
    COUNT(*) as queries,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(AVG(expected_improvement)::numeric, 3) as avg_expected_improvement,
    ROUND(AVG(latency_used_ms)::numeric, 0) as avg_latency_ms,
    ROUND(COUNT(CASE WHEN reward > 0.8 THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as high_reward_pct
FROM optimization_results
WHERE ts > NOW() - INTERVAL '7 days'
GROUP BY personalization_applied
ORDER BY personalization_applied;

-- Context-aware decision analysis
-- Shows how different contexts affect strategy selection
WITH context_buckets AS (
    SELECT
        CASE
            WHEN query_length < 20 THEN 'short'
            WHEN query_length < 50 THEN 'medium'
            ELSE 'long'
        END as length_bucket,
        CASE
            WHEN query_complexity < 0.3 THEN 'simple'
            WHEN query_complexity < 0.7 THEN 'moderate'
            ELSE 'complex'
        END as complexity_bucket,
        CASE
            WHEN latency_budget_ms < 800 THEN 'fast'
            WHEN latency_budget_ms < 1500 THEN 'balanced'
            ELSE 'quality'
        END as latency_bucket,
        strategy,
        reward
    FROM optimization_requests req
    JOIN hierarchical_decisions hd ON req.request_id = hd.request_id
    LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
    WHERE hd.ts > NOW() - INTERVAL '7 days'
)
SELECT
    length_bucket,
    complexity_bucket,
    latency_bucket,
    strategy,
    COUNT(*) as queries,
    ROUND(AVG(reward)::numeric, 3) as avg_reward
FROM context_buckets
GROUP BY length_bucket, complexity_bucket, latency_bucket, strategy
ORDER BY length_bucket, complexity_bucket, latency_bucket, avg_reward DESC;

-- Neural context encoder performance
-- Shows how neural vs rule-based context analysis performs
SELECT
    CASE WHEN confidence >= 0.7 THEN 'neural' ELSE 'rule_based' END as analysis_method,
    COUNT(*) as queries,
    ROUND(AVG(meta_confidence)::numeric, 3) as avg_meta_confidence,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(AVG(expected_improvement)::numeric, 3) as avg_expected_improvement,
    ROUND(COUNT(CASE WHEN reward > 0.8 THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as high_reward_pct
FROM neural_context_analysis nca
JOIN hierarchical_decisions hd ON nca.query_hash = hd.query_hash
LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
WHERE hd.ts > NOW() - INTERVAL '7 days'
GROUP BY CASE WHEN confidence >= 0.7 THEN 'neural' ELSE 'rule_based' END
ORDER BY avg_reward DESC;

-- Neural feature correlations with outcomes
-- Shows which neural features predict good outcomes
SELECT
    ROUND(AVG(complexity)::numeric, 3) as avg_complexity,
    ROUND(AVG(ambiguity)::numeric, 3) as avg_ambiguity,
    MODE() WITHIN GROUP (ORDER BY intent) as dominant_intent,
    COUNT(*) as samples,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(CORR(complexity, reward)::numeric, 3) as complexity_reward_corr,
    ROUND(CORR(ambiguity, reward)::numeric, 3) as ambiguity_reward_corr
FROM neural_context_analysis nca
JOIN hierarchical_decisions hd ON nca.query_hash = hd.query_hash
LEFT JOIN optimization_feedback f ON hd.decision_id = f.decision_id
WHERE hd.ts > NOW() - INTERVAL '7 days' AND nca.confidence >= 0.7
GROUP BY ROUND(complexity * 2) / 2, ROUND(ambiguity * 2) / 2  -- Bin features
ORDER BY avg_reward DESC
LIMIT 10;

-- Neural model training progress
-- Shows how neural encoder learning evolves
SELECT
    DATE_TRUNC('day', training_ts) as training_day,
    COUNT(*) as training_examples,
    ROUND(AVG(final_loss)::numeric, 4) as avg_final_loss,
    ROUND(AVG(final_accuracy)::numeric, 3) as avg_final_accuracy,
    MAX(training_ts) as last_training
FROM neural_training_history
WHERE training_ts > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', training_ts)
ORDER BY training_day DESC;

-- Federated learning rounds and participation
-- Shows cross-deployment collaboration
SELECT
    fr.round_id,
    fr.start_time,
    fr.end_time,
    fr.status,
    array_length(fr.participants, 1) as num_participants,
    COUNT(fu.deployment_id) as updates_received,
    SUM(fu.num_examples) as total_examples,
    fr.global_model_version
FROM federated_rounds fr
LEFT JOIN federated_updates fu ON fr.round_id = fu.round_id
WHERE fr.start_time > NOW() - INTERVAL '30 days'
GROUP BY fr.round_id, fr.start_time, fr.end_time, fr.status, fr.participants, fr.global_model_version
ORDER BY fr.start_time DESC;

-- Federated model performance comparison
-- Shows how federated models perform vs local models
SELECT
    'federated' as model_type,
    COUNT(*) as queries,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(AVG(expected_improvement)::numeric, 3) as avg_improvement,
    ROUND(COUNT(CASE WHEN reward > 0.8 THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as high_reward_pct
FROM optimization_results o
JOIN hierarchical_decisions hd ON o.request_id = hd.request_id
WHERE hd.neural_model_version LIKE 'fed_%'
  AND o.ts > NOW() - INTERVAL '30 days'

UNION ALL

SELECT
    'local' as model_type,
    COUNT(*) as queries,
    ROUND(AVG(reward)::numeric, 3) as avg_reward,
    ROUND(AVG(expected_improvement)::numeric, 3) as avg_improvement,
    ROUND(COUNT(CASE WHEN reward > 0.8 THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as high_reward_pct
FROM optimization_results o
JOIN hierarchical_decisions hd ON o.request_id = hd.request_id
WHERE (hd.neural_model_version NOT LIKE 'fed_%' OR hd.neural_model_version IS NULL)
  AND o.ts > NOW() - INTERVAL '30 days'
ORDER BY avg_reward DESC;

-- Deployment federation activity
-- Shows which deployments are actively participating
SELECT
    deployment_id,
    COUNT(*) as rounds_participated,
    SUM(num_examples) as total_examples_contributed,
    ROUND(AVG(training_loss)::numeric, 4) as avg_training_loss,
    ROUND(AVG(validation_accuracy)::numeric, 3) as avg_validation_accuracy,
    MAX(last_update) as last_participation
FROM federated_updates
WHERE ts > NOW() - INTERVAL '30 days'
GROUP BY deployment_id
ORDER BY rounds_participated DESC, total_examples_contributed DESC;

-- Privacy-preserving federated learning effectiveness
-- Shows that federation improves performance without compromising privacy
WITH federated_performance AS (
    SELECT
        deployment_id,
        AVG(reward) as avg_reward_federated,
        COUNT(*) as federated_queries
    FROM optimization_results o
    JOIN hierarchical_decisions hd ON o.request_id = hd.request_id
    WHERE hd.neural_model_version LIKE 'fed_%'
      AND o.ts > NOW() - INTERVAL '30 days'
    GROUP BY deployment_id
),
local_performance AS (
    SELECT
        deployment_id,
        AVG(reward) as avg_reward_local,
        COUNT(*) as local_queries
    FROM optimization_results o
    JOIN hierarchical_decisions hd ON o.request_id = hd.request_id
    WHERE (hd.neural_model_version NOT LIKE 'fed_%' OR hd.neural_model_version IS NULL)
      AND o.ts > NOW() - INTERVAL '30 days'
    GROUP BY deployment_id
)
SELECT
    COALESCE(f.deployment_id, l.deployment_id) as deployment_id,
    ROUND(f.avg_reward_federated::numeric, 3) as federated_reward,
    ROUND(l.avg_reward_local::numeric, 3) as local_reward,
    ROUND((f.avg_reward_federated - l.avg_reward_local)::numeric, 3) as improvement,
    f.federated_queries,
    l.local_queries
FROM federated_performance f
FULL OUTER JOIN local_performance l ON f.deployment_id = l.deployment_id
ORDER BY improvement DESC NULLS LAST;

-- Adaptive federated scheduling decisions
-- Shows autonomous participation decisions and economic reasoning
SELECT
    round_id,
    should_participate,
    reason,
    ROUND(economic_utility::numeric, 2) as economic_utility,
    ROUND(value_estimate->>'estimated_value'::float::numeric, 2) as expected_value,
    ROUND(value_estimate->>'privacy_cost'::float::numeric, 3) as privacy_cost,
    budget_strategy,
    timestamp
FROM federated_scheduling_decisions
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 50;

-- Economic efficiency of federated participation
-- Shows return on privacy budget investment
SELECT
    deployment_id,
    COUNT(*) as total_decisions,
    COUNT(CASE WHEN should_participate THEN 1 END) as participation_decisions,
    ROUND(AVG(economic_utility)::numeric, 2) as avg_utility_per_decision,
    ROUND(SUM(CASE WHEN should_participate THEN economic_utility ELSE 0 END)::numeric, 2) as total_utility_generated,
    ROUND(AVG(CASE WHEN should_participate THEN value_estimate->>'privacy_cost'::float ELSE NULL END)::numeric, 3) as avg_privacy_cost_when_participating,
    ROUND(
        SUM(CASE WHEN should_participate THEN economic_utility ELSE 0 END) /
        NULLIF(SUM(CASE WHEN should_participate THEN value_estimate->>'privacy_cost'::float ELSE 0 END), 0)::numeric,
        2
    ) as utility_per_privacy_cost
FROM federated_scheduling_decisions
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY deployment_id
ORDER BY utility_per_privacy_cost DESC;

-- Budget optimization performance
-- Shows how well the system manages privacy spending
SELECT
    deployment_id,
    AVG(budget_utilization_rate) as avg_budget_utilization,
    AVG(spending_efficiency) as avg_spending_efficiency,
    COUNT(CASE WHEN budget_strategy = 'aggressive' THEN 1 END) as aggressive_decisions,
    COUNT(CASE WHEN budget_strategy = 'conservative' THEN 1 END) as conservative_decisions,
    COUNT(CASE WHEN budget_strategy = 'balanced' THEN 1 END) as balanced_decisions,
    MAX(last_budget_reset) as last_budget_reset
FROM federated_budget_states
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY deployment_id
ORDER BY avg_spending_efficiency DESC;

-- Participation reason analysis
-- Shows why the system makes different participation decisions
SELECT
    reason,
    COUNT(*) as frequency,
    ROUND(AVG(economic_utility)::numeric, 2) as avg_utility_for_reason,
    ROUND(AVG(CASE WHEN should_participate THEN 1.0 ELSE 0.0 END)::numeric, 3) as participation_rate_for_reason,
    ROUND(AVG(value_estimate->>'participation_probability'::float)::numeric, 3) as avg_participation_probability
FROM federated_scheduling_decisions
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY reason
ORDER BY frequency DESC;

-- Round value estimation accuracy
-- Shows how well the system predicts participation outcomes
WITH round_predictions AS (
    SELECT
        d.round_id,
        d.value_estimate->>'expected_improvement'::float as predicted_improvement,
        d.value_estimate->>'estimated_value'::float as predicted_value,
        o.actual_improvement,
        o.utility as actual_utility,
        d.should_participate
    FROM federated_scheduling_decisions d
    LEFT JOIN federated_round_outcomes o ON d.round_id = o.round_id
    WHERE d.timestamp > NOW() - INTERVAL '30 days'
)
SELECT
    COUNT(*) as total_predictions,
    ROUND(AVG(ABS(predicted_improvement - actual_improvement))::numeric, 3) as avg_improvement_error,
    ROUND(AVG(ABS(predicted_value - actual_utility))::numeric, 2) as avg_utility_error,
    ROUND(
        AVG(CASE WHEN should_participate AND actual_utility > 0 THEN 1.0
                 WHEN NOT should_participate AND actual_utility <= 0 THEN 1.0
                 ELSE 0.0 END)::numeric,
        3
    ) as decision_accuracy,
    ROUND(CORR(predicted_improvement, actual_improvement)::numeric, 3) as improvement_prediction_correlation,
    ROUND(CORR(predicted_value, actual_utility)::numeric, 3) as utility_prediction_correlation
FROM round_predictions;

-- Automated Strategy Generation Statistics
-- Shows the evolution and performance of auto-generated strategies
SELECT
    'strategy_generation' as metric,
    COUNT(*) as total_strategies_generated,
    COUNT(CASE WHEN deployment_status = 'deployed' THEN 1 END) as deployed_strategies,
    COUNT(CASE WHEN deployment_status = 'validated' THEN 1 END) as validated_strategies,
    AVG(fitness_score) as avg_fitness_score,
    MAX(generation) as current_generation,
    AVG(validation_trials) as avg_validation_trials
FROM generated_strategies
WHERE created_at > NOW() - INTERVAL '30 days';

-- Evolutionary Strategy Performance
-- Shows how strategy fitness evolves across generations
SELECT
    generation,
    COUNT(*) as strategies_in_generation,
    AVG(fitness_score) as avg_fitness,
    MAX(fitness_score) as best_fitness,
    MIN(fitness_score) as worst_fitness,
    AVG(complexity_score) as avg_complexity
FROM generated_strategies
WHERE generation > 0
GROUP BY generation
ORDER BY generation DESC
LIMIT 20;

-- Auto-Generated Strategy Components Usage
-- Shows which components are most successful in evolved strategies
SELECT
    component,
    COUNT(*) as times_used,
    AVG(gs.fitness_score) as avg_fitness_when_used,
    COUNT(CASE WHEN gs.deployment_status = 'deployed' THEN 1 END) as deployment_success_rate,
    ROUND(COUNT(CASE WHEN gs.deployment_status = 'deployed' THEN 1 END) * 100.0 / COUNT(*), 1) as deployment_pct
FROM (
    SELECT
        unnest(array[
            CASE WHEN cosine_similarity THEN 'cosine_similarity' END,
            CASE WHEN cross_encoder THEN 'cross_encoder' END,
            CASE WHEN neural_rescoring THEN 'neural_rescoring' END,
            CASE WHEN personalization THEN 'personalization' END,
            CASE WHEN context_filtering THEN 'context_filtering' END,
            CASE WHEN diversity_promotion THEN 'diversity_promotion' END,
            CASE WHEN temporal_weighting THEN 'temporal_weighting' END,
            CASE WHEN user_feedback_integration THEN 'user_feedback_integration' END
        ]) as component
    FROM generated_strategies
    WHERE component IS NOT NULL
) comp
JOIN generated_strategies gs ON gs.id = (
    SELECT id FROM generated_strategies
    WHERE generation = gs.generation
    ORDER BY random() LIMIT 1
)  -- Simplified join - in practice would need proper component tracking
GROUP BY component
ORDER BY deployment_success_rate DESC;

-- Meta-Learning Performance
-- Shows how well the meta-learner predicts strategy success
WITH prediction_accuracy AS (
    SELECT
        predicted_success_prob,
        actual_fitness,
        CASE WHEN predicted_success_prob > 0.7 AND actual_fitness > 0.05 THEN 1
             WHEN predicted_success_prob < 0.3 AND actual_fitness < 0.05 THEN 1
             ELSE 0 END as correct_prediction
    FROM strategy_predictions
    WHERE prediction_date > NOW() - INTERVAL '30 days'
)
SELECT
    COUNT(*) as total_predictions,
    ROUND(AVG(predicted_success_prob)::numeric, 3) as avg_predicted_prob,
    ROUND(AVG(actual_fitness)::numeric, 3) as avg_actual_fitness,
    ROUND(AVG(correct_prediction)::numeric, 3) as prediction_accuracy,
    ROUND(CORR(predicted_success_prob, actual_fitness)::numeric, 3) as prediction_correlation
FROM prediction_accuracy;

-- Strategy Innovation Rate
-- Shows how often new strategies beat existing approaches
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as strategies_generated,
    COUNT(CASE WHEN fitness_score > 0.1 THEN 1 END) as high_performing_strategies,
    ROUND(AVG(fitness_score)::numeric, 3) as avg_improvement,
    ROUND(MAX(fitness_score)::numeric, 3) as best_improvement,
    COUNT(CASE WHEN deployment_status = 'deployed' THEN 1 END) as strategies_deployed
FROM generated_strategies
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;

-- Component Evolution Trends
-- Shows how strategy composition changes over generations
WITH component_evolution AS (
    SELECT
        generation,
        COUNT(CASE WHEN 'cross_encoder' = ANY(components) THEN 1 END) * 100.0 / COUNT(*) as ce_pct,
        COUNT(CASE WHEN 'personalization' = ANY(components) THEN 1 END) * 100.0 / COUNT(*) as personalization_pct,
        COUNT(CASE WHEN 'diversity_promotion' = ANY(components) THEN 1 END) * 100.0 / COUNT(*) as diversity_pct,
        COUNT(CASE WHEN 'neural_rescoring' = ANY(components) THEN 1 END) * 100.0 / COUNT(*) as neural_pct,
        AVG(fitness_score) as avg_fitness
    FROM generated_strategies
    WHERE generation > 0
    GROUP BY generation
    ORDER BY generation DESC
    LIMIT 10
)
SELECT * FROM component_evolution;

-- Automated Strategy Validation Results
-- Shows validation outcomes and statistical significance
SELECT
    strategy_key,
    ROUND(mean_performance::numeric, 3) as mean_performance,
    ROUND(improvement::numeric, 3) as improvement_over_baseline,
    ROUND(std_performance::numeric, 3) as performance_std,
    sample_size,
    is_significant,
    passes_threshold,
    can_deploy,
    ROUND(confidence_interval[1] - confidence_interval[2], 3) as confidence_width
FROM strategy_validation_results
WHERE validation_date > NOW() - INTERVAL '30 days'
ORDER BY improvement_over_baseline DESC
LIMIT 20;

-- Self-Evolving System Health
-- Comprehensive overview of automated strategy generation health
SELECT
    'automated_generation_health' as metric,
    (SELECT COUNT(*) FROM generated_strategies WHERE created_at > NOW() - INTERVAL '7 days') as strategies_this_week,
    (SELECT COUNT(*) FROM generated_strategies WHERE deployment_status = 'deployed') as total_deployed,
    (SELECT ROUND(AVG(fitness_score)::numeric, 3) FROM generated_strategies WHERE generation > 0) as avg_strategy_fitness,
    (SELECT COUNT(*) FROM strategy_validation_results WHERE can_deploy = true AND validation_date > NOW() - INTERVAL '7 days') as validations_passed_this_week,
    (SELECT ROUND(AVG(improvement)::numeric, 3) FROM strategy_validation_results WHERE validation_date > NOW() - INTERVAL '30 days') as avg_improvement,
    (SELECT MAX(generation) FROM generated_strategies) as current_generation,
    (SELECT COUNT(DISTINCT strategy_id) FROM strategy_deployments WHERE deployed_at > NOW() - INTERVAL '30 days'    ) as strategies_auto_deployed;

-- Constitutional Integration Monitoring
-- Shows how governance integrates with live bandit system deployment
SELECT
    'constitutional_integration' as metric,
    (SELECT COUNT(*) FROM generated_strategies WHERE deployment_status = 'deployed') as constitutional_strategies_deployed,
    (SELECT COUNT(DISTINCT strategy) FROM bandit_decisions bd JOIN generated_strategies gs ON bd.strategy = gs.name WHERE gs.deployment_status = 'deployed') as active_constitutional_strategies,
    (SELECT ROUND(AVG(gs.fitness_score)::numeric, 3) FROM generated_strategies gs WHERE gs.deployment_status = 'deployed') as avg_fitness_deployed_strategies,
    (SELECT ROUND(AVG(gs.governance_score)::numeric, 3) FROM generated_strategies gs WHERE gs.deployment_status = 'deployed') as avg_governance_deployed_strategies,
    (SELECT COUNT(*) FROM governance_assessments WHERE overall_clearance = true AND timestamp > NOW() - INTERVAL '7 days') as weekly_governance_approvals,
    (SELECT ROUND(AVG(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3) FROM governance_assessments WHERE timestamp > NOW() - INTERVAL '7 days') as weekly_governance_clearance_rate
FROM governance_assessments
LIMIT 1;

-- Live Constitutional Strategy Performance
-- Shows how auto-deployed strategies perform in production
SELECT
    gs.name as strategy_name,
    gs.generation,
    gs.fitness_score as validation_fitness,
    gs.governance_score,
    COUNT(bd.decision_id) as times_selected,
    ROUND(AVG(bd.expected_improvement)::numeric, 3) as avg_expected_improvement,
    ROUND(AVG(CASE WHEN bd.reward > 0 THEN 1.0 ELSE 0.0 END)::numeric, 3) as win_rate,
    MAX(bd.timestamp) as last_used
FROM generated_strategies gs
LEFT JOIN bandit_decisions bd ON gs.name = bd.strategy
WHERE gs.deployment_status = 'deployed'
  AND bd.timestamp > NOW() - INTERVAL '30 days'
GROUP BY gs.name, gs.generation, gs.fitness_score, gs.governance_score
ORDER BY COUNT(bd.decision_id) DESC, ROUND(AVG(bd.expected_improvement)::numeric, 3) DESC;

-- Constitutional Evolution Pipeline Efficiency
-- Shows end-to-end efficiency from generation to deployment
SELECT
    'evolution_pipeline' as metric,
    (SELECT COUNT(*) FROM generated_strategies WHERE created_at > NOW() - INTERVAL '7 days') as strategies_generated_weekly,
    (SELECT COUNT(*) FROM generated_strategies WHERE deployment_status IN ('validated', 'deployed') AND created_at > NOW() - INTERVAL '7 days') as strategies_validated_weekly,
    (SELECT COUNT(*) FROM generated_strategies WHERE deployment_status = 'deployed' AND created_at > NOW() - INTERVAL '7 days') as strategies_deployed_weekly,
    (SELECT ROUND(
        COUNT(*) FILTER (WHERE deployment_status = 'deployed') * 100.0 /
        NULLIF(COUNT(*), 0)::numeric, 1)
     FROM generated_strategies WHERE created_at > NOW() - INTERVAL '7 days') as weekly_deployment_rate,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (deployed_at - created_at))/3600)::numeric, 1)
     FROM generated_strategies WHERE deployment_status = 'deployed' AND created_at > NOW() - INTERVAL '7 days') as avg_hours_to_deployment,
    (SELECT COUNT(*) FROM human_interventions WHERE status IN ('approved_with_conditions', 'approved') AND timestamp > NOW() - INTERVAL '7 days') as human_approvals_weekly
FROM generated_strategies
LIMIT 1;

-- Constitutional Strategy Impact Analysis
-- Shows the performance difference between constitutional and human-designed strategies
WITH strategy_performance AS (
    SELECT
        CASE WHEN gs.name IS NOT NULL THEN 'constitutional' ELSE 'human_designed' END as strategy_type,
        AVG(bd.reward) as avg_reward,
        AVG(bd.expected_improvement) as avg_expected_improvement,
        COUNT(*) as usage_count,
        ROUND(AVG(CASE WHEN bd.reward > 0 THEN 1.0 ELSE 0.0 END)::numeric, 3) as win_rate
    FROM bandit_decisions bd
    LEFT JOIN generated_strategies gs ON bd.strategy = gs.name AND gs.deployment_status = 'deployed'
    WHERE bd.timestamp > NOW() - INTERVAL '30 days'
    GROUP BY CASE WHEN gs.name IS NOT NULL THEN 'constitutional' ELSE 'human_designed' END
)
SELECT
    strategy_type,
    ROUND(avg_reward::numeric, 3) as avg_reward,
    ROUND(avg_expected_improvement::numeric, 3) as avg_expected_improvement,
    usage_count,
    win_rate,
    ROUND(
        (avg_reward - LAG(avg_reward) OVER (ORDER BY strategy_type)) /
        NULLIF(LAG(avg_reward) OVER (ORDER BY strategy_type), 0)::numeric * 100,
        1
    ) as reward_improvement_pct
FROM strategy_performance
ORDER BY avg_reward DESC;

-- Governance Failure Analysis
-- Shows why strategies fail constitutional review
SELECT
    failure_reason,
    COUNT(*) as frequency,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    ROUND(AVG(CASE WHEN human_intervention_requested THEN 1.0 ELSE 0.0 END)::numeric, 3) as human_intervention_rate,
    ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score_for_reason
FROM (
    SELECT
        CASE
            WHEN array_length(blocking_violations, 1) > 0 THEN blocking_violations[1]
            WHEN ethical_severity_score > 0 THEN 'ethical_concern'
            WHEN safety_score < 0.8 THEN 'safety_concern'
            WHEN compliance_score < 0.9 THEN 'compliance_concern'
            ELSE 'business_alignment'
        END as failure_reason,
        CASE WHEN array_length(blocking_violations, 1) > 0 THEN true ELSE false END as human_intervention_requested,
        governance_score
    FROM governance_assessments
    WHERE overall_clearance = false
      AND timestamp > NOW() - INTERVAL '30 days'
) failures
GROUP BY failure_reason
ORDER BY frequency DESC;

-- Constitutional System Health Dashboard
-- Comprehensive view of constitutional AI platform health
SELECT
    'constitutional_system_health' as metric,
    NOW() as timestamp,
    (SELECT COUNT(*) FROM generated_strategies WHERE deployment_status = 'deployed') as active_constitutional_strategies,
    (SELECT COUNT(*) FROM governance_assessments WHERE overall_clearance = true AND timestamp > NOW() - INTERVAL '7 days') as weekly_approvals,
    (SELECT ROUND(AVG(governance_score)::numeric, 3) FROM governance_assessments WHERE timestamp > NOW() - INTERVAL '7 days') as avg_governance_score,
    (SELECT COUNT(*) FROM human_interventions WHERE status = 'pending') as pending_human_reviews,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (approved_at - created_at))/3600)::numeric, 1)
     FROM human_interventions WHERE status IN ('approved', 'approved_with_conditions') AND created_at > NOW() - INTERVAL '30 days') as avg_human_review_hours,
    (SELECT COUNT(*) FROM bandit_decisions bd JOIN generated_strategies gs ON bd.strategy = gs.name
     WHERE gs.deployment_status = 'deployed' AND bd.timestamp > NOW() - INTERVAL '7 days') as constitutional_strategy_usage_weekly,
    (SELECT ROUND(AVG(reward)::numeric, 3) FROM bandit_decisions bd JOIN generated_strategies gs ON bd.strategy = gs.name
     WHERE gs.deployment_status = 'deployed' AND bd.timestamp > NOW() - INTERVAL '7 days') as avg_constitutional_reward,
    (SELECT COUNT(*) FROM governance_policies WHERE enabled = true) as active_governance_policies,
    (SELECT ROUND(AVG(violation_count)::numeric, 1) FROM governance_policies WHERE enabled = true) as avg_policy_violations,
    (SELECT MAX(generation) FROM generated_strategies) as latest_strategy_generation,
    (SELECT COUNT(*) FROM generated_strategies WHERE created_at > NOW() - INTERVAL '1 hour') as strategies_generated_last_hour;
-- Governance Layer Monitoring
-- Shows ethical, business, safety, and compliance governance enforcement
SELECT
    'governance_overview' as metric,
    (SELECT COUNT(*) FROM governance_assessments WHERE timestamp > NOW() - INTERVAL '7 days') as assessments_this_week,
    (SELECT ROUND(AVG(overall_clearance::int)::numeric, 3) FROM governance_assessments WHERE timestamp > NOW() - INTERVAL '7 days') as clearance_rate,
    (SELECT COUNT(*) FROM governance_assessments WHERE overall_clearance = false AND timestamp > NOW() - INTERVAL '7 days') as blocked_strategies,
    (SELECT COUNT(*) FROM human_interventions WHERE status = 'pending') as pending_interventions,
    (SELECT COUNT(*) FROM human_interventions WHERE status = 'approved_with_conditions' AND timestamp > NOW() - INTERVAL '30 days') as conditional_approvals
FROM governance_assessments
LIMIT 1;

-- Governance Policy Violations
-- Shows which governance policies are most frequently violated
SELECT
    policy_id,
    category,
    enforcement_level,
    violation_count,
    ROUND(violation_count * 100.0 / NULLIF((SELECT COUNT(*) FROM governance_assessments), 0), 2) as violation_rate_pct,
    enabled,
    last_modified
FROM governance_policies
ORDER BY violation_count DESC;

-- Ethical Boundary Violations
-- Shows strategies that violated ethical boundaries
SELECT
    strategy_id,
    timestamp,
    ethical_severity_score,
    ARRAY_LENGTH(ethical_violations, 1) as num_ethical_violations,
    ethical_violations[1:3] as top_violations,  -- First 3 violations
    overall_clearance
FROM governance_assessments
WHERE ethical_severity_score > 0
ORDER BY ethical_severity_score DESC, timestamp DESC
LIMIT 20;

-- Business Alignment Scores
-- Shows how well strategies align with business objectives
SELECT
    strategy_id,
    timestamp,
    ROUND(business_alignment->>'overall_alignment'::float::numeric, 3) as business_alignment_score,
    ROUND(business_alignment->>'alignment_scores'->>'user_satisfaction'::float::numeric, 3) as user_satisfaction_score,
    ROUND(business_alignment->>'alignment_scores'->>'business_value'::float::numeric, 3) as business_value_score,
    ROUND(business_alignment->>'alignment_scores'->>'operational_efficiency'::float::numeric, 3) as efficiency_score,
    business_alignment->>'meets_thresholds'::bool as meets_thresholds,
    overall_clearance
FROM governance_assessments
WHERE business_alignment->>'overall_alignment' IS NOT NULL
ORDER BY business_alignment_score DESC, timestamp DESC
LIMIT 20;

-- Safety Limit Violations
-- Shows strategies that exceeded safety limits
SELECT
    strategy_id,
    timestamp,
    safety_score,
    ARRAY_LENGTH(safety_violations, 1) as num_safety_violations,
    safety_violations[1:2] as critical_violations,  -- Most critical violations
    overall_clearance,
    requires_safety_review
FROM governance_assessments
WHERE safety_score < 0.8
ORDER BY safety_score ASC, timestamp DESC
LIMIT 20;

-- Compliance Assessment Results
-- Shows regulatory compliance evaluation
SELECT
    strategy_id,
    timestamp,
    compliance_score,
    ARRAY_LENGTH(compliance_issues, 1) as num_compliance_issues,
    compliance_issues[1]->>'framework' as primary_framework_violated,
    compliance_issues[1]->>'rule' as primary_rule_violated,
    overall_clearance,
    requires_compliance_review
FROM governance_assessments
WHERE compliance_score < 0.9
ORDER BY compliance_score ASC, timestamp DESC
LIMIT 20;

-- Governance Score Distribution
-- Shows overall governance quality of generated strategies
SELECT
    governance_score_bucket,
    COUNT(*) as strategies_in_bucket,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    ROUND(AVG(overall_clearance::int)::numeric, 3) as clearance_rate_in_bucket
FROM (
    SELECT
        CASE
            WHEN governance_score >= 0.9 THEN 'excellent (0.9-1.0)'
            WHEN governance_score >= 0.8 THEN 'good (0.8-0.9)'
            WHEN governance_score >= 0.7 THEN 'fair (0.7-0.8)'
            WHEN governance_score >= 0.6 THEN 'poor (0.6-0.7)'
            ELSE 'failing (<0.6)'
        END as governance_score_bucket,
        governance_score,
        overall_clearance
    FROM governance_assessments
    WHERE timestamp > NOW() - INTERVAL '30 days'
) buckets
GROUP BY governance_score_bucket
ORDER BY MIN(governance_score) DESC;

-- Human Intervention History
-- Shows strategies requiring human oversight
SELECT
    strategy_id,
    timestamp,
    reason,
    status,
    CASE
        WHEN status = 'approved_with_conditions' THEN ARRAY_LENGTH(conditions, 1)
        ELSE NULL
    END as num_conditions,
    CASE
        WHEN status = 'rejected' THEN rejection_reason
        ELSE NULL
    END as rejection_reason
FROM human_interventions
ORDER BY timestamp DESC
LIMIT 20;

-- Governance Evolution Trends
-- Shows how governance enforcement changes over time
SELECT
    DATE_TRUNC('week', timestamp) as week,
    COUNT(*) as total_assessments,
    ROUND(AVG(ethical_severity_score)::numeric, 3) as avg_ethical_severity,
    ROUND(AVG(business_alignment->>'overall_alignment'::float)::numeric, 3) as avg_business_alignment,
    ROUND(AVG(safety_score)::numeric, 3) as avg_safety_score,
    ROUND(AVG(compliance_score)::numeric, 3) as avg_compliance_score,
    ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score,
    ROUND(AVG(overall_clearance::int)::numeric, 3) as clearance_rate
FROM governance_assessments
WHERE timestamp > NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', timestamp)
ORDER BY week DESC;

-- Policy Effectiveness Analysis
-- Shows which governance policies prevent the most violations
WITH policy_effectiveness AS (
    SELECT
        gp.policy_id,
        gp.category,
        gp.enforcement_level,
        gp.violation_count,
        COUNT(ga.strategy_id) as total_assessments,
        CASE
            WHEN gp.enforcement_level = 'blocking' THEN COUNT(ga.strategy_id) FILTER (WHERE NOT ga.overall_clearance)
            ELSE 0
        END as strategies_blocked
    FROM governance_policies gp
    CROSS JOIN governance_assessments ga
    GROUP BY gp.policy_id, gp.category, gp.enforcement_level, gp.violation_count
)
SELECT
    policy_id,
    category,
    enforcement_level,
    violation_count,
    strategies_blocked,
    ROUND(strategies_blocked * 100.0 / NULLIF(violation_count, 0), 1) as blocking_effectiveness_pct
FROM policy_effectiveness
ORDER BY violation_count DESC, blocking_effectiveness_pct DESC;
-- System health dashboard
-- Comprehensive optimization health check
SELECT
    'system_health' as metric,
    NOW() as timestamp,
    (SELECT ROUND(AVG((helpfulness + factuality + clarity)/3.0)::numeric, 3)
     FROM eval_results WHERE ts > NOW() - INTERVAL '1 hour') as judge_avg_1h,

    (SELECT ROUND(histogram_quantile(0.95, sum(rate(bridge_chat_latency_ms_bucket[1h])) by (le))::numeric, 0)
     FROM prometheus_metrics) as p95_latency_1h,

    (SELECT ROUND(AVG(docs_used)::numeric, 2)
     FROM rag_retrieval WHERE ts > NOW() - INTERVAL '1 hour') as avg_docs_used_1h,

    (SELECT COUNT(*) FROM bandit_selections WHERE ts > NOW() - INTERVAL '1 hour')
     as bandit_selections_1h,

    (SELECT COUNT(*) FROM hierarchical_decisions WHERE ts > NOW() - INTERVAL '1 hour')
     as hierarchical_decisions_1h,

    (SELECT COUNT(CASE WHEN status = 'error' THEN 1 END) * 100.0 / COUNT(*)
     FROM request_logs WHERE ts > NOW() - INTERVAL '1 hour')
     as error_rate_pct_1h,

    (SELECT value::float FROM kv_config WHERE key = 'RAG_THRESHOLD' ORDER BY ts DESC LIMIT 1)
     as current_rag_threshold,

    (SELECT COUNT(*) FROM bandit_variants WHERE is_promoted = true)
     as promoted_variants_count,

    (SELECT ROUND(AVG(meta_confidence)::numeric, 3)
     FROM hierarchical_decisions WHERE ts > NOW() - INTERVAL '1 hour')
     as avg_meta_confidence_1h,

    (SELECT COUNT(DISTINCT strategy) FROM hierarchical_decisions WHERE ts > NOW() - INTERVAL '1 hour')
     as strategies_used_1h,

    (SELECT AVG(confidence) FROM neural_context_analysis WHERE ts > NOW() - INTERVAL '1 hour')
     as neural_confidence_1h,

    (SELECT COUNT(CASE WHEN confidence >= 0.7 THEN 1 END) * 100.0 / COUNT(*)
     FROM neural_context_analysis WHERE ts > NOW() - INTERVAL '1 hour')
     as neural_high_confidence_pct_1h;

-- Dynamic Constitutional Weighting Monitoring
-- Shows how governance adapts based on system state
SELECT
    'dynamic_weighting' as metric,
    (SELECT ROUND(AVG(ethical_weight)::numeric, 3) FROM constitutional_weights WHERE timestamp > NOW() - INTERVAL '7 days') as avg_ethical_weight,
    (SELECT ROUND(AVG(business_weight)::numeric, 3) FROM constitutional_weights WHERE timestamp > NOW() - INTERVAL '7 days') as avg_business_weight,
    (SELECT ROUND(AVG(safety_weight)::numeric, 3) FROM constitutional_weights WHERE timestamp > NOW() - INTERVAL '7 days') as avg_safety_weight,
    (SELECT ROUND(AVG(compliance_weight)::numeric, 3) FROM constitutional_weights WHERE timestamp > NOW() - INTERVAL '7 days') as avg_compliance_weight,
    (SELECT mode() WITHIN GROUP (ORDER BY detected_phase) FROM system_states WHERE timestamp > NOW() - INTERVAL '7 days') as dominant_phase,
    (SELECT COUNT(DISTINCT detected_phase) FROM system_states WHERE timestamp > NOW() - INTERVAL '7 days') as phase_diversity,
    (SELECT ROUND(AVG(weighting_stability)::numeric, 3) FROM weighting_stats WHERE timestamp > NOW() - INTERVAL '7 days') as weighting_stability
FROM constitutional_weights
LIMIT 1;

-- Constitutional Adaptation Effectiveness
-- Shows how dynamic weighting improves governance outcomes
WITH weighted_performance AS (
    SELECT
        CASE
            WHEN weighted_governance_score > governance_score THEN 'improved_by_weighting'
            WHEN weighted_governance_score < governance_score THEN 'worsened_by_weighting'
            ELSE 'unchanged_by_weighting'
        END as weighting_effect,
        overall_clearance,
        dynamic_clearance,
        governance_score,
        weighted_governance_score
    FROM governance_assessments
    WHERE timestamp > NOW() - INTERVAL '30 days'
    AND weighted_governance_score IS NOT NULL
)
SELECT
    weighting_effect,
    COUNT(*) as frequency,
    ROUND(AVG(governance_score)::numeric, 3) as avg_original_score,
    ROUND(AVG(weighted_governance_score)::numeric, 3) as avg_weighted_score,
    ROUND(AVG((weighted_governance_score - governance_score))::numeric, 3) as avg_score_change,
    ROUND(
        COUNT(CASE WHEN dynamic_clearance != overall_clearance THEN 1 END) * 100.0 / COUNT(*)::numeric,
        1
    ) as decision_change_rate
FROM weighted_performance
GROUP BY weighting_effect
ORDER BY frequency DESC;

-- System State Evolution Tracking
-- Shows how system state influences constitutional weighting
SELECT
    detected_phase,
    COUNT(*) as phase_frequency,
    ROUND(AVG(ethical_weight)::numeric, 3) as avg_ethical_weight,
    ROUND(AVG(business_weight)::numeric, 3) as avg_business_weight,
    ROUND(AVG(safety_weight)::numeric, 3) as avg_safety_weight,
    ROUND(AVG(compliance_weight)::numeric, 3) as avg_compliance_weight,
    ROUND(AVG(governance_clearance_rate)::numeric, 3) as avg_clearance_rate_in_phase,
    ROUND(AVG(ethical_violation_rate)::numeric, 4) as avg_ethical_violations,
    ROUND(AVG(error_rate)::numeric, 4) as avg_error_rate
FROM system_states ss
JOIN constitutional_weights cw ON DATE_TRUNC('hour', ss.timestamp) = DATE_TRUNC('hour', cw.timestamp)
WHERE ss.timestamp > NOW() - INTERVAL '30 days'
GROUP BY detected_phase
ORDER BY phase_frequency DESC;

-- Dynamic Governance System Health Dashboard
-- Comprehensive view of adaptive constitutional governance
SELECT
    'dynamic_governance_health' as metric,
    NOW() as timestamp,
    (SELECT COUNT(*) FROM constitutional_weights WHERE timestamp > NOW() - INTERVAL '1 hour') as weights_updated_last_hour,
    (SELECT COUNT(DISTINCT detected_phase) FROM system_states WHERE timestamp > NOW() - INTERVAL '24 hours') as phases_detected_today,
    (SELECT mode() WITHIN GROUP (ORDER BY detected_phase) FROM system_states WHERE timestamp > NOW() - INTERVAL '1 hour') as current_dominant_phase,
    (SELECT ROUND(AVG(weighting_stability)::numeric, 3) FROM weighting_stats WHERE timestamp > NOW() - INTERVAL '24 hours') as current_weighting_stability,
    (SELECT ROUND(AVG(CASE WHEN dynamic_clearance != overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3)
     FROM governance_assessments WHERE timestamp > NOW() - INTERVAL '24 hours') as weighting_decision_change_rate,
    (SELECT COUNT(*) FROM meta_learning_updates WHERE timestamp > NOW() - INTERVAL '24 hours') as meta_learning_updates_today,
    (SELECT ROUND(AVG(performance_improvement)::numeric, 3) FROM weighting_performance_feedback WHERE timestamp > NOW() - INTERVAL '7 days') as avg_performance_improvement_from_weighting,
    (SELECT ROUND(STDDEV(ethical_weight + business_weight + safety_weight + compliance_weight)::numeric, 3)
     FROM constitutional_weights WHERE timestamp > NOW() - INTERVAL '24 hours') as weight_distribution_stability;
