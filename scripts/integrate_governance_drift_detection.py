#!/usr/bin/env python3
"""
Governance Drift Detection Integration Script
==============================================

Drop-in integration script that adds comprehensive governance drift detection
to the Constitutional AI Framework.

This script:
1. Imports and configures the governance drift detection module
2. Integrates it with the existing governance layer
3. Sets up rollback and quarantine mechanisms
4. Provides configuration and monitoring hooks

Usage:
    python3 scripts/integrate_governance_drift_detection.py

Or import in your application:
    from scripts.integrate_governance_drift_detection import integrate_governance_drift_detection
    drift_detector = integrate_governance_drift_detection()
"""

import logging
import asyncio
from typing import Optional, Dict, Any

# Import the governance drift detection components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI-Projects', 'universal-ai-tools', 'src'))

from core.governance_drift_detection import (
    GovernanceDriftDetector,
    DriftDetectionConfig,
    get_governance_drift_detector,
    integrate_drift_detection_with_governance
)

from scripts.governance_drift_rollback_hooks import (
    GovernanceRollbackManager,
    RollbackConfiguration,
    get_governance_rollback_manager,
    integrate_rollback_with_drift_detection
)

# Import existing governance components
from AI_Projects.universal_ai_tools.src.core.governance_layer import get_governance_engine

logger = logging.getLogger(__name__)

# Default configuration - can be customized
DEFAULT_DRIFT_CONFIG = DriftDetectionConfig(
    # Statistical thresholds
    violation_rate_threshold=0.1,      # 10% violation rate increase
    policy_delta_threshold=0.15,       # 15% policy change
    behavioral_shift_threshold=0.2,    # 20% behavioral change
    governance_score_threshold=0.1,    # 10% score degradation

    # Time windows
    short_window_minutes=30,
    medium_window_minutes=120,
    long_window_minutes=1440,

    # Statistical parameters
    min_samples_for_significance=50,
    confidence_level=0.95,
    z_score_threshold=2.0,

    # Response actions
    auto_quarantine_enabled=True,
    constitutional_reweight_enabled=True,
    human_intervention_threshold="high",

    # Monitoring
    drift_check_interval_seconds=300,  # 5 minutes
    baseline_update_interval_hours=24
)

DEFAULT_ROLLBACK_CONFIG = RollbackConfiguration(
    # Quarantine settings
    default_quarantine_hours=24,
    max_quarantine_hours=168,  # 1 week
    quarantine_extension_factor=1.5,

    # Rollback thresholds
    constitutional_rollback_threshold="critical",
    strategy_rollback_threshold="high",
    governance_pause_threshold="critical",

    # Recovery settings
    auto_recovery_enabled=True,
    recovery_monitoring_hours=6,
    recovery_success_threshold=0.8,

    # Human intervention
    human_intervention_severity="critical",
    human_intervention_timeout_hours=4
)

def integrate_governance_drift_detection(
    drift_config: Optional[DriftDetectionConfig] = None,
    rollback_config: Optional[RollbackConfiguration] = None
) -> Dict[str, Any]:
    """
    Integrate governance drift detection into the Constitutional AI Framework.

    Returns a dictionary with the integrated components for monitoring and control.
    """
    logger.info("Starting governance drift detection integration...")

    # Use default configs if not provided
    drift_config = drift_config or DEFAULT_DRIFT_CONFIG
    rollback_config = rollback_config or DEFAULT_ROLLBACK_CONFIG

    # Get the governance engine
    governance_engine = get_governance_engine()
    if not governance_engine:
        raise RuntimeError("Governance engine not available. Make sure the governance layer is initialized.")

    # Initialize drift detector
    drift_detector = get_governance_drift_detector(drift_config)
    logger.info("Initialized governance drift detector")

    # Initialize rollback manager
    rollback_manager = get_governance_rollback_manager(rollback_config)
    logger.info("Initialized governance rollback manager")

    # Integrate components
    integrate_drift_detection_with_governance(governance_engine, drift_detector)
    integrate_rollback_with_drift_detection(drift_detector, rollback_config)

    # Start background monitoring
    monitoring_task = asyncio.create_task(run_drift_monitoring(drift_detector, rollback_manager))

    # Return integration status
    integration_status = {
        "status": "integrated",
        "drift_detector": drift_detector,
        "rollback_manager": rollback_manager,
        "governance_engine": governance_engine,
        "monitoring_task": monitoring_task,
        "configuration": {
            "drift_config": drift_config.__dict__,
            "rollback_config": rollback_config.__dict__
        }
    }

    logger.info("✅ Governance drift detection integration completed successfully")
    logger.info(f"Monitoring will run every {drift_config.drift_check_interval_seconds} seconds")

    return integration_status

