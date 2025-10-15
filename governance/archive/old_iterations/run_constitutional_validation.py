#!/usr/bin/env python3
"""
Constitutional Auto-Evolution Validation Runner
===============================================

Runs the 30-minute validation sprint and generates hardening reports.

Usage:
    python3 run_constitutional_validation.py [--db-url URL] [--format json|table]
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

class ConstitutionalValidator:
    """Runs comprehensive validation checks for constitutional auto-evolution."""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable required")

    def run_validation(self) -> Dict[str, Any]:
        """Run the complete 30-minute validation sprint."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {}
        }

        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                # 1. Policy Integrity Check
                cursor.execute("""
                    SELECT COUNT(*) as invalid_policies
                    FROM active_strategies
                    WHERE policy_hash != (SELECT current_policy_hash FROM constitution_version)
                """)
                invalid_count = cursor.fetchone()['invalid_policies']
                results["checks"]["policy_integrity"] = {
                    "status": "PASS" if invalid_count == 0 else "FAIL",
                    "value": invalid_count,
                    "threshold": 0
                }

                # 2. Exploration Sanity Check
                cursor.execute("""
                    SELECT AVG(exploration_rate) as avg_rate
                    FROM bandit_performance
                    WHERE confidence_bucket = 'medium'
                    AND ts > NOW() - INTERVAL '30 minutes'
                """)
                exploration_rate = cursor.fetchone()['avg_rate'] or 0
                results["checks"]["exploration_sanity"] = {
                    "status": "PASS" if 0.05 <= exploration_rate <= 0.20 else "FAIL",
                    "value": round(exploration_rate, 3),
                    "threshold": "0.05-0.20"
                }

                # 3. Utility Scoreboard
                cursor.execute("""
                    WITH policy_utils AS (
                        SELECT
                            policy_name,
                            AVG(utility_score) as avg_utility
                        FROM utility_analysis
                        WHERE ts > NOW() - INTERVAL '7 days'
                        GROUP BY policy_name
                    )
                    SELECT
                        (SELECT avg_utility FROM policy_utils WHERE policy_name = 'neural+bandit+const') as neural_utility,
                        (SELECT MAX(avg_utility) FROM policy_utils WHERE policy_name LIKE '%static%') as static_utility
                """)
                utils = cursor.fetchone()
                neural_util = utils['neural_utility'] or 0
                static_util = utils['static_utility'] or 0
                threshold = static_util * 1.1 if static_util > 0 else 0
                results["checks"]["utility_scoreboard"] = {
                    "status": "PASS" if neural_util >= threshold else "FAIL",
                    "value": round(neural_util, 3),
                    "threshold": round(threshold, 3)
                }

                # 4. Federation DP Check
                cursor.execute("""
                    SELECT MAX(epsilon_30d_total) as max_epsilon
                    FROM privacy_accounting
                    WHERE ts > NOW() - INTERVAL '30 days'
                """)
                max_epsilon = cursor.fetchone()['max_epsilon'] or 0
                results["checks"]["federation_dp"] = {
                    "status": "PASS" if max_epsilon <= 2.0 else "FAIL",
                    "value": round(max_epsilon, 2),
                    "threshold": 2.0
                }

                # 5. Over-filtering Check
                cursor.execute("""
                    SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY docs_used) as median_docs
                    FROM routing_outcomes
                    WHERE ts > NOW() - INTERVAL '1 hour'
                """)
                median_docs = cursor.fetchone()['median_docs'] or 0
                results["checks"]["over_filtering"] = {
                    "status": "PASS" if median_docs >= 3 else "FAIL",
                    "value": round(median_docs, 1),
                    "threshold": 3.0
                }

                # 6. Monoculture Check
                cursor.execute("""
                    SELECT MAX(traffic_pct) as max_traffic
                    FROM (
                        SELECT COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () as traffic_pct
                        FROM routing_outcomes
                        WHERE ts > NOW() - INTERVAL '2 hours'
                        GROUP BY strategy_id
                    ) t
                """)
                max_traffic = cursor.fetchone()['max_traffic'] or 0
                results["checks"]["monoculture"] = {
                    "status": "PASS" if max_traffic <= 0.70 else "FAIL",
                    "value": round(max_traffic, 3),
                    "threshold": 0.70
                }

                # 7. Governance Quality (FP/FN rates)
                cursor.execute("""
                    SELECT
                        false_positive_rate_pct,
                        false_negative_rate_pct
                    FROM governance_quality
                """)
                gov_quality = cursor.fetchone()
                fp_rate = gov_quality['false_positive_rate_pct'] or 0
                fn_rate = gov_quality['false_negative_rate_pct'] or 0

                results["checks"]["governance_fp_rate"] = {
                    "status": "PASS" if fp_rate <= 10 else "FAIL",
                    "value": round(fp_rate, 1),
                    "threshold": 10.0
                }
                results["checks"]["governance_fn_rate"] = {
                    "status": "PASS" if fn_rate <= 10 else "FAIL",
                    "value": round(fn_rate, 1),
                    "threshold": 10.0
                }

        # Calculate summary
        checks = results["checks"]
        passed = sum(1 for c in checks.values() if c["status"] == "PASS")
        total = len(checks)
        results["summary"] = {
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "compliance_rate": round(passed / total * 100, 1),
            "overall_status": "PASS" if passed == total else "REVIEW"
        }

        return results

def print_table_results(results: Dict[str, Any]):
    """Print validation results in table format."""
    print("\n🛡️  CONSTITUTIONAL AUTO-EVOLUTION VALIDATION")
    print("=" * 55)
    print(f"Timestamp: {results['timestamp']}")
    print()

    print("📋 CHECK RESULTS:")
    print("-" * 55)
    print(f"{'Check':<25} {'Status':<8} {'Value':<10} {'Threshold':<10}")
    print("-" * 55)

    for check_name, check_data in results["checks"].items():
        status_icon = "✅" if check_data["status"] == "PASS" else "❌"
        print(f"{check_name:<25} {status_icon:<8} {str(check_data['value']):<10} {str(check_data['threshold']):<10}")

    print()
    summary = results["summary"]
    print("📊 SUMMARY:")
    print(f"  Total Checks: {summary['total_checks']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Compliance Rate: {summary['compliance_rate']}%")
    print(f"  Overall Status: {'✅ PASS' if summary['overall_status'] == 'PASS' else '⚠️  REVIEW'}")

    if summary["failed"] > 0:
        print("\n⚠️  FAILED CHECKS REQUIRE ATTENTION")
        failed_checks = [name for name, data in results["checks"].items() if data["status"] == "FAIL"]
        for check in failed_checks:
            print(f"  • {check}")

def main():
    parser = argparse.ArgumentParser(description="Constitutional Auto-Evolution Validation")
    parser.add_argument("--db-url", help="Database URL (or set DATABASE_URL env var)")
    parser.add_argument("--format", choices=["table", "json"], default="table",
                       help="Output format")
    args = parser.parse_args()

    try:
        validator = ConstitutionalValidator(args.db_url)
        results = validator.run_validation()

        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            print_table_results(results)

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
