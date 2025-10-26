# SPDX-License-Identifier: MIT
"""
Adaptive TRM Policy Engine - Self-Learning Recursive Reasoning
Learns when to invoke TRM, how deep to recurse, and context budget sizing.
"""
from __future__ import annotations
import math
import json
import time
import os
import threading
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Optional

try:
    import numpy as np
except Exception:
    np = None  # optional; fall back to naive stats

# --- Metrics (lazy; replace with your metrics emitter if you have one) ---
class _Counter:
    def __init__(self):
        self.c = defaultdict(float)
    
    def inc(self, **labels):
        self.c[tuple(sorted(labels.items()))] += 1.0
    
    def get(self):
        return dict(self.c)

TRM_POLICY_PREDICTIONS = _Counter()
TRM_POLICY_OUTCOMES    = _Counter()

@dataclass
class PolicyConfig:
    """Configuration for adaptive TRM policy"""
    # cutoffs can be tuned via env vars
    trigger_threshold: float = float(os.getenv("TRM_TRIGGER_THRESH", "0.60"))
    min_cycles: int = int(os.getenv("TRM_MIN_CYCLES", "4"))
    max_cycles: int = int(os.getenv("TRM_MAX_CYCLES", "24"))
    retrain_every: int = int(os.getenv("TRM_RETRAIN_EVERY", "250"))
    history_size: int = int(os.getenv("TRM_HISTORY_SIZE", "5000"))

