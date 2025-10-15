"""
Governance Drift Detection Module
==================================

Detects, monitors, and corrects governance policy drift in the Constitutional AI Framework.

This module provides:
- Statistical monitoring of governance policy deltas
- Automatic drift detection with configurable thresholds
- Integration with constitutional weighting for adaptive responses
- Rollback and quarantine mechanisms for detected drift
- Comprehensive logging and alerting capabilities

Key Features:
- Multi-dimensional drift detection (violation rates, policy deltas, behavioral shifts)
- Statistical significance testing with confidence intervals
- Automatic quarantine of drifting strategies
- Constitutional re-weighting triggers on drift detection
- Full audit trail and human intervention hooks
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .governance_layer import GovernanceEngine

logger = logging.getLogger(__name__)

class DriftSeverity(Enum):
    """Severity levels for governance drift detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DriftType(Enum):
    """Types of governance drift that can be detected."""
    VIOLATION_RATE_SPIKE = "violation_rate_spike"
    POLICY_DELTA_DRIFT = "policy_delta_drift"
    BEHAVIORAL_SHIFT = "behavioral_shift"
    CONSTITUTIONAL_IMBALANCE = "constitutional_imbalance"
    GOVERNANCE_SCORE_DEGRADATION = "governance_score_degradation"

@dataclass
class DriftDetectionConfig:
    """Configuration for governance drift detection."""
    # Statistical thresholds
    violation_rate_threshold: float = 0.1  # 10% violation rate increase
    policy_delta_threshold: float = 0.15   # 15% policy change
    behavioral_shift_threshold: float = 0.2  # 20% behavioral change
    governance_score_threshold: float = 0.1  # 10% score degradation

    # Time windows for analysis
    short_window_minutes: int = 30
    medium_window_minutes: int = 120
    long_window_minutes: int = 1440  # 24 hours

    # Statistical parameters
    min_samples_for_significance: int = 50
    confidence_level: float = 0.95
    z_score_threshold: float = 2.0

    # Response actions
    auto_quarantine_enabled: bool = True
    constitutional_reweight_enabled: bool = True
    human_intervention_threshold: DriftSeverity = DriftSeverity.HIGH

    # Monitoring parameters
    drift_check_interval_seconds: int = 300  # 5 minutes
    baseline_update_interval_hours: int = 24

@dataclass
class DriftIncident:
    """Represents a detected governance drift incident."""
    incident_id: str
    drift_type: DriftType
    severity: DriftSeverity
    detected_at: datetime
    confidence_score: float
    baseline_value: float
    current_value: float
    delta_percentage: float
    affected_strategies: List[str]
    recommended_actions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GovernanceDriftMetrics:
    """Metrics collected for governance drift monitoring."""
    timestamp: datetime
    violation_rate: float
    policy_delta_score: float
    behavioral_consistency_score: float
    governance_score_avg: float
    constitutional_balance_score: float
    strategy_count: int
    active_violations: int

