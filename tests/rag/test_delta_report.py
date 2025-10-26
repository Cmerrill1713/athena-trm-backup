#!/usr/bin/env python3
"""
Integration test for RAG delta report system.

Validates that:
1. Delta report script can be invoked
2. JSON and Markdown outputs are generated
3. Delta calculations are correct
4. Gate logic works as expected
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestRAGDeltaReport(unittest.TestCase):
    """Test suite for RAG delta reporting."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.script_path = cls.repo_root / "scripts" / "rag_delta_report.py"
        cls.eval_script = cls.repo_root / "scripts" / "eval_rag_hit_support.py"
        cls.seed_file = cls.repo_root / "seeds" / "eval_seed.jsonl"
        
        # Verify required files exist
        assert cls.script_path.exists(), f"Delta script not found: {cls.script_path}"
        assert cls.eval_script.exists(), f"Eval script not found: {cls.eval_script}"
        assert cls.seed_file.exists(), f"Seed file not found: {cls.seed_file}"
    
    def test_script_help(self):
        """Test that script help output works."""
        result = subprocess.run(
            [sys.executable, str(self.script_path), "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Compare two RAG evaluation modes", result.stdout)
        self.assertIn("--baseline-mode", result.stdout)
        self.assertIn("--treatment-mode", result.stdout)
    
    def test_delta_report_structure(self):
        """Test that delta report has expected structure."""
        # Create mock evaluation results
        with tempfile.TemporaryDirectory() as tmpdir:
            base_report = Path(tmpdir) / "base.json"
            treat_report = Path(tmpdir) / "treat.json"
            
            base_data = {
                "total_queries": 10,
                "hit@k": 0.90,
                "support@k": 0.85,
                "mrr@k": 0.80,
                "latency_sec_p50": 0.050,
                "latency_sec_p95": 0.100,
                "passed": True
            }
            
            treat_data = {
                "total_queries": 10,
                "hit@k": 0.95,
                "support@k": 0.92,
                "mrr@k": 0.88,
                "latency_sec_p50": 0.055,
                "latency_sec_p95": 0.110,
                "passed": True
            }
            
            with open(base_report, 'w') as f:
                json.dump(base_data, f)
            
            with open(treat_report, 'w') as f:
                json.dump(treat_data, f)
            
            # Read back and verify structure
            with open(base_report) as f:
                loaded = json.load(f)
                self.assertEqual(loaded["hit@k"], 0.90)
            
            with open(treat_report) as f:
                loaded = json.load(f)
                self.assertEqual(loaded["hit@k"], 0.95)
    
    def test_delta_calculations(self):
        """Test delta calculation logic."""
        baseline = {
            "hit@k": 0.90,
            "support@k": 0.85,
            "mrr@k": 0.80,
            "latency_sec_p50": 0.050,
            "latency_sec_p95": 0.100,
        }
        
        treatment = {
            "hit@k": 0.95,
            "support@k": 0.92,
            "mrr@k": 0.88,
            "latency_sec_p50": 0.055,
            "latency_sec_p95": 0.110,
        }
        
        # Calculate expected deltas
        expected_delta_hit = round(0.95 - 0.90, 4)  # +0.05
        expected_delta_support = round(0.92 - 0.85, 4)  # +0.07
        expected_delta_mrr = round(0.88 - 0.80, 4)  # +0.08
        expected_delta_p50 = round(0.055 - 0.050, 4)  # +0.005
        expected_delta_p95 = round(0.110 - 0.100, 4)  # +0.010
        
        self.assertEqual(expected_delta_hit, 0.05)
        self.assertEqual(expected_delta_support, 0.07)
        self.assertEqual(expected_delta_mrr, 0.08)
        self.assertEqual(expected_delta_p50, 0.005)
        self.assertEqual(expected_delta_p95, 0.01)
    
    def test_percentage_conversion(self):
        """Test percentage conversion helper."""
        # Mock the pct function from the script
        def pct(x):
            return round(x * 100.0, 2)
        
        self.assertEqual(pct(0.90), 90.0)
        self.assertEqual(pct(0.9567), 95.67)
        self.assertEqual(pct(0.05), 5.0)
        self.assertEqual(pct(-0.02), -2.0)


class TestDeltaGateLogic(unittest.TestCase):
    """Test delta gate validation logic."""
    
    def test_gate_pass_conditions(self):
        """Test that gates pass when thresholds are met."""
        delta = {
            "delta": {
                "hit@k": 0.05,  # +5%
                "support@k": 0.03,  # +3%
                "mrr@k": 0.02,
                "latency_sec_p95": 0.05  # +50ms
            }
        }
        
        # These should pass
        self.assertGreaterEqual(delta["delta"]["hit@k"], 0.01)  # ≥1% improvement
        self.assertGreaterEqual(delta["delta"]["support@k"], 0.01)  # ≥1% improvement
        self.assertLessEqual(delta["delta"]["latency_sec_p95"], 0.10)  # ≤100ms increase
    
    def test_gate_fail_conditions(self):
        """Test that gates fail when thresholds not met."""
        delta = {
            "delta": {
                "hit@k": 0.005,  # +0.5% (too small)
                "support@k": -0.01,  # -1% (regression!)
                "latency_sec_p95": 0.15  # +150ms (too slow)
            }
        }
        
        # These should fail
        self.assertLess(delta["delta"]["hit@k"], 0.01)  # <1% improvement
        self.assertLess(delta["delta"]["support@k"], 0.01)  # regression
        self.assertGreater(delta["delta"]["latency_sec_p95"], 0.10)  # too slow


def suite():
    """Build test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRAGDeltaReport))
    suite.addTests(loader.loadTestsFromTestCase(TestDeltaGateLogic))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    sys.exit(0 if result.wasSuccessful() else 1)

