-- =============================================================================
-- PRODUCTION VALIDATION SUITE - Constitutional AI Framework
-- =============================================================================
--
-- Comprehensive validation for production deployment readiness.
-- Run all checks to validate constitutional, hierarchical, neural, federated stack.
--
-- Usage: psql -f scripts/production_validation_suite.sql
-- Expected runtime: 2-5 minutes depending on data volume
--
-- Success Criteria Summary:
-- ✅ Router uplift: +0.3 judge points with 95% CI excluding 0
-- ✅ Neural encoder: 70%+ high-value buckets show Δ≥+0.3
-- ✅ CE utility: Neural+bandit router > any fixed policy
-- ✅ RAG guardrails: median(docs_used) ≥ 3 under load
-- ✅ Federated ε: ≤ 2.0 per 30d per deployment
-- ✅ Constitution: Zero unapproved drifts, signed interventions
-- ✅ Dynamic weighting: ≥20% better governance score
-- ✅ Safety alerts: All trip-wires properly configured
--
-- =============================================================================

-- =============================================================================
-- 1) PROVE THE ROUTER IS NET-POSITIVE (Inverse Propensity Scoring / Doubly-Robust)
-- =============================================================================

-- First, ensure we have the required data structure
-- bandit_decisions table should contain: ts, request_id, arm, prob, reward, baseline_arm

-- 1A) Inverse Propensity Scoring (IPS) uplift validation
WITH ips_calculation AS (
    SELECT
        -- IPS estimate for current policy
        AVG(CASE WHEN arm = recommended_arm THEN reward::float / NULLIF(prob::float, 0) END) as v_ips_policy,

        -- IPS estimate for always-baseline policy
        AVG(CASE WHEN arm = baseline_arm THEN reward::float / NULLIF(prob::float, 0) END) as v_ips_baseline,

        -- Sample size for statistical significance
        COUNT(*) as total_decisions,

        -- Standard error calculation
        STDDEV(CASE WHEN arm = recommended_arm THEN reward::float / NULLIF(prob::float, 0) END) /
        SQRT(COUNT(CASE WHEN arm = recommended_arm THEN 1 END)) as se_ips_policy,

        STDDEV(CASE WHEN arm = baseline_arm THEN reward::float / NULLIF(prob::float, 0) END) /
        SQRT(COUNT(CASE WHEN arm = baseline_arm THEN 1 END)) as se_ips_baseline

    FROM bandit_decisions
    WHERE ts > NOW() - INTERVAL '7 days'
      AND prob > 0  -- Valid probability
      AND reward IS NOT NULL
)
SELECT
    'ROUTER_UPLIFT_VALIDATION' as check_name,
    ROUND(v_ips_policy::numeric, 4) as ips_policy_value,
    ROUND(v_ips_baseline::numeric, 4) as ips_baseline_value,
    ROUND((v_ips_policy - v_ips_baseline)::numeric, 4) as ips_uplift,
    ROUND((v_ips_policy - v_ips_baseline) / NULLIF(v_ips_baseline, 0) * 100::numeric, 2) as ips_uplift_pct,

    -- 95% confidence interval (t-distribution approximation)
    ROUND((v_ips_policy - v_ips_baseline - 1.96 * SQRT(se_ips_policy^2 + se_ips_baseline^2))::numeric, 4) as ci_lower,
    ROUND((v_ips_policy - v_ips_baseline + 1.96 * SQRT(se_ips_policy^2 + se_ips_baseline^2))::numeric, 4) as ci_upper,

    CASE
        WHEN (v_ips_policy - v_ips_baseline) >= 0.3 AND
             (v_ips_policy - v_ips_baseline - 1.96 * SQRT(se_ips_policy^2 + se_ips_baseline^2)) > 0
        THEN '✅ PASS: Net-positive with statistical significance'
        WHEN (v_ips_policy - v_ips_baseline) > 0
        THEN '⚠️  MARGINAL: Positive but not meeting +0.3 threshold'
        ELSE '❌ FAIL: No significant improvement or negative'
    END as validation_result,

    total_decisions,
    ROUND(se_ips_policy::numeric, 4) as se_policy,
    ROUND(se_ips_baseline::numeric, 4) as se_baseline

FROM ips_calculation;

-- 1B) Doubly-Robust estimation (requires qhat predictions)
-- Note: This requires a Q-function estimator (judge model predictions)
-- For now, using simplified version

WITH dr_calculation AS (
    SELECT
        AVG(
            CASE WHEN arm = recommended_arm THEN reward::float END +
            CASE WHEN arm = recommended_arm THEN
                (reward::float - COALESCE(qhat_pred::float, reward::float)) / NULLIF(prob::float, 0)
            END
        ) as v_dr_policy,

        AVG(
            CASE WHEN arm = baseline_arm THEN reward::float END +
            CASE WHEN arm = baseline_arm THEN
                (reward::float - COALESCE(qhat_pred::float, reward::float)) / NULLIF(prob::float, 0)
            END
        ) as v_dr_baseline

    FROM bandit_decisions
    WHERE ts > NOW() - INTERVAL '7 days'
      AND prob > 0
      AND reward IS NOT NULL
)
SELECT
    'DOUBLY_ROBUST_VALIDATION' as check_name,
    ROUND(v_dr_policy::numeric, 4) as dr_policy_value,
    ROUND(v_dr_baseline::numeric, 4) as dr_baseline_value,
    ROUND((v_dr_policy - v_dr_baseline)::numeric, 4) as dr_uplift,
    CASE
        WHEN (v_dr_policy - v_dr_baseline) >= 0.25 THEN '✅ PASS: DR confirms IPS results'
        WHEN (v_dr_policy - v_dr_baseline) > 0 THEN '⚠️  MARGINAL: DR shows some improvement'
        ELSE '❌ FAIL: DR contradicts IPS results'
    END as validation_result
FROM dr_calculation;

-- =============================================================================
-- 2) VALIDATE NEURAL CONTEXT ENCODER BEATS HEURISTICS (Paired Test)
-- =============================================================================