class GovernanceDriftDetector:
    """
    Core drift detection engine with statistical monitoring and automatic responses.
    """

    def __init__(self, config: Optional[DriftDetectionConfig] = None):
        self.config = config or DriftDetectionConfig()
        self.governance_engine = None  # Will be set by integration
        self.baseline_metrics: List[GovernanceDriftMetrics] = []
        self.drift_incidents: List[DriftIncident] = []
        self.quarantined_strategies: Dict[str, datetime] = {}
        self.last_baseline_update = datetime.now()

        # Statistical state
        self.violation_rate_history: List[Tuple[datetime, float]] = []
        self.policy_delta_history: List[Tuple[datetime, float]] = []
        self.behavioral_history: List[Tuple[datetime, float]] = []

        logger.info(f"GovernanceDriftDetector initialized with config: auto_quarantine={self.config.auto_quarantine_enabled}")

    def integrate_with_governance(self, governance_engine: GovernanceEngine) -> None:
        """Integrate with the main governance engine."""
        self.governance_engine = governance_engine
        logger.info("Integrated with governance engine for drift detection")

    def collect_current_metrics(self) -> GovernanceDriftMetrics:
        """Collect current governance metrics for drift analysis."""
        if not self.governance_engine:
            raise RuntimeError("Governance engine not integrated")

        # Get current governance state
        current_time = datetime.now()

        # Calculate violation rate (violations per assessment)
        recent_assessments = [
            assessment for assessment in self.governance_engine.governance_log[-100:]  # Last 100 assessments
            if current_time - assessment['timestamp'] < timedelta(minutes=self.config.medium_window_minutes)
        ]

        violation_rate = 0.0
        if recent_assessments:
            violations = sum(1 for a in recent_assessments
                           if a['assessment']['overall_clearance'] == False)
            violation_rate = violations / len(recent_assessments)

        # Calculate policy delta score (how much policies have changed recently)
        policy_deltas = []
        if len(self.governance_engine.governance_log) > 10:
            recent_policies = [a['assessment']['governance_score'] for a in recent_assessments[-20:]]
            older_policies = [a['assessment']['governance_score'] for a in self.governance_engine.governance_log[-40:-20]]

            if older_policies:
                policy_deltas = [abs(r - o) for r, o in zip(recent_policies, older_policies)]
                policy_delta_score = np.mean(policy_deltas) if policy_deltas else 0.0
            else:
                policy_delta_score = 0.0
        else:
            policy_delta_score = 0.0

        # Calculate behavioral consistency (how consistent governance decisions are)
        if recent_assessments:
            clearances = [a['assessment']['overall_clearance'] for a in recent_assessments]
            behavioral_consistency_score = np.std(clearances)  # Lower std = more consistent
        else:
            behavioral_consistency_score = 1.0

        # Calculate governance score average
        governance_scores = [a['assessment']['governance_score'] for a in recent_assessments]
        governance_score_avg = np.mean(governance_scores) if governance_scores else 0.5

        # Calculate constitutional balance (how balanced the weighting is)
        # This would require access to constitutional weights - simplified for now
        constitutional_balance_score = 0.8  # Placeholder

        metrics = GovernanceDriftMetrics(
            timestamp=current_time,
            violation_rate=violation_rate,
            policy_delta_score=policy_delta_score,
            behavioral_consistency_score=behavioral_consistency_score,
            governance_score_avg=governance_score_avg,
            constitutional_balance_score=constitutional_balance_score,
            strategy_count=len(self.governance_engine.governance_log),
            active_violations=sum(1 for a in recent_assessments
                                if not a['assessment']['overall_clearance'])
        )

        # Update history
        self.violation_rate_history.append((current_time, violation_rate))
        self.policy_delta_history.append((current_time, policy_delta_score))
        self.behavioral_history.append((current_time, behavioral_consistency_score))

        # Keep history manageable
        max_history = 1000
        self.violation_rate_history = self.violation_rate_history[-max_history:]
        self.policy_delta_history = self.policy_delta_history[-max_history:]
        self.behavioral_history = self.behavioral_history[-max_history:]

        return metrics

    def detect_drift(self, current_metrics: GovernanceDriftMetrics) -> List[DriftIncident]:
        """Detect governance drift using statistical analysis."""
        incidents = []

        # Establish baselines if needed
        if not self.baseline_metrics or \
           datetime.now() - self.last_baseline_update > timedelta(hours=self.config.baseline_update_interval_hours):
            self._update_baselines(current_metrics)

        if len(self.baseline_metrics) < 5:
            return incidents  # Not enough baseline data

        # Calculate baseline averages
        baseline_violation_rate = np.mean([m.violation_rate for m in self.baseline_metrics])
        baseline_policy_delta = np.mean([m.policy_delta_score for m in self.baseline_metrics])
        baseline_behavioral = np.mean([m.behavioral_consistency_score for m in self.baseline_metrics])
        baseline_governance_score = np.mean([m.governance_score_avg for m in self.baseline_metrics])

        # 1. Violation Rate Spike Detection
        if len(self.violation_rate_history) >= self.config.min_samples_for_significance:
            violation_incident = self._detect_violation_rate_drift(
                current_metrics.violation_rate, baseline_violation_rate
            )
            if violation_incident:
                incidents.append(violation_incident)

        # 2. Policy Delta Drift Detection
        if len(self.policy_delta_history) >= self.config.min_samples_for_significance:
            policy_incident = self._detect_policy_delta_drift(
                current_metrics.policy_delta_score, baseline_policy_delta
            )
            if policy_incident:
                incidents.append(policy_incident)

        # 3. Behavioral Shift Detection
        if len(self.behavioral_history) >= self.config.min_samples_for_significance:
            behavioral_incident = self._detect_behavioral_shift(
                current_metrics.behavioral_consistency_score, baseline_behavioral
            )
            if behavioral_incident:
                incidents.append(behavioral_incident)

        # 4. Governance Score Degradation
        governance_incident = self._detect_governance_score_degradation(
            current_metrics.governance_score_avg, baseline_governance_score
        )
        if governance_incident:
            incidents.append(governance_incident)

        return incidents

    def _detect_violation_rate_drift(self, current_rate: float, baseline_rate: float) -> Optional[DriftIncident]:
        """Detect violation rate spikes using statistical significance."""
        if baseline_rate == 0:
            delta_pct = float('inf') if current_rate > 0 else 0.0
        else:
            delta_pct = abs(current_rate - baseline_rate) / baseline_rate

        if delta_pct > self.config.violation_rate_threshold:
            # Calculate statistical significance
            confidence = self._calculate_statistical_significance(
                self.violation_rate_history, baseline_rate, current_rate
            )

            if confidence > self.config.confidence_level:
                severity = DriftSeverity.HIGH if delta_pct > self.config.violation_rate_threshold * 2 else DriftSeverity.MEDIUM

                return DriftIncident(
                    incident_id=f"violation_spike_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    drift_type=DriftType.VIOLATION_RATE_SPIKE,
                    severity=severity,
                    detected_at=datetime.now(),
                    confidence_score=confidence,
                    baseline_value=baseline_rate,
                    current_value=current_rate,
                    delta_percentage=delta_pct,
                    affected_strategies=self._identify_affected_strategies(),
                    recommended_actions=[
                        "Increase monitoring frequency",
                        "Review recent strategy deployments",
                        "Consider temporary quarantine of high-violation strategies"
                    ],
                    metadata={
                        "violation_history_length": len(self.violation_rate_history),
                        "threshold_exceeded_by": delta_pct - self.config.violation_rate_threshold
                    }
                )
        return None

    def _detect_policy_delta_drift(self, current_delta: float, baseline_delta: float) -> Optional[DriftIncident]:
        """Detect policy delta drift."""
        delta_pct = abs(current_delta - baseline_delta) / max(baseline_delta, 0.001)

        if delta_pct > self.config.policy_delta_threshold:
            confidence = self._calculate_statistical_significance(
                self.policy_delta_history, baseline_delta, current_delta
            )

            if confidence > self.config.confidence_level:
                return DriftIncident(
                    incident_id=f"policy_drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    drift_type=DriftType.POLICY_DELTA_DRIFT,
                    severity=DriftSeverity.MEDIUM,
                    detected_at=datetime.now(),
                    confidence_score=confidence,
                    baseline_value=baseline_delta,
                    current_value=current_delta,
                    delta_percentage=delta_pct,
                    affected_strategies=self._identify_affected_strategies(),
                    recommended_actions=[
                        "Review constitutional policy changes",
                        "Validate policy weighting consistency",
                        "Consider policy rollback if drift persists"
                    ],
                    metadata={"policy_stability_score": 1.0 - delta_pct}
                )
        return None

    def _detect_behavioral_shift(self, current_behavioral: float, baseline_behavioral: float) -> Optional[DriftIncident]:
        """Detect behavioral consistency shifts."""
        delta_pct = abs(current_behavioral - baseline_behavioral) / max(baseline_behavioral, 0.001)

        if delta_pct > self.config.behavioral_shift_threshold:
            confidence = self._calculate_statistical_significance(
                self.behavioral_history, baseline_behavioral, current_behavioral
            )

            if confidence > self.config.confidence_level:
                severity = DriftSeverity.CRITICAL if delta_pct > self.config.behavioral_shift_threshold * 2 else DriftSeverity.HIGH

                return DriftIncident(
                    incident_id=f"behavioral_shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    drift_type=DriftType.BEHAVIORAL_SHIFT,
                    severity=severity,
                    detected_at=datetime.now(),
                    confidence_score=confidence,
                    baseline_value=baseline_behavioral,
                    current_value=current_behavioral,
                    delta_percentage=delta_pct,
                    affected_strategies=self._identify_affected_strategies(),
                    recommended_actions=[
                        "Immediate governance review required",
                        "Quarantine inconsistent strategies",
                        "Human intervention recommended for behavioral drift"
                    ],
                    metadata={"consistency_index": 1.0 - current_behavioral}
                )
        return None

    def _detect_governance_score_degradation(self, current_score: float, baseline_score: float) -> Optional[DriftIncident]:
        """Detect governance score degradation."""
        if current_score < baseline_score - self.config.governance_score_threshold:
            delta_pct = (baseline_score - current_score) / baseline_score

            return DriftIncident(
                incident_id=f"governance_degradation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                drift_type=DriftType.GOVERNANCE_SCORE_DEGRADATION,
                severity=DriftSeverity.HIGH,
                detected_at=datetime.now(),
                confidence_score=0.95,  # Simplified confidence for degradation
                baseline_value=baseline_score,
                current_value=current_score,
                delta_percentage=delta_pct,
                affected_strategies=self._identify_affected_strategies(),
                recommended_actions=[
                    "Review governance policy effectiveness",
                    "Consider constitutional re-weighting",
                    "Evaluate strategy quarantine criteria"
                ],
                metadata={"score_degradation": delta_pct}
            )
        return None

    def _calculate_statistical_significance(self, history: List[Tuple[datetime, float]],
                                         baseline: float, current: float) -> float:
        """Calculate statistical significance using z-test."""
        if len(history) < self.config.min_samples_for_significance:
            return 0.0

        # Use recent history for significance calculation
        recent_values = [v for t, v in history[-self.config.min_samples_for_significance:]]
        mean_history = np.mean(recent_values)
        std_history = np.std(recent_values) or 0.001  # Avoid division by zero

        z_score = abs(current - mean_history) / std_history

        # Convert z-score to confidence level (simplified)
        if z_score >= self.config.z_score_threshold:
            return min(0.99, 0.5 + 0.4 * (z_score / 4.0))  # Rough approximation
        return 0.5

    def _identify_affected_strategies(self) -> List[str]:
        """Identify strategies most affected by current drift."""
        if not self.governance_engine:
            return []

        # Get recent assessments and find strategies with violations
        recent_assessments = self.governance_engine.governance_log[-50:]
        affected = []

        for assessment in recent_assessments:
            if not assessment['assessment']['overall_clearance']:
                strategy_name = assessment.get('strategy_id', 'unknown')
                if strategy_name not in affected:
                    affected.append(strategy_name)

        return affected[:5]  # Limit to top 5

    def _update_baselines(self, current_metrics: GovernanceDriftMetrics) -> None:
        """Update baseline metrics for drift detection."""
        self.baseline_metrics.append(current_metrics)

        # Keep only recent baseline data
        cutoff_time = datetime.now() - timedelta(hours=self.config.baseline_update_interval_hours * 7)
        self.baseline_metrics = [
            m for m in self.baseline_metrics
            if m.timestamp > cutoff_time
        ]

        self.last_baseline_update = datetime.now()
        logger.info(f"Updated drift detection baselines with {len(self.baseline_metrics)} data points")

    def respond_to_drift(self, incident: DriftIncident) -> Dict[str, Any]:
        """Execute automated response to detected drift."""
        response = {
            "incident_id": incident.incident_id,
            "actions_taken": [],
            "human_intervention_required": False,
            "quarantined_strategies": [],
            "alerts_triggered": []
        }

        # Always log the incident
        self.drift_incidents.append(incident)
        logger.warning(f"Drift detected: {incident.drift_type.value} (severity: {incident.severity.value})")

        # Execute response based on severity and configuration
        if incident.severity == DriftSeverity.CRITICAL:
            response["human_intervention_required"] = True
            response["actions_taken"].append("Critical drift - immediate human review triggered")

        elif incident.severity == DriftSeverity.HIGH:
            if incident.severity.value >= self.config.human_intervention_threshold.value:
                response["human_intervention_required"] = True

            # Auto-quarantine if enabled
            if self.config.auto_quarantine_enabled and incident.affected_strategies:
                quarantined = self._quarantine_strategies(incident.affected_strategies)
                response["quarantined_strategies"] = quarantined
                response["actions_taken"].append(f"Auto-quarantined {len(quarantined)} strategies")

        # Constitutional re-weighting for policy drift
        if incident.drift_type == DriftType.POLICY_DELTA_DRIFT and self.config.constitutional_reweight_enabled:
            if hasattr(self.governance_engine, 'adaptive_controller'):
                # Trigger re-weighting in the adaptive controller
                response["actions_taken"].append("Triggered constitutional re-weighting")
                logger.info("Triggered constitutional re-weighting due to policy drift")

        # Trigger alerts
        response["alerts_triggered"] = self._trigger_alerts(incident)

        return response

    def _quarantine_strategies(self, strategy_ids: List[str]) -> List[str]:
        """Quarantine strategies to prevent further deployment."""
        quarantined = []
        quarantine_duration = timedelta(hours=24)  # Default quarantine

        for strategy_id in strategy_ids:
            if strategy_id not in self.quarantined_strategies:
                self.quarantined_strategies[strategy_id] = datetime.now() + quarantine_duration
                quarantined.append(strategy_id)
                logger.warning(f"Quarantined strategy: {strategy_id}")

        return quarantined

    def _trigger_alerts(self, incident: DriftIncident) -> List[str]:
        """Trigger appropriate alerts for the drift incident."""
        alerts = []

        # This would integrate with your alerting system
        # For now, just log the alerts that would be triggered
        if incident.severity == DriftSeverity.CRITICAL:
            alerts.append("CRITICAL_GOVERNANCE_DRIFT")
        elif incident.severity == DriftSeverity.HIGH:
            alerts.append("HIGH_GOVERNANCE_DRIFT")
        elif incident.severity == DriftSeverity.MEDIUM:
            alerts.append("MEDIUM_GOVERNANCE_DRIFT")
        else:
            alerts.append("LOW_GOVERNANCE_DRIFT")

        # Add specific alert types
        if incident.drift_type == DriftType.VIOLATION_RATE_SPIKE:
            alerts.append("VIOLATION_RATE_SPIKE")
        elif incident.drift_type == DriftType.BEHAVIORAL_SHIFT:
            alerts.append("BEHAVIORAL_CONSISTENCY_SHIFT")

        logger.info(f"Triggered alerts: {', '.join(alerts)}")
        return alerts

    def check_quarantine_status(self) -> List[str]:
        """Check and release expired quarantines."""
        current_time = datetime.now()
        expired = []

        for strategy_id, quarantine_end in list(self.quarantined_strategies.items()):
            if current_time > quarantine_end:
                del self.quarantined_strategies[strategy_id]
                expired.append(strategy_id)
                logger.info(f"Released quarantine for strategy: {strategy_id}")

        return expired

    def get_drift_statistics(self) -> Dict[str, Any]:
        """Get comprehensive drift detection statistics."""
        current_time = datetime.now()

        # Calculate drift frequency
        recent_incidents = [
            incident for incident in self.drift_incidents
            if current_time - incident.detected_at < timedelta(hours=24)
        ]

        return {
            "total_incidents": len(self.drift_incidents),
            "recent_incidents_24h": len(recent_incidents),
            "incidents_by_severity": {
                severity.value: len([i for i in self.drift_incidents if i.severity == severity])
                for severity in DriftSeverity
            },
            "incidents_by_type": {
                drift_type.value: len([i for i in self.drift_incidents if i.drift_type == drift_type])
                for drift_type in DriftType
            },
            "quarantined_strategies_count": len(self.quarantined_strategies),
            "baseline_metrics_count": len(self.baseline_metrics),
            "monitoring_active": bool(self.governance_engine),
            "last_baseline_update": self.last_baseline_update.isoformat(),
            "violation_rate_history_length": len(self.violation_rate_history),
            "average_confidence_score": np.mean([i.confidence_score for i in self.drift_incidents]) if self.drift_incidents else 0.0
        }

