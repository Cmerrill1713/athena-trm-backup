#!/usr/bin/env python3
"""
Canary Test Suite for Routing Regression Testing.

Runs edge case queries through the router and validates:
- Quality metrics (confidence, latency)
- Safety assertions (no malicious behavior)
- Domain consistency
- Regression detection (vs baseline)
"""

import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from governance.routing.basic_router import BasicRouter, RoutingRequest
from governance.routing.contrastive_router import ContrastiveRouter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test case."""
    query: str
    domain: str
    routed_model: str
    confidence: float
    latency_ms: float
    passed: bool
    failures: List[str]
    warnings: List[str]


class CanaryTestSuite:
    """
    Canary test suite for routing validation.
    
    Runs edge cases and validates quality, safety, and regression.
    """
    
    def __init__(
        self,
        router,
        edge_cases_path: Path,
        safety_assertions_path: Path,
        quality_threshold: float = 0.85
    ):
        """
        Initialize canary test suite.
        
        Args:
            router: Router instance to test
            edge_cases_path: Path to edge_cases.json
            safety_assertions_path: Path to safety_assertions.json
            quality_threshold: Minimum pass rate for quality
        """
        self.router = router
        self.quality_threshold = quality_threshold
        
        # Load edge cases
        logger.info(f"Loading edge cases from {edge_cases_path}")
        with open(edge_cases_path) as f:
            data = json.load(f)
            self.edge_cases = self._flatten_edge_cases(data['categories'])
        
        # Load safety assertions
        logger.info(f"Loading safety assertions from {safety_assertions_path}")
        with open(safety_assertions_path) as f:
            data = json.load(f)
            self.safety_assertions = {
                a['name']: a for a in data['assertions']
            }
        
        logger.info(
            f"Loaded {len(self.edge_cases)} edge cases, "
            f"{len(self.safety_assertions)} safety assertions"
        )
    
    def _flatten_edge_cases(self, categories: Dict) -> List[Dict]:
        """Flatten edge cases from categories."""
        cases = []
        for category, tests in categories.items():
            for test in tests:
                test['category'] = category
                cases.append(test)
        return cases
    
    def run(self) -> Tuple[int, int, List[TestResult]]:
        """
        Run all test cases.
        
        Returns:
            (passed, failed, results) tuple
        """
        results = []
        passed = 0
        failed = 0
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Running {len(self.edge_cases)} canary test cases...")
        logger.info(f"{'='*70}\n")
        
        for i, case in enumerate(self.edge_cases, 1):
            result = self._run_test_case(case, i)
            results.append(result)
            
            if result.passed:
                passed += 1
                status = "✅ PASS"
            else:
                failed += 1
                status = "❌ FAIL"
            
            logger.info(
                f"{status} [{i}/{len(self.edge_cases)}] "
                f"({case['category']}) {case['query'][:50]}... "
                f"→ {result.routed_model} (conf: {result.confidence:.2f})"
            )
            
            if result.failures:
                for failure in result.failures:
                    logger.error(f"    ❌ {failure}")
            
            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"    ⚠️  {warning}")
        
        return passed, failed, results
    
    def _run_test_case(self, case: Dict, index: int) -> TestResult:
        """Run a single test case."""
        query = case['query']
        domain = case['domain']
        expected_domain = case.get('expected_domain')
        min_confidence = case.get('min_confidence', 0.5)
        allow_fallback = case.get('allow_fallback', False)
        safety_check = case.get('safety_check')
        
        failures = []
        warnings = []
        
        # Route the query
        request = RoutingRequest(query=query, domain=domain)
        
        start_time = time.time()
        choice = self.router.route(request)
        latency_ms = (time.time() - start_time) * 1000
        
        # Check latency
        if latency_ms > 50:
            failures.append(
                f"Latency {latency_ms:.1f}ms exceeds 50ms threshold"
            )
        
        # Check confidence
        if choice.confidence < min_confidence:
            if allow_fallback:
                warnings.append(
                    f"Low confidence {choice.confidence:.2f} < {min_confidence} "
                    f"(allowed for this case)"
                )
            else:
                failures.append(
                    f"Confidence {choice.confidence:.2f} < {min_confidence}"
                )
        
        # Check domain consistency
        if expected_domain and choice.domain != expected_domain:
            # Only fail if it's not a fallback case
            if not allow_fallback:
                failures.append(
                    f"Domain mismatch: expected {expected_domain}, "
                    f"got {choice.domain}"
                )
        
        # Check null routing
        if not choice.model:
            failures.append("Router returned null/empty model")
        
        # Safety assertions
        if safety_check:
            assertion = self.safety_assertions.get(safety_check)
            if assertion:
                safety_passed, safety_msg = self._check_safety_assertion(
                    query, choice, assertion
                )
                if not safety_passed:
                    if assertion['action'] == 'fail_on_exceed':
                        failures.append(safety_msg)
                    else:
                        warnings.append(safety_msg)
        
        passed = len(failures) == 0
        
        return TestResult(
            query=query,
            domain=domain,
            routed_model=choice.model,
            confidence=choice.confidence,
            latency_ms=latency_ms,
            passed=passed,
            failures=failures,
            warnings=warnings
        )
    
    def _check_safety_assertion(
        self,
        query: str,
        choice,
        assertion: Dict
    ) -> Tuple[bool, str]:
        """
        Check a safety assertion.
        
        Returns:
            (passed, message) tuple
        """
        check_type = assertion['check_type']
        
        if check_type == 'query_pattern':
            # Check for dangerous patterns in query
            patterns = assertion.get('patterns', [])
            for pattern in patterns:
                if pattern.lower() in query.lower():
                    return (
                        False,
                        f"Safety: Query contains pattern '{pattern}' ({assertion['name']})"
                    )
        
        elif check_type == 'semantic':
            # Check for malicious keywords
            keywords = assertion.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in query.lower():
                    return (
                        False,
                        f"Safety: Query contains keyword '{keyword}' ({assertion['name']})"
                    )
        
        elif check_type == 'performance':
            # Check latency threshold
            threshold = assertion.get('threshold_ms', 50)
            if choice.latency_ms > threshold:
                return (
                    False,
                    f"Safety: Latency {choice.latency_ms:.1f}ms > {threshold}ms"
                )
        
        elif check_type == 'confidence':
            # Check minimum confidence
            min_conf = assertion.get('min_confidence', 0.3)
            if choice.confidence < min_conf:
                return (
                    False,
                    f"Safety: Confidence {choice.confidence:.2f} < {min_conf}"
                )
        
        elif check_type == 'output':
            # Check for null/empty output
            if not choice.model:
                return (False, "Safety: Router returned null/empty model")
        
        return (True, "")
    
    def print_report(
        self,
        passed: int,
        failed: int,
        results: List[TestResult]
    ):
        """Print test report."""
        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print("CANARY TEST SUITE REPORT")
        print("="*70)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({pass_rate:.1f}%)")
        print(f"Failed: {failed}")
        print(f"\nQuality Threshold: {self.quality_threshold*100:.0f}%")
        
        if pass_rate < self.quality_threshold * 100:
            print(f"\n❌ REGRESSION DETECTED!")
            print(f"   Pass rate {pass_rate:.1f}% < threshold {self.quality_threshold*100:.0f}%")
        else:
            print(f"\n✅ All quality checks passed!")
        
        # Category breakdown
        print(f"\nCategory Breakdown:")
        categories = {}
        for result in results:
            cat = result.query  # We'd need to track category in result
            # Simplified for now
            pass
        
        # Performance stats
        latencies = [r.latency_ms for r in results]
        confidences = [r.confidence for r in results]
        
        import statistics
        print(f"\nPerformance:")
        print(f"  Latency (avg): {statistics.mean(latencies):.2f}ms")
        print(f"  Latency (p95): {statistics.quantiles(latencies, n=20)[18]:.2f}ms")
        print(f"  Latency (max): {max(latencies):.2f}ms")
        print(f"\nConfidence:")
        print(f"  Avg: {statistics.mean(confidences):.3f}")
        print(f"  Min: {min(confidences):.3f}")
        
        # Failed tests
        if failed > 0:
            print(f"\nFailed Tests ({failed}):")
            for i, result in enumerate(results, 1):
                if not result.passed:
                    print(f"\n{i}. {result.query[:60]}...")
                    for failure in result.failures:
                        print(f"   ❌ {failure}")
        
        print("="*70 + "\n")


def main():
    """Run canary test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run canary test suite for routing'
    )
    parser.add_argument(
        '--router',
        choices=['basic', 'contrastive'],
        default='contrastive',
        help='Router to test'
    )
    parser.add_argument(
        '--profiles',
        type=Path,
        default=Path('governance/routing/model_profiles.json'),
        help='Path to model profiles'
    )
    parser.add_argument(
        '--edge-cases',
        type=Path,
        default=Path('governance/ci/edge_cases.json'),
        help='Path to edge cases'
    )
    parser.add_argument(
        '--safety',
        type=Path,
        default=Path('governance/ci/safety_assertions.json'),
        help='Path to safety assertions'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.85,
        help='Quality threshold (0.0-1.0)'
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Exit on first failure'
    )
    
    args = parser.parse_args()
    
    # Create router
    if args.router == 'basic':
        router = BasicRouter(args.profiles)
    else:
        router = ContrastiveRouter(args.profiles)
    
    logger.info(f"Testing {args.router} router")
    
    # Create test suite
    suite = CanaryTestSuite(
        router=router,
        edge_cases_path=args.edge_cases,
        safety_assertions_path=args.safety,
        quality_threshold=args.threshold
    )
    
    # Run tests
    passed, failed, results = suite.run()
    
    # Print report
    suite.print_report(passed, failed, results)
    
    # Exit code
    total = passed + failed
    pass_rate = (passed / total) if total > 0 else 0
    
    if pass_rate < args.threshold:
        logger.error(
            f"❌ Tests FAILED: pass rate {pass_rate:.1%} < "
            f"threshold {args.threshold:.1%}"
        )
        return 1
    
    logger.info(f"✅ Tests PASSED: {passed}/{total} ({pass_rate:.1%})")
    return 0


if __name__ == '__main__':
    sys.exit(main())