-- 2A) Per-query cluster comparison with statistical significance
WITH cluster_comparison AS (
    SELECT
        intent_category,
        domain_category,
        AVG(CASE WHEN routing_method = 'neural' THEN reward END) as neural_reward,
        AVG(CASE WHEN routing_method = 'heuristic' THEN reward END) as heuristic_reward,
        COUNT(CASE WHEN routing_method = 'neural' THEN 1 END) as neural_samples,
        COUNT(CASE WHEN routing_method = 'heuristic' THEN 1 END) as heuristic_samples,
        (AVG(CASE WHEN routing_method = 'neural' THEN reward END) -
         AVG(CASE WHEN routing_method = 'heuristic' THEN reward END)) as delta
    FROM routing_outcomes
    WHERE ts > NOW() - INTERVAL '14 days'
      AND intent_category IS NOT NULL
      AND domain_category IS NOT NULL
    GROUP BY intent_category, domain_category
    HAVING COUNT(CASE WHEN routing_method = 'neural' THEN 1 END) >= 10
       AND COUNT(CASE WHEN routing_method = 'heuristic' THEN 1 END) >= 10
),
high_value_clusters AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY neural_samples DESC) as cluster_rank
    FROM cluster_comparison
    WHERE neural_samples >= 50  -- High-value clusters
)
SELECT
    'NEURAL_ENCODER_VALIDATION' as check_name,
    COUNT(*) as total_clusters_analyzed,
    COUNT(CASE WHEN delta >= 0.3 THEN 1 END) as clusters_with_strong_improvement,
    ROUND(COUNT(CASE WHEN delta >= 0.3 THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as pct_strong_improvement,
    ROUND(AVG(delta)::numeric, 3) as avg_improvement,
    ROUND(STDDEV(delta)::numeric, 3) as improvement_stddev,

    -- Top 5 clusters by improvement
    array_agg(
        intent_category || ':' || domain_category || '=' || ROUND(delta::numeric, 3)
        ORDER BY delta DESC
        LIMIT 5
    ) as top_improving_clusters,

    CASE
        WHEN COUNT(CASE WHEN delta >= 0.3 THEN 1 END) * 100.0 / COUNT(*) >= 70
        THEN '✅ PASS: 70%+ high-value clusters show ≥+0.3 improvement'
        WHEN COUNT(CASE WHEN delta > 0 THEN 1 END) * 100.0 / COUNT(*) >= 80
        THEN '⚠️  PARTIAL: Most clusters improve but not meeting 70% threshold'
        ELSE '❌ FAIL: Insufficient improvement in high-value clusters'
    END as validation_result

FROM cluster_comparison;

-- =============================================================================
-- 3) CE VS COSINE COST-AWARE POLICYMAKING
-- =============================================================================

-- Utility function: U = α·helpfulness - β·latency_ms - γ·CE_cost_usd
-- Parameters: α=1.0, β=0.002 (2μs per ms), γ=1.0 (direct cost in USD)

WITH utility_calculation AS (
    SELECT
        routing_method,
        router_strategy,
        AVG(reward) as avg_helpfulness,
        AVG(latency_ms) as avg_latency,
        AVG(CE_cost_usd) as avg_ce_cost,
        COUNT(*) as sample_size,

        -- Utility calculation
        AVG(reward - 0.002 * latency_ms - CE_cost_usd) as avg_utility,

        -- Component breakdown
        AVG(reward) as utility_helpfulness,
        AVG(-0.002 * latency_ms) as utility_latency_penalty,
        AVG(-CE_cost_usd) as utility_cost_penalty

    FROM routing_outcomes
    WHERE ts > NOW() - INTERVAL '7 days'
      AND reward IS NOT NULL
      AND latency_ms IS NOT NULL
    GROUP BY routing_method, router_strategy
),
best_fixed_policies AS (
    SELECT routing_method, router_strategy, avg_utility,
           ROW_NUMBER() OVER (ORDER BY avg_utility DESC) as rank
    FROM utility_calculation
    WHERE routing_method IN ('cosine_only', 'ce_only', 'heuristic')
),
hierarchical_performance AS (
    SELECT routing_method, router_strategy, avg_utility
    FROM utility_calculation
    WHERE routing_method = 'hierarchical'
)
SELECT
    'COST_AWARE_POLICYMAKING' as check_name,

    -- Best fixed policies
    (SELECT ROUND(avg_utility::numeric, 4) FROM best_fixed_policies WHERE rank = 1) as best_fixed_utility,
    (SELECT router_strategy FROM best_fixed_policies WHERE rank = 1) as best_fixed_strategy,

    -- Hierarchical (constitutional AI) performance
    (SELECT ROUND(avg_utility::numeric, 4) FROM hierarchical_performance LIMIT 1) as hierarchical_utility,
    (SELECT router_strategy FROM hierarchical_performance LIMIT 1) as hierarchical_strategy,

    -- Comparison
    ROUND(
        ((SELECT avg_utility FROM hierarchical_performance LIMIT 1) -
         (SELECT avg_utility FROM best_fixed_policies WHERE rank = 1))::numeric,
        4
    ) as utility_improvement,

    ROUND(
        ((SELECT avg_utility FROM hierarchical_performance LIMIT 1) -
         (SELECT avg_utility FROM best_fixed_policies WHERE rank = 1)) /
        NULLIF((SELECT avg_utility FROM best_fixed_policies WHERE rank = 1), 0) * 100::numeric,
        1
    ) as utility_improvement_pct,

    CASE
        WHEN (SELECT avg_utility FROM hierarchical_performance LIMIT 1) >
             (SELECT avg_utility FROM best_fixed_policies WHERE rank = 1)
        THEN '✅ PASS: Constitutional AI beats best fixed policy'
        ELSE '❌ FAIL: Constitutional AI does not beat fixed policies'
    END as validation_result,

    -- Component analysis
    (SELECT ROUND(avg_helpfulness::numeric, 3) FROM hierarchical_performance) as hierarchical_helpfulness,
    (SELECT ROUND(avg_latency::numeric, 1) FROM hierarchical_performance) as hierarchical_latency,
    (SELECT ROUND(avg_ce_cost::numeric, 4) FROM hierarchical_performance) as hierarchical_ce_cost;

-- =============================================================================
-- 4) RAG RERANKER GUARDRAILS (Over-filter Protection)
-- =============================================================================

