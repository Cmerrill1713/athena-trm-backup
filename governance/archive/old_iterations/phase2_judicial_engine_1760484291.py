#!/usr/bin/env python3
# Phase 2 Judicial Enforcement Engine
# Responsibilities: adjudication, graduated response, quarantine, tribunal workflow, reputation updates.

from __future__ import annotations
import time
import json
import hashlib
import enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
from pathlib import Path

POLICY_FILE = Path(__file__).with_name("phase2_tribunal_policies.yaml")
QUAR_FILE   = Path(__file__).with_name("phase2_quarantine_profiles.yaml")
REP_FILE    = Path(__file__).with_name("phase2_reputation_rules.yaml")
EVENT_SCHEMA= Path(__file__).with_name("phase2_event_schema.json")
# Use local directories for development/testing
AUDIT_LOG   = Path("./judicial_audit.log")
STATE_DIR   = Path("./phase2_state")

STATE_DIR.mkdir(parents=True, exist_ok=True)

try:
    import yaml
except Exception:
    raise SystemExit("pip install pyyaml")

class Verdict(enum.Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    TRIBUNAL = "TRIBUNAL"

@dataclass
class Case:
    event: Dict[str, Any]
    severity: float
    confidence: float
    article: str
    classification: str
    actor_id: str
    instance_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class Adjudication:
    verdict: Verdict
    rationale: str
    actions: List[Dict[str, Any]]
    reputation_delta: float = 0.0
    review_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum values."""
        return {
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "actions": self.actions,
            "reputation_delta": self.reputation_delta,
            "review_required": self.review_required
        }

def _sha256(o: Any) -> str:
    s = json.dumps(o, sort_keys=True, default=str).encode()
    return hashlib.sha256(s).hexdigest()

def load_yaml(p: Path) -> Dict[str, Any]:
    with open(p, "r") as f:
        return yaml.safe_load(f) or {}

def load_json(p: Path) -> Dict[str, Any]:
    with open(p, "r") as f:
        return json.load(f)

POLICY = load_yaml(POLICY_FILE)
QUAR   = load_yaml(QUAR_FILE)
REPR   = load_yaml(REP_FILE)
SCHEMA = load_json(EVENT_SCHEMA)

def audit(record: Dict[str, Any]) -> None:
    # Convert enums to values for JSON serialization
    def convert_enums(obj):
        if isinstance(obj, dict):
            return {k: convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(item) for item in obj]
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        else:
            return obj

    record = convert_enums(record)
    record["hash"] = _sha256(record)
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")

def classify(case: Case) -> str:
    # Simple mapping; replace with your actual classifier if needed
    if case.severity >= 0.85 or case.confidence >= 0.9:
        return "CRITICAL"
    if case.severity >= 0.6:
        return "MAJOR"
    if case.severity >= 0.3:
        return "MINOR"
    return "INFO"

def select_response(level: str) -> Tuple[Verdict, str, List[Dict[str, Any]]]:
    pol = POLICY.get("responses", {})
    chosen = pol.get(level, pol.get("DEFAULT", {"verdict":"ALLOW","actions":[]}))
    return Verdict(chosen["verdict"]), chosen.get("rationale","policy"), chosen.get("actions",[])

def apply_quarantine(profile_name: str, case: Case) -> Dict[str, Any]:
    prof = QUAR.get("profiles", {}).get(profile_name, QUAR.get("profiles", {}).get("strict", {}))
    # Persist quarantine state
    qstate = STATE_DIR / f"quarantine_{case.actor_id}.json"
    with open(qstate, "w") as f:
        json.dump({"actor": case.actor_id, "profile": profile_name, "ts": time.time(), "profileSpec": prof}, f)
    return {"quarantine_applied": profile_name, "profile": prof}

def update_reputation(actor_id: str, delta: float) -> float:
    rep_file = STATE_DIR / f"rep_{actor_id}.json"
    current = {"score": REPR.get("defaults", {}).get("baseline", 0.0)}
    if rep_file.exists():
        current = json.loads(rep_file.read_text())
    current["score"] = round(current.get("score", 0.0) + delta, 4)
    rep_file.write_text(json.dumps(current))
    return current["score"]

def tribunal_required(verdict: Verdict, actions: List[Dict[str, Any]]) -> bool:
    return verdict in (Verdict.QUARANTINE, Verdict.TRIBUNAL) or any(a.get("requires_human", False) for a in actions)

def adjudicate(event: Dict[str, Any]) -> Adjudication:
    # Minimal schema check
    missing = [k for k in SCHEMA["required"] if k not in event]
    if missing:
        a = Adjudication(Verdict.BLOCK, f"Schema missing fields: {missing}", actions=[{"block": True}])
        audit({"type":"schema_violation","event":event,"adjudication":a.__dict__})
        return a

    case = Case(
        event=event,
        severity=float(event.get("severity", 0.0)),
        confidence=float(event.get("confidence", 0.0)),
        article=str(event.get("article","I")),
        classification=str(event.get("classification","unknown")),
        actor_id=str(event.get("actor_id","unknown")),
        instance_id=str(event.get("instance_id","local"))
    )
    level = classify(case)
    verdict, rationale, actions = select_response(level)

    # Attach quarantine profiles when needed
    if verdict in (Verdict.QUARANTINE, Verdict.TRIBUNAL):
        qp = POLICY.get("quarantine_policy_map", {}).get(level, "strict")
        qres = apply_quarantine(qp, case)
        actions.append({"quarantine": qres})

    # Reputation
    delta = REPR.get("deltas", {}).get(verdict.value, 0.0)
    new_score = update_reputation(case.actor_id, delta)
    # Human review?
    review = tribunal_required(verdict, actions)

    adj = Adjudication(verdict, rationale, actions, reputation_delta=delta, review_required=review)
    audit({"type":"adjudication","level":level,"event":event,"adjudication":adj.to_dict(),"rep_score":new_score})
    return adj

# Simple CLI for piping events in JSON
if __name__ == "__main__":
    import sys
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(adjudicate(payload).to_dict(), indent=2))