async def run_drift_monitoring(
    drift_detector: GovernanceDriftDetector,
    rollback_manager: GovernanceRollbackManager
) -> None:
    """
    Run continuous drift monitoring in the background.
    """
    logger.info("Starting continuous governance drift monitoring...")

    while True:
        try:
            # Collect current metrics
            current_metrics = drift_detector.collect_current_metrics()

            # Check for drift
            drift_incidents = drift_detector.detect_drift(current_metrics)

            # Handle any incidents
            for incident in drift_incidents:
                logger.warning(f"Drift incident detected: {incident.incident_id}")
                await rollback_manager.handle_drift_incident(incident)

            # Check quarantine status
            released_quarantines = rollback_manager.check_quarantine_status()
            if released_quarantines:
                logger.info(f"Released quarantines for strategies: {released_quarantines}")

            # Wait for next check
            await asyncio.sleep(drift_detector.config.drift_check_interval_seconds)

        except Exception as e:
            logger.error(f"Error in drift monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying

def get_drift_detection_status(integration_status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current status of the drift detection system.
    """
    drift_detector = integration_status["drift_detector"]
    rollback_manager = integration_status["rollback_manager"]

    return {
        "drift_detection": {
            "active": True,
            "last_check": getattr(drift_detector, 'last_check_time', None),
            "baseline_metrics_count": len(drift_detector.baseline_metrics),
            "total_incidents": len(drift_detector.drift_incidents),
            "active_quarantines": len(drift_detector.quarantined_strategies)
        },
        "rollback_system": {
            "total_rollback_incidents": len(rollback_manager.rollback_incidents),
            "active_quarantines": len(rollback_manager.active_quarantines),
            "successful_recoveries": len([r for r in rollback_manager.rollback_incidents if r.status == "recovered"]),
            "quarantine_effectiveness": rollback_manager._calculate_quarantine_effectiveness()
        },
        "configuration": integration_status["configuration"]
    }

def create_monitoring_dashboard_data(integration_status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create dashboard data for monitoring the drift detection system.
    """
    status = get_drift_detection_status(integration_status)

    return {
        "governance_drift_dashboard": {
            "timestamp": "now",
            "system_health": "healthy" if status["drift_detection"]["total_incidents"] < 10 else "warning",
            "metrics": {
                "drift_incidents_total": status["drift_detection"]["total_incidents"],
                "active_quarantines": status["rollback_system"]["active_quarantines"],
                "successful_recoveries": status["rollback_system"]["successful_recoveries"],
                "quarantine_effectiveness": status["rollback_system"]["quarantine_effectiveness"]
            },
            "alerts": [],  # Would be populated by actual monitoring
            "recommendations": _generate_monitoring_recommendations(status)
        }
    }

def _generate_monitoring_recommendations(status: Dict[str, Any]) -> List[str]:
    """Generate monitoring recommendations based on current status."""
    recommendations = []

    incidents = status["drift_detection"]["total_incidents"]
    quarantines = status["rollback_system"]["active_quarantines"]
    effectiveness = status["rollback_system"]["quarantine_effectiveness"]

    if incidents > 20:
        recommendations.append("High incident rate detected - review governance policies")
    elif incidents > 10:
        recommendations.append("Moderate incident rate - monitor closely")

    if quarantines > 10:
        recommendations.append("High quarantine count - review quarantine policies")

    if effectiveness < 0.5:
        recommendations.append("Low quarantine effectiveness - review quarantine criteria")

    if not recommendations:
        recommendations.append("Governance drift detection operating normally")

    return recommendations

# Global integration state
_integration_status = None

def get_integration_status() -> Optional[Dict[str, Any]]:
    """Get the current integration status."""
    return _integration_status

def main():
    """
    Main integration function when run as a script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Perform integration
        global _integration_status
        _integration_status = integrate_governance_drift_detection()

        print("🎉 Governance drift detection integration completed!")
        print("\nIntegration Status:")
        print(f"  ✅ Drift Detector: Active")
        print(f"  ✅ Rollback Manager: Active")
        print(f"  ✅ Monitoring: Running every {_integration_status['configuration']['drift_config']['drift_check_interval_seconds']} seconds")

        # Get initial status
        status = get_drift_detection_status(_integration_status)
        print("
Initial Status:")
        print(f"  📊 Baseline Metrics: {status['drift_detection']['baseline_metrics_count']}")
        print(f"  🚨 Active Incidents: {status['drift_detection']['total_incidents']}")
        print(f"  🛡️ Active Quarantines: {status['rollback_system']['active_quarantines']}")

        print("
🚀 System is now protected against governance drift!")

        # Keep the script running to maintain monitoring
        print("\nMonitoring active... Press Ctrl+C to stop.")
        asyncio.get_event_loop().run_forever()

    except KeyboardInterrupt:
        print("\n👋 Shutting down governance drift detection...")
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        print(f"❌ Integration failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
