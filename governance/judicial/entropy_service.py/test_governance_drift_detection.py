#!/usr/bin/env python3
"""
Governance Drift Detection Test Suite
======================================

Comprehensive tests for the governance drift detection system.

This test suite validates:
- Drift detection algorithms and statistical significance
- Rollback and quarantine mechanisms
- Integration with governance layer
- Alert triggering and monitoring
- Recovery and auto-release functionality

Usage:
    python3 scripts/test_governance_drift_detection.py
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI-Projects', 'universal-ai-tools', 'src'))

from core.governance_drift_detection import (
    GovernanceDriftDetector,
    DriftDetectionConfig,
    DriftIncident,
    DriftSeverity,
    DriftType,
    GovernanceDriftMetrics
)

from scripts.governance_drift_rollback_hooks import (
    GovernanceRollbackManager,
    RollbackConfiguration,
    RollbackAction
)

from scripts.integrate_governance_drift_detection import (
    integrate_governance_drift_detection,
    get_drift_detection_status
)

class TestGovernanceDriftDetection(unittest.TestCase):
    """Test governance drift detection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = DriftDetectionConfig(
            violation_rate_threshold=0.1,
            policy_delta_threshold=0.15,
            behavioral_shift_threshold=0.2,
            governance_score_threshold=0.1,
            min_samples_for_significance=5,  # Lower for testing
            confidence_level=0.95
        )
        self.detector = GovernanceDriftDetector(self.config)

        # Mock governance engine
        self.mock_governance_engine = Mock()
        self.mock_governance_engine.governance_log = []

    def test_detector_initialization(self):
        """Test that the detector initializes correctly."""
        self.assertIsInstance(self.detector, GovernanceDriftDetector)
        self.assertEqual(len(self.detector.baseline_metrics), 0)
        self.assertEqual(len(self.detector.drift_incidents), 0)

    def test_metrics_collection(self):
        """Test collection of governance metrics."""
        # Mock governance log with some data
        self.mock_governance_engine.governance_log = [
            {
                'assessment': {'overall_clearance': True, 'governance_score': 0.8},
                'timestamp': datetime.now()
            },
            {
                'assessment': {'overall_clearance': False, 'governance_score': 0.6},
                'timestamp': datetime.now()
            }
        ]

        self.detector.integrate_with_governance(self.mock_governance_engine)
        metrics = self.detector.collect_current_metrics()

        self.assertIsInstance(metrics, GovernanceDriftMetrics)
        self.assertIsInstance(metrics.violation_rate, float)
        self.assertIsInstance(metrics.governance_score_avg, float)
        self.assertGreaterEqual(metrics.violation_rate, 0.0)
        self.assertLessEqual(metrics.violation_rate, 1.0)

    def test_violation_rate_drift_detection(self):
        """Test detection of violation rate spikes."""
        # Create baseline data (low violations)
        baseline_data = [
            (datetime.now() - timedelta(hours=i), 0.05) for i in range(10, 0, -1)
        ]
        self.detector.violation_rate_history = baseline_data

        # Test current high violation rate
        current_rate = 0.25  # 25% violations vs 5% baseline

        incident = self.detector._detect_violation_rate_drift(current_rate, 0.05)

        self.assertIsNotNone(incident)
        self.assertEqual(incident.drift_type, DriftType.VIOLATION_RATE_SPIKE)
        self.assertGreater(incident.confidence_score, 0)

    def test_policy_delta_drift_detection(self):
        """Test detection of policy delta drift."""
        # Create baseline data (stable policies)
        baseline_data = [
            (datetime.now() - timedelta(hours=i), 0.02) for i in range(10, 0, -1)
        ]
        self.detector.policy_delta_history = baseline_data

        # Test current high policy delta
        current_delta = 0.25  # 25% policy change vs 2% baseline

        incident = self.detector._detect_policy_delta_drift(current_delta, 0.02)

        self.assertIsNotNone(incident)
        self.assertEqual(incident.drift_type, DriftType.POLICY_DELTA_DRIFT)
        self.assertGreater(incident.delta_percentage, 0)

    def test_behavioral_shift_detection(self):
        """Test detection of behavioral consistency shifts."""
        # Create baseline data (consistent behavior)
        baseline_data = [
            (datetime.now() - timedelta(hours=i), 0.1) for i in range(10, 0, -1)
        ]
        self.detector.behavioral_history = baseline_data

        # Test current inconsistent behavior
        current_behavioral = 0.35  # High variance vs low baseline

        incident = self.detector._detect_behavioral_shift(current_behavioral, 0.1)

        self.assertIsNotNone(incident)
        self.assertEqual(incident.drift_type, DriftType.BEHAVIORAL_SHIFT)
        self.assertEqual(incident.severity, DriftSeverity.HIGH)

    def test_quarantine_calculation(self):
        """Test quarantine duration calculation."""
        # Test normal case
        duration = self.detector._calculate_quarantine_duration("strategy_1", Mock(severity=DriftSeverity.MEDIUM))
        self.assertEqual(duration, self.config.default_quarantine_hours)

        # Test critical severity
        duration = self.detector._calculate_quarantine_duration("strategy_2", Mock(severity=DriftSeverity.CRITICAL))
        self.assertEqual(duration, self.config.default_quarantine_hours * 2)

    def test_baseline_updates(self):
        """Test baseline metric updates."""
        metrics = GovernanceDriftMetrics(
            timestamp=datetime.now(),
            violation_rate=0.05,
            policy_delta_score=0.02,
            behavioral_consistency_score=0.1,
            governance_score_avg=0.85,
            constitutional_balance_score=0.9,
            strategy_count=100,
            active_violations=5
        )

        initial_baseline_count = len(self.detector.baseline_metrics)
        self.detector._update_baselines(metrics)

        self.assertEqual(len(self.detector.baseline_metrics), initial_baseline_count + 1)

