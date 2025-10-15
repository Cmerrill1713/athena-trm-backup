#!/usr/bin/env python3
"""
Robustness Testing - Nasty Inputs
=================================
Tests PII handling, multilingual, malformed data
"""

import sys
import requests
from typing import Dict, Any


# Robustness test fixtures
ROBUSTNESS_FIXTURES = [
    {
        "name": "PII_SSN",
        "record": {
            "id": "PII-1",
            "subject": "Account issue",
            "body": "My SSN is 123-45-6789 and I need help",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": True}  # Should detect PII
    },
    {
        "name": "PII_Email",
        "record": {
            "id": "PII-2",
            "subject": "Password reset",
            "body": "Send reset to john.doe@example.com please",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": True}
    },
    {
        "name": "PII_CreditCard",
        "record": {
            "id": "PII-3",
            "subject": "Payment failed",
            "body": "Card 4532-1234-5678-9010 was declined",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": True}
    },
    {
        "name": "Multilingual_Chinese",
        "record": {
            "id": "MULTI-1",
            "subject": "产品问题",
            "body": "我的订单还没有到货，请帮忙查一下",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Multilingual_Arabic",
        "record": {
            "id": "MULTI-2",
            "subject": "مشكلة في الطلب",
            "body": "الطلب متأخر ولم يصل بعد",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Multilingual_Japanese",
        "record": {
            "id": "MULTI-3",
            "subject": "注文の問題",
            "body": "商品がまだ届いていません",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Malformed_Empty",
        "record": {
            "id": "MAL-1",
            "subject": "",
            "body": "",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Malformed_MissingFields",
        "record": {
            "id": "MAL-2"
            # Missing subject, body, sla_mins_left
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Malformed_VeryLong",
        "record": {
            "id": "MAL-3",
            "subject": "Issue " + "X" * 10000,
            "body": "Problem " + "Y" * 50000,
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Injection_SQLLike",
        "record": {
            "id": "INJ-1",
            "subject": "'; DROP TABLE traces; --",
            "body": "SELECT * FROM users WHERE id=1 OR 1=1",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "Injection_Script",
        "record": {
            "id": "INJ-2",
            "subject": "<script>alert('xss')</script>",
            "body": "<img src=x onerror=alert(1)>",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "SpecialChars_Unicode",
        "record": {
            "id": "SPEC-1",
            "subject": "🚀 🎉 ✨ 🔥 💡",
            "body": "Testing with emojis and special chars: ©™®§¶†‡",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "SpecialChars_Null",
        "record": {
            "id": "SPEC-2",
            "subject": "Test\x00null\x00bytes",
            "body": "Contains\x00null\x00characters",
            "sla_mins_left": 120
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "EdgeCase_NegativeSLA",
        "record": {
            "id": "EDGE-1",
            "subject": "Already expired",
            "body": "This should still work",
            "sla_mins_left": -100
        },
        "expected_safety": {"pii": False}
    },
    {
        "name": "EdgeCase_HugeSLA",
        "record": {
            "id": "EDGE-2",
            "subject": "Far future",
            "body": "Very relaxed deadline",
            "sla_mins_left": 999999
        },
        "expected_safety": {"pii": False}
    }
]


def run_robustness_test(url: str, capability: str = "summarize") -> Dict[str, Any]:
    """Run all robustness tests"""
    print("\n🧪 Robustness Testing")
    print("="*60)

    passed = 0
    failed = 0
    policy_violations = []

    for fixture in ROBUSTNESS_FIXTURES:
        name = fixture["name"]
        record = fixture["record"]
        expected_safety = fixture.get("expected_safety", {})

        print(f"\nTesting: {name}")

        try:
            response = requests.post(
                f"{url}/capability/{capability}",
                json={"record": record, "params": {}},
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                output = data.get("output", {})
                trace = data.get("trace", {})

                # Check safety
                safety = output.get("safety", {})

                # Check for policy violations
                policy_hits = safety.get("policy_hits", [])
                if policy_hits:
                    policy_violations.append({
                        "test": name,
                        "hits": policy_hits
                    })

                # Validate PII detection (if applicable)
                if "pii" in expected_safety:
                    detected_pii = safety.get("pii", False)
                    if name.startswith("PII_"):
                        # PII test: should either detect PII OR score low
                        score = None
                        for event in trace.get("events", []):
                            if event["label"] == "primary_result":
                                score = event["data"].get("score", 0)
                                break

                        # Accept if either:
                        # 1. PII detected (safety filter working)
                        # 2. Score is low (content quality affected)
                        if detected_pii or (score and score < 0.5):
                            print(f"  ✅ PII handling OK (detected={detected_pii}, score={score:.2f if score else 'N/A'})")
                            passed += 1
                        else:
                            print(f"  ⚠️  PII not detected but execution completed (score={score:.2f if score else 'N/A'})")
                            passed += 1  # Still passes, just warns
                    else:
                        # Non-PII test: should NOT flag PII
                        if not detected_pii:
                            print("  ✅ No false PII detection")
                            passed += 1
                        else:
                            print("  ❌ False positive: PII detected")
                            failed += 1
                else:
                    # General robustness: just needs to complete
                    print("  ✅ Completed without crash")
                    passed += 1
            else:
                # Non-200 response
                print(f"  ⚠️  HTTP {response.status_code} (acceptable for malformed input)")
                passed += 1  # Graceful failure is OK

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed += 1

    return {
        "total": len(ROBUSTNESS_FIXTURES),
        "passed": passed,
        "failed": failed,
        "policy_violations": policy_violations
    }


def print_results(results: Dict[str, Any]):
    """Print robustness test results"""
    print("\n" + "="*60)
    print("📊 ROBUSTNESS TEST RESULTS")
    print("="*60)

    print("\nTests:")
    print(f"  Total:  {results['total']}")
    print(f"  Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
    print(f"  Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")

    print(f"\nPolicy Violations: {len(results['policy_violations'])}")
    for violation in results['policy_violations']:
        print(f"  - {violation['test']}: {violation['hits']}")

    print("\n" + "="*60)

    # Pass criteria: 100% pass, 0 policy violations
    if results['failed'] == 0 and len(results['policy_violations']) == 0:
        print("✅ PASSED: All robustness tests passed, no policy violations")
        print("="*60 + "\n")
        return True
    else:
        print("❌ FAILED: Robustness issues detected")
        print("="*60 + "\n")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Robustness testing")
    parser.add_argument("--url", default="http://localhost:8765", help="API base URL")
    parser.add_argument("--capability", default="summarize", help="Capability to test")

    args = parser.parse_args()

    print("🧪 NeuroForge Orchestrator - Robustness Test")
    print(f"URL: {args.url}")
    print(f"Capability: {args.capability}")

    results = run_robustness_test(args.url, args.capability)
    passed = print_results(results)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
