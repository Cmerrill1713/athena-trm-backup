"""
Prometheus Metrics for Experimental Remediation Phases

Tracks metrics for all 7 experimental phases:
- Phase 1: Shadow remediation
- Phase 2: Guarded auto-remediation
- Phase 3: A/B policy testing
- Phase 4: Adversarial gates
- Phase 5: Cost-aware remediation
- Phase 6: Human fast-track
- Phase 7: Long-run drift tracking
"""

from prometheus_client import Counter, Gauge, Histogram


# ============================================================================
# Phase 1: Shadow Remediation
# ============================================================================

governance_shadow_experiments_total = Counter(
    "governance_shadow_experiments_total",
    "Total shadow remediation experiments run"
)

governance_shadow_would_promote_total = Counter(
    "governance_shadow_would_promote_total",
    "Shadow experiments that would have resulted in PROMOTE"
)

governance_shadow_passed_gates_total = Counter(
    "governance_shadow_passed_gates_total",
    "Shadow experiments that passed all canary gates"
)

governance_shadow_decision_agreement_rate = Gauge(
    "governance_shadow_decision_agreement_rate",
    "Agreement rate between shadow and manual decisions"
)

governance_shadow_canary_pass_rate = Gauge(
    "governance_shadow_canary_pass_rate",
    "Pass rate for shadow canary simulations"
)


# ============================================================================
# Phase 2: Guarded Auto-Remediation
# ============================================================================

governance_remediations_requested_total = Counter(
    "governance_remediations_requested_total",
    "Total remediation requests",
    ["verdict_type"]  # HARD_FAIL, SOFT_FAIL
)

governance_remediations_started_total = Counter(
    "governance_remediations_started_total",
    "Remediations that started execution"
)

governance_remediations_completed_total = Counter(
    "governance_remediations_completed_total",
    "Completed remediations",
    ["decision"]  # PROMOTE, HOLD, ROLLBACK
)

governance_remediation_time_seconds = Histogram(
    "governance_remediation_time_seconds",
    "Time from incident to mitigation (seconds)",
    buckets=[30, 60, 120, 300, 600, 1200, 1800]  # 30s to 30min
)

governance_rollback_rate = Gauge(
    "governance_rollback_rate",
    "Rate of emergency rollbacks (rolling window)"
)

governance_time_to_mitigation_seconds = Histogram(
    "governance_time_to_mitigation_seconds",
    "Time from incident detection to successful mitigation",
    buckets=[60, 300, 600, 1800, 3600]  # 1min to 1hr
)


# ============================================================================
# Phase 3: A/B Policy Testing
# ============================================================================

governance_ab_experiments_total = Counter(
    "governance_ab_experiments_total",
    "A/B experiments run",
    ["arm"]  # A=free_form, B=templated
)

governance_ab_promote_rate = Gauge(
    "governance_ab_promote_rate",
    "Promote rate by experiment arm",
    ["arm"]
)

governance_ab_human_approval_rate = Gauge(
    "governance_ab_human_approval_rate",
    "Human approval rate by arm",
    ["arm"]
)


# ============================================================================
# Phase 4: Adversarial Gates
# ============================================================================

governance_edge_case_score = Gauge(
    "governance_edge_case_score",
    "Edge case probe score (0-1)",
    ["plan_id"]
)

governance_adversarial_probes_total = Counter(
    "governance_adversarial_probes_total",
    "Total adversarial probes run"
)

governance_adversarial_failures_total = Counter(
    "governance_adversarial_failures_total",
    "Adversarial probes that failed",
    ["probe_type"]
)

governance_post_promotion_incidents_total = Counter(
    "governance_post_promotion_incidents_total",
    "Incidents after promotion",
    ["root_cause"]  # brittle_fix, edge_case, other
)


# ============================================================================
# Phase 5: Cost-Aware Remediation
# ============================================================================

governance_remediation_cost_usd = Histogram(
    "governance_remediation_cost_usd",
    "Cost per remediation in USD",
    buckets=[0.01, 0.05, 0.10, 0.25, 0.50, 1.00, 2.00, 5.00]
)

governance_cost_per_success_usd = Gauge(
    "governance_cost_per_success_usd",
    "Average cost per successful remediation"
)

governance_budget_utilization = Gauge(
    "governance_budget_utilization",
    "Fraction of remediation budget used (0-1)"
)


# ============================================================================
# Phase 6: Human Fast-Track
# ============================================================================

governance_fasttrack_requests_total = Counter(
    "governance_fasttrack_requests_total",
    "Fast-track approval requests"
)

governance_fasttrack_approved_total = Counter(
    "governance_fasttrack_approved_total",
    "Fast-track requests approved"
)

governance_mttr_seconds = Histogram(
    "governance_mttr_seconds",
    "Mean Time To Recovery (MTTR) for critical incidents",
    buckets=[60, 300, 600, 1800, 3600, 7200]  # 1min to 2hrs
)


# ============================================================================
# Phase 7: Long-Run Drift & Adaptation
# ============================================================================

governance_threshold_drift = Gauge(
    "governance_threshold_drift",
    "Drift in learned thresholds from baseline",
    ["threshold_name"]
)

governance_false_positive_rate = Gauge(
    "governance_false_positive_rate",
    "False positive rate of gates (rolling window)"
)

governance_false_negative_rate = Gauge(
    "governance_false_negative_rate",
    "False negative rate of gates (rolling window)"
)

governance_adaptive_learning_runs_total = Counter(
    "governance_adaptive_learning_runs_total",
    "Total adaptive learning runs"
)


# ============================================================================
# General Experimental Metrics
# ============================================================================

governance_experiment_active = Gauge(
    "governance_experiment_active",
    "Whether experiment is currently active",
    ["phase"]  # Phase 1-7
)

governance_experiment_success_rate = Gauge(
    "governance_experiment_success_rate",
    "Success rate for experiment phase",
    ["phase"]
)


# Export all metrics as a list for easy import
__all__ = [
    # Phase 1
    "governance_shadow_experiments_total",
    "governance_shadow_would_promote_total",
    "governance_shadow_passed_gates_total",
    "governance_shadow_decision_agreement_rate",
    "governance_shadow_canary_pass_rate",
    
    # Phase 2
    "governance_remediations_requested_total",
    "governance_remediations_started_total",
    "governance_remediations_completed_total",
    "governance_remediation_time_seconds",
    "governance_rollback_rate",
    "governance_time_to_mitigation_seconds",
    
    # Phase 3
    "governance_ab_experiments_total",
    "governance_ab_promote_rate",
    "governance_ab_human_approval_rate",
    
    # Phase 4
    "governance_edge_case_score",
    "governance_adversarial_probes_total",
    "governance_adversarial_failures_total",
    "governance_post_promotion_incidents_total",
    
    # Phase 5
    "governance_remediation_cost_usd",
    "governance_cost_per_success_usd",
    "governance_budget_utilization",
    
    # Phase 6
    "governance_fasttrack_requests_total",
    "governance_fasttrack_approved_total",
    "governance_mttr_seconds",
    
    # Phase 7
    "governance_threshold_drift",
    "governance_false_positive_rate",
    "governance_false_negative_rate",
    "governance_adaptive_learning_runs_total",
    
    # General
    "governance_experiment_active",
    "governance_experiment_success_rate",
]

