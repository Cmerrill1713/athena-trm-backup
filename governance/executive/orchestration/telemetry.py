"""
Clean Telemetry - Agent-Agnostic Tracing
========================================
Logs traces for every decision with hashes and subscores
"""

import time
import uuid
import hashlib
import json
from typing import Dict, Any, Optional


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


# ============================================
# Optional: SQLite Persistence
# ============================================

import sqlite3
import os

_DB = os.environ.get("TELEMETRY_DB", "./state/telemetry.sqlite")


def _ensure_db():
    """Ensure telemetry database exists"""
    os.makedirs(os.path.dirname(_DB), exist_ok=True)
    with sqlite3.connect(_DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS traces(
            trace_id TEXT PRIMARY KEY,
            capability TEXT,
            policy_version TEXT,
            started_at REAL,
            ended_at REAL,
            duration_ms INTEGER,
            input_hash TEXT,
            output_hash TEXT,
            raw_json TEXT
        )""")
        c.commit()


def persist_trace(trace: Dict):
    """
    Persist trace to SQLite for queryable history

    Args:
        trace: Completed trace dictionary
    """
    _ensure_db()

    with sqlite3.connect(_DB) as c:
        c.execute("""INSERT OR REPLACE INTO traces
            (trace_id, capability, policy_version, started_at, ended_at,
             duration_ms, input_hash, output_hash, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                trace["trace_id"],
                trace["capability"],
                trace["policy_version"],
                trace["started_at"],
                trace.get("ended_at"),
                trace.get("duration_ms"),
                trace["input_hash"],
                trace.get("output_hash"),
                json.dumps(trace, default=str)
            )
        )
        c.commit()


def query_traces(capability: str = None, limit: int = 100) -> list:
    """
    Query traces from SQLite

    Args:
        capability: Optional capability filter
        limit: Max results

    Returns:
        List of trace dicts
    """
    _ensure_db()

    with sqlite3.connect(_DB) as c:
        c.row_factory = sqlite3.Row

        if capability:
            cursor = c.execute(
                "SELECT * FROM traces WHERE capability = ? ORDER BY started_at DESC LIMIT ?",
                (capability, limit)
            )
        else:
            cursor = c.execute(
                "SELECT * FROM traces ORDER BY started_at DESC LIMIT ?",
                (limit,)
            )

        return [dict(row) for row in cursor.fetchall()]


def get_trace_by_id(trace_id: str) -> Optional[dict]:
    """
    Get a specific trace by ID

    Args:
        trace_id: Trace identifier

    Returns:
        Trace dict or None if not found
    """
    _ensure_db()

    with sqlite3.connect(_DB) as c:
        c.row_factory = sqlite3.Row
        cursor = c.execute(
            "SELECT * FROM traces WHERE trace_id = ?",
            (trace_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
