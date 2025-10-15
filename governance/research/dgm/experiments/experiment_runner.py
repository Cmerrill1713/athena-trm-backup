#!/usr/bin/env python3
"""
DGM Experiment Runner
Framework for running controlled DGM evolution experiments.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yaml

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from governance.executive.orchestration.dgm_orchestrator import DGMOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DGMExperiment:
    """Controlled DGM evolution experiment with governance oversight."""
    
    def __init__(self, experiment_config: Dict):
        self.config = experiment_config
        self.experiment_id = experiment_config['experiment_id']
        self.results_dir = Path(f"governance/research/dgm/results/{self.experiment_id}")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    async def run(self) -> Dict:
        """Execute experiment with full tracking."""
        logger.info(f"Starting experiment: {self.experiment_id}")
        logger.info(f"Description: {self.config['description']}")
        
        start_time = datetime.now()
        
        # Initialize orchestrator
        orchestrator = DGMOrchestrator(
            config_path=self.config.get('dgm_config', 'governance/research/dgm/config/dgm_config.yaml')
        )
        
        # Run evolution cycles
        max_generations = self.config.get('max_generations', 20)
        results = await orchestrator.run_continuous_evolution(max_generations=max_generations)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        analysis = self._analyze_results(results)
        
        # Generate report
        report = {
            "experiment_id": self.experiment_id,
            "config": self.config,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "results": results,
            "analysis": analysis,
            "status": "COMPLETED"
        }
        
        # Save report
        report_path = self.results_dir / "experiment_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Experiment completed. Report saved to {report_path}")
        
        return report
    
    def _analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze experiment results."""
        total = len(results)
        
        if total == 0:
            return {"error": "No results to analyze"}
        
        approved = sum(1 for r in results if r.get('verdict') == 'APPROVE')
        canary = sum(1 for r in results if r.get('verdict') == 'CANARY_DEPLOY')
        rejected = sum(1 for r in results if r.get('verdict') == 'REJECT')
        
        # Performance trend
        performances = [
            r.get('benchmark_results', {}).get('new_performance', 0)
            for r in results
            if 'benchmark_results' in r
        ]
        
        avg_performance = sum(performances) / len(performances) if performances else 0
        max_performance = max(performances) if performances else 0
        min_performance = min(performances) if performances else 0
        
        return {
            "total_generations": total,
            "verdicts": {
                "approved": approved,
                "canary": canary,
                "rejected": rejected,
                "approval_rate": (approved + canary) / total if total > 0 else 0
            },
            "performance": {
                "average": avg_performance,
                "max": max_performance,
                "min": min_performance,
                "improvement": max_performance - min_performance if performances else 0
            },
            "efficiency": {
                "successful_mutations": approved + canary,
                "mutation_rate": (approved + canary) / total if total > 0 else 0
            }
        }


class ExperimentManager:
    """Manages multiple DGM experiments."""
    
    def __init__(self, experiments_dir: str = "governance/research/dgm/experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
    
    def load_experiment_config(self, config_file: str) -> Dict:
        """Load experiment configuration from YAML."""
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    async def run_experiment(self, config_file: str) -> Dict:
        """Run single experiment from config file."""
        config = self.load_experiment_config(config_file)
        experiment = DGMExperiment(config)
        return await experiment.run()
    
    async def run_batch_experiments(self, config_files: List[str]) -> List[Dict]:
        """Run multiple experiments in sequence."""
        results = []
        
        for config_file in config_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running experiment from: {config_file}")
            logger.info(f"{'='*60}\n")
            
            try:
                result = await self.run_experiment(config_file)
                results.append(result)
            except Exception as e:
                logger.error(f"Experiment failed: {e}")
                results.append({
                    "config_file": config_file,
                    "status": "FAILED",
                    "error": str(e)
                })
        
        # Generate batch summary
        self._generate_batch_summary(results)
        
        return results
    
    def _generate_batch_summary(self, results: List[Dict]):
        """Generate summary report for batch experiments."""
        summary_path = Path("governance/research/dgm/results/batch_summary.json")
        
        summary = {
            "total_experiments": len(results),
            "completed": sum(1 for r in results if r.get('status') == 'COMPLETED'),
            "failed": sum(1 for r in results if r.get('status') == 'FAILED'),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\nBatch summary saved to {summary_path}")


async def main():
    """CLI entry point for running experiments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run DGM experiments")
    parser.add_argument('config', help="Path to experiment config YAML")
    parser.add_argument('--batch', action='store_true', help="Run as batch (config is list)")
    
    args = parser.parse_args()
    
    manager = ExperimentManager()
    
    if args.batch:
        # Load batch config
        with open(args.config, 'r') as f:
            batch_config = yaml.safe_load(f)
        config_files = batch_config.get('experiments', [])
        await manager.run_batch_experiments(config_files)
    else:
        # Run single experiment
        await manager.run_experiment(args.config)


if __name__ == "__main__":
    asyncio.run(main())