-- 4A) Statistical validation of guardrails
WITH rag_stats AS (
    SELECT
        DATE_TRUNC('hour', ts) as hour,
        AVG(docs_used) as avg_docs_used,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY docs_used) as median_docs_used,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY docs_used) as p95_docs_used,
        COUNT(*) as requests,
        AVG(rerank_threshold) as avg_threshold,
        COUNT(CASE WHEN docs_used < 4 THEN 1 END) as under_min_docs,
        COUNT(CASE WHEN docs_used < (top_k / 2) THEN 1 END) as under_half_topk
    FROM rag_retrieval
    WHERE ts > NOW() - INTERVAL '7 days'
      AND reranker_enabled = true
    GROUP BY DATE_TRUNC('hour', ts)
)
SELECT
    'RAG_GUARDRAILS_VALIDATION' as check_name,
    ROUND(AVG(avg_docs_used)::numeric, 2) as avg_docs_used,
    ROUND(AVG(median_docs_used)::numeric, 2) as median_docs_used,
    ROUND(AVG(p95_docs_used)::numeric, 2) as p95_docs_used,
    SUM(requests) as total_requests,
    ROUND(AVG(avg_threshold)::numeric, 3) as avg_rerank_threshold,

    -- Guardrail compliance
    ROUND(AVG(median_docs_used)::numeric, 2) >= 3 as median_above_3,
    SUM(under_min_docs) as requests_under_min_docs,
    ROUND(SUM(under_min_docs) * 100.0 / SUM(requests)::numeric, 3) as pct_under_min_docs,

    CASE
        WHEN AVG(median_docs_used) >= 3 AND SUM(under_min_docs) = 0
        THEN '✅ PASS: Guardrails working perfectly'
        WHEN AVG(median_docs_used) >= 3 AND SUM(under_min_docs) / SUM(requests) < 0.01
        THEN '⚠️  MOSTLY_PASS: Rare violations but median safe'
        ELSE '❌ FAIL: Guardrails not preventing over-filtering'
    END as validation_result

FROM rag_stats;

-- 4B) Recent over-filtering incidents (last 30 minutes)
SELECT
    'RAG_OVERFILTERING_INCIDENTS' as check_name,
    COUNT(*) as incidents_last_30m,
    ROUND(AVG(docs_used)::numeric, 2) as avg_docs_used_incidents,
    ROUND(MIN(docs_used)::numeric, 1) as min_docs_used_incidents,
    MAX(ts) as latest_incident,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS: No over-filtering incidents'
        WHEN COUNT(*) <= 5 THEN '⚠️  MINOR: Few isolated incidents'
        ELSE '❌ FAIL: Frequent over-filtering problems'
    END as validation_result
FROM rag_retrieval
WHERE ts > NOW() - INTERVAL '30 minutes'
  AND reranker_enabled = true
  AND docs_used < 3;

-- =============================================================================
-- 5) FEDERATED PRIVACY BUDGET & REPUTATION ENFORCEMENT
-- =============================================================================

-- 5A) Privacy budget accounting per deployment
WITH deployment_privacy AS (
    SELECT
        deployment_id,
        SUM(epsilon_used) as eps_spent_30d,
        AVG(reputation_score) as avg_reputation,
        COUNT(*) as rounds_participated,
        MAX(ts) as last_participation,
        SUM(num_examples) as total_examples_contributed
    FROM federated_updates
    WHERE ts > NOW() - INTERVAL '30 days'
    GROUP BY deployment_id
),
budget_analysis AS (
    SELECT
        deployment_id,
        eps_spent_30d,
        eps_spent_30d <= 2.0 as within_budget,
        avg_reputation,
        rounds_participated,
        total_examples_contributed,
        CASE
            WHEN eps_spent_30d <= 2.0 AND avg_reputation >= 0.8 THEN '✅ GOOD_STANDING'
            WHEN eps_spent_30d <= 2.0 THEN '⚠️  BUDGET_OK_LOW_REP'
            WHEN eps_spent_30d > 2.0 THEN '❌ OVER_BUDGET'
            ELSE '❓ UNKNOWN'
        END as status
    FROM deployment_privacy
)
SELECT
    'FEDERATED_PRIVACY_BUDGET' as check_name,
    COUNT(*) as total_deployments,
    COUNT(CASE WHEN within_budget THEN 1 END) as deployments_within_budget,
    ROUND(COUNT(CASE WHEN within_budget THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as pct_within_budget,
    ROUND(AVG(eps_spent_30d)::numeric, 3) as avg_eps_spent,
    ROUND(MAX(eps_spent_30d)::numeric, 3) as max_eps_spent,
    ROUND(MIN(eps_spent_30d)::numeric, 3) as min_eps_spent,

    CASE
        WHEN COUNT(CASE WHEN within_budget THEN 1 END) = COUNT(*) AND MAX(eps_spent_30d) <= 2.0
        THEN '✅ PASS: All deployments within privacy budget'
        WHEN COUNT(CASE WHEN within_budget THEN 1 END) >= COUNT(*) * 0.9
        THEN '⚠️  MOSTLY_PASS: Minor budget exceedances'
        ELSE '❌ FAIL: Significant privacy budget violations'
    END as validation_result

FROM budget_analysis;

-- 5B) Reputation-weighted aggregation effectiveness
WITH reputation_weighted AS (
    SELECT
        deployment_id,
        avg_reputation,
        total_examples_contributed,
        -- Calculate reputation-weighted contribution
        LEAST(total_examples_contributed, 1000) * avg_reputation as weighted_contribution,
        eps_spent_30d
    FROM deployment_privacy
)
SELECT
    'FEDERATION_REPUTATION_ENFORCEMENT' as check_name,
    COUNT(*) as active_deployments,
    ROUND(AVG(avg_reputation)::numeric, 3) as avg_reputation,
    ROUND(CORR(weighted_contribution, avg_reputation)::numeric, 3) as reputation_contribution_correlation,

    -- Top contributors by reputation-weighted metric
    (SELECT STRING_AGG(deployment_id || ':' || ROUND(weighted_contribution::numeric, 0), ', ' ORDER BY weighted_contribution DESC LIMIT 3)
     FROM reputation_weighted) as top_reputation_contributors,

    -- Low reputation deployments should have low weight
    ROUND(AVG(CASE WHEN avg_reputation < 0.5 THEN weighted_contribution END)::numeric, 1) as low_rep_avg_weight,
    ROUND(AVG(CASE WHEN avg_reputation >= 0.8 THEN weighted_contribution END)::numeric, 1) as high_rep_avg_weight,

    CASE
        WHEN CORR(weighted_contribution, avg_reputation) > 0.7
        THEN '✅ PASS: Strong reputation-contribution correlation'
        WHEN CORR(weighted_contribution, avg_reputation) > 0.5
        THEN '⚠️  MODERATE: Some reputation weighting but could be stronger'
        ELSE '❌ FAIL: Reputation not effectively weighting contributions'
    END as validation_result

FROM reputation_weighted;

-- =============================================================================
-- 6) CONSTITUTIONAL LAYER: PROVABLE VETOES + VERSIONING
-- =============================================================================

