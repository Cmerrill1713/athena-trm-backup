#!/usr/bin/env python3
"""
Endpoint Probe - Detailed endpoint testing and diagnostics

Tests all governance endpoints and provides detailed diagnostic information.
"""

import sys
import json
import time
import requests
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Service configurations
SERVICES = {
    "orchestrator": {
        "port": 9110,
        "endpoints": [
            ("GET", "/health"),
            ("GET", "/ready"),
            ("GET", "/version"),
            ("GET", "/metrics"),
            ("GET", "/state"),
            ("POST", "/verdict"),
            ("POST", "/verdict/replay")
        ]
    },
    "canary": {
        "port": 9111,
        "endpoints": [
            ("GET", "/health"),
            ("GET", "/ready"),
            ("GET", "/version"),
            ("GET", "/metrics"),
            ("POST", "/canary-window")
        ]
    },
    "metrics": {
        "port": 9109,
        "endpoints": [
            ("GET", "/health"),
            ("GET", "/metrics")
        ]
    },
    "prometheus": {
        "port": 9090,
        "endpoints": [
            ("GET", "/-/ready"),
            ("GET", "/-/healthy"),
            ("GET", "/api/v1/targets"),
            ("GET", "/api/v1/series?match[]=governance_*")
        ]
    },
    "grafana": {
        "port": 3001,
        "endpoints": [
            ("GET", "/api/health")
        ]
    }
}


def test_endpoint(
    service: str,
    port: int,
    method: str,
    path: str,
    timeout: int = 5
) -> Tuple[bool, int, str, Dict[str, Any]]:
    """
    Test an endpoint and return detailed results
    
    Returns: (success, status_code, message, response_data)
    """
    url = f"http://localhost:{port}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            # Use test data for POST endpoints
            test_data = get_test_data(service, path)
            response = requests.post(url, json=test_data, timeout=timeout)
        else:
            return False, 0, f"Unsupported method: {method}", {}
        
        success = 200 <= response.status_code < 300
        
        try:
            data = response.json() if response.text else {}
        except:
            data = {"raw": response.text[:200]}
        
        message = "OK" if success else f"HTTP {response.status_code}"
        
        return success, response.status_code, message, data
        
    except requests.Timeout:
        return False, 0, f"Timeout after {timeout}s", {}
    except requests.ConnectionError:
        return False, 0, "Connection refused", {}
    except Exception as e:
        return False, 0, str(e), {}


def get_test_data(service: str, path: str) -> Dict[str, Any]:
    """Get test data for POST endpoints"""
    
    if "verdict" in path:
        return {
            "task_id": f"T-probe-{int(time.time())}",
            "verdict": "PASS",
            "ece_estimate": 0.045,
            "entropy_drift": 0.1,
            "violation_rate_delta": 0.001,
            "latency_p95_delta": -0.02,
            "actions": ["HOLD"]
        }
    
    if "canary" in path:
        return {
            "window_id": f"w-probe-{int(time.time())}",
            "decision": "HOLD",
            "samples": 100,
            "deltas": {
                "solve_rate": 0.01,
                "violation_rate": -0.001,
                "latency_p95": -0.05
            },
            "ece_post": 0.05,
            "confidence": 0.85
        }
    
    return {}


def main():
    """Run endpoint probes"""
    print("=" * 80)
    print("Governance System Endpoint Probe")
    print("=" * 80)
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    results = []
    
    for service_name, config in SERVICES.items():
        port = config["port"]
        endpoints = config["endpoints"]
        
        print(f"\n┌─ {service_name.upper()} (port {port})")
        print(f"│  Testing {len(endpoints)} endpoint(s)...")
        
        for method, path in endpoints:
            total_tests += 1
            success, status, message, data = test_endpoint(service_name, port, method, path)
            
            if success:
                print(f"│  ✓ {method:4s} {path:30s} → {message}")
                passed_tests += 1
            else:
                print(f"│  ✗ {method:4s} {path:30s} → {message}")
                failed_tests += 1
            
            results.append({
                "service": service_name,
                "port": port,
                "method": method,
                "path": path,
                "success": success,
                "status_code": status,
                "message": message,
                "data": data
            })
        
        print(f"└─")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"✓ Passed: {passed_tests}")
    print(f"✗ Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    print()
    
    # Save detailed results
    results_file = "endpoint_probe_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "results": results
        }, f, indent=2)
    
    print(f"Detailed results saved to: {results_file}")
    print()
    
    if failed_tests == 0:
        print("✅ ALL ENDPOINTS RESPONDING")
        return 0
    else:
        print(f"❌ {failed_tests} ENDPOINT(S) FAILED")
        print()
        print("Failed endpoints:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['service']}:{r['port']} {r['method']} {r['path']} → {r['message']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

