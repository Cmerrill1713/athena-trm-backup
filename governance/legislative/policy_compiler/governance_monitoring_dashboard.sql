-- Constitutional Governance Monitoring Dashboard
-- Track ethical compliance and safety of federated RAG routing

-- 1. Governance Health Overview (Last 24h)
SELECT
    date_trunc('hour', now()) as current_hour,
    (SELECT count(*) FROM governance_validations WHERE ts > now() - interval '24 hours') as recent_validations,
    (SELECT count(*) FILTER (WHERE compliant) FROM governance_validations WHERE ts > now() - interval '24 hours')::float /
    nullif((SELECT count(*) FROM governance_validations WHERE ts > now() - interval '24 hours'), 0) as compliance_rate_24h,
    (SELECT count(*) FROM governance_violations WHERE ts > now() - interval '24 hours') as recent_violations,
    (SELECT count(*) FROM federation_contributions WHERE constitutional_validation->>'compliant' = 'true' AND ts > now() - interval '24 hours') as compliant_contributions,
    (SELECT count(*) FROM federation_contributions WHERE constitutional_validation IS NULL OR constitutional_validation->>'compliant' != 'true' AND ts > now() - interval '24 hours') as blocked_contributions
FROM governance_health;

-- 2. Violation Patterns (Last 7 days)
SELECT
    violation_type,
    count(*) as violations,
    count(distinct deployment_id) as affected_deployments,
    max(ts) as last_violation,
    avg(severity_score) as avg_severity
FROM governance_violations gv
WHERE gv.ts > now() - interval '7 days'
GROUP BY violation_type
ORDER BY violations DESC
LIMIT 10;

-- 3. Deployment Compliance History
SELECT
    deployment_id,
    date_trunc('day', ts) as day,
    count(*) as total_validations,
    count(*) FILTER (WHERE compliant) as compliant_validations,
    count(*) FILTER (WHERE NOT compliant) as violations,
    count(*) FILTER (WHERE compliant)::float / count(*) as compliance_rate
FROM governance_validations
WHERE ts > now() - interval '30 days'
GROUP BY deployment_id, day
ORDER BY deployment_id, day DESC
LIMIT 20;

-- 4. Constitutional Rule Effectiveness
SELECT
    rule_id,
    rule_name,
    count(*) as triggers,
    count(*) FILTER (WHERE violation_type IS NOT NULL) as violations_caught,
    count(*) FILTER (WHERE violation_type IS NULL) as warnings_issued,
    max(last_triggered) as last_triggered
FROM constitutional_rules cr
LEFT JOIN governance_violations gv ON cr.rule_id = gv.rule_id
WHERE cr.enabled = true
GROUP BY cr.rule_id, cr.rule_name
ORDER BY violations_caught DESC;

-- 5. Federation Safety Metrics
SELECT
    date_trunc('day', fc.ts) as day,
    count(*) as total_contributions,
    count(*) FILTER (WHERE constitutional_validation->>'compliant' = 'true') as compliant_contributions,
    count(*) FILTER (WHERE constitutional_validation IS NULL OR constitutional_validation->>'compliant' != 'true') as blocked_contributions,
    count(*) FILTER (WHERE constitutional_validation->>'compliant' = 'true')::float / count(*) as federation_safety_rate,
    avg((constitutional_validation->>'violations')::int) as avg_violations_per_contribution
FROM federation_contributions fc
WHERE fc.ts > now() - interval '30 days'
GROUP BY day
ORDER BY day DESC;

-- 6. Privacy vs Compliance Trade-offs
SELECT
    deployment_id,
    avg(privacy_budget) as avg_privacy_budget,
    count(*) FILTER (WHERE constitutional_validation->>'compliant' = 'true')::float / count(*) as compliance_rate,
    count(*) as total_contributions,
    -- Correlation between privacy strictness and compliance
    corr(privacy_budget, (constitutional_validation->>'compliant')::int) as privacy_compliance_correlation
FROM federation_contributions fc
WHERE fc.ts > now() - interval '30 days'
GROUP BY deployment_id
HAVING count(*) >= 5
ORDER BY compliance_rate DESC
LIMIT 10;

-- 7. Governance Incident Response
SELECT
    incident_id,
    incident_type,
    severity,
    affected_deployments,
    response_action,
    resolution_status,
    created_at,
    resolved_at,
    extract(epoch from (resolved_at - created_at))/3600 as resolution_hours
FROM governance_incidents gi
WHERE gi.created_at > now() - interval '30 days'
ORDER BY created_at DESC
LIMIT 10;

-- 8. Constitutional Learning Effectiveness
WITH validation_trends AS (
    SELECT
        date_trunc('week', ts) as week,
        count(*) as validations,
        count(*) FILTER (WHERE compliant) as compliant,
        count(*) FILTER (WHERE NOT compliant) as violations
    FROM governance_validations
    WHERE ts > now() - interval '12 weeks'
    GROUP BY week
)
SELECT
    week,
    validations,
    compliant,
    violations,
    compliant::float / validations as compliance_rate,
    -- Trend analysis
    lag(compliance_rate, 1) OVER (ORDER BY week) as prev_compliance,
    (compliance_rate - lag(compliance_rate, 1) OVER (ORDER BY week)) as compliance_change
FROM validation_trends
ORDER BY week DESC;

-- 9. Risk Assessment by Strategy Type
SELECT
    strategy_type,
    count(*) as strategies_validated,
    count(*) FILTER (WHERE compliant) as compliant_strategies,
    count(*) FILTER (WHERE NOT compliant) as non_compliant_strategies,
    avg(risk_score) as avg_risk_score,
    max(risk_score) as max_risk_score,
    count(*) FILTER (WHERE risk_score > 0.7) as high_risk_strategies
FROM (
    SELECT
        CASE
            WHEN exploration_rate_recent > 0.3 THEN 'high_exploration'
            WHEN federation_enabled AND privacy_budget > 1.0 THEN 'high_privacy_risk'
            WHEN history_size < 500 THEN 'insufficient_history'
            ELSE 'standard'
        END as strategy_type,
        compliant,
        exploration_rate_recent,
        history_size,
        privacy_budget,
        -- Calculate risk score
        (
            CASE WHEN exploration_rate_recent > 0.3 THEN 0.3 ELSE 0 END +
            CASE WHEN privacy_budget > 1.0 THEN 0.4 ELSE 0 END +
            CASE WHEN history_size < 500 THEN 0.3 ELSE 0 END
        ) as risk_score
    FROM governance_validations gv
    LEFT JOIN strategy_metadata sm ON gv.strategy_hash = sm.strategy_hash
    WHERE gv.ts > now() - interval '30 days'
) risk_analysis
GROUP BY strategy_type
ORDER BY avg_risk_score DESC;

-- 10. Governance Audit Trail
SELECT
    audit_id,
    event_type,
    event_description,
    actor_deployment,
    affected_resources,
    governance_decision,
    evidence_hash,
    timestamp,
    compliance_status
FROM governance_audit_trail gat
WHERE gat.timestamp > now() - interval '7 days'
ORDER BY timestamp DESC
LIMIT 50;

-- Note: These queries assume tables exist for governance tracking.
-- In a real implementation, you'd create:
-- - governance_validations (validation results)
-- - governance_violations (detailed violations)
-- - constitutional_rules (rule definitions)
-- - governance_incidents (incident tracking)
-- - governance_audit_trail (complete audit log)
-- - strategy_metadata (strategy characteristics)