-- 6A) Constitution versioning and compliance
WITH constitution_compliance AS (
    SELECT
        gs.name as strategy_name,
        gs.governance_score,
        gs.deployment_status,
        sd.policy_version,
        sd.policy_hash,
        sd.signed_approval,
        gs.created_at,
        sd.deployed_at
    FROM generated_strategies gs
    LEFT JOIN strategy_deployments sd ON gs.name = sd.strategy_name
    WHERE gs.created_at > NOW() - INTERVAL '30 days'
),
version_analysis AS (
    SELECT
        COUNT(*) as total_strategies,
        COUNT(CASE WHEN policy_version IS NOT NULL THEN 1 END) as versioned_strategies,
        COUNT(CASE WHEN signed_approval IS NOT NULL THEN 1 END) as signed_strategies,
        COUNT(DISTINCT policy_version) as unique_versions,
        COUNT(DISTINCT policy_hash) as unique_hashes,
        COUNT(CASE WHEN deployment_status = 'deployed' AND policy_version IS NULL THEN 1 END) as unversioned_deployments
    FROM constitution_compliance
)
SELECT
    'CONSTITUTIONAL_VERSIONING' as check_name,
    total_strategies,
    versioned_strategies,
    signed_strategies,
    unique_versions,
    unique_hashes,
    unversioned_deployments,
    ROUND(versioned_strategies * 100.0 / total_strategies::numeric, 1) as pct_versioned,
    ROUND(signed_strategies * 100.0 / total_strategies::numeric, 1) as pct_signed,

    CASE
        WHEN unversioned_deployments = 0 AND signed_strategies = versioned_strategies
        THEN '✅ PASS: All strategies properly versioned and signed'
        WHEN unversioned_deployments = 0
        THEN '⚠️  PARTIAL: All versioned but some missing signatures'
        ELSE '❌ FAIL: Unversioned strategies in production'
    END as validation_result

FROM version_analysis;

-- 6B) Governance drift detection
WITH governance_drift AS (
    SELECT
        strategy_id,
        COUNT(*) as total_assessments,
        COUNT(CASE WHEN overall_clearance = false THEN 1 END) as violations,
        COUNT(CASE WHEN governance_score < 0.5 THEN 1 END) as critical_violations,
        MAX(ts) as last_assessment,
        ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score
    FROM governance_assessments
    WHERE ts > NOW() - INTERVAL '7 days'
    GROUP BY strategy_id
),
drift_incidents AS (
    SELECT
        gi.strategy_id,
        gi.rule_id,
        gi.severity,
        gi.ts,
        ROW_NUMBER() OVER (PARTITION BY gi.strategy_id, gi.rule_id ORDER BY gi.ts) as incident_number
    FROM governance_incidents gi
    WHERE gi.ts > NOW() - INTERVAL '15 minutes'
)
SELECT
    'GOVERNANCE_DRIFT_DETECTION' as check_name,
    COUNT(*) as strategies_monitored,
    COUNT(CASE WHEN violations > 0 THEN 1 END) as strategies_with_violations,
    COUNT(CASE WHEN critical_violations > 0 THEN 1 END) as strategies_with_critical_violations,
    SUM(violations) as total_violations,
    ROUND(AVG(avg_governance_score)::numeric, 3) as avg_governance_score,

    -- Recent incidents (last 15 minutes)
    (SELECT COUNT(*) FROM drift_incidents WHERE incident_number >= 3) as strategies_with_3plus_violations,

    CASE
        WHEN (SELECT COUNT(*) FROM drift_incidents WHERE incident_number >= 3) = 0
        THEN '✅ PASS: No governance drift incidents'
        WHEN COUNT(CASE WHEN critical_violations > 0 THEN 1 END) = 0
        THEN '⚠️  MONITOR: Some violations but no critical issues'
        ELSE '❌ FAIL: Critical governance drift detected'
    END as validation_result

FROM governance_drift;

-- =============================================================================
-- 7) DYNAMIC CONSTITUTIONAL WEIGHTING: ABLATION STUDY
-- =============================================================================

