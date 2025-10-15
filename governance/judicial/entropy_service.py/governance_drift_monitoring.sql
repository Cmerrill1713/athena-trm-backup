-- =============================================================================
-- GOVERNANCE DRIFT MONITORING QUERIES
-- =============================================================================
--
-- SQL queries for monitoring governance policy drift, violation patterns,
-- and constitutional consistency in the Constitutional AI Framework.
--
-- Usage: Run these queries regularly to detect governance drift before it
-- becomes critical. Can be automated in monitoring dashboards or alerting.
--
-- =============================================================================

-- =============================================================================
-- 1. GOVERNANCE POLICY DELTA MONITORING
-- =============================================================================

-- 1A. Policy Delta Over Time (Hourly)
-- Tracks how much governance policies have changed recently
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as assessments_count,
    ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score,
    ROUND(STDDEV(governance_score)::numeric, 3) as governance_score_stddev,
    ROUND(AVG(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3) as clearance_rate,
    -- Calculate policy delta (change from previous hour)
    ROUND(
        AVG(governance_score) - LAG(AVG(governance_score)) OVER (ORDER BY DATE_TRUNC('hour', timestamp))
    ::numeric, 3) as policy_delta_from_prev_hour
FROM governance_assessments
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- 1B. Constitutional Weighting Drift Detection
-- Monitors if constitutional weights are drifting from baseline
WITH weight_baselines AS (
    SELECT
        DATE_TRUNC('day', timestamp) as day,
        ROUND(AVG(ethical_weight)::numeric, 3) as baseline_ethical_weight,
        ROUND(AVG(business_weight)::numeric, 3) as baseline_business_weight,
        ROUND(AVG(safety_weight)::numeric, 3) as baseline_safety_weight,
        ROUND(AVG(compliance_weight)::numeric, 3) as baseline_compliance_weight,
        COUNT(*) as baseline_samples
    FROM constitutional_weights
    WHERE timestamp > NOW() - INTERVAL '30 days'
      AND timestamp < NOW() - INTERVAL '7 days'  -- Use older data as baseline
    GROUP BY DATE_TRUNC('day', timestamp)
),
current_weights AS (
    SELECT
        DATE_TRUNC('hour', timestamp) as hour,
        ROUND(AVG(ethical_weight)::numeric, 3) as current_ethical_weight,
        ROUND(AVG(business_weight)::numeric, 3) as current_business_weight,
        ROUND(AVG(safety_weight)::numeric, 3) as current_safety_weight,
        ROUND(AVG(compliance_weight)::numeric, 3) as current_compliance_weight,
        COUNT(*) as current_samples
    FROM constitutional_weights
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY DATE_TRUNC('hour', timestamp)
),
baseline_avg AS (
    SELECT
        ROUND(AVG(baseline_ethical_weight)::numeric, 3) as avg_ethical_baseline,
        ROUND(AVG(baseline_business_weight)::numeric, 3) as avg_business_baseline,
        ROUND(AVG(baseline_safety_weight)::numeric, 3) as avg_safety_baseline,
        ROUND(AVG(baseline_compliance_weight)::numeric, 3) as avg_compliance_baseline
    FROM weight_baselines
)
SELECT
    cw.hour,
    cw.current_samples,
    -- Weight deltas from baseline
    ROUND((cw.current_ethical_weight - ba.avg_ethical_baseline)::numeric, 3) as ethical_weight_delta,
    ROUND((cw.current_business_weight - ba.avg_business_baseline)::numeric, 3) as business_weight_delta,
    ROUND((cw.current_safety_weight - ba.avg_safety_baseline)::numeric, 3) as safety_weight_delta,
    ROUND((cw.current_compliance_weight - ba.avg_compliance_baseline)::numeric, 3) as compliance_weight_delta,

    -- Overall weighting drift score (Euclidean distance)
    ROUND(
        SQRT(
            POWER(cw.current_ethical_weight - ba.avg_ethical_baseline, 2) +
            POWER(cw.current_business_weight - ba.avg_business_baseline, 2) +
            POWER(cw.current_safety_weight - ba.avg_safety_baseline, 2) +
            POWER(cw.current_compliance_weight - ba.avg_compliance_baseline, 2)
        )::numeric,
    3) as constitutional_drift_score,

    -- Alert conditions
    CASE
        WHEN SQRT(POWER(cw.current_ethical_weight - ba.avg_ethical_baseline, 2) +
                  POWER(cw.current_business_weight - ba.avg_business_baseline, 2) +
                  POWER(cw.current_safety_weight - ba.avg_safety_baseline, 2) +
                  POWER(cw.current_compliance_weight - ba.avg_compliance_baseline, 2)) > 0.3
        THEN '🚨 CRITICAL: Constitutional drift detected'
        WHEN SQRT(POWER(cw.current_ethical_weight - ba.avg_ethical_baseline, 2) +
                  POWER(cw.current_business_weight - ba.avg_business_baseline, 2) +
                  POWER(cw.current_safety_weight - ba.avg_safety_baseline, 2) +
                  POWER(cw.current_compliance_weight - ba.avg_compliance_baseline, 2)) > 0.15
        THEN '⚠️ WARNING: Constitutional drift trending'
        ELSE '✅ STABLE: Constitutional weights within normal range'
    END as drift_status

FROM current_weights cw
CROSS JOIN baseline_avg ba
ORDER BY cw.hour DESC;

-- =============================================================================
-- 2. VIOLATION PATTERN ANALYSIS
-- =============================================================================

-- 2A. Violation Rate Trends (By Hour)
-- Monitors governance violation rates over time
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_assessments,
    COUNT(CASE WHEN overall_clearance = false THEN 1 END) as violations,
    ROUND(COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*)::numeric, 2) as violation_rate_pct,

    -- Violation rate delta from previous hour
    ROUND(
        (COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*) -
         LAG(COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*)) OVER (ORDER BY DATE_TRUNC('hour', timestamp)))
    ::numeric, 2) as violation_rate_delta_pct,

    -- Statistical significance (simplified z-score approximation)
    CASE
        WHEN COUNT(*) >= 10 AND
             ABS(COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*) - 10.0) > 15.0
        THEN '🚨 SIGNIFICANT_SPIKE'
        WHEN COUNT(*) >= 10 AND
             ABS(COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*) - 10.0) > 8.0
        THEN '⚠️ MODERATE_SPIKE'
        ELSE '✅ NORMAL_RANGE'
    END as violation_status

