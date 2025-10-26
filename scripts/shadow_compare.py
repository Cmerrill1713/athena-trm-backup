#!/usr/bin/env python3
"""
Shadow Traffic Comparison
Sends same requests to Python and Go stacks, compares outputs
"""
import json
import time
import hashlib
import statistics as st
from typing import Dict, Any, List
import httpx

PYTHON_GATEWAY = "http://localhost:8080"
GO_GATEWAY = "http://localhost:8081"
TIMEOUT = 30.0

def norm(s: str) -> str:
    """Normalize whitespace & numbers to ignore tokenization drift"""
    return " ".join(s.split())

def fingerprint(resp: dict) -> str:
    """
    Hash of top model, route, and first 200 chars of response
    Used for parity comparison
    """
    try:
        # Extract key fields
        model = resp.get("model", "")
        choices = resp.get("choices", [])
        text = choices[0].get("message", {}).get("content", "") if choices else ""
        
        # Create fingerprint
        key = (model, norm(text)[:200])
        return hashlib.sha1("|".join([str(x) for x in key]).encode()).hexdigest()
    except Exception as e:
        print(f"Fingerprint error: {e}")
        return "error"

def run_case(prompt: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Send same prompt to both Python and Go gateways
    Compare responses
    """
    print(f"Test {index}: {prompt.get('messages', [{}])[0].get('content', '')[:50]}...")
    
    results = {
        "index": index,
        "prompt": prompt,
        "python": {},
        "go": {},
        "same": False,
        "error": None
    }
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Call Python gateway
            start_py = time.time()
            resp_py = client.post(
                f"{PYTHON_GATEWAY}/v1/chat/completions",
                json=prompt
            )
            py_latency = (time.time() - start_py) * 1000
            
            # Call Go gateway
            start_go = time.time()
            resp_go = client.post(
                f"{GO_GATEWAY}/v1/chat/completions",
                json=prompt
            )
            go_latency = (time.time() - start_go) * 1000
            
            # Parse responses
            py_data = resp_py.json() if resp_py.status_code == 200 else {}
            go_data = resp_go.json() if resp_go.status_code == 200 else {}
            
            results["python"] = {
                "status": resp_py.status_code,
                "latency_ms": py_latency,
                "data": py_data,
                "fingerprint": fingerprint(py_data)
            }
            
            results["go"] = {
                "status": resp_go.status_code,
                "latency_ms": go_latency,
                "data": go_data,
                "fingerprint": fingerprint(go_data)
            }
            
            # Check parity
            results["same"] = (
                results["python"]["fingerprint"] == results["go"]["fingerprint"] and
                resp_py.status_code == resp_go.status_code == 200
            )
            
            # Performance delta
            results["latency_delta_pct"] = (
                ((go_latency - py_latency) / py_latency * 100)
                if py_latency > 0 else 0
            )
            
            print(f"  Python: {py_latency:.0f}ms, Go: {go_latency:.0f}ms, "
                  f"Delta: {results['latency_delta_pct']:+.1f}%, "
                  f"Parity: {'✅' if results['same'] else '❌'}")
            
    except Exception as e:
        results["error"] = str(e)
        print(f"  ERROR: {e}")
    
    return results

def main():
    print("🔬 SHADOW TRAFFIC COMPARISON")
    print("=" * 80)
    print("")
    
    # Load test prompts
    try:
        with open("seeds/e2e_prompts.jsonl", "r") as f:
            prompts = [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        print("⚠️  seeds/e2e_prompts.jsonl not found, using default prompts")
        prompts = [
            {
                "model": "athena-chat",
                "messages": [{"role": "user", "content": "What is the router service?"}],
                "temperature": 0.7,
                "stream": False
            },
            {
                "model": "athena-chat",
                "messages": [{"role": "user", "content": "Explain RAG in one sentence"}],
                "temperature": 0.7,
                "stream": False
            },
            {
                "model": "athena-chat",
                "messages": [{"role": "user", "content": "How does governance work?"}],
                "temperature": 0.7,
                "stream": False
            }
        ]
    
    print(f"Running {len(prompts)} test cases...")
    print("")
    
    # Run all test cases
    results = []
    for i, prompt in enumerate(prompts, 1):
        result = run_case(prompt, i)
        results.append(result)
        time.sleep(0.5)  # Rate limit
    
    # Calculate metrics
    successful = [r for r in results if not r.get("error")]
    parity_count = sum(1 for r in successful if r["same"])
    parity_rate = parity_count / len(successful) if successful else 0
    
    py_latencies = [r["python"]["latency_ms"] for r in successful if "latency_ms" in r["python"]]
    go_latencies = [r["go"]["latency_ms"] for r in successful if "latency_ms" in r["go"]]
    
    py_p95 = st.quantiles(py_latencies, n=20)[18] if py_latencies else 0  # 95th percentile
    go_p95 = st.quantiles(go_latencies, n=20)[18] if go_latencies else 0
    
    improvement = ((py_p95 - go_p95) / py_p95 * 100) if py_p95 > 0 else 0
    
    # Print summary
    print("")
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total cases: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Errors: {len(results) - len(successful)}")
    print(f"")
    print(f"Parity: {parity_count}/{len(successful)} ({parity_rate:.1%})")
    print(f"")
    print(f"Python p95: {py_p95:.0f}ms")
    print(f"Go p95: {go_p95:.0f}ms")
    print(f"Improvement: {improvement:+.1f}%")
    print("")
    
    # Gate checks
    print("=" * 80)
    print("🎯 GATE CHECKS")
    print("=" * 80)
    
    gates = {
        "Parity ≥ 99%": parity_rate >= 0.99,
        "P95 improvement ≥ 20%": improvement >= 20,
        "No errors": len(results) == len(successful)
    }
    
    for gate, passed in gates.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {gate}")
    
    all_passed = all(gates.values())
    print("")
    print("=" * 80)
    if all_passed:
        print("🎉 ALL GATES PASSED! Ready to promote Go gateway!")
    else:
        print("⚠️  GATES FAILED! Keep shadowing, don't promote yet.")
    print("=" * 80)
    
    # Save detailed results
    output = {
        "timestamp": time.time(),
        "summary": {
            "total": len(results),
            "successful": len(successful),
            "errors": len(results) - len(successful),
            "parity_rate": parity_rate,
            "python_p95_ms": py_p95,
            "go_p95_ms": go_p95,
            "improvement_pct": improvement
        },
        "gates": gates,
        "all_passed": all_passed,
        "results": results
    }
    
    with open("artifacts/shadow_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("")
    print("📁 Detailed results saved to: artifacts/shadow_results.json")
    
    # Exit code: 0 if all gates passed, 1 if any failed
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())

