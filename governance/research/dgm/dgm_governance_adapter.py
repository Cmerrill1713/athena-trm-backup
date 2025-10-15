"""
Darwin Gödel Machine - Governance System Adapter
Integrates DGM self-improvement with Athena's governance framework.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


class DGMGovernanceAdapter:
    """Adapter connecting DGM to Athena Governance System."""
    
    def __init__(self, config_path: str = "governance/research/dgm/config/dgm_config.yaml"):
        self.config = self._load_config(config_path)
        self.archive_path = Path(self.config['dgm']['archive']['storage_path'])
        self.results_path = Path(self.config['dgm']['monitoring']['log_directory'])
        
        # Ensure directories exist
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, path: str) -> Dict:
        """Load DGM configuration."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    async def request_judicial_verdict(self, agent_code: str, performance_metrics: Dict) -> Dict:
        """
        Request verdict from judicial system for proposed agent modification.
        
        Args:
            agent_code: The modified agent code
            performance_metrics: Benchmark results
            
        Returns:
            Verdict dict with {approved: bool, confidence: float, reasoning: str}
        """
        verdict_request = {
            "task_id": f"dgm_agent_{datetime.now().isoformat()}",
            "task_type": "SELF_MODIFICATION",
            "artifact_type": "CODE",
            "code_diff": agent_code,
            "metrics": performance_metrics,
            "safety_constraints": self.config['dgm']['safety']
        }
        
        # Call judicial verdict system
        # In practice, this would call governance/judicial/verdict_engine.py
        logger.info(f"Requesting verdict for agent modification")
        
        # For now, use ECE-based decision
        ece = self._calculate_ece(performance_metrics)
        
        if ece < self.config['dgm']['safety']['human_oversight_threshold']:
            logger.warning(f"ECE {ece:.3f} below threshold, requiring human review")
            return {
                "approved": False,
                "confidence": ece,
                "reasoning": "ECE below human oversight threshold",
                "requires_human_review": True
            }
        
        # Auto-approve if performance improved and ECE is high
        performance_delta = performance_metrics.get('improvement', 0)
        if performance_delta > 0 and ece > 0.7:
            return {
                "approved": True,
                "confidence": ece,
                "reasoning": f"Performance improved by {performance_delta:.2%} with high confidence"
            }
        
        return {
            "approved": False,
            "confidence": ece,
            "reasoning": "Insufficient performance improvement or confidence"
        }
    
    def _calculate_ece(self, metrics: Dict) -> float:
        """Calculate Epistemic Confidence Estimate from metrics."""
        # Simplified ECE based on consistency and performance
        performance = metrics.get('accuracy', 0.5)
        consistency = metrics.get('consistency', 0.5)
        return (performance + consistency) / 2
    
    async def check_constitutional_compliance(self, agent_code: str) -> Dict[str, Any]:
        """
        Check if agent modification complies with constitutional policies.
        
        Args:
            agent_code: Proposed agent code
            
        Returns:
            Compliance report
        """
        violations = []
        
        # Check for forbidden patterns
        forbidden_patterns = [
            "os.system(",
            "subprocess.call(",
            "eval(",
            "exec(",
            "__import__",
            "open(",  # Restrict file access
        ]
        
        for pattern in forbidden_patterns:
            if pattern in agent_code:
                violations.append({
                    "pattern": pattern,
                    "severity": "HIGH",
                    "reason": "Potentially unsafe code execution"
                })
        
        # Check file size (prevent code bloat)
        if len(agent_code) > 50000:  # 50KB limit
            violations.append({
                "pattern": "code_size",
                "severity": "MEDIUM",
                "reason": "Agent code exceeds size limit"
            })
        
        is_compliant = len(violations) == 0
        
        return {
            "compliant": is_compliant,
            "violations": violations,
            "checked_at": datetime.now().isoformat()
        }
    
    def save_agent_to_archive(self, agent_id: str, agent_code: str, metadata: Dict) -> None:
        """Save agent to archive with governance metadata."""
        agent_file = self.archive_path / f"{agent_id}.json"
        
        archive_entry = {
            "id": agent_id,
            "created_at": datetime.now().isoformat(),
            "code": agent_code,
            "metadata": metadata,
            "governance": {
                "verdict": metadata.get('verdict'),
                "constitutional_check": metadata.get('constitutional_check'),
                "ece_estimate": metadata.get('ece', 0.0)
            }
        }
        
        with open(agent_file, 'w') as f:
            json.dump(archive_entry, f, indent=2)
        
        logger.info(f"Saved agent {agent_id} to archive")
    
    def load_archive(self) -> List[Dict]:
        """Load all agents from archive."""
        agents = []
        for agent_file in self.archive_path.glob("*.json"):
            with open(agent_file, 'r') as f:
                agents.append(json.load(f))
        return agents
    
    def get_top_performers(self, n: int = 10) -> List[Dict]:
        """Get top N performing agents from archive."""
        agents = self.load_archive()
        sorted_agents = sorted(
            agents,
            key=lambda x: x['metadata'].get('performance', 0),
            reverse=True
        )
        return sorted_agents[:n]
    
    async def evaluate_with_governance(self, agent_code: str) -> Dict:
        """
        Full governance evaluation pipeline for agent.
        
        Returns:
            Evaluation result with verdict, compliance, and metrics
        """
        # Step 1: Constitutional compliance
        compliance = await self.check_constitutional_compliance(agent_code)
        
        if not compliance['compliant']:
            return {
                "approved": False,
                "stage": "constitutional_check",
                "compliance": compliance
            }
        
        # Step 2: Run benchmarks (mock for now)
        performance_metrics = {
            "accuracy": 0.35,  # Would be actual benchmark results
            "consistency": 0.75,
            "improvement": 0.05
        }
        
        # Step 3: Request judicial verdict
        verdict = await self.request_judicial_verdict(agent_code, performance_metrics)
        
        return {
            "approved": verdict['approved'],
            "stage": "complete",
            "compliance": compliance,
            "verdict": verdict,
            "metrics": performance_metrics
        }


# Example usage for integration
if __name__ == "__main__":
    import asyncio
    
    async def test_integration():
        adapter = DGMGovernanceAdapter()
        
        # Example agent code
        test_agent = """
def solve_task(problem):
    # Improved coding agent
    return solution
"""
        
        result = await adapter.evaluate_with_governance(test_agent)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_integration())

