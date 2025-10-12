"""
Clean Telemetry - Agent-Agnostic Tracing
========================================
Logs traces for every decision with hashes and subscores
"""

import time
import uuid
import hashlib
import json
from typing import Dict, Any


def _hash_obj(obj: Any) -> str:
    """Create short hash of object"""
    json_str = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()[:12]


def start_trace(capability: str, record: Dict, params: Dict, policy_version: str) -> Dict[str, Any]:
    """
    Start a new trace

    Args:
        capability: Capability being executed
        record: Input record
        params: Execution parameters
        policy_version: Policy version

    Returns:
        Trace dictionary
    """
    trace_id = str(uuid.uuid4())

    return {
        "trace_id": trace_id,
        "capability": capability,
        "policy_version": policy_version,
        "started_at": time.time(),
        "input_hash": _hash_obj({"record": record, "params": params}),
        "events": [],
    }


def log_event(trace: Dict, label: str, data: Dict):
    """
    Log an event to trace

    Args:
        trace: Trace dictionary
        label: Event label
        data: Event data
    """
    trace["events"].append({
        "ts": time.time(),
        "label": label,
        "data": data
    })


def finish_trace(trace: Dict, output: Dict) -> Dict:
    """
    Finalize trace with output

    Args:
        trace: Trace dictionary
        output: Capability output

    Returns:
        Completed trace
    """
    trace["ended_at"] = time.time()
    trace["duration_ms"] = int(1000 * (trace["ended_at"] - trace["started_at"]))
    trace["output_hash"] = _hash_obj(output)
    return trace


def export_trace(trace: Dict) -> str:
    """Export trace as JSON string"""
    return json.dumps(trace, indent=2, default=str)
