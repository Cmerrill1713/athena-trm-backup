#!/usr/bin/env python3
"""
End-to-End Integration Workflows
Complete pipelines connecting all Athena subsystems.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowStage:
    """Represents a stage in an integration workflow."""
    
    def __init__(self, name: str, subsystem: str, handler):
        self.name = name
        self.subsystem = subsystem
        self.handler = handler
        self.start_time = None
        self.end_time = None
        self.result = None
        self.status = "pending"
    
    async def execute(self, context: Dict) -> Dict:
        """Execute this workflow stage."""
        self.start_time = datetime.now()
        self.status = "running"
        
        logger.info(f"  ▶ Stage: {self.name} ({self.subsystem})")
        
        try:
            self.result = await self.handler(context)
            self.status = "completed"
            logger.info(f"    ✓ {self.name} completed")
        except Exception as e:
            self.status = "failed"
            self.result = {"error": str(e)}
            logger.error(f"    ✗ {self.name} failed: {e}")
            raise
        finally:
            self.end_time = datetime.now()
        
        return self.result
    
    def get_metrics(self) -> Dict:
        """Get stage metrics."""
        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            "stage": self.name,
            "subsystem": self.subsystem,
            "status": self.status,
            "duration_seconds": duration,
            "result_summary": self._summarize_result()
        }
    
    def _summarize_result(self) -> Dict:
        """Summarize result for metrics."""
        if not self.result:
            return {}
        
        return {
            "has_result": self.result is not None,
            "has_error": "error" in self.result if isinstance(self.result, dict) else False
        }


class IntegratedWorkflow:
    """Base class for integrated workflows."""
    
    def __init__(self, workflow_name: str):
        self.name = workflow_name
        self.stages = []
        self.context = {"workflow_name": workflow_name}
        self.start_time = None
        self.end_time = None
    
    def add_stage(self, stage: WorkflowStage):
        """Add a stage to the workflow."""
        self.stages.append(stage)
    
    async def execute(self, initial_context: Optional[Dict] = None) -> Dict:
        """Execute all workflow stages in sequence."""
        self.start_time = datetime.now()
        
        logger.info(f"🔄 Starting workflow: {self.name}")
        logger.info(f"   Stages: {len(self.stages)}")
        
        if initial_context:
            self.context.update(initial_context)
        
        results = []
        
        for stage in self.stages:
            try:
                stage_result = await stage.execute(self.context)
                
                # Update context with stage results
                self.context[f"{stage.name}_result"] = stage_result
                
                results.append(stage.get_metrics())
                
            except Exception as e:
                logger.error(f"✗ Workflow failed at stage: {stage.name}")
                self.end_time = datetime.now()
                
                return {
                    "workflow": self.name,
                    "status": "failed",
                    "failed_at_stage": stage.name,
                    "error": str(e),
                    "completed_stages": results,
                    "duration": (self.end_time - self.start_time).total_seconds()
                }
        
        self.end_time = datetime.now()
        
        return {
            "workflow": self.name,
            "status": "completed",
            "stages": results,
            "total_duration": (self.end_time - self.start_time).total_seconds(),
            "context": self._sanitize_context(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _sanitize_context(self) -> Dict:
        """Remove large objects from context for logging."""
        sanitized = {}
        for key, value in self.context.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, dict) and len(str(value)) < 1000:
                sanitized[key] = value
            else:
                sanitized[key] = f"<{type(value).__name__}>"
        return sanitized


class FullEvolutionWorkflow(IntegratedWorkflow):
    """
    Complete evolution workflow:
    Research → DGM Evolution → AGI Review → Governance → Canary → Monitor
    """
    
    def __init__(self):
        super().__init__("full_evolution")
        
        # Stage 1: DGM Evolution
        self.add_stage(WorkflowStage(
            "dgm_evolution",
            "dgm",
            self._dgm_evolution_handler
        ))
        
        # Stage 2: AGI Core Review
        self.add_stage(WorkflowStage(
            "agi_review",
            "agi_core",
            self._agi_review_handler
        ))
        
        # Stage 3: Governance Validation
        self.add_stage(WorkflowStage(
            "governance_validation",
            "governance",
            self._governance_handler
        ))
        
        # Stage 4: Canary Deployment
        self.add_stage(WorkflowStage(
            "canary_deployment",
            "deployment",
            self._canary_handler
        ))
        
        # Stage 5: Monitoring
        self.add_stage(WorkflowStage(
            "monitoring_setup",
            "monitoring",
            self._monitoring_handler
        ))
    
    async def _dgm_evolution_handler(self, context: Dict) -> Dict:
        """Handle DGM evolution stage."""
        # Would call DGM orchestrator
        return {
            "agent_id": "dgm_gen_new",
            "generation": 1,
            "performance": 0.35,
            "code": "# Evolved agent code"
        }
    
    async def _agi_review_handler(self, context: Dict) -> Dict:
        """Handle AGI Core review stage."""
        from governance.research.dgm.dgm_agi_bridge import DGMAGIBridge
        
        bridge = DGMAGIBridge()
        
        dgm_result = context.get('dgm_evolution_result', {})
        agent_code = dgm_result.get('code', '')
        
        review = await bridge.review_dgm_agent(agent_code, dgm_result)
        
        return {
            "review": review,
            "consensus": review['consensus']
        }
    
    async def _governance_handler(self, context: Dict) -> Dict:
        """Handle governance validation stage."""
        from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator
        
        validator = DGMVerdictValidator()
        
        dgm_result = context.get('dgm_evolution_result', {})
        agi_review = context.get('agi_review_result', {})
        
        # Request verdict
        verdict = validator.evaluate_agent_modification(
            agent_id=dgm_result.get('agent_id', 'unknown'),
            old_code="# baseline",
            new_code=dgm_result.get('code', ''),
            benchmark_results={
                "baseline_performance": 0.30,
                "new_performance": dgm_result.get('performance', 0.30)
            }
        )
        
        return {
            "verdict": verdict,
            "approved": verdict['verdict'] in ['APPROVE', 'CANARY_DEPLOY']
        }
    
    async def _canary_handler(self, context: Dict) -> Dict:
        """Handle canary deployment stage."""
        governance_result = context.get('governance_validation_result', {})
        
        if not governance_result.get('approved'):
            return {
                "deployed": False,
                "reason": "Not approved by governance"
            }
        
        verdict = governance_result.get('verdict', {})
        
        if verdict.get('verdict') == 'CANARY_DEPLOY':
            # Would call scripts/gov_canary_decider.py
            return {
                "deployed": True,
                "deployment_type": "canary",
                "traffic_percentage": 0.05,
                "monitoring_enabled": True
            }
        elif verdict.get('verdict') == 'APPROVE':
            # Direct deployment
            return {
                "deployed": True,
                "deployment_type": "production",
                "traffic_percentage": 1.0
            }
        
        return {"deployed": False}
    
    async def _monitoring_handler(self, context: Dict) -> Dict:
        """Handle monitoring setup stage."""
        canary_result = context.get('canary_deployment_result', {})
        
        if canary_result.get('deployed'):
            # Would configure enhanced monitoring
            return {
                "monitoring_enabled": True,
                "alert_rules_active": True,
                "dashboard_updated": True
            }
        
        return {"monitoring_enabled": False}


class ResearchToProductionWorkflow(IntegratedWorkflow):
    """
    Research to production pipeline:
    Experiment → Statistical Analysis → Governance → Staged Rollout → Validation
    """
    
    def __init__(self):
        super().__init__("research_to_production")
        
        self.add_stage(WorkflowStage("run_experiment", "research", self._experiment_handler))
        self.add_stage(WorkflowStage("statistical_analysis", "research", self._analysis_handler))
        self.add_stage(WorkflowStage("governance_approval", "governance", self._approval_handler))
        self.add_stage(WorkflowStage("staged_rollout", "deployment", self._rollout_handler))
        self.add_stage(WorkflowStage("validation", "monitoring", self._validation_handler))
    
    async def _experiment_handler(self, context: Dict) -> Dict:
        """Run research experiment."""
        from governance.research.dgm.experiments.experiment_runner import ExperimentManager
        
        manager = ExperimentManager()
        experiment_config = context.get('experiment_config', 'governance/research/dgm/experiments/pilot_experiment.yaml')
        
        result = await manager.run_experiment(experiment_config)
        
        return result
    
    async def _analysis_handler(self, context: Dict) -> Dict:
        """Perform statistical analysis."""
        experiment_result = context.get('run_experiment_result', {})
        analysis = experiment_result.get('analysis', {})
        
        # Check statistical significance
        improvement = analysis.get('performance', {}).get('improvement', 0)
        approval_rate = analysis.get('verdicts', {}).get('approval_rate', 0)
        
        significant = improvement > 0.05 and approval_rate > 0.3
        
        return {
            "significant": significant,
            "improvement": improvement,
            "approval_rate": approval_rate,
            "recommendation": "DEPLOY" if significant else "ITERATE"
        }
    
    async def _approval_handler(self, context: Dict) -> Dict:
        """Get governance approval."""
        analysis = context.get('statistical_analysis_result', {})
        
        if not analysis.get('significant'):
            return {
                "approved": False,
                "reason": "Results not statistically significant"
            }
        
        return {
            "approved": True,
            "reason": "Statistically significant improvement",
            "confidence": 0.85
        }
    
    async def _rollout_handler(self, context: Dict) -> Dict:
        """Execute staged rollout."""
        approval = context.get('governance_approval_result', {})
        
        if not approval.get('approved'):
            return {"deployed": False}
        
        # Simulate staged rollout
        stages = [
            {"name": "canary", "traffic": 0.05, "duration_hours": 24},
            {"name": "staging", "traffic": 0.25, "duration_hours": 48},
            {"name": "production", "traffic": 1.0, "duration_hours": 0}
        ]
        
        return {
            "deployed": True,
            "rollout_plan": stages,
            "current_stage": stages[0]['name']
        }
    
    async def _validation_handler(self, context: Dict) -> Dict:
        """Validate rollout success."""
        rollout = context.get('staged_rollout_result', {})
        
        if not rollout.get('deployed'):
            return {"validated": False}
        
        # Would run validation checks
        return {
            "validated": True,
            "health_checks_passed": True,
            "performance_maintained": True
        }


# Workflow Registry
WORKFLOWS = {
    "full_evolution": FullEvolutionWorkflow,
    "research_to_production": ResearchToProductionWorkflow
}


async def run_workflow(workflow_name: str, context: Optional[Dict] = None) -> Dict:
    """
    Run a named workflow.
    
    Args:
        workflow_name: Name of workflow to run
        context: Initial context
        
    Returns:
        Workflow execution results
    """
    if workflow_name not in WORKFLOWS:
        raise ValueError(f"Unknown workflow: {workflow_name}")
    
    workflow_class = WORKFLOWS[workflow_name]
    workflow = workflow_class()
    
    result = await workflow.execute(initial_context=context)
    
    # Save workflow result
    results_dir = Path("state/workflows")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = results_dir / f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"✓ Workflow result saved: {result_file}")
    
    return result


async def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Athena Integration Workflows")
    parser.add_argument('workflow', choices=list(WORKFLOWS.keys()), help="Workflow to run")
    parser.add_argument('--config', help="Experiment config (for research workflows)")
    
    args = parser.parse_args()
    
    context = {}
    if args.config:
        context['experiment_config'] = args.config
    
    result = await run_workflow(args.workflow, context)
    
    print(json.dumps(result, indent=2))
    
    if result['status'] == 'failed':
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

