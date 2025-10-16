#!/usr/bin/env python3
"""
Full System Integration Tests
Tests the complete integration of all Athena subsystems.
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from athena_master_orchestrator import AthenaMasterOrchestrator, SystemMode
from governance.research.dgm.dgm_agi_bridge import DGMAGIBridge
from workflows.end_to_end_integration import run_workflow


class TestMasterOrchestrator:
    """Test master orchestrator initialization and coordination."""
    
    def test_orchestrator_initialization(self):
        """Test that master orchestrator initializes all subsystems."""
        orchestrator = AthenaMasterOrchestrator()
        
        assert orchestrator is not None
        assert orchestrator.state is not None
        assert orchestrator.state.governance_active is True
    
    def test_system_status(self):
        """Test system status reporting."""
        orchestrator = AthenaMasterOrchestrator()
        
        status = orchestrator.get_system_status()
        
        assert 'orchestrator' in status
        assert 'state' in status
        assert 'subsystems' in status
        assert 'capabilities' in status
        
        # Should have at least governance active
        assert status['subsystems']['governance']['active'] is True
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test comprehensive health check."""
        orchestrator = AthenaMasterOrchestrator()
        
        health = await orchestrator.health_check()
        
        assert 'overall' in health
        assert 'subsystems' in health
        assert health['overall'] in ['healthy', 'degraded', 'unhealthy']
    
    @pytest.mark.asyncio
    async def test_task_routing_governance(self):
        """Test task routing to governance system."""
        orchestrator = AthenaMasterOrchestrator()
        
        task = {
            "id": "test_gov_task",
            "type": "governance",
            "payload": {"test": "data"}
        }
        
        result = await orchestrator.process_task(task)
        
        assert result is not None
        assert 'task_id' in result or 'status' in result
    
    @pytest.mark.asyncio
    async def test_constitutional_validation(self):
        """Test constitutional validation in task processing."""
        orchestrator = AthenaMasterOrchestrator()
        
        unsafe_task = {
            "id": "test_unsafe",
            "type": "code",
            "code": "import os; os.system('rm -rf /')"
        }
        
        result = await orchestrator.process_task(unsafe_task)
        
        # Should be rejected by constitutional policy
        assert result['status'] == 'REJECTED'
        assert 'constitutional_violation' in result['reason']


class TestDGMAGIIntegration:
    """Test DGM and AGI Core integration."""
    
    @pytest.mark.asyncio
    async def test_bridge_initialization(self):
        """Test DGM-AGI bridge initializes."""
        bridge = DGMAGIBridge()
        
        assert bridge is not None
        assert bridge.state_dir.exists()
    
    @pytest.mark.asyncio
    async def test_agi_review_of_dgm_agent(self):
        """Test AGI Core reviewing DGM-generated agent."""
        bridge = DGMAGIBridge()
        
        test_agent = """
def solve_task(problem):
    solution = analyze(problem)
    return solution
"""
        
        metadata = {
            "agent_id": "test_integration_001",
            "generation": 5,
            "performance": 0.35
        }
        
        review = await bridge.review_dgm_agent(test_agent, metadata)
        
        assert 'reviews' in review
        assert 'consensus' in review
        assert review['consensus']['decision'] in ['APPROVE', 'REJECT', 'APPROVE_WITH_CHANGES', 'NEEDS_IMPROVEMENT']
    
    @pytest.mark.asyncio
    async def test_enhancement_application(self):
        """Test applying AGI Core enhancements to DGM agent."""
        bridge = DGMAGIBridge()
        
        original_code = "def solve(): pass"
        
        review = {
            "enhancements": [
                {"type": "documentation", "priority": "medium", "description": "Add docs"},
                {"type": "error_handling", "priority": "high", "description": "Add try/except"}
            ]
        }
        
        enhanced = await bridge.enhance_dgm_agent(original_code, review)
        
        # Enhanced should be longer and include improvements
        assert len(enhanced) > len(original_code)
        assert 'logging' in enhanced.lower() or 'try' in enhanced.lower()
    
    def test_integration_statistics(self):
        """Test getting integration statistics."""
        bridge = DGMAGIBridge()
        
        stats = bridge.get_integration_statistics()
        
        assert 'total' in stats
        assert isinstance(stats['total'], int)


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest.mark.asyncio
    async def test_full_evolution_workflow(self):
        """Test complete evolution workflow."""
        from workflows.end_to_end_integration import FullEvolutionWorkflow
        
        workflow = FullEvolutionWorkflow()
        
        assert len(workflow.stages) == 5
        assert workflow.stages[0].name == "dgm_evolution"
        assert workflow.stages[1].name == "agi_review"
        assert workflow.stages[2].name == "governance_validation"
        assert workflow.stages[3].name == "canary_deployment"
        assert workflow.stages[4].name == "monitoring_setup"
    
    @pytest.mark.asyncio
    async def test_research_to_production_workflow(self):
        """Test research to production pipeline."""
        from workflows.end_to_end_integration import ResearchToProductionWorkflow
        
        workflow = ResearchToProductionWorkflow()
        
        assert len(workflow.stages) == 5
        assert workflow.stages[0].name == "run_experiment"
        assert workflow.stages[2].name == "governance_approval"
    
    @pytest.mark.asyncio
    async def test_workflow_stage_execution(self):
        """Test individual workflow stage execution."""
        from workflows.end_to_end_integration import WorkflowStage
        
        async def test_handler(context):
            return {"test": "result"}
        
        stage = WorkflowStage("test_stage", "test_subsystem", test_handler)
        
        result = await stage.execute({"input": "data"})
        
        assert result == {"test": "result"}
        assert stage.status == "completed"
        assert stage.start_time is not None
        assert stage.end_time is not None


