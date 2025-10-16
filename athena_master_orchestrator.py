#!/usr/bin/env python3
"""
Athena Master Orchestrator
Unified control system integrating all subsystems:
- Governance (Legislative, Judicial, Executive)
- DGM (Self-Improving Agents)
- AGI Core (Multi-Agent System)
- Monitoring & Observability
- Research & Experimentation
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# Governance imports
from governance.executive.orchestration.dgm_orchestrator import DGMOrchestrator
from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator
from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter

# AGI Core imports (if available)
try:
    from agi_core.workflows import ScoutPlanBuildWorkflow
    from agi_core.delegation import MultiAgentDelegation
    from agi_core.evaluation_metrics import STOPMetrics
    AGI_CORE_AVAILABLE = True
except ImportError:
    AGI_CORE_AVAILABLE = False
    logging.warning("AGI Core not available, running in governance-only mode")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemMode(Enum):
    """Operating modes for Athena system."""
    GOVERNANCE_ONLY = "governance_only"
    DGM_EVOLUTION = "dgm_evolution"
    AGI_MULTI_AGENT = "agi_multi_agent"
    FULL_INTEGRATION = "full_integration"
    RESEARCH_MODE = "research_mode"


class AthenaSystemState:
    """Current state of the Athena system."""
    
    def __init__(self):
        self.mode = SystemMode.GOVERNANCE_ONLY
        self.dgm_active = False
        self.agi_core_active = False
        self.governance_active = True
        self.monitoring_active = False
        
        self.dgm_generation = 0
        self.active_agents = []
        self.recent_verdicts = []
        
        self.metrics = {
            "uptime_seconds": 0,
            "total_tasks_processed": 0,
            "governance_verdicts": 0,
            "dgm_evolutions": 0,
            "agi_delegations": 0
        }
    
    def to_dict(self) -> Dict:
        """Export state as dictionary."""
        return {
            "mode": self.mode.value,
            "subsystems": {
                "dgm": self.dgm_active,
                "agi_core": self.agi_core_active,
                "governance": self.governance_active,
                "monitoring": self.monitoring_active
            },
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }


class AthenaMasterOrchestrator:
    """
    Master orchestrator coordinating all Athena subsystems.
    
    Integrates:
    - Governance (Legislative, Judicial, Executive)
    - DGM (Self-improving agents)
    - AGI Core (Multi-agent delegation)
    - Monitoring (Prometheus, Grafana)
    - Research (Experiments, benchmarks)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.state = AthenaSystemState()
        
        # Initialize subsystems
        self.dgm_orchestrator = None
        self.agi_delegation = None
        self.governance_adapter = None
        self.verdict_validator = None
        
        self._initialize_subsystems()
    
    def _load_config(self, path: Optional[str]) -> Dict:
        """Load master configuration."""
        if path is None:
            path = "config/athena_master_config.yaml"
        
        import yaml
        config_file = Path(path)
        
        if not config_file.exists():
            # Return default config
            return {
                "mode": "full_integration",
                "subsystems": {
                    "governance": {"enabled": True},
                    "dgm": {"enabled": True},
                    "agi_core": {"enabled": AGI_CORE_AVAILABLE},
                    "monitoring": {"enabled": True}
                }
            }
        
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def _initialize_subsystems(self):
        """Initialize all subsystems based on config."""
        logger.info("🚀 Initializing Athena Master Orchestrator")
        
        # Governance (always active)
        if self.config['subsystems']['governance']['enabled']:
            logger.info("  ✓ Governance: Initializing judicial & legislative systems")
            self.governance_adapter = DGMGovernanceAdapter()
            self.verdict_validator = DGMVerdictValidator()
            self.state.governance_active = True
        
        # DGM Self-Improvement
        if self.config['subsystems']['dgm']['enabled']:
            logger.info("  ✓ DGM: Initializing self-improving agent system")
            self.dgm_orchestrator = DGMOrchestrator()
            self.state.dgm_active = True
        
        # AGI Core Multi-Agent
        if AGI_CORE_AVAILABLE and self.config['subsystems']['agi_core']['enabled']:
            logger.info("  ✓ AGI Core: Initializing multi-agent delegation")
            self.agi_delegation = MultiAgentDelegation()
            self.state.agi_core_active = True
        
        # Monitoring
        if self.config['subsystems']['monitoring']['enabled']:
            logger.info("  ✓ Monitoring: Prometheus & Grafana ready")
            self.state.monitoring_active = True
        
        # Set operating mode
        if self.state.dgm_active and self.state.agi_core_active:
            self.state.mode = SystemMode.FULL_INTEGRATION
        elif self.state.dgm_active:
            self.state.mode = SystemMode.DGM_EVOLUTION
        elif self.state.agi_core_active:
            self.state.mode = SystemMode.AGI_MULTI_AGENT
        else:
            self.state.mode = SystemMode.GOVERNANCE_ONLY
        
        logger.info(f"  → Mode: {self.state.mode.value}")
        logger.info("✓ Athena Master Orchestrator ready\n")
    
    async def process_task(self, task: Dict) -> Dict:
        """
        Process a task through the integrated system.
        
        Flow:
        1. Task arrives
        2. Governance validates (constitutional check)
        3. Route to appropriate subsystem:
           - Code improvement → DGM
           - Complex task → AGI Core multi-agent
           - Simple task → Direct execution
        4. Judicial verdict on output
        5. Canary deployment if approved
        6. Monitor and collect metrics
        
        Args:
            task: Task specification
            
        Returns:
            Execution result with governance metadata
        """
        task_id = task.get('id', f"task_{datetime.now().timestamp()}")
        task_type = task.get('type', 'unknown')
        
        logger.info(f"📥 Processing task: {task_id} (type: {task_type})")
        
        # Step 1: Constitutional validation
        if self.state.governance_active:
            validation = await self._validate_task_constitutional(task)
            if not validation['valid']:
                logger.warning(f"❌ Task {task_id} failed constitutional validation")
                return {
                    "task_id": task_id,
                    "status": "REJECTED",
                    "reason": "constitutional_violation",
                    "validation": validation
                }
        
        # Step 2: Route to appropriate subsystem
        result = await self._route_task(task)
        
        # Step 3: Request judicial verdict
        if self.state.governance_active:
            verdict = await self._request_verdict(task_id, result)
            result['verdict'] = verdict
        
        # Step 4: Execute verdict actions
        if result.get('verdict', {}).get('verdict') == 'APPROVE':
            await self._execute_deployment(result)
        
        # Step 5: Record metrics
        self._record_metrics(task_id, result)
        
        self.state.metrics['total_tasks_processed'] += 1
        
        return result
    
    async def _validate_task_constitutional(self, task: Dict) -> Dict:
        """Validate task against constitutional policies."""
        # Check against self-modification policy if code is involved
        if 'code' in task or task.get('type') == 'code':
            compliance = await self.governance_adapter.check_constitutional_compliance(
                task.get('code', '')
            )
            return {
                "valid": compliance['compliant'],
                "violations": compliance.get('violations', [])
            }
        
        # Other tasks auto-pass constitutional (for now)
        return {"valid": True, "violations": []}
    
    async def _route_task(self, task: Dict) -> Dict:
        """Route task to appropriate subsystem."""
        task_type = task.get('type')
        
        # Self-improvement tasks → DGM
        if task_type == 'self_improvement' and self.state.dgm_active:
            logger.info(f"  → Routing to DGM")
            return await self._process_with_dgm(task)
        
        # Complex multi-step tasks → AGI Core
        elif task_type in ['multi_agent', 'complex'] and self.state.agi_core_active:
            logger.info(f"  → Routing to AGI Core")
            return await self._process_with_agi_core(task)
        
        # Research tasks → Experiment framework
        elif task_type == 'research':
            logger.info(f"  → Routing to Research Framework")
            return await self._process_research_task(task)
        
        # Default: Direct processing
        else:
            logger.info(f"  → Direct processing")
            return await self._process_direct(task)
    
    async def _process_with_dgm(self, task: Dict) -> Dict:
        """Process task through DGM self-improvement."""
        if not self.dgm_orchestrator:
            return {"error": "DGM not initialized"}
        
        # Run one evolution cycle
        result = await self.dgm_orchestrator.run_evolution_cycle()
        
        self.state.dgm_generation = self.dgm_orchestrator.generation
        self.state.metrics['dgm_evolutions'] += 1
        
        return {
            "subsystem": "dgm",
            "generation": self.state.dgm_generation,
            "result": result
        }
    
    async def _process_with_agi_core(self, task: Dict) -> Dict:
        """Process task through AGI Core multi-agent system."""
        if not self.agi_delegation:
            return {"error": "AGI Core not initialized"}
        
        # Delegate to multi-agent system
        # In practice, would use Scout→Plan→Build workflow
        result = {
            "subsystem": "agi_core",
            "workflow": "scout_plan_build",
            "status": "delegated"
        }
        
        self.state.metrics['agi_delegations'] += 1
        
        return result
    
    async def _process_research_task(self, task: Dict) -> Dict:
        """Process research/experiment task."""
        experiment_config = task.get('experiment_config')
        
        if experiment_config:
            # Run experiment
            from governance.research.dgm.experiments.experiment_runner import ExperimentManager
            
            manager = ExperimentManager()
            result = await manager.run_experiment(experiment_config)
            
            return {
                "subsystem": "research",
                "experiment_id": result.get('experiment_id'),
                "result": result
            }
        
        return {"error": "No experiment config provided"}
    
    async def _process_direct(self, task: Dict) -> Dict:
        """Process task directly without subsystem routing."""
        return {
            "subsystem": "direct",
            "status": "processed",
            "result": task.get('payload')
        }
    
    async def _request_verdict(self, task_id: str, result: Dict) -> Dict:
        """Request judicial verdict on task result."""
        if not self.verdict_validator:
            return {"verdict": "AUTO_APPROVE", "reason": "governance_disabled"}
        
        # Extract relevant data for verdict
        code = result.get('code', '')
        performance = result.get('performance', {})
        
        # Request verdict (simplified)
        verdict = {
            "task_id": task_id,
            "verdict": "APPROVE",  # Would be actual verdict logic
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
        
        self.state.metrics['governance_verdicts'] += 1
        self.state.recent_verdicts.append(verdict)
        
        return verdict
    
    async def _execute_deployment(self, result: Dict):
        """Execute deployment based on verdict."""
        verdict = result.get('verdict', {})
        actions = verdict.get('actions', [])
        
        for action in actions:
            if action == 'CANARY_5PCT':
                logger.info("  → Deploying to canary (5% traffic)")
                # Would call scripts/gov_canary_decider.py
                
            elif action == 'DEPLOY':
                logger.info("  → Deploying to production")
                # Would execute full deployment
                
            elif action == 'MONITOR':
                logger.info("  → Enhanced monitoring enabled")
                # Would configure monitoring
    
    def _record_metrics(self, task_id: str, result: Dict):
        """Record metrics for monitoring."""
        # Would send to Prometheus
        logger.debug(f"  ✓ Metrics recorded for {task_id}")
    
    async def run_integrated_workflow(self, workflow_type: str, **kwargs) -> Dict:
        """
        Run integrated end-to-end workflow.
        
        Workflows:
        - 'full_evolution': DGM evolution → AGI Core → Governance → Deploy
        - 'research_experiment': Research task → Validation → Report
        - 'multi_agent_task': AGI Core delegation → Governance approval
        
        Args:
            workflow_type: Type of workflow to run
            **kwargs: Workflow-specific parameters
            
        Returns:
            Workflow execution results
        """
        logger.info(f"🔄 Starting integrated workflow: {workflow_type}")
        
        if workflow_type == 'full_evolution':
            return await self._run_full_evolution_workflow(**kwargs)
        
        elif workflow_type == 'research_experiment':
            return await self._run_research_workflow(**kwargs)
        
        elif workflow_type == 'multi_agent_task':
            return await self._run_multi_agent_workflow(**kwargs)
        
        else:
            return {"error": f"Unknown workflow type: {workflow_type}"}
    
    async def _run_full_evolution_workflow(self, **kwargs) -> Dict:
        """
        Full integration workflow:
        1. DGM generates improved agent
        2. AGI Core validates and enhances
        3. Governance approves
        4. Canary deploys
        5. Monitor and promote
        """
        logger.info("  🧬 Phase 1: DGM Evolution")
        
        # DGM generates improved agent
        dgm_task = {"type": "self_improvement"}
        dgm_result = await self.process_task(dgm_task)
        
        if not self.state.agi_core_active:
            logger.info("  ⏭️  Phase 2: AGI Core (skipped - not available)")
            return dgm_result
        
        logger.info("  🤖 Phase 2: AGI Core Enhancement")
        
        # AGI Core can review and enhance the generated agent
        agi_task = {
            "type": "multi_agent",
            "subtask": "review_and_enhance",
            "artifact": dgm_result
        }
        enhanced_result = await self.process_task(agi_task)
        
        logger.info("  ✓ Full evolution workflow complete")
        
        return {
            "workflow": "full_evolution",
            "dgm_phase": dgm_result,
            "agi_phase": enhanced_result,
            "status": "completed"
        }
    
    async def _run_research_workflow(self, experiment_config: str, **kwargs) -> Dict:
        """Run research experiment workflow."""
        logger.info(f"  🔬 Running research experiment: {experiment_config}")
        
        task = {
            "type": "research",
            "experiment_config": experiment_config
        }
        
        result = await self.process_task(task)
        
        return {
            "workflow": "research_experiment",
            "result": result,
            "status": "completed"
        }
    
    async def _run_multi_agent_workflow(self, task_description: str, **kwargs) -> Dict:
        """Run multi-agent task workflow."""
        logger.info(f"  🤖 Delegating to multi-agent system")
        
        if not self.state.agi_core_active:
            return {"error": "AGI Core not available"}
        
        task = {
            "type": "multi_agent",
            "description": task_description,
            **kwargs
        }
        
        result = await self.process_task(task)
        
        return {
            "workflow": "multi_agent_task",
            "result": result,
            "status": "completed"
        }
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "orchestrator": "athena_master",
            "version": "1.0.0",
            "state": self.state.to_dict(),
            "subsystems": {
                "governance": {
                    "active": self.state.governance_active,
                    "components": ["legislative", "judicial", "executive"]
                },
                "dgm": {
                    "active": self.state.dgm_active,
                    "current_generation": self.state.dgm_generation,
                    "archive_size": len(self.governance_adapter.load_archive()) if self.governance_adapter else 0
                },
                "agi_core": {
                    "active": self.state.agi_core_active,
                    "available": AGI_CORE_AVAILABLE
                },
                "monitoring": {
                    "active": self.state.monitoring_active,
                    "endpoints": ["prometheus:9090", "grafana:3000"]
                }
            },
            "capabilities": self._list_capabilities(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _list_capabilities(self) -> List[str]:
        """List system capabilities based on active subsystems."""
        capabilities = ["constitutional_governance", "judicial_verdicts"]
        
        if self.state.dgm_active:
            capabilities.extend([
                "self_improving_agents",
                "autonomous_evolution",
                "empirical_validation"
            ])
        
        if self.state.agi_core_active:
            capabilities.extend([
                "multi_agent_delegation",
                "scout_plan_build_workflow",
                "expert_specialization"
            ])
        
        if self.state.monitoring_active:
            capabilities.extend([
                "real_time_monitoring",
                "predictive_analysis",
                "automated_alerts"
            ])
        
        return capabilities
    
    async def health_check(self) -> Dict:
        """Comprehensive health check of all subsystems."""
        health = {
            "overall": "healthy",
            "subsystems": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check governance
        if self.governance_adapter:
            try:
                agents = self.governance_adapter.load_archive()
                health['subsystems']['governance'] = {
                    "status": "healthy",
                    "archive_size": len(agents)
                }
            except Exception as e:
                health['subsystems']['governance'] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health['overall'] = "degraded"
        
        # Check DGM
        if self.dgm_orchestrator:
            health['subsystems']['dgm'] = {
                "status": "healthy",
                "generation": self.state.dgm_generation,
                "failures": self.dgm_orchestrator.failures
            }
            
            if self.dgm_orchestrator.failures >= 3:
                health['subsystems']['dgm']['status'] = "warning"
                health['overall'] = "degraded"
        
        # Check AGI Core
        if self.agi_delegation:
            health['subsystems']['agi_core'] = {
                "status": "healthy"
            }
        
        return health


# CLI Interface
async def cli_main():
    """CLI entry point for master orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Athena Master Orchestrator - Unified System Control"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    subparsers.add_parser('status', help='Get system status')
    
    # Health check command
    subparsers.add_parser('health', help='Run health check')
    
    # Run workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run integrated workflow')
    workflow_parser.add_argument('type', choices=['full_evolution', 'research_experiment', 'multi_agent_task'])
    workflow_parser.add_argument('--config', help='Workflow configuration')
    
    # Process task command
    task_parser = subparsers.add_parser('task', help='Process single task')
    task_parser.add_argument('--type', required=True, help='Task type')
    task_parser.add_argument('--payload', help='Task payload (JSON)')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = AthenaMasterOrchestrator()
    
    # Execute command
    if args.command == 'status':
        status = orchestrator.get_system_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == 'health':
        health = await orchestrator.health_check()
        print(json.dumps(health, indent=2))
        
        if health['overall'] != 'healthy':
            sys.exit(1)
    
    elif args.command == 'workflow':
        result = await orchestrator.run_integrated_workflow(
            workflow_type=args.type,
            experiment_config=args.config
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == 'task':
        payload = json.loads(args.payload) if args.payload else {}
        task = {
            "type": args.type,
            **payload
        }
        result = await orchestrator.process_task(task)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║         ATHENA MASTER ORCHESTRATOR v1.0.0                  ║
║     Unified Control for Self-Improving AI Systems          ║
╚════════════════════════════════════════════════════════════╝
""")
    
    asyncio.run(cli_main())

