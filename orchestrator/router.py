"""
Agent-Agnostic Router with Shadow Execution
===========================================
Routes by capability + policy + bandit, completely model-agnostic
WITH constraint enforcement, timeouts, and clean shadow logic
"""

import time
import yaml
import random
import signal
import contextlib
from typing import Dict, Any, Tuple
from pathlib import Path

from contracts import CapabilityInput, CapabilityOutput
from registry import REGISTRY
from loader import load_callable
from scorer import choose_arm, reward
from features import build_features
from telemetry import start_trace, log_event, finish_trace
from memory.vector_store import upsert, search
from memory.hygiene import dedupe


# Load policy
POLICY_PATH = Path(__file__).parent / "policies.yaml"
with open(POLICY_PATH, "r") as f:
    POLICY = yaml.safe_load(f)


@contextlib.contextmanager
def time_limit(ms: int):
    """Context manager for timeout enforcement"""
    def handler(signum, frame):
        raise TimeoutError("Execution exceeded time limit")

    secs = max(1, int(ms / 1000))
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(secs)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _composite_score(output: CapabilityOutput, weights: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """
    Calculate composite score from output

    Args:
        output: CapabilityOutput
        weights: Scorecard weights from policy

    Returns:
        (composite_score, subscore_dict)
    """
    # Subscores
    subs = {
        "correctness": 1.0 if output.get("tldr") and output.get("next_action") else 0.5,
        "structure":   1.0 if isinstance(output.get("facts"), list) and isinstance(output.get("actions"), list) else 0.5,
        "safety":      1.0 if not output.get("safety", {}).get("pii", False) else 0.0,
        "latency":     1.0,
        "acceptance":  0.8,  # Placeholder for user feedback
    }

    # Latency penalty
    lat = output.get("metrics", {}).get("latency_ms", 0)
    max_lat = POLICY["constraints"].get("max_latency_ms", 0)
    if max_lat and lat > max_lat:
        subs["latency"] = 0.3

    # Weighted composite
    composite = sum(subs[k] * weights[k] for k in weights if k in subs)

    return composite, subs


def _filter_by_constraints(providers):
    """
    Filter providers by policy constraints

    TODO: Add richer constraint checks
    - offline_only: filter providers with "requires_network" tag
    - pii_rules: filter providers without proper safety
    """
    # For now, return all (constraints enforced at router level)
    return list(providers)


def run_capability(capability: str, record: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a capability with agent-agnostic routing
    WITH constraint enforcement, timeouts, and shadow execution

    Args:
        capability: Capability name (e.g., "summarize", "plan")
        record: Input record
        params: Execution parameters

    Returns:
        {
            "output": CapabilityOutput,
            "trace": Trace dict with telemetry
        }
    """
    policy_ver = POLICY.get("policy_version", "v1")
    trace = start_trace(capability, record, params, policy_ver)

    # Context preparation
    record_text = f"{record.get('subject', '')} {record.get('body', '')}"
    upsert("docs", [record_text])
    ctx = search("docs", record.get("subject", ""), k=5)
    dedupe("docs")

    log_event(trace, "context_retrieved", {"k": len(ctx)})

    # Provider selection with constraint filtering
    providers = _filter_by_constraints(REGISTRY.get(capability, []))

    if not providers:
        log_event(trace, "routing_error", {"reason": "no_providers"})
        result = finish_trace(trace, {"error": "no providers"})
        return {
            "output": {
                "tldr": "",
                "facts": [],
                "next_action": "noop",
                "actions": [],
                "metrics": {"latency_ms": 0},
                "safety": {"pii": False}
            },
            "trace": result
        }

    primary = choose_arm(capability, providers)
    log_event(trace, "provider_selected", {
        "provider": primary["name"],
        "capability": capability
    })

    # Shadow execution decision
    shadow = None
    shadow_percent = POLICY["routing"].get(capability, {}).get("shadow_percent", 0.0)
    if len(providers) > 1 and random.random() < shadow_percent:
        shadow = next((p for p in providers if p["name"] != primary["name"]), None)
        if shadow:
            log_event(trace, "shadow_enabled", {"shadow_provider": shadow["name"]})

    # Build capability input
    cap_in: CapabilityInput = {
        "capability": capability,
        "record": record,
        "context": ctx,
        "params": params,
        "meta": {"policy_version": policy_ver, "trace_id": trace["trace_id"]}
    }

    # Execute primary with timeout guard
    weights = POLICY["scorecard_weights"]
    max_lat = POLICY["constraints"].get("max_latency_ms", 15000) or 15000

    t0 = time.time()
    try:
        with time_limit(max_lat):
            primary_fn = load_callable(primary["entry"])
            out_p: CapabilityOutput = primary_fn(cap_in)
    except TimeoutError:
        log_event(trace, "primary_timeout", {"provider": primary["name"], "max_ms": max_lat})
        out_p = {
            "tldr": "",
            "facts": [],
            "next_action": "timeout",
            "actions": [],
            "metrics": {"latency_ms": max_lat + 1, "timeout": True},
            "safety": {"pii": False}
        }

    # Ensure metrics exist
    if "metrics" not in out_p:
        out_p["metrics"] = {}
    if "latency_ms" not in out_p["metrics"]:
        out_p["metrics"]["latency_ms"] = int(1000 * (time.time() - t0))

    # Score primary
    score_p, subs_p = _composite_score(out_p, weights)
    log_event(trace, "primary_result", {
        "provider": primary["name"],
        "score": score_p,
        "subscores": subs_p
    })

    # Execute shadow (if enabled)
    score_s = -1.0
    subs_s = {}
    out_s = None

    if shadow:
        t1 = time.time()
        try:
            with time_limit(max_lat):
                shadow_fn = load_callable(shadow["entry"])
                out_s = shadow_fn(cap_in)
        except TimeoutError:
            log_event(trace, "shadow_timeout", {"provider": shadow["name"], "max_ms": max_lat})
            out_s = {
                "tldr": "",
                "facts": [],
                "next_action": "timeout",
                "actions": [],
                "metrics": {"latency_ms": max_lat + 1, "timeout": True},
                "safety": {"pii": False}
            }

        if "metrics" not in out_s:
            out_s["metrics"] = {}
        if "latency_ms" not in out_s["metrics"]:
            out_s["metrics"]["latency_ms"] = int(1000 * (time.time() - t1))

        score_s, subs_s = _composite_score(out_s, weights)
        log_event(trace, "shadow_result", {
            "provider": shadow["name"],
            "score": score_s,
            "subscores": subs_s
        })

    # Reward learning (primary only)
    min_samples = POLICY["routing"].get(capability, {}).get("min_samples_for_promotion", 5)
    reward(capability, primary["name"], score_p, min_samples)

    # Shadow preference decision
    min_composite = POLICY["thresholds"]["composite_min"]

    if shadow and score_s > score_p and score_s >= min_composite:
        # Shadow performed better AND meets threshold
        log_event(trace, "shadow_preferred", {
            "primary_score": score_p,
            "shadow_score": score_s,
            "action": "switched"
        })
        result = finish_trace(trace, out_s)
        return {"output": out_s, "trace": result}

    # Return primary result
    result = finish_trace(trace, out_p)
    return {"output": out_p, "trace": result}