FROM governance_assessments
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- 2B. Violation Patterns by Strategy Type
-- Identifies which types of strategies are most prone to violations
SELECT
    strategy_genome->>'generation' as strategy_generation,
    COUNT(*) as total_strategies,
    COUNT(CASE WHEN overall_clearance = false THEN 1 END) as violating_strategies,
    ROUND(COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*)::numeric, 2) as violation_rate_pct,

    -- Most common violation types for this generation
    MODE() WITHIN GROUP (ORDER BY CASE
        WHEN governance_score < 0.3 THEN 'critical_ethical'
        WHEN governance_score < 0.5 THEN 'high_safety'
        WHEN governance_score < 0.7 THEN 'medium_business'
        ELSE 'low_compliance'
    END) as primary_violation_type,

    -- Average governance score for this generation
    ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score

FROM governance_assessments ga
WHERE timestamp > NOW() - INTERVAL '30 days'
  AND strategy_genome IS NOT NULL
GROUP BY strategy_genome->>'generation'
ORDER BY violation_rate_pct DESC;

-- 2C. Rolling Violation Rate with Statistical Control Limits
-- Uses statistical process control to detect governance violations
WITH hourly_violations AS (
    SELECT
        DATE_TRUNC('hour', timestamp) as hour,
        COUNT(*) as total_assessments,
        COUNT(CASE WHEN overall_clearance = false THEN 1 END) as violations,
        ROUND(COUNT(CASE WHEN overall_clearance = false THEN 1 END) * 100.0 / COUNT(*)::numeric, 2) as violation_rate_pct
    FROM governance_assessments
    WHERE timestamp > NOW() - INTERVAL '14 days'
    GROUP BY DATE_TRUNC('hour', timestamp)
    HAVING COUNT(*) >= 5  -- Minimum sample size
),
baseline_stats AS (
    SELECT
        ROUND(AVG(violation_rate_pct)::numeric, 2) as baseline_mean,
        ROUND(STDDEV(violation_rate_pct)::numeric, 2) as baseline_stddev,
        COUNT(*) as baseline_hours
    FROM hourly_violations
    WHERE hour < NOW() - INTERVAL '1 day'  -- Use older data as baseline
)
SELECT
    hv.hour,
    hv.total_assessments,
    hv.violations,
    hv.violation_rate_pct,
    bs.baseline_mean,
    bs.baseline_stddev,

    -- Control limits (3-sigma)
    ROUND((bs.baseline_mean - 3 * bs.baseline_stddev)::numeric, 2) as lcl_3sigma,
    ROUND((bs.baseline_mean + 3 * bs.baseline_stddev)::numeric, 2) as ucl_3sigma,

    -- Statistical process control status
    CASE
        WHEN hv.violation_rate_pct > bs.baseline_mean + 3 * bs.baseline_stddev THEN '🚨 OUT_OF_CONTROL_HIGH'
        WHEN hv.violation_rate_pct < bs.baseline_mean - 3 * bs.baseline_stddev THEN '🚨 OUT_OF_CONTROL_LOW'
        WHEN hv.violation_rate_pct > bs.baseline_mean + 2 * bs.baseline_stddev THEN '⚠️ WARNING_HIGH'
        WHEN hv.violation_rate_pct < bs.baseline_mean - 2 * bs.baseline_stddev THEN '⚠️ WARNING_LOW'
        ELSE '✅ IN_CONTROL'
    END as spc_status

