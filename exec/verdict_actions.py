# exec/verdict_actions.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ExecState:
    safe_version: str
    current_version: str
    def rollback_to(self, v: str):
        print(f"[exec] ROLLBACK -> {v}")
        self.current_version = v
    def freeze_promotions(self, minutes: int):
        print(f"[exec] freeze promotions {minutes}m")
    def route_to_quarantine(self, percent: int):
        print(f"[exec] QUARANTINE {percent}%")
    def require_human_review(self, on: bool):
        print(f"[exec] human review: {on}")
    def promote_canary_to_prod(self, window: str = "w2"):
        print(f"[exec] PROMOTE canary ({window})")
    def emit_exec_receipt(self, verdict: Dict[str, Any]):
        print(f"[exec] receipt emitted: {verdict.get('task_id','?')}")

def apply_verdict(verdict: Dict[str, Any], state: ExecState):
    v = verdict.get("verdict", "SOFT_FAIL")
    acts = set(verdict.get("actions", []))
    if v == "HARD_FAIL" or "ROLLBACK" in acts:
        state.rollback_to(state.safe_version)
        state.freeze_promotions(minutes=10)
    elif v == "SOFT_FAIL" or "QUARANTINE" in acts:
        state.route_to_quarantine(percent=100)
        state.require_human_review(True)
    elif v == "PASS" or "PROMOTE" in acts:
        state.promote_canary_to_prod(window="w2")
    state.emit_exec_receipt(verdict)