class TestGovernanceRollbackManager(unittest.TestCase):
    """Test governance rollback manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = RollbackConfiguration(
            default_quarantine_hours=24,
            auto_recovery_enabled=True,
            recovery_monitoring_hours=6
        )
        self.rollback_manager = GovernanceRollbackManager(self.config)

    def test_rollback_action_determination(self):
        """Test determination of rollback actions based on severity."""
        # Test critical severity
        incident = DriftIncident(
            incident_id="test_critical",
            drift_type=DriftType.VIOLATION_RATE_SPIKE,
            severity=DriftSeverity.CRITICAL,
            detected_at=datetime.now(),
            confidence_score=0.95,
            baseline_value=0.05,
            current_value=0.25,
            delta_percentage=4.0,
            affected_strategies=["strategy_1"],
            recommended_actions=[]
        )

        actions = self.rollback_manager._determine_rollback_actions(incident)

        self.assertIn(RollbackAction.STRATEGY_QUARANTINE, actions)
        self.assertIn(RollbackAction.CONSTITUTIONAL_ROLLBACK, actions)
        self.assertIn(RollbackAction.HUMAN_INTERVENTION, actions)

    async def test_strategy_quarantine_execution(self):
        """Test execution of strategy quarantine."""
        incident = DriftIncident(
            incident_id="test_quarantine",
            drift_type=DriftType.VIOLATION_RATE_SPIKE,
            severity=DriftSeverity.HIGH,
            detected_at=datetime.now(),
            confidence_score=0.95,
            baseline_value=0.05,
            current_value=0.25,
            delta_percentage=4.0,
            affected_strategies=["strategy_1", "strategy_2"],
            recommended_actions=[]
        )

        quarantined = await self.rollback_manager._execute_strategy_quarantine(incident)

        self.assertEqual(len(quarantined), 2)
        self.assertIn("strategy_1", quarantined)
        self.assertIn("strategy_2", quarantined)

        # Check quarantine records
        self.assertIn("strategy_1", self.rollback_manager.active_quarantines)
        self.assertIn("strategy_2", self.rollback_manager.active_quarantines)

    def test_quarantine_status_checking(self):
        """Test quarantine status checking and auto-release."""
        # Add an expired quarantine
        past_time = datetime.now() - timedelta(hours=25)
        self.rollback_manager.active_quarantines["expired_strategy"] = {
            "quarantine_start": past_time,
            "quarantine_end": past_time + timedelta(hours=24),
            "reason": "test",
            "incident_severity": "high",
            "auto_release": True
        }

        # Add an active quarantine
        self.rollback_manager.active_quarantines["active_strategy"] = {
            "quarantine_start": datetime.now(),
            "quarantine_end": datetime.now() + timedelta(hours=24),
            "reason": "test",
            "incident_severity": "high",
            "auto_release": True
        }

        released = self.rollback_manager.check_quarantine_status()

        self.assertIn("expired_strategy", released)
        self.assertNotIn("expired_strategy", self.rollback_manager.active_quarantines)
        self.assertIn("active_strategy", self.rollback_manager.active_quarantines)

class TestIntegration(unittest.TestCase):
    """Test integration between components."""

    @patch('scripts.integrate_governance_drift_detection.get_governance_engine')
    def test_full_integration(self, mock_get_governance_engine):
        """Test full integration setup."""
        # Mock governance engine
        mock_engine = Mock()
        mock_engine.governance_log = []
        mock_get_governance_engine.return_value = mock_engine

        # Test integration
        integration_status = integrate_governance_drift_detection()

        self.assertEqual(integration_status["status"], "integrated")
        self.assertIn("drift_detector", integration_status)
        self.assertIn("rollback_manager", integration_status)
        self.assertIn("governance_engine", integration_status)

    def test_status_reporting(self):
        """Test status reporting functionality."""
        # Create mock integration status
        mock_status = {
            "drift_detector": Mock(),
            "rollback_manager": Mock(),
            "configuration": {"drift_config": {}, "rollback_config": {}}
        }

        # Mock the detector and manager methods
        mock_status["drift_detector"].baseline_metrics = []
        mock_status["drift_detector"].drift_incidents = []
        mock_status["drift_detector"].quarantined_strategies = {}
        mock_status["rollback_manager"].rollback_incidents = []
        mock_status["rollback_manager"].active_quarantines = {}
        mock_status["rollback_manager"]._calculate_quarantine_effectiveness = Mock(return_value=0.8)

        # Test status retrieval
        status = get_drift_detection_status(mock_status)

        self.assertIn("drift_detection", status)
        self.assertIn("rollback_system", status)
        self.assertIn("configuration", status)

def run_async_tests():
    """Run async tests."""
    async def test_async_functions():
        # Test async quarantine execution
        rollback_manager = GovernanceRollbackManager()
        incident = DriftIncident(
            incident_id="async_test",
            drift_type=DriftType.VIOLATION_RATE_SPIKE,
            severity=DriftSeverity.MEDIUM,
            detected_at=datetime.now(),
            confidence_score=0.9,
            baseline_value=0.05,
            current_value=0.15,
            delta_percentage=2.0,
            affected_strategies=["async_strategy"],
            recommended_actions=[]
        )

        quarantined = await rollback_manager._execute_strategy_quarantine(incident)
        assert len(quarantined) == 1
        assert quarantined[0] == "async_strategy"

        print("✅ Async quarantine test passed")

    # Run async test
    asyncio.run(test_async_functions())

def main():
    """Run the test suite."""
    print("🧪 Running Governance Drift Detection Test Suite")
    print("=" * 60)

    # Run sync tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Run async tests
    print("\n🌀 Running async tests...")
    run_async_tests()

    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        return 1

if __name__ == "__main__":
    exit(main())
