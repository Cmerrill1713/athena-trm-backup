#!/usr/bin/env python3
"""
DGM Orchestrator - Executive Layer
Orchestrates Darwin Gödel Machine within Athena Governance System.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter
from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DGMOrchestrator:
    """
    Executive orchestrator for DGM self-improvement cycles.
    Coordinates between DGM evolution and governance systems.
    """
    
    def __init__(self, config_path: str = "governance/research/dgm/config/dgm_config.yaml"):
        self.adapter = DGMGovernanceAdapter(config_path)
        self.validator = DGMVerdictValidator()
        self.generation = 0
        self.failures = 0
        self.max_failures = 5
        
    async def run_evolution_cycle(self) -> Dict:
        """
        Run single evolution cycle with full governance integration.
        
        Returns:
            Cycle results with verdict and metrics
        """
        self.generation += 1
        logger.info(f"=== Generation {self.generation} ===")
        
        # Step 1: Select parent agent from archive
        parent_agent = self._select_parent_agent()
        
        # Step 2: Generate offspring (mutated/improved version)
        # In practice, this would call DGM's self_improve_step.py
        offspring_code = await self._generate_offspring(parent_agent)
        
        # Step 3: Constitutional compliance check
        compliance = await self.adapter.check_constitutional_compliance(offspring_code)
        
        if not compliance['compliant']:
            logger.warning(f"Generation {self.generation}: Constitutional violation")
            self.failures += 1
            return {
                "generation": self.generation,
                "status": "REJECTED",
                "reason": "constitutional_violation",
                "compliance": compliance
            }
        
        # Step 4: Run benchmarks
        benchmark_results = await self._run_benchmarks(offspring_code)
        
        # Step 5: Request judicial verdict
        verdict = self.validator.evaluate_agent_modification(
            agent_id=f"dgm_gen_{self.generation}",
            old_code=parent_agent.get('code', ''),
            new_code=offspring_code,
            benchmark_results=benchmark_results
        )
        
        # Step 6: Execute verdict actions
        result = await self._execute_verdict(
            verdict=verdict,
            agent_code=offspring_code,
            benchmark_results=benchmark_results
        )
        
        # Step 7: Update archive if approved
        if verdict['verdict'] in ['APPROVE', 'CANARY_DEPLOY']:
            self.adapter.save_agent_to_archive(
                agent_id=verdict['agent_id'],
                agent_code=offspring_code,
                metadata={
                    'generation': self.generation,
                    'parent': parent_agent.get('id'),
                    'performance': benchmark_results['new_performance'],
                    'verdict': verdict,
                    'constitutional_check': compliance
                }
            )
            self.failures = 0  # Reset failure counter
        else:
            self.failures += 1
        
        return result
    
    def _select_parent_agent(self) -> Dict:
        """Select parent agent from archive using quality-diversity."""
        agents = self.adapter.load_archive()
        
        if not agents:
            # Return seed agent
            return {
                "id": "seed_agent",
                "code": self._get_seed_agent_code(),
                "metadata": {"performance": 0.20}
            }
        
        # Quality-diversity selection (simplified)
        # In practice, use novelty + performance
        top_performers = self.adapter.get_top_performers(n=10)
        
        # Randomly select from top performers for diversity
        import random
        return random.choice(top_performers) if top_performers else agents[0]
    
    def _get_seed_agent_code(self) -> str:
        """Get initial seed agent code."""
        # Path to DGM's initial coding agent
        seed_path = Path("governance/research/dgm-upstream/coding_agent.py")
        if seed_path.exists():
            return seed_path.read_text()
        return "# Seed agent placeholder"
    
    async def _generate_offspring(self, parent: Dict) -> str:
        """
        Generate improved offspring from parent agent.
        Uses foundation model to mutate/improve code.
        """
        # In practice, this would use DGM's self_improve_step.py
        # with foundation model calls
        logger.info(f"Generating offspring from parent {parent.get('id')}")
        
        # Mock for now - returns parent code with comment
        parent_code = parent.get('code', '')
        offspring = f"""# Generation {self.generation} - Evolved Agent
# Parent: {parent.get('id')}

{parent_code}