class TestGovernanceIntegration:
    """Test governance integration with all subsystems."""
    
    @pytest.mark.asyncio
    async def test_verdict_flow_dgm(self):
        """Test verdict flow for DGM agent."""
        from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator
        
        validator = DGMVerdictValidator()
        
        verdict = validator.evaluate_agent_modification(
            agent_id="test_verdict_flow",
            old_code="def baseline(): return 0.3",
            new_code="def improved(): return 0.4",
            benchmark_results={
                "baseline_performance": 0.30,
                "new_performance": 0.40,
                "consistency": 0.85
            }
        )
        
        assert verdict['verdict'] in ['APPROVE', 'CANARY_DEPLOY']
        assert verdict['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_constitutional_policy_enforcement(self):
        """Test constitutional policy is enforced."""
        orchestrator = AthenaMasterOrchestrator()
        
        # Try to process unsafe task
        unsafe_task = {
            "type": "code",
            "code": "eval('malicious code')"
        }
        
        result = await orchestrator.process_task(unsafe_task)
        
        # Should be blocked
        assert result['status'] == 'REJECTED'


class TestSystemIntegration:
    """Test full system integration points."""
    
    @pytest.mark.asyncio
    async def test_dgm_to_governance_flow(self):
        """Test DGM output flows through governance."""
        orchestrator = AthenaMasterOrchestrator()
        
        if not orchestrator.state.dgm_active:
            pytest.skip("DGM not active")
        
        task = {"type": "self_improvement"}
        result = await orchestrator.process_task(task)
        
        # Should have governance verdict
        assert 'verdict' in result or 'status' in result
    
    @pytest.mark.asyncio
    async def test_agi_to_governance_flow(self):
        """Test AGI Core output validated by governance."""
        orchestrator = AthenaMasterOrchestrator()
        
        if not orchestrator.state.agi_core_active:
            pytest.skip("AGI Core not active")
        
        task = {"type": "multi_agent", "description": "Test task"}
        result = await orchestrator.process_task(task)
        
        assert result is not None
    
    def test_monitoring_integration(self):
        """Test monitoring is integrated with all subsystems."""
        orchestrator = AthenaMasterOrchestrator()
        
        status = orchestrator.get_system_status()
        
        # Monitoring should report on all active subsystems
        assert 'subsystems' in status
    
    @pytest.mark.asyncio
    async def test_complete_pipeline(self):
        """Test complete pipeline: DGM → AGI → Governance → Deploy."""
        orchestrator = AthenaMasterOrchestrator()
        
        if orchestrator.state.mode != SystemMode.FULL_INTEGRATION:
            pytest.skip("Full integration mode not active")
        
        # Run full evolution workflow
        result = await orchestrator.run_integrated_workflow('full_evolution')
        
        assert result['workflow'] == 'full_evolution'
        assert 'dgm_phase' in result
        assert result['status'] == 'completed'


class TestDataFlow:
    """Test data flows correctly between subsystems."""
    
    @pytest.mark.asyncio
    async def test_context_propagation(self):
        """Test context propagates through workflow stages."""
        from workflows.end_to_end_integration import FullEvolutionWorkflow
        
        workflow = FullEvolutionWorkflow()
        
        initial_context = {"test_value": "propagate_me"}
        result = await workflow.execute(initial_context)
        
        # Context should be updated by each stage
        assert len(workflow.context) > 1
        assert 'workflow_name' in workflow.context
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics are collected from all stages."""
        from workflows.end_to_end_integration import WorkflowStage
        
        async def metric_handler(context):
            return {"metric_value": 42}
        
        stage = WorkflowStage("test", "test", metric_handler)
        await stage.execute({})
        
        metrics = stage.get_metrics()
        
        assert 'duration_seconds' in metrics
        assert 'status' in metrics
        assert metrics['status'] == 'completed'


# Fixture for cleanup
@pytest.fixture(autouse=True)
def cleanup_integration_tests():
    """Clean up integration test artifacts."""
    yield
    
    # Cleanup test files
    test_dirs = [
        Path("governance/research/dgm/agents"),
        Path("state/dgm_agi_integration"),
        Path("state/workflows")
    ]
    
    for test_dir in test_dirs:
        if test_dir.exists():
            for test_file in test_dir.glob("test_*.json"):
                test_file.unlink(missing_ok=True)
            for test_file in test_dir.glob("*_test_*.json"):
                test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    # Run all integration tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "not slow"])

