"""
DGM Verdict Validator
Judicial evaluation system for Darwin Gödel Machine agent modifications.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DGMVerdictValidator:
    """
    Validates DGM agent modifications through the judicial verdict system.
    Ensures self-improving agents meet governance standards.
    """
    
    def __init__(self):
        self.verdicts_log = Path("governance/judicial/evaluation/dgm_verdicts.jsonl")
        self.verdicts_log.parent.mkdir(parents=True, exist_ok=True)
    
    def evaluate_agent_modification(
        self,
        agent_id: str,
        old_code: str,
        new_code: str,
        benchmark_results: Dict
    ) -> Dict:
        """
        Evaluate proposed agent modification.
        
        Args:
            agent_id: Unique agent identifier
            old_code: Previous agent code
            new_code: Proposed modified code
            benchmark_results: Performance on benchmarks
            
        Returns:
            Verdict dictionary
        """
        # Calculate performance delta
        old_perf = benchmark_results.get('baseline_performance', 0.0)
        new_perf = benchmark_results.get('new_performance', 0.0)
        delta = new_perf - old_perf
        
        # Calculate code complexity delta
        complexity_delta = len(new_code) - len(old_code)
        
        # Safety checks
        safety_violations = self._check_safety_violations(new_code)
        
        # Determine verdict
        verdict = self._render_verdict(
            agent_id=agent_id,
            performance_delta=delta,
            complexity_delta=complexity_delta,
            safety_violations=safety_violations,
            benchmark_results=benchmark_results
        )
        
        # Log verdict
        self._log_verdict(verdict)
        
        return verdict
    
    def _check_safety_violations(self, code: str) -> List[Dict]:
        """Check for safety violations in agent code."""
        violations = []
        
        dangerous_patterns = {
            "os.remove": "File deletion",
            "os.rmdir": "Directory deletion",  
            "shutil.rmtree": "Recursive deletion",
            "subprocess.Popen": "Subprocess execution",
            "pickle.load": "Arbitrary code execution via pickle",
            "eval(": "Dynamic code evaluation",
            "exec(": "Dynamic code execution",
            "__import__": "Dynamic imports",
            "compile(": "Code compilation",
        }
        
        for pattern, description in dangerous_patterns.items():
            if pattern in code:
                violations.append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "HIGH"
                })
        
        return violations
    
    def _render_verdict(
        self,
        agent_id: str,
        performance_delta: float,
        complexity_delta: int,
        safety_violations: List[Dict],
        benchmark_results: Dict
    ) -> Dict:
        """Render final verdict on agent modification."""
        
        # Automatic rejection criteria
        if safety_violations:
            return {
                "agent_id": agent_id,
                "verdict": "REJECT",
                "confidence": 0.95,
                "ece_estimate": 0.05,
                "reason": "Safety violations detected",
                "violations": safety_violations,
                "actions": ["BLOCK", "ALERT_HUMAN"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Performance regression
        if performance_delta < -0.05:  # >5% regression
            return {
                "agent_id": agent_id,
                "verdict": "REJECT",
                "confidence": 0.85,
                "ece_estimate": 0.15,
                "reason": f"Performance regression of {performance_delta:.2%}",
                "actions": ["ROLLBACK"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Significant code bloat without performance gain
        if complexity_delta > 5000 and performance_delta < 0.02:
            return {
                "agent_id": agent_id,
                "verdict": "REVIEW_REQUIRED",
                "confidence": 0.6,
                "ece_estimate": 0.4,
                "reason": "Significant complexity increase without sufficient performance gain",
                "actions": ["HUMAN_REVIEW"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Moderate improvement - canary deployment
        if 0.02 <= performance_delta < 0.10:
            return {
                "agent_id": agent_id,
                "verdict": "CANARY_DEPLOY",
                "confidence": 0.75,
                "ece_estimate": 0.75,
                "reason": f"Moderate improvement of {performance_delta:.2%}",
                "actions": ["CANARY_5PCT", "MONITOR"],
                "benchmark_results": benchmark_results,
                "timestamp": datetime.now().isoformat()
            }
        
        # Strong improvement - approve with monitoring
        if performance_delta >= 0.10:
            return {
                "agent_id": agent_id,
                "verdict": "APPROVE",
                "confidence": 0.90,
                "ece_estimate": 0.90,
                "reason": f"Strong improvement of {performance_delta:.2%}",
                "actions": ["DEPLOY", "MONITOR", "ARCHIVE"],
                "benchmark_results": benchmark_results,
                "timestamp": datetime.now().isoformat()
            }
        
        # Minor or no change - neutral
        return {
            "agent_id": agent_id,
            "verdict": "NEUTRAL",
            "confidence": 0.70,
            "ece_estimate": 0.70,
            "reason": f"Minor change, delta: {performance_delta:.2%}",
            "actions": ["MONITOR"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_verdict(self, verdict: Dict) -> None:
        """Log verdict to JSONL file."""
        with open(self.verdicts_log, 'a') as f:
            f.write(json.dumps(verdict) + '\n')
        
        logger.info(
            f"Verdict for {verdict['agent_id']}: {verdict['verdict']} "
            f"(confidence: {verdict['confidence']:.2f})"
        )
    
    def get_verdict_history(self, limit: int = 100) -> List[Dict]:
        """Retrieve recent verdict history."""
        if not self.verdicts_log.exists():
            return []
        
        verdicts = []
        with open(self.verdicts_log, 'r') as f:
            for line in f:
                verdicts.append(json.loads(line))
        
        return verdicts[-limit:]
    
    def get_approval_rate(self) -> Dict[str, float]:
        """Calculate approval rate statistics."""
        verdicts = self.get_verdict_history()
        
        if not verdicts:
            return {"total": 0, "approved": 0, "rate": 0.0}
        
        total = len(verdicts)
        approved = sum(1 for v in verdicts if v['verdict'] in ['APPROVE', 'CANARY_DEPLOY'])
        
        return {
            "total": total,
            "approved": approved,
            "rejected": total - approved,
            "approval_rate": approved / total if total > 0 else 0.0
        }


# CLI for testing
if __name__ == "__main__":
    validator = DGMVerdictValidator()
    
    # Test verdict
    test_verdict = validator.evaluate_agent_modification(
        agent_id="test_001",
        old_code="def solve(): pass",
        new_code="def solve(): return improved_solution()",
        benchmark_results={
            "baseline_performance": 0.30,
            "new_performance": 0.38,
            "consistency": 0.85
        }
    )
    
    print(json.dumps(test_verdict, indent=2))
    
    # Show stats
    stats = validator.get_approval_rate()
    print(f"\nApproval Rate: {stats['approval_rate']:.1%}")

