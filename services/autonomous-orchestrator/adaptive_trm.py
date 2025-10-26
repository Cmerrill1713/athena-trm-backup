"""
Adaptive TRM Reasoning
Learn when to use deeper TRM reasoning vs fast LLM
"""
import json
import random
import time
from pathlib import Path
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class AdaptiveTRMDecider:
    def __init__(self, policy_path: str = "state/trm/policy.json"):
        self.policy_path = Path(policy_path)
        self.policy = self.load_policy()
        self.history = []
        logger.info(f"🧠 Adaptive TRM initialized (trigger_prob={self.policy['trigger_probability']:.2%})")
    
    def load_policy(self) -> Dict:
        """Load or create policy"""
        if self.policy_path.exists():
            try:
                return json.loads(self.policy_path.read_text())
            except:
                logger.warning("Failed to load policy, using defaults")
        
        # Default policy
        return {
            "trigger_probability": 0.3,
            "min_complexity_score": 0.5,
            "success_with_trm": 0,
            "success_without_trm": 0,
            "total_decisions": 0,
            "trm_avg_latency_ms": 0,
            "llm_avg_latency_ms": 0
        }
    
    def save_policy(self):
        """Persist learned policy"""
        try:
            self.policy_path.parent.mkdir(parents=True, exist_ok=True)
            self.policy_path.write_text(json.dumps(self.policy, indent=2))
            logger.debug("💾 Policy saved")
        except Exception as e:
            logger.error(f"Failed to save policy: {e}")
    
    def assess_complexity(self, query: str) -> float:
        """
        Assess query complexity (0-1)
        Higher = needs deeper reasoning
        """
        complexity_indicators = [
            ("solve", 0.3),
            ("calculate", 0.3),
            ("compute", 0.3),
            ("reason", 0.4),
            ("prove", 0.5),
            ("logic", 0.4),
            ("puzzle", 0.5),
            ("sudoku", 0.9),
            ("maze", 0.8),
            ("arc", 0.9),
            ("chess", 0.7),
            ("math", 0.5),
            ("if.*then", 0.4),
            ("because", 0.3),
            ("therefore", 0.4),
        ]
        
        score = 0.2  # Base score
        query_lower = query.lower()
        
        for keyword, weight in complexity_indicators:
            if keyword in query_lower:
                score += weight
        
        # Question marks suggest reasoning
        score += min(query.count("?") * 0.1, 0.3)
        
        # Length complexity
        if len(query.split()) > 20:
            score += 0.2
        
        # Multiple steps
        if any(word in query_lower for word in ["first", "then", "next", "finally"]):
            score += 0.3
        
        return min(score, 1.0)
    
    def should_use_trm(self, query: str) -> Tuple[bool, float, str]:
        """
        Decide if query should use TRM reasoning
        
        Returns: (use_trm, complexity_score, reasoning)
        """
        complexity = self.assess_complexity(query)
        
        # Always use TRM for high complexity
        if complexity > 0.7:
            return (True, complexity, f"High complexity ({complexity:.2f}) → TRM")
        
        # Never use TRM for trivial queries
        if complexity < self.policy["min_complexity_score"]:
            return (False, complexity, f"Low complexity ({complexity:.2f}) → LLM")
        
        # For medium complexity, use learned probability
        use_trm = random.random() < self.policy["trigger_probability"]
        reasoning = f"Medium complexity ({complexity:.2f}), probability={self.policy['trigger_probability']:.2%} → {'TRM' if use_trm else 'LLM'}"
        
        return (use_trm, complexity, reasoning)
    
    def record_outcome(self, 
                       used_trm: bool, 
                       success: bool, 
                       complexity: float,
                       latency_ms: float):
        """
        Record reasoning outcome for learning
        """
        self.policy["total_decisions"] += 1
        
        if used_trm:
            if success:
                self.policy["success_with_trm"] += 1
            # Update TRM latency average
            prev_avg = self.policy["trm_avg_latency_ms"]
            self.policy["trm_avg_latency_ms"] = (prev_avg * 0.9) + (latency_ms * 0.1)
        else:
            if success:
                self.policy["success_without_trm"] += 1
            # Update LLM latency average
            prev_avg = self.policy["llm_avg_latency_ms"]
            self.policy["llm_avg_latency_ms"] = (prev_avg * 0.9) + (latency_ms * 0.1)
        
        # Adapt policy after sufficient data
        if self.policy["total_decisions"] >= 50 and self.policy["total_decisions"] % 10 == 0:
            self._adapt_policy()
        
        # Save updated policy
        self.save_policy()
        
        # Record in history
        self.history.append({
            "used_trm": used_trm,
            "success": success,
            "complexity": complexity,
            "latency_ms": latency_ms,
            "timestamp": time.time()
        })
        
        # Keep history bounded
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
    
    def _adapt_policy(self):
        """
        Adapt trigger probability based on performance
        """
        trm_count = sum(1 for h in self.history if h["used_trm"])
        non_trm_count = sum(1 for h in self.history if not h["used_trm"])
        
        if trm_count == 0 or non_trm_count == 0:
            return
        
        trm_success_rate = self.policy["success_with_trm"] / trm_count
        non_trm_success_rate = self.policy["success_without_trm"] / non_trm_count
        
        # Adjust trigger probability
        if trm_success_rate > non_trm_success_rate + 0.1:
            # TRM is performing better, increase usage
            old_prob = self.policy["trigger_probability"]
            self.policy["trigger_probability"] = min(0.8, old_prob + 0.05)
            logger.info(f"📈 TRM success rate {trm_success_rate:.1%} > LLM {non_trm_success_rate:.1%}")
            logger.info(f"   Increasing TRM usage: {old_prob:.2%} → {self.policy['trigger_probability']:.2%}")
            
        elif trm_success_rate < non_trm_success_rate - 0.1:
            # LLM is performing better, decrease TRM usage
            old_prob = self.policy["trigger_probability"]
            self.policy["trigger_probability"] = max(0.1, old_prob - 0.05)
            logger.info(f"📉 LLM success rate {non_trm_success_rate:.1%} > TRM {trm_success_rate:.1%}")
            logger.info(f"   Decreasing TRM usage: {old_prob:.2%} → {self.policy['trigger_probability']:.2%}")
        
        # Also consider latency in the decision
        if self.policy["trm_avg_latency_ms"] > self.policy["llm_avg_latency_ms"] * 2:
            logger.info(f"⚡ TRM slower than LLM (2x), reducing usage slightly")
            self.policy["trigger_probability"] = max(0.1, self.policy["trigger_probability"] - 0.02)
    
    def get_stats(self) -> Dict:
        """Get learning statistics"""
        trm_count = sum(1 for h in self.history if h["used_trm"])
        return {
            "trigger_probability": self.policy["trigger_probability"],
            "total_decisions": self.policy["total_decisions"],
            "trm_success_rate": self.policy["success_with_trm"] / max(trm_count, 1),
            "llm_success_rate": self.policy["success_without_trm"] / max(len(self.history) - trm_count, 1),
            "trm_avg_latency_ms": self.policy["trm_avg_latency_ms"],
            "llm_avg_latency_ms": self.policy["llm_avg_latency_ms"],
            "recent_history_size": len(self.history)
        }