FROM hourly_violations hv
CROSS JOIN baseline_stats bs
WHERE hv.hour > NOW() - INTERVAL '1 day'  -- Show recent data
ORDER BY hv.hour DESC;

-- =============================================================================
-- 3. BEHAVIORAL CONSISTENCY MONITORING
-- =============================================================================

-- 3A. Governance Decision Consistency Over Time
-- Measures how consistent governance decisions are (lower variance = more consistent)
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as assessments_count,

    -- Clearance rate variance (0 = perfectly consistent, 1 = random)
    ROUND(VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 4) as clearance_variance,

    -- Governance score variance
    ROUND(VAR_POP(governance_score)::numeric, 4) as governance_score_variance,

    -- Behavioral consistency score (1 - normalized variance)
    ROUND(
        (1 - LEAST(VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END), 0.25) / 0.25)::numeric,
    3) as behavioral_consistency_score,

    CASE
        WHEN VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END) > 0.2 THEN '🚨 HIGH_VARIANCE_INCONSISTENT'
        WHEN VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END) > 0.1 THEN '⚠️ MODERATE_VARIANCE_UNSTABLE'
        ELSE '✅ LOW_VARIANCE_CONSISTENT'
    END as consistency_status

FROM governance_assessments
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
HAVING COUNT(*) >= 10  -- Minimum sample size for variance calculation
ORDER BY hour DESC;

