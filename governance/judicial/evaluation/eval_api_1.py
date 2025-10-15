"""
Evaluation API for Orchestrator
================================
Runs capability evaluations with golden fixtures
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from router import run_capability


app = FastAPI(title="NeuroForge Eval API", version="1.0.0")


# Golden evaluation fixtures
EVAL_FIXTURES = [
    {
        "id": "EVAL-1",
        "capability": "summarize",
        "record": {
            "id": "TICKET-1001",
            "subject": "Delayed shipment - urgent",
            "body": "Vendor confirmed shipment delayed by 3 days. Customer expecting delivery tomorrow. Need to notify customer and arrange compensation.",
            "sla_mins_left": 120
        },
        "expected_contains": ["delay", "customer", "notify"],
        "min_score": 0.70
    },
    {
        "id": "EVAL-2",
        "capability": "plan",
        "record": {
            "id": "TICKET-1002",
            "subject": "Quality issue - board failing AOI",
            "body": "PCB batch #2024-Q3-089 failing automated optical inspection on U15 component. 15 units affected. Root cause analysis needed.",
            "sla_mins_left": 60
        },
        "expected_contains": ["inspect", "analysis", "component"],
        "min_score": 0.70
    },
    {
        "id": "EVAL-3",
        "capability": "summarize",
        "record": {
            "id": "TICKET-1003",
            "subject": "Customer complaint - missing parts",
            "body": "Order #45678 received incomplete. Missing 2 power adapters and 1 cable. Customer requesting immediate replacement or refund.",
            "sla_mins_left": 180
        },
        "expected_contains": ["missing", "replacement", "order"],
        "min_score": 0.70
    },
    {
        "id": "EVAL-4",
        "capability": "plan",
        "record": {
            "id": "TICKET-1004",
            "subject": "System integration failure",
            "body": "New API version causing 500 errors in production. Rollback initiated. Need to identify breaking changes and create hotfix.",
            "sla_mins_left": 30
        },
        "expected_contains": ["rollback", "api", "hotfix"],
        "min_score": 0.70
    },
    {
        "id": "EVAL-5",
        "capability": "summarize",
        "record": {
            "id": "TICKET-1005",
            "subject": "Payment processing issue",
            "body": "Customer reports card charged twice for same order. Transaction IDs: TXN-7890, TXN-7891. Need to investigate and issue refund for duplicate charge.",
            "sla_mins_left": 240
        },
        "expected_contains": ["duplicate", "refund", "transaction"],
        "min_score": 0.70
    }
]


class EvalRequest(BaseModel):
    """Evaluation request"""
    capability: Optional[str] = None  # If None, test all
    limit: Optional[int] = None  # Max fixtures to test


class EvalResult(BaseModel):
    """Evaluation result"""
    total: int
    passed: int
    failed: int
    pass_rate: float
    results: List[Dict[str, Any]]


@app.post("/eval/run", response_model=EvalResult)
def run_eval(req: EvalRequest):
    """
    Run evaluation suite

    Args:
        req: Eval request with optional filters

    Returns:
        Evaluation results
    """
    # Filter fixtures
    fixtures = EVAL_FIXTURES
    if req.capability:
        fixtures = [f for f in fixtures if f["capability"] == req.capability]
    if req.limit:
        fixtures = fixtures[:req.limit]

    results = []
    passed = 0
    failed = 0

    for fixture in fixtures:
        fixture_id = fixture["id"]
        capability = fixture["capability"]
        record = fixture["record"]
        expected_contains = fixture.get("expected_contains", [])
        min_score = fixture.get("min_score", 0.70)

        try:
            # Execute capability
            result = run_capability(capability, record, {})
            output = result["output"]
            trace = result["trace"]

            # Extract score from trace
            score = None
            for event in trace.get("events", []):
                if event["label"] == "primary_result":
                    score = event["data"].get("score", 0)
                    break

            # Check if tldr contains expected terms
            tldr = output.get("tldr", "").lower()
            contains_all = all(term.lower() in tldr for term in expected_contains)

            # Pass criteria
            score_pass = score is not None and score >= min_score
            content_pass = contains_all or len(expected_contains) == 0

            fixture_passed = score_pass and content_pass

            if fixture_passed:
                passed += 1
            else:
                failed += 1

            results.append({
                "fixture_id": fixture_id,
                "capability": capability,
                "passed": fixture_passed,
                "score": score,
                "min_score": min_score,
                "expected_terms_found": contains_all,
                "latency_ms": output.get("metrics", {}).get("latency_ms", 0),
                "trace_id": trace.get("trace_id")
            })

        except Exception as e:
            failed += 1
            results.append({
                "fixture_id": fixture_id,
                "capability": capability,
                "passed": False,
                "error": str(e)
            })

    return EvalResult(
        total=len(results),
        passed=passed,
        failed=failed,
        pass_rate=passed / len(results) if results else 0,
        results=results
    )


@app.get("/health")
def health():
    """Health check"""
    return {"ok": True, "service": "eval"}


# ============================================
# CLI Runner
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8788, log_level="info")