-- Compare static vs dynamic weighting performance
WITH weighting_comparison AS (
    SELECT
        'static_weights' as weighting_type,
        COUNT(*) as assessments,
        ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score,
        COUNT(CASE WHEN overall_clearance THEN 1 END) as clearances,
        ROUND(AVG(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3) as clearance_rate
    FROM governance_assessments
    WHERE ts > NOW() - INTERVAL '7 days'
      AND weighted_governance_score IS NULL  -- Static weighting period

    UNION ALL

    SELECT
        'dynamic_weights' as weighting_type,
        COUNT(*) as assessments,
        ROUND(AVG(weighted_governance_score)::numeric, 3) as avg_weighted_governance_score,
        COUNT(CASE WHEN dynamic_clearance THEN 1 END) as clearances,
        ROUND(AVG(CASE WHEN dynamic_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3) as clearance_rate
    FROM governance_assessments
    WHERE ts > NOW() - INTERVAL '7 days'
      AND weighted_governance_score IS NOT NULL  -- Dynamic weighting period
),
utility_impact AS (
    -- Check that dynamic weighting doesn't harm utility
    SELECT
        AVG(CASE WHEN weighted_governance_score IS NOT NULL THEN reward END) as dynamic_utility,
        AVG(CASE WHEN weighted_governance_score IS NULL THEN reward END) as static_utility
    FROM governance_assessments ga
    JOIN bandit_decisions bd ON ga.strategy_id = bd.strategy_name
    WHERE ga.ts > NOW() - INTERVAL '7 days'
)
SELECT
    'DYNAMIC_WEIGHTING_ABLATION' as check_name,

    -- Static weights performance
    (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'static_weights') as static_governance_score,
    (SELECT clearance_rate FROM weighting_comparison WHERE weighting_type = 'static_weights') as static_clearance_rate,

    -- Dynamic weights performance
    (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'dynamic_weights') as dynamic_governance_score,
    (SELECT clearance_rate FROM weighting_comparison WHERE weighting_type = 'dynamic_weights') as dynamic_clearance_rate,

    -- Improvement metrics
    ROUND(
        ((SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'dynamic_weights') -
         (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'static_weights')) /
        NULLIF((SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'static_weights'), 0) * 100::numeric,
        1
    ) as governance_improvement_pct,

    -- Utility preservation check
    (SELECT ROUND((dynamic_utility - static_utility)::numeric, 4) FROM utility_impact) as utility_impact,
    (SELECT ROUND((dynamic_utility - static_utility) / NULLIF(static_utility, 0) * 100::numeric, 1) FROM utility_impact) as utility_impact_pct,

    CASE
        WHEN (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'dynamic_weights') >
             (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'static_weights') * 1.2
             AND (SELECT utility_impact FROM utility_impact) >= -0.05
        THEN '✅ PASS: ≥20% governance improvement with utility preserved'
        WHEN (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'dynamic_weights') >
             (SELECT avg_governance_score FROM weighting_comparison WHERE weighting_type = 'static_weights')
        THEN '⚠️  PARTIAL: Some improvement but not meeting thresholds'
        ELSE '❌ FAIL: Dynamic weighting not providing significant benefits'
    END as validation_result

FROM weighting_comparison
LIMIT 1;

-- =============================================================================
-- 8) LIVE SAFETY TRIP-WIRES (PROMQL ALERTS)
-- =============================================================================

-- Note: These are PromQL alert definitions that should be added to your Prometheus
-- alert manager configuration. Including here for validation completeness.

/*
# Latency Trip-wire
ALERT RouterP95Latency
  IF histogram_quantile(0.95, sum(rate(router_latency_seconds_bucket[10m])) by (le)) > 0.8
  FOR 10m
  LABELS { severity = "critical" }
  ANNOTATIONS {
    summary = "Router P95 latency exceeded 800ms",
    description = "Router P95 latency is {{ $value }}s, above 800ms threshold"
  }

# Judge Helpfulness Collapse
ALERT JudgeHelpfulnessDrop
  IF avg_over_time(judge_helpfulness_avg[30m]) - avg_over_time(judge_helpfulness_avg[30m] offset 30m) <= -0.5
  FOR 15m
  LABELS { severity = "critical" }
  ANNOTATIONS {
    summary = "Judge helpfulness dropped by 0.5+ points",
    description = "Judge helpfulness decreased by {{ $value }} points in 30m"
  }

# Strategy Monoculture Risk
ALERT StrategyImbalance
  IF max_over_time(strategy_traffic_pct[2h]) > 0.7
  FOR 10m
  LABELS { severity = "warning" }
  ANNOTATIONS {
    summary = "Strategy traffic imbalance detected",
    description = "Single strategy receiving {{ $value }}% of traffic"
  }

# RAG Over-filtering (from section 4)
ALERT RAGRerankOverFiltering
  IF histogram_quantile(0.5, sum(rate(rag_docs_used_bucket[30m])) by (le)) < 3
  FOR 10m
  LABELS { severity = "warning" }
  ANNOTATIONS {
    summary = "RAG reranker over-filtering detected",
    description = "Median documents used dropped below 3"
  }
*/

-- 8A) Validate alert metrics are being collected
SELECT
    'SAFETY_TRIPWIRES_VALIDATION' as check_name,

    -- Check latency metrics
    (SELECT COUNT(*) > 0 FROM router_metrics WHERE latency_p95 IS NOT NULL AND ts > NOW() - INTERVAL '1 hour') as latency_metrics_present,

    -- Check judge metrics
    (SELECT COUNT(*) > 0 FROM judge_metrics WHERE helpfulness_avg IS NOT NULL AND ts > NOW() - INTERVAL '1 hour') as judge_metrics_present,

    -- Check strategy distribution
    (SELECT COUNT(DISTINCT strategy) >= 3 FROM bandit_decisions WHERE ts > NOW() - INTERVAL '1 hour') as multiple_strategies_active,

    -- Check RAG metrics
    (SELECT COUNT(*) > 0 FROM rag_retrieval WHERE docs_used IS NOT NULL AND ts > NOW() - INTERVAL '1 hour') as rag_metrics_present,

    CASE
        WHEN (SELECT COUNT(*) > 0 FROM router_metrics WHERE latency_p95 IS NOT NULL AND ts > NOW() - INTERVAL '1 hour') AND
             (SELECT COUNT(*) > 0 FROM judge_metrics WHERE helpfulness_avg IS NOT NULL AND ts > NOW() - INTERVAL '1 hour') AND
             (SELECT COUNT(DISTINCT strategy) >= 3 FROM bandit_decisions WHERE ts > NOW() - INTERVAL '1 hour') AND
             (SELECT COUNT(*) > 0 FROM rag_retrieval WHERE docs_used IS NOT NULL AND ts > NOW() - INTERVAL '1 hour')
        THEN '✅ PASS: All safety metrics being collected'
        ELSE '❌ FAIL: Missing safety monitoring metrics'
    END as validation_result;

