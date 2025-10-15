#!/usr/bin/env python3
"""
Load Testing Script for Orchestrator
====================================
Tests concurrency, latency, and error rates
"""

import argparse
import time
import sys
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any


def execute_capability(url: str, capability: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single capability request"""
    start = time.time()

    try:
        response = requests.post(
            f"{url}/capability/{capability}",
            json={"record": record, "params": {}},
            timeout=5.0
        )

        elapsed_ms = int((time.time() - start) * 1000)

        if response.status_code == 200:
            data = response.json()
            score = None
            for event in data.get("trace", {}).get("events", []):
                if event["label"] == "primary_result":
                    score = event["data"].get("score", 0)
                    break

            return {
                "success": True,
                "latency_ms": elapsed_ms,
                "score": score,
                "error": None
            }
        else:
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "score": None,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "success": False,
            "latency_ms": elapsed_ms,
            "score": None,
            "error": str(e)
        }


def run_sequential(url: str, requests_count: int, capability: str) -> List[Dict]:
    """Run requests sequentially"""
    print(f"\n🔄 Running {requests_count} sequential requests...")

    results = []
    for i in range(requests_count):
        if i % 100 == 0:
            print(f"  Progress: {i}/{requests_count}")

        record = {
            "id": f"LOAD-{i}",
            "subject": f"Test {i}",
            "body": "Load testing orchestrator",
            "sla_mins_left": 120
        }

        result = execute_capability(url, capability, record)
        results.append(result)

    return results


def run_parallel(url: str, requests_count: int, concurrency: int, capability: str) -> List[Dict]:
    """Run requests in parallel"""
    print(f"\n🚀 Running {requests_count} requests with {concurrency} concurrency...")

    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        for i in range(requests_count):
            record = {
                "id": f"LOAD-{i}",
                "subject": f"Test {i}",
                "body": "Load testing orchestrator",
                "sla_mins_left": 120
            }

            future = executor.submit(execute_capability, url, capability, record)
            futures.append(future)

        completed = 0
        for future in as_completed(futures):
            results.append(future.result())
            completed += 1
            if completed % 100 == 0:
                print(f"  Progress: {completed}/{requests_count}")

    return results


def run_soak(url: str, requests_count: int, rate: float, capability: str) -> List[Dict]:
    """Run requests at a specific rate over time"""
    print(f"\n⏱️  Running soak test: {requests_count} requests at {rate} req/sec...")

    interval = 1.0 / rate
    results = []

    for i in range(requests_count):
        start = time.time()

        if i % 100 == 0:
            print(f"  Progress: {i}/{requests_count}")

        record = {
            "id": f"SOAK-{i}",
            "subject": f"Test {i}",
            "body": "Soak testing orchestrator",
            "sla_mins_left": 120
        }

        result = execute_capability(url, capability, record)
        results.append(result)

        # Rate limiting
        elapsed = time.time() - start
        sleep_time = interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    return results


def analyze_results(results: List[Dict]) -> Dict[str, Any]:
    """Analyze test results"""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    latencies = [r["latency_ms"] for r in successful]
    scores = [r["score"] for r in successful if r["score"] is not None]

    analysis = {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "error_rate": len(failed) / len(results) if results else 0,
    }

    if latencies:
        latencies.sort()
        analysis.update({
            "latency_p50": latencies[int(len(latencies) * 0.50)],
            "latency_p95": latencies[int(len(latencies) * 0.95)],
            "latency_p99": latencies[int(len(latencies) * 0.99)],
            "latency_max": max(latencies),
            "latency_avg": statistics.mean(latencies),
        })

    if scores:
        analysis.update({
            "score_avg": statistics.mean(scores),
            "score_min": min(scores),
            "score_max": max(scores),
        })

    return analysis


def print_results(analysis: Dict[str, Any], sla_latency: int = 1500, sla_score: float = 0.70):
    """Print formatted results"""
    print("\n" + "="*60)
    print("📊 LOAD TEST RESULTS")
    print("="*60)

    print("\nRequests:")
    print(f"  Total:      {analysis['total']}")
    print(f"  Successful: {analysis['successful']} ({analysis['successful']/analysis['total']*100:.1f}%)")
    print(f"  Failed:     {analysis['failed']} ({analysis['error_rate']*100:.1f}%)")

    if "latency_p50" in analysis:
        print("\nLatency (ms):")
        print(f"  p50:  {analysis['latency_p50']}ms")
        print(f"  p95:  {analysis['latency_p95']}ms {'✅' if analysis['latency_p95'] <= sla_latency else '❌ SLA VIOLATION'}")
        print(f"  p99:  {analysis['latency_p99']}ms")
        print(f"  max:  {analysis['latency_max']}ms")
        print(f"  avg:  {analysis['latency_avg']:.1f}ms")

    if "score_avg" in analysis:
        print("\nScores:")
        print(f"  avg:  {analysis['score_avg']:.3f} {'✅' if analysis['score_avg'] >= sla_score else '❌ SLA VIOLATION'}")
        print(f"  min:  {analysis['score_min']:.3f}")
        print(f"  max:  {analysis['score_max']:.3f}")

    # Pass/Fail determination
    print(f"\n{'='*60}")

    passed = True
    if analysis['error_rate'] > 0.01:  # >1% error rate
        print("❌ FAILED: Error rate > 1%")
        passed = False

    if "latency_p95" in analysis and analysis['latency_p95'] > sla_latency:
        print(f"❌ FAILED: p95 latency > {sla_latency}ms")
        passed = False

    if "score_avg" in analysis and analysis['score_avg'] < sla_score:
        print(f"❌ FAILED: Average score < {sla_score}")
        passed = False

    if passed:
        print("✅ PASSED: All SLAs met")

    print("="*60 + "\n")

    return passed


def main():
    parser = argparse.ArgumentParser(description="Load test orchestrator")
    parser.add_argument("--url", default="http://localhost:8765", help="API base URL")
    parser.add_argument("--requests", type=int, default=100, help="Total requests")
    parser.add_argument("--mode", choices=["sequential", "parallel", "soak"], default="sequential")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent workers (parallel mode)")
    parser.add_argument("--rate", type=float, default=1.0, help="Requests per second (soak mode)")
    parser.add_argument("--capability", default="summarize", help="Capability to test")
    parser.add_argument("--sla-latency", type=int, default=1500, help="SLA: max p95 latency (ms)")
    parser.add_argument("--sla-score", type=float, default=0.70, help="SLA: min average score")

    args = parser.parse_args()

    print("🧪 NeuroForge Orchestrator - Load Test")
    print("="*60)
    print(f"URL:         {args.url}")
    print(f"Mode:        {args.mode}")
    print(f"Requests:    {args.requests}")
    print(f"Capability:  {args.capability}")
    if args.mode == "parallel":
        print(f"Concurrency: {args.concurrency}")
    elif args.mode == "soak":
        print(f"Rate:        {args.rate} req/sec")

    # Run load test
    start_time = time.time()

    if args.mode == "sequential":
        results = run_sequential(args.url, args.requests, args.capability)
    elif args.mode == "parallel":
        results = run_parallel(args.url, args.requests, args.concurrency, args.capability)
    elif args.mode == "soak":
        results = run_soak(args.url, args.requests, args.rate, args.capability)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")

    # Analyze and print results
    analysis = analyze_results(results)
    passed = print_results(analysis, args.sla_latency, args.sla_score)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
