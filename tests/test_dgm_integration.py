#!/usr/bin/env python3
"""
Integration tests for Darwin Gödel Machine governance integration.
Validates that DGM works correctly with judicial, legislative, and executive systems.
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter
from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator
from governance.executive.orchestration.dgm_orchestrator import DGMOrchestrator


class TestDGMGovernanceIntegration:
    """Test DGM integration with governance systems."""
    
    def test_adapter_initialization(self):
        """Test that DGM adapter initializes correctly."""
        adapter = DGMGovernanceAdapter()
        
        assert adapter.config is not None
        assert adapter.archive_path.exists()
        assert adapter.results_path.exists()
    
    @pytest.mark.asyncio
    async def test_constitutional_compliance_safe_code(self):
        """Test that safe code passes constitutional checks."""
        adapter = DGMGovernanceAdapter()
        
        safe_code = """
def solve_problem(input_data):
    # Safe agent code
    result = process_input(input_data)
    return result
"""
        
        compliance = await adapter.check_constitutional_compliance(safe_code)
        
        assert compliance['compliant'] is True
        assert len(compliance['violations']) == 0
    
    @pytest.mark.asyncio
    async def test_constitutional_compliance_unsafe_code(self):
        """Test that unsafe code fails constitutional checks."""
        adapter = DGMGovernanceAdapter()
        
        unsafe_code = """
import os
def solve_problem(input_data):
    os.system('rm -rf /')  # DANGEROUS!
    return eval(input_data)
"""
        
        compliance = await adapter.check_constitutional_compliance(unsafe_code)
        
        assert compliance['compliant'] is False
        assert len(compliance['violations']) > 0
        assert any('os.system' in v['pattern'] for v in compliance['violations'])
    
    def test_verdict_validator_performance_improvement(self):
        """Test verdict for performance improvement."""
        validator = DGMVerdictValidator()
        
        verdict = validator.evaluate_agent_modification(
            agent_id="test_improve",
            old_code="def solve(): pass",
            new_code="def solve(): return better_solution()",
            benchmark_results={
                "baseline_performance": 0.30,
                "new_performance": 0.45,  # 15% improvement
                "consistency": 0.85
            }
        )
        
        assert verdict['verdict'] == 'APPROVE'
        assert verdict['confidence'] > 0.8
        assert 'DEPLOY' in verdict['actions']
    
    def test_verdict_validator_performance_regression(self):
        """Test verdict for performance regression."""
        validator = DGMVerdictValidator()
        
        verdict = validator.evaluate_agent_modification(
            agent_id="test_regress",
            old_code="def solve(): return good()",
            new_code="def solve(): return worse()",
            benchmark_results={
                "baseline_performance": 0.40,
                "new_performance": 0.30,  # 10% regression
                "consistency": 0.75
            }
        )
        
        assert verdict['verdict'] == 'REJECT'
        assert 'ROLLBACK' in verdict['actions']
    
    def test_verdict_validator_safety_violation(self):
        """Test that safety violations are rejected."""
        validator = DGMVerdictValidator()
        
        unsafe_code = """
import pickle
def solve(): 
    pickle.load(open('data', 'rb'))  # Unsafe deserialization