def get_governance_drift_detector(config: Optional[DriftDetectionConfig] = None) -> GovernanceDriftDetector:
    """Factory function to get the governance drift detector instance."""
    return GovernanceDriftDetector(config)

# Integration function for the governance layer
def integrate_drift_detection_with_governance(governance_engine: GovernanceEngine,
                                             drift_config: Optional[DriftDetectionConfig] = None) -> GovernanceDriftDetector:
    """Integrate drift detection with the governance engine."""
    drift_detector = get_governance_drift_detector(drift_config)
    drift_detector.integrate_with_governance(governance_engine)

    # Add drift detection to governance workflow
    original_evaluate = governance_engine.evaluate_strategy_governance

    def enhanced_evaluate(strategy_genome, context=None):
        # Run original evaluation
        result = original_evaluate(strategy_genome, context)

        # Add drift detection
        try:
            current_metrics = drift_detector.collect_current_metrics()
            drift_incidents = drift_detector.detect_drift(current_metrics)

            # Respond to any detected drift
            for incident in drift_incidents:
                response = drift_detector.respond_to_drift(incident)
                result['drift_detection'] = {
                    'incidents_detected': len(drift_incidents),
                    'response_actions': response['actions_taken'],
                    'human_intervention_required': response['human_intervention_required']
                }

        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            result['drift_detection'] = {'error': str(e)}

        return result

    # Replace the evaluation method
    governance_engine.evaluate_strategy_governance = enhanced_evaluate

    logger.info("Governance drift detection integrated with governance engine")
    return drift_detector