class AdaptiveTRMPolicy:
    """
    Zero-dependency, in-process policy that learns when to call TRM
    and how deep to recurse. Starts with heuristics, improves online.
    """
    def __init__(self, cfg: Optional[PolicyConfig] = None):
        self.cfg = cfg or PolicyConfig()
        self.history: deque[Dict[str, Any]] = deque(maxlen=self.cfg.history_size)
        self._lock = threading.Lock()
        
        # "model" is a simple weighted scorer to avoid sklearn dependency.
        self.weights = {
            "objective_len":  0.15,
            "tool_count_neg": 0.12,
            "rag_hits":       0.22,
            "uncertainty":    0.28,  # your existing planner confidence ∈ [0,1], mapped to (1-conf)
            "novelty":        0.23,  # cache-miss / unfamiliar objective bucket
        }
        self.bias = -0.35

    # ----- feature engineering -----
    def _features(self, objective: str, signals: Dict[str, Any]) -> Dict[str, float]:
        obj_len = min(len(objective), 1500)
        tool_count = float(signals.get("tool_count", 0))
        rag_hits = float(signals.get("rag_hits", 0))
        conf = float(signals.get("planner_confidence", 0.0))
        novelty = float(signals.get("novelty_score", 0.0))  # 0..1 (0 known, 1 new)
        return {
            "objective_len": obj_len / 1500.0,     # 0..1
            "tool_count_neg": 1.0 - min(tool_count, 8.0) / 8.0,
            "rag_hits": min(rag_hits, 10.0) / 10.0,
            "uncertainty": 1.0 - conf,            # 0..1
            "novelty": min(novelty, 1.0),
        }

    def _score(self, x: Dict[str, float]) -> float:
        """Logistic score for trigger probability"""
        z = self.bias + sum(self.weights[k] * x.get(k, 0.0) for k in self.weights)
        return 1.0 / (1.0 + math.exp(-z))

    # ----- public API -----
    def should_invoke(self, objective: str, signals: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Predict if TRM will improve outcome.
        Returns: (invoke: bool, confidence: float)
        """
        x = self._features(objective, signals)
        p = self._score(x)
        TRM_POLICY_PREDICTIONS.inc(result="pred", bucket="trigger")
        return (p >= self.cfg.trigger_threshold, p)

    def allocate_cycles(self, mode: str, signals: Dict[str, Any]) -> int:
        """
        Adaptive cycle allocation based on complexity + historical ROI.
        Returns: optimal cycle count [min_cycles, max_cycles]
        """
        # heuristic + learned nudges
        base = {"classify": 6, "deliberate": 12, "critique": 8}.get(mode, 8)
        conf = float(signals.get("planner_confidence", 0.0))
        rag_hits = float(signals.get("rag_hits", 0))
        
        # push deeper for low confidence / many hits; shallower for high confidence / few hits
        delta = 0
        if conf < 0.4:
            delta += 4
        if conf > 0.75:
            delta -= 3
        if rag_hits >= 5:
            delta += 2
        if rag_hits == 0:
            delta -= 2
        
        # mild learned nudge: if recent history shows diminishing returns, trim 2 cycles
        if self._diminishing_returns(mode):
            delta -= 2
        
        return int(max(self.cfg.min_cycles, min(self.cfg.max_cycles, base + delta)))

    def budget_context_chars(self, complexity: str, mode: str, signals: Dict[str, Any]) -> int:
        """
        Dynamic RAG context sizing based on TRM's actual usage.
        Returns: context character budget
        """
        # start with your static budgets, adapt down if "waste" observed
        base = {"low": 1000, "medium": 3000, "high": 5000}.get(complexity, 3000)
        waste_ratio = self._recent_waste_ratio(complexity, mode)  # 0..1
        
        # if we've been wasting >40% context recently, shrink by 20%
        if waste_ratio > 0.4:
            base = int(base * 0.8)
        
        # if TRM cycles deep + low confidence, expand a bit
        if float(signals.get("planner_confidence", 0.0)) < 0.3:
            base = int(base * 1.15)
        
        return max(600, min(8000, base))

    def record_outcome(
        self, *, task_id: str, used_trm: bool, success: bool,
        wall_time_ms: float, tool_errors: int, mode: str,
        cycles: int, context_chars: int, context_used_chars: int
    ) -> None:
        """
        Track outcome for continuous learning.
        Called after each task completion.
        """
        with self._lock:
            self.history.append({
                "t": time.time(),
                "task_id": task_id,
                "used_trm": used_trm,
                "success": bool(success),
                "wall_ms": float(wall_time_ms),
                "tool_err": int(tool_errors),
                "mode": mode,
                "cycles": int(cycles),
                "ctx": int(context_chars),
                "ctx_used": int(context_used_chars),
            })
            TRM_POLICY_OUTCOMES.inc(mode=mode, success=str(success).lower())
            
            # retrain periodically
            if len(self.history) % self.cfg.retrain_every == 0:
                self._retrain_async()

    # ----- simple "online learning" stubs -----
    def _recent_waste_ratio(self, complexity: str, mode: str) -> float:
        """% unused context over last 200 items of this mode"""
        items = [h for h in reversed(self.history) if h["mode"] == mode]
        items = items[:200]
        if not items:
            return 0.0
        used = sum(min(h["ctx_used"], h["ctx"]) for h in items)
        total = sum(h["ctx"] for h in items)
        return 0.0 if total == 0 else max(0.0, 1.0 - (used / total))

    def _diminishing_returns(self, mode: str) -> bool:
        """
        If success rate difference between high vs mid cycles is small, returns True
        (signals we should reduce cycles)
        """
        items = [h for h in self.history if h["mode"] == mode]
        if len(items) < 60:
            return False
        hi = [h["success"] for h in items if h["cycles"] >= 16]
        mid = [h["success"] for h in items if 8 <= h["cycles"] < 16]
        if not hi or not mid:
            return False
        return (sum(hi) / len(hi)) - (sum(mid) / len(mid)) < 0.03

    def _retrain_async(self):
        """
        Place-holder hook for background retraining.
        For now, adjusts bias slightly based on recent accuracy drift.
        """
        def _job():
            items = list(self.history)[-400:]
            if not items:
                return
            
            # crude: if TRM used → success rate improved, nudge bias down (more triggers)
            used = [h for h in items if h["used_trm"]]
            not_used = [h for h in items if not h["used_trm"]]
            
            if used and not_used:
                success_with = sum(h["success"] for h in used) / len(used)
                success_without = sum(h["success"] for h in not_used) / len(not_used)
                d = success_with - success_without
                
                # adjust bias: positive d → TRM helps → lower threshold (more invocations)
                adjustment = (0.05 * (1 if d > 0 else -1)) * min(1.0, abs(d))
                self.bias += adjustment
                
                print(f"🧠 TRM policy retrained: bias={self.bias:.3f}, Δ success={d:.3f}")
        
        threading.Thread(target=_job, daemon=True).start()

    def get_stats(self) -> Dict[str, Any]:
        """Return current policy statistics"""
        with self._lock:
            if not self.history:
                return {"status": "no_data"}
            
            recent = list(self.history)[-200:]
            used_trm = [h for h in recent if h["used_trm"]]
            not_used = [h for h in recent if not h["used_trm"]]
            
            return {
                "total_decisions": len(self.history),
                "recent_invocations": len(used_trm),
                "recent_skips": len(not_used),
                "success_rate_with_trm": sum(h["success"] for h in used_trm) / len(used_trm) if used_trm else 0.0,
                "success_rate_without_trm": sum(h["success"] for h in not_used) / len(not_used) if not_used else 0.0,
                "avg_cycles": sum(h["cycles"] for h in used_trm) / len(used_trm) if used_trm else 0.0,
                "current_bias": self.bias,
                "weights": self.weights,
            }

# Singleton instance
policy = AdaptiveTRMPolicy()