-- 3B. Strategy-Specific Behavioral Drift
-- Identifies individual strategies that are behaving inconsistently
WITH strategy_behavior AS (
    SELECT
        strategy_id,
        COUNT(*) as total_assessments,
        AVG(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END) as avg_clearance_rate,
        VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END) as clearance_variance,
        AVG(governance_score) as avg_governance_score,
        MAX(timestamp) as last_assessment
    FROM governance_assessments
    WHERE timestamp > NOW() - INTERVAL '30 days'
    GROUP BY strategy_id
    HAVING COUNT(*) >= 5  -- Minimum assessments for analysis
)
SELECT
    strategy_id,
    total_assessments,
    ROUND(avg_clearance_rate::numeric, 3) as avg_clearance_rate,
    ROUND(clearance_variance::numeric, 4) as behavioral_variance,
    ROUND(avg_governance_score::numeric, 3) as avg_governance_score,
    last_assessment,

    -- Behavioral stability score
    ROUND((1 - LEAST(clearance_variance, 0.25) / 0.25)::numeric, 3) as behavioral_stability_score,

    CASE
        WHEN clearance_variance > 0.2 THEN '🚨 HIGHLY_INCONSISTENT'
        WHEN clearance_variance > 0.1 THEN '⚠️ MODERATELY_INCONSISTENT'
        WHEN clearance_variance IS NULL THEN '❓ INSUFFICIENT_DATA'
        ELSE '✅ CONSISTENT_BEHAVIOR'
    END as behavioral_status

FROM strategy_behavior
ORDER BY clearance_variance DESC NULLS LAST;

-- =============================================================================
-- 4. GOVERNANCE DRIFT DASHBOARD QUERIES
-- =============================================================================