"""
        
        verdict = validator.evaluate_agent_modification(
            agent_id="test_unsafe",
            old_code="def solve(): pass",
            new_code=unsafe_code,
            benchmark_results={
                "baseline_performance": 0.30,
                "new_performance": 0.50  # Even with improvement
            }
        )
        
        assert verdict['verdict'] == 'REJECT'
        assert 'BLOCK' in verdict['actions'] or 'ALERT_HUMAN' in verdict['actions']
    
    def test_verdict_validator_moderate_improvement_canary(self):
        """Test that moderate improvements go to canary."""
        validator = DGMVerdictValidator()
        
        verdict = validator.evaluate_agent_modification(
            agent_id="test_canary",
            old_code="def solve(): return ok()",
            new_code="def solve(): return better()",
            benchmark_results={
                "baseline_performance": 0.30,
                "new_performance": 0.35,  # 5% improvement
                "consistency": 0.80
            }
        )
        
        assert verdict['verdict'] == 'CANARY_DEPLOY'
        assert 'CANARY_5PCT' in verdict['actions']
    
    def test_archive_management(self):
        """Test agent archive save and load."""
        adapter = DGMGovernanceAdapter()
        
        # Save test agent
        agent_code = "def solve(): return 42"
        metadata = {
            "performance": 0.35,
            "generation": 5,
            "verdict": {"approved": True}
        }
        
        adapter.save_agent_to_archive(
            agent_id="test_agent_001",
            agent_code=agent_code,
            metadata=metadata
        )
        
        # Load archive
        agents = adapter.load_archive()
        
        # Find our agent
        test_agent = next((a for a in agents if a['id'] == 'test_agent_001'), None)
        
        assert test_agent is not None
        assert test_agent['code'] == agent_code
        assert test_agent['metadata']['performance'] == 0.35
    
    def test_top_performers_selection(self):
        """Test selecting top performing agents."""
        adapter = DGMGovernanceAdapter()
        
        # Save multiple agents with different performance
        for i in range(5):
            adapter.save_agent_to_archive(
                agent_id=f"perf_test_{i}",
                agent_code=f"def solve(): return {i}",
                metadata={"performance": 0.2 + (i * 0.05)}
            )
        
        # Get top 3
        top = adapter.get_top_performers(n=3)
        
        assert len(top) <= 3
        # Verify sorted by performance (descending)
        if len(top) >= 2:
            assert top[0]['metadata']['performance'] >= top[1]['metadata']['performance']
    
    def test_ece_calculation(self):
        """Test ECE calculation from metrics."""
        adapter = DGMGovernanceAdapter()
        
        metrics = {
            "accuracy": 0.8,
            "consistency": 0.9
        }
        
        ece = adapter._calculate_ece(metrics)
        
        assert 0 <= ece <= 1
        assert ece == 0.85  # (0.8 + 0.9) / 2
    
    @pytest.mark.asyncio
    async def test_judicial_verdict_request(self):
        """Test requesting judicial verdict."""
        adapter = DGMGovernanceAdapter()
        
        agent_code = "def improved(): return better_result()"
        metrics = {
            "accuracy": 0.85,
            "consistency": 0.90,
            "improvement": 0.10
        }
        
        verdict = await adapter.request_judicial_verdict(agent_code, metrics)
        
        assert 'approved' in verdict
        assert 'confidence' in verdict
        assert 'reasoning' in verdict
    
    def test_verdict_statistics(self):
        """Test verdict approval rate calculation."""
        validator = DGMVerdictValidator()
        
        # Generate some test verdicts
        for i in range(10):
            perf_delta = 0.05 if i % 2 == 0 else -0.02
            
            validator.evaluate_agent_modification(
                agent_id=f"stats_test_{i}",
                old_code="def solve(): pass",
                new_code=f"def solve(): return {i}",
                benchmark_results={
                    "baseline_performance": 0.30,
                    "new_performance": 0.30 + perf_delta,
                    "consistency": 0.75
                }
            )
        
        stats = validator.get_approval_rate()
        
        assert stats['total'] >= 10
        assert 'approval_rate' in stats
        assert 0 <= stats['approval_rate'] <= 1


class TestDGMOrchestrator:
    """Test DGM orchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orchestrator = DGMOrchestrator()
        
        assert orchestrator.generation == 0
        assert orchestrator.failures == 0
        assert orchestrator.adapter is not None
        assert orchestrator.validator is not None
    
    def test_seed_agent_retrieval(self):
        """Test getting seed agent."""
        orchestrator = DGMOrchestrator()
        
        parent = orchestrator._select_parent_agent()
        
        assert parent is not None
        assert 'id' in parent
        assert 'code' in parent


class TestSafetyConstraints:
    """Test safety constraint enforcement."""
    
    @pytest.mark.asyncio
    async def test_eval_blocked(self):
        """Test that eval() is blocked."""
        adapter = DGMGovernanceAdapter()
        
        code_with_eval = "result = eval(user_input)"
        compliance = await adapter.check_constitutional_compliance(code_with_eval)
        
        assert compliance['compliant'] is False
        assert any('eval' in str(v) for v in compliance['violations'])
    
    @pytest.mark.asyncio
    async def test_exec_blocked(self):
        """Test that exec() is blocked."""
        adapter = DGMGovernanceAdapter()
        
        code_with_exec = "exec('import os; os.system(cmd)')"
        compliance = await adapter.check_constitutional_compliance(code_with_exec)
        
        assert compliance['compliant'] is False
    
    @pytest.mark.asyncio
    async def test_subprocess_blocked(self):
        """Test that subprocess calls are blocked."""
        adapter = DGMGovernanceAdapter()
        
        code_with_subprocess = "subprocess.Popen(['rm', '-rf', '/'])"
        compliance = await adapter.check_constitutional_compliance(code_with_subprocess)
        
        assert compliance['compliant'] is False
    
    @pytest.mark.asyncio
    async def test_code_size_limit(self):
        """Test that oversized code triggers warning."""
        adapter = DGMGovernanceAdapter()
        
        huge_code = "# " + ("x" * 60000)  # 60KB
        compliance = await adapter.check_constitutional_compliance(huge_code)
        
        assert compliance['compliant'] is False
        size_violation = next((v for v in compliance['violations'] if 'size' in str(v)), None)
        assert size_violation is not None


# Fixture for cleanup
@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Clean up test artifacts after each test."""
    yield
    
    # Cleanup test files from archive
    test_files = Path("governance/research/dgm/agents").glob("test_*.json")
    for f in test_files:
        f.unlink(missing_ok=True)
    
    test_files = Path("governance/research/dgm/agents").glob("*_test_*.json")
    for f in test_files:
        f.unlink(missing_ok=True)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

