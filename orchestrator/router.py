"""
Agent-Agnostic Router with Shadow Execution
===========================================
Routes by capability + policy + bandit, completely model-agnostic
"""

import time
import yaml
import random
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


def _composite_score(output: CapabilityOutput, weights: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """
    Calculate composite score from output

    Args:
        output: CapabilityOutput
        weights: Scorecard weights from policy

    Returns:
        (composite_score, subscore_dict)
    """
    # Subscores (crude but explicit; replace with task-specific checks)
    subs = {
        "correctness": 1.0 if output.get("tldr") and output.get("next_action") else 0.5,
        "structure":   1.0 if isinstance(output.get("facts"), list) and isinstance(output.get("actions"), list) else 0.5,
        "safety":      1.0 if not output.get("safety", {}).get("pii", False) else 0.0,
        "latency":     1.0,  # Default, adjusted below
        "acceptance":  0.8,  # Placeholder (bind to user feedback later)
    }

    # Latency penalty
    lat = output.get("metrics", {}).get("latency_ms", 0)
    max_lat = POLICY["constraints"].get("max_latency_ms", 1500)
    if lat > max_lat:
        subs["latency"] = 0.3

    # Weighted composite
    composite = sum(subs[k] * weights[k] for k in weights if k in subs)

    return composite, subs


def run_capability(capability: str, record: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a capability with agent-agnostic routing

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

    # Context preparation (agent-agnostic)
    # Store record for future context retrieval
    record_text = f"{record.get('subject', '')} {record.get('body', '')}"
    upsert("docs", [record_text])

    # Retrieve relevant context
    ctx = search("docs", record.get("subject", ""), k=5)
    dedupe("docs")  # Keep store clean

    log_event(trace, "context_retrieved", {"context_items": len(ctx)})

    # Provider selection (capability pool + bandit)
    providers = REGISTRY.get(capability, [])
    if not providers:
        raise RuntimeError(f"No providers registered for capability: {capability}")

    primary = choose_arm(capability, providers)
    log_event(trace, "provider_selected", {"provider": primary["name"], "capability": capability})

    # Shadow execution (optional)
    shadow = None
    shadow_percent = POLICY["routing"].get(capability, {}).get("shadow_percent", 0.0)
    if random.random() < shadow_percent and len(providers) > 1:
        # Pick a different provider for shadow
        shadow = next((p for p in providers if p["name"] != primary["name"]), None)
        if shadow:
            log_event(trace, "shadow_enabled", {"shadow_provider": shadow["name"]})

    # Build capability input (contract)
    cap_in: CapabilityInput = {
        "capability": capability,
        "record": record,
        "context": ctx,
        "params": params,
        "meta": {"policy_version": policy_ver, "trace_id": trace["trace_id"]}
    }

    # Execute primary
    t0 = time.time()
    primary_fn = load_callable(primary["entry"])
    out_p: CapabilityOutput = primary_fn(cap_in)

    # Ensure metrics exist
    if "metrics" not in out_p:
        out_p["metrics"] = {}
    if "latency_ms" not in out_p["metrics"]:
        out_p["metrics"]["latency_ms"] = int(1000 * (time.time() - t0))

    # Score primary
    weights = POLICY["scorecard_weights"]
    score_p, subs_p = _composite_score(out_p, weights)
    log_event(trace, "primary_result", {
        "provider": primary["name"],
        "score": score_p,
        "subscores": subs_p
    })

    # Execute shadow (if enabled)
    score_s = 0.0
    out_s = None
    if shadow:
        t1 = time.time()
        shadow_fn = load_callable(shadow["entry"])
        out_s: CapabilityOutput = shadow_fn(cap_in)

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

    # Reward learning (primary only - shadow is observation)
    min_samples = POLICY["routing"].get(capability, {}).get("min_samples_for_promotion", 5)
    reward(capability, primary["name"], score_p, min_samples)

    # Threshold gate + shadow preference
    min_composite = POLICY["thresholds"]["composite_min"]

    if score_p < min_composite and shadow and score_s > score_p:
        # Shadow performed better - log but still use primary (safe default)
        # In production, you might switch to shadow here
        log_event(trace, "shadow_preferred", {
            "primary_score": score_p,
            "shadow_score": score_s,
            "action": "logged_only"  # or "switched" if you want to use shadow
        })
        # Optional: Use shadow output instead
        # result = finish_trace(trace, out_s)
        # return {"output": out_s, "trace": result}

    # Return primary result
    result = finish_trace(trace, out_p)
    return {"output": out_p, "trace": result}