# Improvement: Enhanced error handling
"""
        return offspring
    
    async def _run_benchmarks(self, agent_code: str) -> Dict:
        """
        Run agent on configured benchmarks.
        Returns performance metrics.
        """
        logger.info("Running benchmarks...")
        
        # Mock benchmark results
        # In practice, would run SWE-bench, Polyglot, etc.
        import random
        baseline = 0.30
        variation = random.uniform(-0.05, 0.15)
        
        return {
            "baseline_performance": baseline,
            "new_performance": baseline + variation,
            "consistency": random.uniform(0.7, 0.95),
            "benchmark": "swe-bench-lite",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_verdict(
        self,
        verdict: Dict,
        agent_code: str,
        benchmark_results: Dict
    ) -> Dict:
        """Execute actions based on verdict."""
        actions = verdict.get('actions', [])
        
        logger.info(f"Executing verdict: {verdict['verdict']}")
        logger.info(f"Actions: {', '.join(actions)}")
        
        result = {
            "generation": self.generation,
            "verdict": verdict['verdict'],
            "actions_executed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for action in actions:
            if action == "CANARY_5PCT":
                logger.info("→ Routing to canary deployment (5% traffic)")
                result['actions_executed'].append("canary_deployed")
                
            elif action == "DEPLOY":
                logger.info("→ Deploying to production")
                result['actions_executed'].append("deployed")
                
            elif action == "ROLLBACK":
                logger.info("→ Rolling back to previous agent")
                result['actions_executed'].append("rolled_back")
                
            elif action == "ARCHIVE":
                logger.info("→ Archiving successful agent")
                result['actions_executed'].append("archived")
                
            elif action == "MONITOR":
                logger.info("→ Enhanced monitoring enabled")
                result['actions_executed'].append("monitoring_enabled")
                
            elif action == "ALERT_HUMAN":
                logger.warning("→ Alerting human operators")
                result['actions_executed'].append("human_alerted")
                
            elif action == "HUMAN_REVIEW":
                logger.warning("→ Queuing for human review")
                result['actions_executed'].append("review_queued")
                
            elif action == "HARD_BLOCK":
                logger.error("→ HARD BLOCK - Stopping evolution")
                result['actions_executed'].append("hard_blocked")
                break
        
        return result
    
    async def run_continuous_evolution(self, max_generations: int = 100):
        """
        Run continuous evolution with governance oversight.
        
        Args:
            max_generations: Maximum number of generations to run
        """
        logger.info(f"Starting DGM continuous evolution (max {max_generations} generations)")
        
        results = []
        
        while self.generation < max_generations:
            # Circuit breaker: stop if too many failures
            if self.failures >= self.max_failures:
                logger.error(
                    f"Circuit breaker triggered: {self.failures} consecutive failures. "
                    "Stopping evolution."
                )
                break
            
            try:
                cycle_result = await self.run_evolution_cycle()
                results.append(cycle_result)
                
                # Log progress
                if self.generation % 10 == 0:
                    self._log_progress(results)
                
                # Sleep between generations
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Generation {self.generation} failed: {e}")
                self.failures += 1
                continue
        
        # Final report
        self._generate_final_report(results)
        
        return results
    
    def _log_progress(self, results: List[Dict]):
        """Log evolution progress."""
        approved = sum(1 for r in results if r.get('verdict') == 'APPROVE')
        canary = sum(1 for r in results if r.get('verdict') == 'CANARY_DEPLOY')
        rejected = sum(1 for r in results if r.get('verdict') == 'REJECT')
        
        logger.info(f"""
=== Progress Report: Generation {self.generation} ===
Approved: {approved}
Canary: {canary}
Rejected: {rejected}
Approval Rate: {(approved + canary) / len(results) * 100:.1f}%
Consecutive Failures: {self.failures}
""")
    
    def _generate_final_report(self, results: List[Dict]):
        """Generate final evolution report."""
        report_path = Path(f"governance/research/dgm/results/evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        stats = self.validator.get_approval_rate()
        
        report = {
            "total_generations": self.generation,
            "results": results,
            "statistics": stats,
            "final_archive_size": len(self.adapter.load_archive()),
            "top_performers": self.adapter.get_top_performers(n=5),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Final report saved to {report_path}")


async def main():
    """Main entry point for DGM orchestration."""
    orchestrator = DGMOrchestrator()
    
    # Run limited evolution for testing
    results = await orchestrator.run_continuous_evolution(max_generations=5)
    
    print(f"\nEvolution complete. {len(results)} generations processed.")


if __name__ == "__main__":
    asyncio.run(main())