-- 4A. Comprehensive Drift Dashboard
-- Single query providing all key drift metrics
WITH recent_metrics AS (
    SELECT
        DATE_TRUNC('hour', timestamp) as hour,
        COUNT(*) as assessments_count,
        COUNT(CASE WHEN overall_clearance = false THEN 1 END) as violations,
        ROUND(AVG(governance_score)::numeric, 3) as avg_governance_score,
        ROUND(VAR_POP(governance_score)::numeric, 4) as governance_variance,
        ROUND(AVG(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3) as clearance_rate,
        ROUND(VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 4) as clearance_variance
    FROM governance_assessments
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY DATE_TRUNC('hour', timestamp)
    ORDER BY hour DESC
    LIMIT 24
),
baseline_metrics AS (
    SELECT
        ROUND(AVG(governance_score)::numeric, 3) as baseline_governance_score,
        ROUND(AVG(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)::numeric, 3) as baseline_clearance_rate,
        COUNT(*) as baseline_assessments
    FROM governance_assessments
    WHERE timestamp > NOW() - INTERVAL '7 days'
      AND timestamp < NOW() - INTERVAL '1 day'  -- Exclude most recent day
),
drift_incidents AS (
    SELECT COUNT(*) as total_incidents_24h
    FROM governance_incidents
    WHERE ts > NOW() - INTERVAL '24 hours'
      AND rule_id LIKE '%drift%'
)
SELECT
    'GOVERNANCE_DRIFT_DASHBOARD' as dashboard_name,
    NOW() as generated_at,

    -- Current health metrics
    (SELECT ROUND(AVG(avg_governance_score)::numeric, 3) FROM recent_metrics) as current_governance_score,
    (SELECT ROUND(AVG(clearance_rate)::numeric, 3) FROM recent_metrics) as current_clearance_rate,
    (SELECT ROUND(AVG(violations * 100.0 / assessments_count)::numeric, 2) FROM recent_metrics) as current_violation_rate_pct,

    -- Baseline comparison
    bm.baseline_governance_score,
    bm.baseline_clearance_rate,

    -- Drift calculations
    ROUND(
        ((SELECT AVG(avg_governance_score) FROM recent_metrics) - bm.baseline_governance_score)::numeric,
    3) as governance_score_drift,

    ROUND(
        ((SELECT AVG(clearance_rate) FROM recent_metrics) - bm.baseline_clearance_rate)::numeric,
    3) as clearance_rate_drift,

    -- Behavioral consistency
    ROUND((SELECT AVG(1 - LEAST(clearance_variance, 0.25) / 0.25) FROM recent_metrics)::numeric, 3) as behavioral_consistency_score,

    -- Incident tracking
    di.total_incidents_24h,

    -- Overall drift status
    CASE
        WHEN ABS((SELECT AVG(avg_governance_score) FROM recent_metrics) - bm.baseline_governance_score) > 0.15
          OR ABS((SELECT AVG(clearance_rate) FROM recent_metrics) - bm.baseline_clearance_rate) > 0.1
          OR (SELECT AVG(violations * 100.0 / assessments_count) FROM recent_metrics) > 20.0
        THEN '🚨 CRITICAL_DRIFT_DETECTED'
        WHEN ABS((SELECT AVG(avg_governance_score) FROM recent_metrics) - bm.baseline_governance_score) > 0.1
          OR ABS((SELECT AVG(clearance_rate) FROM recent_metrics) - bm.baseline_clearance_rate) > 0.05
          OR (SELECT AVG(violations * 100.0 / assessments_count) FROM recent_metrics) > 15.0
        THEN '⚠️ WARNING_DRIFT_TRENDING'
        WHEN di.total_incidents_24h > 5 THEN '⚠️ HIGH_INCIDENT_RATE'
        ELSE '✅ GOVERNANCE_STABLE'
    END as overall_drift_status,

    -- Action recommendations
    CASE
        WHEN ABS((SELECT AVG(avg_governance_score) FROM recent_metrics) - bm.baseline_governance_score) > 0.15
          OR ABS((SELECT AVG(clearance_rate) FROM recent_metrics) - bm.baseline_clearance_rate) > 0.1
        THEN 'Immediate constitutional review required - consider policy rollback'
        WHEN (SELECT AVG(violations * 100.0 / assessments_count) FROM recent_metrics) > 15.0
        THEN 'Increased monitoring recommended - review recent strategy deployments'
        WHEN di.total_incidents_24h > 3 THEN 'Investigate recent incidents - check for systemic issues'
        ELSE 'Continue normal monitoring - governance stable'
    END as recommended_actions

FROM baseline_metrics bm
CROSS JOIN drift_incidents di;

-- 4B. Governance Drift Alert Candidates
-- Identifies governance states that should trigger alerts
SELECT
    'GOVERNANCE_DRIFT_ALERTS' as alert_check,
    NOW() as check_time,

    -- Violation rate alerts
    CASE
        WHEN (SELECT AVG(CASE WHEN overall_clearance = false THEN 1.0 ELSE 0.0 END)
              FROM governance_assessments
              WHERE timestamp > NOW() - INTERVAL '1 hour') > 0.25
        THEN '🚨 ALERT: Violation rate >25% in last hour'
        ELSE '✅ OK: Violation rate within normal range'
    END as violation_rate_alert,

    -- Governance score degradation
    CASE
        WHEN (SELECT AVG(governance_score)
              FROM governance_assessments
              WHERE timestamp > NOW() - INTERVAL '2 hours') <
             (SELECT AVG(governance_score)
              FROM governance_assessments
              WHERE timestamp > NOW() - INTERVAL '7 days'
                AND timestamp < NOW() - INTERVAL '2 hours') * 0.9
        THEN '🚨 ALERT: Governance score degraded >10% in 2 hours'
        ELSE '✅ OK: Governance score stable'
    END as governance_score_alert,

    -- Behavioral inconsistency
    CASE
        WHEN (SELECT VAR_POP(CASE WHEN overall_clearance THEN 1.0 ELSE 0.0 END)
              FROM governance_assessments
              WHERE timestamp > NOW() - INTERVAL '1 hour') > 0.2
        THEN '🚨 ALERT: High behavioral inconsistency detected'
        ELSE '✅ OK: Behavioral patterns consistent'
    END as behavioral_consistency_alert,

    -- Recent incident spike
    CASE
        WHEN (SELECT COUNT(*) FROM governance_incidents
              WHERE ts > NOW() - INTERVAL '30 minutes') >= 3
        THEN '🚨 ALERT: 3+ governance incidents in 30 minutes'
        ELSE '✅ OK: Incident rate normal'
    END as incident_spike_alert

FROM governance_assessments
LIMIT 1;

-- =============================================================================
-- 5. STRATEGY QUARANTINE AND RECOVERY MONITORING
-- =============================================================================

-- 5A. Active Strategy Quarantines
-- Shows currently quarantined strategies and their status
SELECT
    strategy_id,
    quarantine_start,
    quarantine_end,
    EXTRACT(EPOCH FROM (quarantine_end - NOW())) / 3600 as hours_remaining,
    quarantine_reason,

    CASE
        WHEN quarantine_end > NOW() THEN 'ACTIVE_QUARANTINE'
        WHEN quarantine_end <= NOW() THEN 'EXPIRED_QUARANTINE'
        ELSE 'UNKNOWN_STATUS'
    END as quarantine_status

FROM strategy_quarantines
WHERE quarantine_end > NOW() - INTERVAL '24 hours'  -- Include recently expired
ORDER BY quarantine_end DESC;

-- 5B. Quarantine Effectiveness Analysis
-- Measures how effective quarantines are at reducing violations
WITH quarantine_impact AS (
    SELECT
        sq.strategy_id,
        sq.quarantine_start,
        sq.quarantine_end,

        -- Violations before quarantine (24h window)
        (SELECT COUNT(*)
         FROM governance_assessments ga
         WHERE ga.strategy_id = sq.strategy_id
           AND ga.timestamp >= sq.quarantine_start - INTERVAL '24 hours'
           AND ga.timestamp < sq.quarantine_start
           AND ga.overall_clearance = false) as violations_before,

        -- Violations during quarantine
        (SELECT COUNT(*)
         FROM governance_assessments ga
         WHERE ga.strategy_id = sq.strategy_id
           AND ga.timestamp >= sq.quarantine_start
           AND ga.timestamp <= LEAST(sq.quarantine_end, NOW())
           AND ga.overall_clearance = false) as violations_during,

        -- Violations after quarantine (if ended)
        CASE
            WHEN sq.quarantine_end <= NOW() THEN
                (SELECT COUNT(*)
                 FROM governance_assessments ga
                 WHERE ga.strategy_id = sq.strategy_id
                   AND ga.timestamp > sq.quarantine_end
                   AND ga.timestamp <= sq.quarantine_end + INTERVAL '24 hours'
                   AND ga.overall_clearance = false)
            ELSE NULL
        END as violations_after

    FROM strategy_quarantines sq
    WHERE sq.quarantine_start > NOW() - INTERVAL '30 days'
)
SELECT
    strategy_id,
    quarantine_start,
    quarantine_end,
    violations_before,
    violations_during,
    violations_after,

    -- Quarantine effectiveness score
    CASE
        WHEN violations_before = 0 THEN NULL  -- No baseline violations
        WHEN violations_before > 0 THEN
            ROUND((1 - violations_during::numeric / violations_before)::numeric, 3)
        ELSE NULL
    END as quarantine_effectiveness_score,

    CASE
        WHEN violations_before = 0 THEN 'NO_BASELINE_VIOLATIONS'
        WHEN violations_before > 0 AND violations_during::numeric / violations_before < 0.5 THEN 'HIGHLY_EFFECTIVE'
        WHEN violations_before > 0 AND violations_during::numeric / violations_before < 0.8 THEN 'MODERATELY_EFFECTIVE'
        WHEN violations_before > 0 THEN 'INEFFECTIVE'
        ELSE 'INSUFFICIENT_DATA'
    END as quarantine_effectiveness_status

FROM quarantine_impact
ORDER BY quarantine_start DESC;

-- =============================================================================
-- END OF GOVERNANCE DRIFT MONITORING QUERIES
-- =============================================================================
