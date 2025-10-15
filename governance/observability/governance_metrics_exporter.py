#!/usr/bin/env python3
"""
Governance Metrics Exporter for Prometheus
Exports governance signals to enable monitoring and alerting
"""

import time
import json
from typing import Dict, Any
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import threading

class GovernanceMetricsExporter:
    def __init__(self, port: int = 9109):
        self.port = port

        # ECE and Calibration Metrics
        self.ece_gauge = Gauge(
            'governance_ece',
            'Expected Calibration Error - measures probability calibration quality',
            ['component']
        )

        # Entropy and Drift Metrics
        self.entropy_drift_gauge = Gauge(
            'governance_entropy_drift',
            'System entropy drift over time',
            ['component']
        )

        # Auto-heal Metrics
        self.autoheal_errors_gauge = Gauge(
            'governance_autoheal_errors_total',
            'Total auto-heal errors encountered',
            ['component']
        )

        self.autoheal_rules_matched_gauge = Gauge(
            'governance_autoheal_rules_matched_total',
            'Number of auto-heal rules that matched',
            ['component']
        )

        self.autoheal_fixes_applied_gauge = Gauge(
            'governance_autoheal_fixes_applied_total',
            'Number of fixes successfully applied by auto-heal',
            ['component']
        )

        # Fix Confidence Metrics
        self.fix_confidence_gauge = Gauge(
            'governance_fix_confidence',
            'Confidence score for auto-fix operations',
            ['component']
        )

        # Evaluation Metrics
        self.edge_case_score_gauge = Gauge(
            'governance_edge_case_score',
            'Performance score on edge cases and adversarial inputs',
            ['component']
        )

        self.consistency_index_gauge = Gauge(
            'governance_consistency_index',
            'Measure of output consistency across similar inputs',
            ['component']
        )

        # Violation and Error Metrics
        self.violation_rate_gauge = Gauge(
            'governance_violation_rate',
            'Rate of governance violations detected',
            ['component', 'severity']
        )

        # Performance Metrics
        self.receipt_processing_time = Histogram(
            'governance_receipt_processing_duration_seconds',
            'Time spent processing governance receipts',
            ['component']
        )

        # Verdict Counters
        self.verdict_counter = Counter(
            'governance_verdicts_total',
            'Number of governance verdicts issued',
            ['verdict_type', 'component']
        )

    def update_from_receipt(self, receipt: Dict[str, Any], component: str = 'god_judge'):
        """Update metrics from a governance receipt"""

        with self.receipt_processing_time.labels(component).time():
            # ECE and Calibration
            if 'ece' in receipt:
                self.ece_gauge.labels(component=component).set(receipt['ece'])

            # Entropy Drift
            if 'entropy_drift' in receipt:
                self.entropy_drift_gauge.labels(component=component).set(receipt['entropy_drift'])

            # Auto-heal Metrics
            if 'autoheal' in receipt:
                autoheal = receipt['autoheal']
                self.autoheal_errors_gauge.labels(component=component).set(autoheal.get('errors', 0))
                self.autoheal_rules_matched_gauge.labels(component=component).set(autoheal.get('rules_matched', 0))
                self.autoheal_fixes_applied_gauge.labels(component=component).set(autoheal.get('fixes_applied', 0))

            # Fix Confidence
            if 'fix_confidence' in receipt:
                self.fix_confidence_gauge.labels(component=component).set(receipt['fix_confidence'])

            # Evaluation Scores
            if 'edge_case_score' in receipt:
                self.edge_case_score_gauge.labels(component=component).set(receipt['edge_case_score'])

            if 'consistency_index' in receipt:
                self.consistency_index_gauge.labels(component=component).set(receipt['consistency_index'])

            # Issue verdict based on receipt analysis
            verdict = self._analyze_receipt(receipt)
            self.verdict_counter.labels(verdict_type=verdict, component=component).inc()

            # Update violation rate (simplified example)
            violations = 0
            if receipt.get('ece', 0) > 0.06:
                violations += 1
            if receipt.get('entropy_drift', 0) >= 0.10:
                violations += 1
            if receipt.get('autoheal', {}).get('errors', 0) > 0 and receipt.get('autoheal', {}).get('rules_matched', 0) == 0:
                violations += 1

            self.violation_rate_gauge.labels(component=component, severity='high').set(violations)

    def _analyze_receipt(self, receipt: Dict[str, Any]) -> str:
        """Analyze receipt and return verdict type"""
        ece = receipt.get('ece', 0)
        entropy_drift = receipt.get('entropy_drift', 0)
        autoheal = receipt.get('autoheal', {})
        fix_confidence = receipt.get('fix_confidence', 0)
        tests_pass = receipt.get('tests_pass', 0)
        critical_errors = receipt.get('critical_errors', 0)
        class_min = 10  # Example minimum

        # Hard fail conditions
        if (ece > 0.06 or
            (autoheal.get('errors', 0) > 0 and autoheal.get('rules_matched', 0) == 0) or
            critical_errors > 0 or
            (fix_confidence < 0.6 and critical_errors > 0)):
            return 'hard_fail'

        # Soft fail conditions
        if (0.6 <= fix_confidence < 0.8 or entropy_drift >= 0.10):
            return 'soft_fail'

        # Pass conditions
        if (ece <= 0.06 and
            (autoheal.get('errors', 0) == 0 or autoheal.get('rules_matched', 0) > 0) and
            fix_confidence >= 0.8 and
            tests_pass >= class_min and
            critical_errors == 0):
            return 'pass'

        return 'unknown'

    def start_server(self):
        """Start the Prometheus metrics server"""
        start_http_server(self.port)
        print(f"🚀 Governance Metrics Exporter listening on port {self.port}")

        # Keep server running
        while True:
            time.sleep(60)

def main():
    exporter = GovernanceMetricsExporter()

    # Example receipt data (replace with actual receipt processing)
    sample_receipt = {
        "ece": 0.055,
        "entropy_drift": 0.04,
        "autoheal": {"errors": 7, "rules_matched": 0, "fixes_applied": 0},
        "fix_confidence": 0.0,
        "edge_case_score": 0.78,
        "consistency_index": 0.92,
        "tests_pass": 15,
        "critical_errors": 0
    }

    # Update metrics from sample receipt
    exporter.update_from_receipt(sample_receipt)

    # Start server
    exporter.start_server()

if __name__ == '__main__':
    main()