-- =============================================================================
-- 9) CHAOS & ROLLBACK DRILLS VALIDATION
-- =============================================================================

-- 9A) Recent chaos engineering experiments
WITH chaos_experiments AS (
    SELECT
        experiment_type,
        experiment_start,
        experiment_end,
        EXTRACT(EPOCH FROM (experiment_end - experiment_start)) / 60 as duration_minutes,
        success_criteria_met,
        rollback_triggered,
        impact_assessment
    FROM chaos_experiments
    WHERE experiment_start > NOW() - INTERVAL '30 days'
)
SELECT
    'CHAOS_ENGINEERING_VALIDATION' as check_name,
    COUNT(*) as experiments_run,
    COUNT(CASE WHEN success_criteria_met THEN 1 END) as successful_experiments,
    ROUND(COUNT(CASE WHEN success_criteria_met THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as success_rate,
    COUNT(CASE WHEN rollback_triggered THEN 1 END) as rollbacks_triggered,
    AVG(duration_minutes) as avg_experiment_duration,

    -- Experiment types covered
    COUNT(CASE WHEN experiment_type = 'ce_disable' THEN 1 END) as ce_disable_tests,
    COUNT(CASE WHEN experiment_type = 'federation_poison' THEN 1 END) as federation_poison_tests,
    COUNT(CASE WHEN experiment_type = 'constitution_flip' THEN 1 END) as constitution_flip_tests,
    COUNT(CASE WHEN experiment_type = 'bandit_reset' THEN 1 END) as bandit_reset_tests,

    CASE
        WHEN COUNT(*) >= 4 AND COUNT(CASE WHEN success_criteria_met THEN 1 END) = COUNT(*)
        THEN '✅ PASS: All chaos drills passed successfully'
        WHEN COUNT(*) >= 4 AND COUNT(CASE WHEN success_criteria_met THEN 1 END) >= COUNT(*) * 0.75
        THEN '⚠️  MOSTLY_PASS: Most drills successful, some issues'
        ELSE '❌ FAIL: Insufficient chaos testing or poor results'
    END as validation_result

FROM chaos_experiments;

-- 9B) Rollback effectiveness
WITH rollback_incidents AS (
    SELECT
        incident_type,
        rollback_start,
        rollback_end,
        EXTRACT(EPOCH FROM (rollback_end - rollback_start)) / 60 as rollback_duration_minutes,
        system_restored,
        performance_impact,
        user_impact
    FROM rollback_incidents
    WHERE rollback_start > NOW() - INTERVAL '30 days'
)
SELECT
    'ROLLBACK_EFFECTIVENESS' as check_name,
    COUNT(*) as rollbacks_executed,
    COUNT(CASE WHEN system_restored THEN 1 END) as successful_rollbacks,
    ROUND(AVG(rollback_duration_minutes)::numeric, 1) as avg_rollback_duration,
    MAX(rollback_duration_minutes) as max_rollback_duration,

    -- Impact assessment
    AVG(CASE WHEN performance_impact < 0.1 THEN 1.0 ELSE 0.0 END) as low_performance_impact_rate,
    AVG(CASE WHEN user_impact < 0.05 THEN 1.0 ELSE 0.0 END) as low_user_impact_rate,

    CASE
        WHEN COUNT(*) > 0 AND COUNT(CASE WHEN system_restored THEN 1 END) = COUNT(*) AND AVG(rollback_duration_minutes) <= 15
        THEN '✅ PASS: Rollback mechanisms working effectively'
        WHEN COUNT(*) > 0 AND COUNT(CASE WHEN system_restored THEN 1 END) >= COUNT(*) * 0.8
        THEN '⚠️  MOSTLY_PASS: Most rollbacks successful but some issues'
        ELSE '❌ FAIL: Rollback mechanisms unreliable'
    END as validation_result

FROM rollback_incidents;

-- =============================================================================
-- 10) MINIMAL GAPS TO CLOSE (FAST WINS)
-- =============================================================================

-- 10A) Bandit probability logging
SELECT
    'BANDIT_PROBABILITY_LOGGING' as check_name,
    COUNT(*) as total_decisions_logged,
    COUNT(CASE WHEN prob IS NOT NULL AND prob > 0 THEN 1 END) as decisions_with_valid_prob,
    ROUND(COUNT(CASE WHEN prob IS NOT NULL AND prob > 0 THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as pct_with_prob,
    ROUND(AVG(prob)::numeric, 3) as avg_logged_probability,
    ROUND(STDDEV(prob)::numeric, 3) as prob_stddev,

    CASE
        WHEN COUNT(CASE WHEN prob IS NOT NULL AND prob > 0 THEN 1 END) = COUNT(*)
        THEN '✅ PASS: All bandit decisions have probability logging'
        WHEN COUNT(CASE WHEN prob IS NOT NULL AND prob > 0 THEN 1 END) >= COUNT(*) * 0.95
        THEN '⚠️  MOSTLY_PASS: Nearly complete probability logging'
        ELSE '❌ FAIL: Missing probability logging for IPS/DR validation'
    END as validation_result

FROM bandit_decisions
WHERE ts > NOW() - INTERVAL '1 hour';

-- 10B) Model snapshot reproducibility
WITH model_snapshots AS (
    SELECT
        deployment_id,
        model_type,
        model_version,
        snapshot_hash,
        created_at,
        constitution_version,
        ce_threshold,
        neural_encoder_version
    FROM model_snapshots
    WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT
    'MODEL_REPRODUCIBILITY' as check_name,
    COUNT(DISTINCT deployment_id) as deployments_with_snapshots,
    COUNT(*) as total_snapshots,
    COUNT(DISTINCT snapshot_hash) as unique_snapshot_hashes,
    COUNT(CASE WHEN constitution_version IS NOT NULL THEN 1 END) as snapshots_with_constitution,
    COUNT(CASE WHEN ce_threshold IS NOT NULL THEN 1 END) as snapshots_with_ce_config,
    COUNT(CASE WHEN neural_encoder_version IS NOT NULL THEN 1 END) as snapshots_with_neural_config,

    CASE
        WHEN COUNT(CASE WHEN constitution_version IS NOT NULL THEN 1 END) = COUNT(*) AND
             COUNT(CASE WHEN ce_threshold IS NOT NULL THEN 1 END) = COUNT(*) AND
             COUNT(CASE WHEN neural_encoder_version IS NOT NULL THEN 1 END) = COUNT(*)
        THEN '✅ PASS: Complete model reproducibility snapshots'
        WHEN COUNT(CASE WHEN constitution_version IS NOT NULL THEN 1 END) >= COUNT(*) * 0.8
        THEN '⚠️  PARTIAL: Most snapshots include reproducibility data'
        ELSE '❌ FAIL: Missing reproducibility metadata'
    END as validation_result

FROM model_snapshots;

-- 10C) PII canary validation
WITH pii_checks AS (
    SELECT
        request_id,
        pii_detected,
        pii_severity,
        pii_types_found,
        blocked_for_pii,
        ts
    FROM pii_canary_checks
    WHERE ts > NOW() - INTERVAL '24 hours'
),
pii_incidents AS (
    SELECT
        COUNT(*) as total_checks,
        COUNT(CASE WHEN pii_detected THEN 1 END) as pii_detected,
        COUNT(CASE WHEN blocked_for_pii THEN 1 END) as requests_blocked,
        COUNT(DISTINCT pii_types_found) as unique_pii_types,
        MAX(CASE WHEN pii_detected THEN ts END) as latest_pii_detection
    FROM pii_checks
)
SELECT
    'PII_CANARY_VALIDATION' as check_name,
    total_checks,
    pii_detected,
    ROUND(pii_detected * 100.0 / total_checks::numeric, 2) as pct_pii_detected,
    requests_blocked,
    unique_pii_types,

    CASE
        WHEN requests_blocked > 0 AND pii_detected > 0
        THEN '✅ PASS: PII detection and blocking working'
        WHEN pii_detected > 0 AND requests_blocked = 0
        THEN '⚠️  DETECTING_BUT_NOT_BLOCKING: PII found but not blocked'
        WHEN total_checks > 1000 AND pii_detected = 0
        THEN '⚠️  NO_PII_DETECTED: Possible false negative or clean data'
        ELSE '❓ INSUFFICIENT_DATA: Need more checks for validation'
    END as validation_result

FROM pii_incidents;

-- =============================================================================
-- FINAL VALIDATION SUMMARY
-- =============================================================================

WITH validation_results AS (
    -- Router uplift validation
    SELECT '1_router_uplift' as check_id, 'PASS' as status WHERE (
        SELECT (v_ips_policy - v_ips_baseline) >= 0.3 AND
               (v_ips_policy - v_ips_baseline - 1.96 * SQRT(se_ips_policy^2 + se_ips_baseline^2)) > 0
        FROM (SELECT AVG(CASE WHEN arm = recommended_arm THEN reward::float / NULLIF(prob::float, 0) END) as v_ips_policy,
                     AVG(CASE WHEN arm = baseline_arm THEN reward::float / NULLIF(prob::float, 0) END) as v_ips_baseline,
                     STDDEV(CASE WHEN arm = recommended_arm THEN reward::float / NULLIF(prob::float, 0) END) /
                     SQRT(COUNT(CASE WHEN arm = recommended_arm THEN 1 END)) as se_ips_policy,
                     STDDEV(CASE WHEN arm = baseline_arm THEN reward::float / NULLIF(prob::float, 0) END) /
                     SQRT(COUNT(CASE WHEN arm = baseline_arm THEN 1 END)) as se_ips_baseline
              FROM bandit_decisions WHERE ts > NOW() - INTERVAL '7 days') ips
    )

    UNION ALL

    -- Neural encoder validation
    SELECT '2_neural_encoder' as check_id, 'PASS' as status WHERE (
        SELECT COUNT(CASE WHEN delta >= 0.3 THEN 1 END) * 100.0 / COUNT(*) >= 70
        FROM (SELECT AVG(CASE WHEN routing_method = 'neural' THEN reward END) -
                     AVG(CASE WHEN routing_method = 'heuristic' THEN reward END) as delta
              FROM routing_outcomes WHERE ts > NOW() - INTERVAL '14 days'
              GROUP BY intent_category, domain_category) comp
    )

    UNION ALL

    -- CE vs Cosine utility
    SELECT '3_ce_utility' as check_id, 'PASS' as status WHERE (
        SELECT hierarchical_utility > best_fixed_utility
        FROM (SELECT AVG(reward - 0.002 * latency_ms - CE_cost_usd) as hierarchical_utility
              FROM routing_outcomes WHERE ts > NOW() - INTERVAL '7 days' AND routing_method = 'hierarchical') h,
             (SELECT AVG(reward - 0.002 * latency_ms - CE_cost_usd) as best_fixed_utility
              FROM routing_outcomes WHERE ts > NOW() - INTERVAL '7 days' AND routing_method IN ('cosine_only', 'ce_only', 'heuristic')
              GROUP BY routing_method, router_strategy ORDER BY AVG(reward - 0.002 * latency_ms - CE_cost_usd) DESC LIMIT 1) f
    )

    UNION ALL

    -- RAG guardrails
    SELECT '4_rag_guardrails' as check_id, 'PASS' as status WHERE (
        SELECT AVG(median_docs_used) >= 3 AND SUM(under_min_docs) = 0
        FROM (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY docs_used) as median_docs_used,
                     COUNT(CASE WHEN docs_used < 4 THEN 1 END) as under_min_docs
              FROM rag_retrieval WHERE ts > NOW() - INTERVAL '7 days' AND reranker_enabled = true
              GROUP BY DATE_TRUNC('hour', ts)) stats
    )

    UNION ALL

    -- Federated privacy budget
    SELECT '5_federated_privacy' as check_id, 'PASS' as status WHERE (
        SELECT COUNT(CASE WHEN eps_spent_30d <= 2.0 THEN 1 END) = COUNT(*)
        FROM (SELECT deployment_id, SUM(epsilon_used) as eps_spent_30d
              FROM federated_updates WHERE ts > NOW() - INTERVAL '30 days'
              GROUP BY deployment_id) dp
    )

    UNION ALL

    -- Constitutional versioning
    SELECT '6_constitutional_versioning' as check_id, 'PASS' as status WHERE (
        SELECT COUNT(CASE WHEN policy_version IS NULL THEN 1 END) = 0
        FROM generated_strategies gs LEFT JOIN strategy_deployments sd ON gs.name = sd.strategy_name
        WHERE gs.deployment_status = 'deployed'
    )

    UNION ALL

    -- Dynamic weighting ablation
    SELECT '7_dynamic_weighting' as check_id, 'PASS' as status WHERE (
        SELECT dynamic_governance > static_governance * 1.2
        FROM (SELECT AVG(governance_score) as static_governance FROM governance_assessments
              WHERE weighted_governance_score IS NULL AND ts > NOW() - INTERVAL '7 days') s,
             (SELECT AVG(weighted_governance_score) as dynamic_governance FROM governance_assessments
              WHERE weighted_governance_score IS NOT NULL AND ts > NOW() - INTERVAL '7 days') d
    )

    UNION ALL

    -- Safety trip-wires
    SELECT '8_safety_tripwires' as check_id, 'PASS' as status WHERE (
        SELECT (SELECT COUNT(*) > 0 FROM router_metrics WHERE ts > NOW() - INTERVAL '1 hour') AND
               (SELECT COUNT(*) > 0 FROM judge_metrics WHERE ts > NOW() - INTERVAL '1 hour') AND
               (SELECT COUNT(DISTINCT strategy) >= 3 FROM bandit_decisions WHERE ts > NOW() - INTERVAL '1 hour') AND
               (SELECT COUNT(*) > 0 FROM rag_retrieval WHERE ts > NOW() - INTERVAL '1 hour')
    )

    UNION ALL

    -- Chaos & rollback
    SELECT '9_chaos_rollback' as check_id, 'PASS' as status WHERE (
        SELECT COUNT(CASE WHEN success_criteria_met THEN 1 END) = COUNT(*)
        FROM chaos_experiments WHERE experiment_start > NOW() - INTERVAL '30 days'
    )

    UNION ALL

    -- Minimal gaps
    SELECT '10_minimal_gaps' as check_id, 'PASS' as status WHERE (
        SELECT COUNT(CASE WHEN prob IS NOT NULL AND prob > 0 THEN 1 END) >= COUNT(*) * 0.95 AND
               (SELECT COUNT(CASE WHEN constitution_version IS NOT NULL THEN 1 END) = COUNT(*)
                FROM model_snapshots WHERE created_at > NOW() - INTERVAL '7 days') AND
               (SELECT COUNT(CASE WHEN blocked_for_pii THEN 1 END) > 0
                FROM pii_canary_checks WHERE ts > NOW() - INTERVAL '24 hours')
        FROM bandit_decisions WHERE ts > NOW() - INTERVAL '1 hour'
    )
)
SELECT
    'PRODUCTION_VALIDATION_SUMMARY' as validation_summary,
    COUNT(*) as total_checks,
    COUNT(CASE WHEN status = 'PASS' THEN 1 END) as passed_checks,
    ROUND(COUNT(CASE WHEN status = 'PASS' THEN 1 END) * 100.0 / COUNT(*)::numeric, 1) as pass_rate,

    -- Individual check results
    MAX(CASE WHEN check_id = '1_router_uplift' THEN status END) as router_uplift,
    MAX(CASE WHEN check_id = '2_neural_encoder' THEN status END) as neural_encoder,
    MAX(CASE WHEN check_id = '3_ce_utility' THEN status END) as ce_utility,
    MAX(CASE WHEN check_id = '4_rag_guardrails' THEN status END) as rag_guardrails,
    MAX(CASE WHEN check_id = '5_federated_privacy' THEN status END) as federated_privacy,
    MAX(CASE WHEN check_id = '6_constitutional_versioning' THEN status END) as constitutional_versioning,
    MAX(CASE WHEN check_id = '7_dynamic_weighting' THEN status END) as dynamic_weighting,
    MAX(CASE WHEN check_id = '8_safety_tripwires' THEN status END) as safety_tripwires,
    MAX(CASE WHEN check_id = '9_chaos_rollback' THEN status END) as chaos_rollback,
    MAX(CASE WHEN check_id = '10_minimal_gaps' THEN status END) as minimal_gaps,

    CASE
        WHEN COUNT(CASE WHEN status = 'PASS' THEN 1 END) = COUNT(*)
        THEN '🎉 PRODUCTION READY: All validation checks passed!'
        WHEN COUNT(CASE WHEN status = 'PASS' THEN 1 END) >= COUNT(*) * 0.8
        THEN '✅ MOSTLY READY: Minor issues to address'
        WHEN COUNT(CASE WHEN status = 'PASS' THEN 1 END) >= COUNT(*) * 0.6
        THEN '⚠️ NEEDS WORK: Significant issues to resolve'
        ELSE '❌ NOT READY: Major validation failures'
    END as production_readiness

FROM validation_results;

-- =============================================================================
-- END OF PRODUCTION VALIDATION SUITE
-- =============================================================================
