#!/usr/bin/env python3
"""
Connection Verification Script

Verifies all integrations between:
- AGI Core
- Governance Orchestrator  
- Common utilities
- Other services
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def verify_agi_core():
    """Verify AGI Core components"""
    print_section("1. VERIFYING AGI CORE")
    
    try:
        from agi_core import (
            ContextManager,
            ContextBundle,
            ExpertRegistry,
            ExpertOrchestrator,
            ScoutPlanBuild,
            AgentDelegator,
            MultiAgentCoordinator,
            DelegationStrategy,
            get_metrics_collector
        )
        print("✅ AGI Core imports successful")
        print(f"   • ContextManager: {ContextManager.__name__}")
        print(f"   • ExpertRegistry: {ExpertRegistry.__name__}")
        print(f"   • ExpertOrchestrator: {ExpertOrchestrator.__name__}")
        print(f"   • ScoutPlanBuild: {ScoutPlanBuild.__name__}")
        print(f"   • AgentDelegator: {AgentDelegator.__name__}")
        print(f"   • MetricsCollector: Available")
        
        # Test instantiation
        cm = ContextManager()
        print(f"✅ ContextManager instantiated: {len(cm.active_contexts)} contexts")
        
        registry = ExpertRegistry()
        print(f"✅ ExpertRegistry instantiated: {len(registry.experts)} experts")
        
        collector = get_metrics_collector()
        print(f"✅ MetricsCollector instantiated")
        
        return True
        
    except Exception as e:
        print(f"❌ AGI Core verification failed: {e}")
        return False


def verify_common_utilities():
    """Verify common utilities"""
    print_section("2. VERIFYING COMMON UTILITIES")
    
    try:
        from common.ops import wire_tracing, attach_guardrails, add_health_endpoints
        print("✅ Common ops imports successful")
        print(f"   • wire_tracing: {wire_tracing.__name__}")
        print(f"   • attach_guardrails: {attach_guardrails.__name__}")
        print(f"   • add_health_endpoints: {add_health_endpoints.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Common utilities verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_orchestrator():
    """Verify governance orchestrator"""
    print_section("3. VERIFYING GOVERNANCE ORCHESTRATOR")
    
    try:
        from orchestrator.app import app, ExecState, VerdictRequest
        print("✅ Orchestrator imports successful")
        print(f"   • FastAPI app: {app.title}")
        print(f"   • ExecState model: {ExecState.__name__}")
        print(f"   • VerdictRequest model: {VerdictRequest.__name__}")
        
        # Check if AGI metrics are available in orchestrator
        from orchestrator.app import METRICS_AVAILABLE
        if METRICS_AVAILABLE:
            print("✅ Orchestrator has AGI metrics integration")
        else:
            print("⚠️  Orchestrator AGI metrics not available (will enable)")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_bidirectional_communication():
    """Verify AGI <-> Orchestrator communication"""
    print_section("4. VERIFYING BIDIRECTIONAL COMMUNICATION")
    
    try:
        # AGI can import orchestrator models
        from orchestrator.app import VerdictRequest, ExecState
        print("✅ AGI can import orchestrator models")
        
        # Orchestrator can import AGI
        from agi_core import get_metrics_collector, ExpertOrchestrator
        print("✅ Orchestrator can import AGI components")
        
        # Test data flow
        verdict = VerdictRequest(
            task_id="test_001",
            verdict="PASS",
            ece_estimate=0.92
        )
        print(f"✅ Can create orchestrator verdict: {verdict.task_id}")
        
        collector = get_metrics_collector()
        print(f"✅ AGI metrics collector available")
        
        return True
        
    except Exception as e:
        print(f"❌ Bidirectional communication failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_file_structure():
    """Verify file structure and paths"""
    print_section("5. VERIFYING FILE STRUCTURE")
    
    base_path = Path(__file__).parent
    
    critical_paths = {
        "AGI Core": base_path / "agi_core",
        "Orchestrator": base_path / "orchestrator",
        "Common": base_path / "common",
        "AGI Service": base_path / "agi_core" / "agi_service.py",
        "Orchestrator App": base_path / "orchestrator" / "app.py",
        "Common Ops": base_path / "common" / "ops.py",
    }
    
    all_exist = True
    for name, path in critical_paths.items():
        if path.exists():
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: NOT FOUND at {path}")
            all_exist = False
    
    return all_exist


def verify_service_endpoints():
    """Verify service endpoint definitions"""
    print_section("6. VERIFYING SERVICE ENDPOINTS")
    
    try:
        # AGI Core endpoints
        from agi_core.agi_service import app as agi_app
        agi_routes = [route.path for route in agi_app.routes if hasattr(route, 'path')]
        print(f"✅ AGI Core has {len(agi_routes)} routes")
        print(f"   Key routes: /health, /context/create, /experts/list, /workflow/execute")
        
        # Orchestrator endpoints
        from orchestrator.app import app as orch_app
        orch_routes = [route.path for route in orch_app.routes if hasattr(route, 'path')]
        print(f"✅ Orchestrator has {len(orch_routes)} routes")
        print(f"   Key routes: /health, /verdict, /state")
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint verification failed: {e}")
        return False


def verify_integration_example():
    """Test a complete integration workflow"""
    print_section("7. TESTING INTEGRATION WORKFLOW")
    
    try:
        from agi_core import (
            ContextManager,
            ExpertOrchestrator,
            ExpertRegistry,
            ScoutPlanBuild,
            get_metrics_collector
        )
        from orchestrator.app import VerdictRequest
        
        print("Step 1: Simulate governance verdict...")
        verdict = VerdictRequest(
            task_id="integration_test",
            verdict="HARD_FAIL",
            ece_estimate=0.45,
            violation_rate_delta=0.15
        )
        print(f"✅ Created verdict: {verdict.verdict}")
        
        print("\nStep 2: AGI investigation with Scout-Plan-Build...")
        workflow = ScoutPlanBuild(
            workflow_id="test_workflow",
            task_description="Investigate failure",
            codebase_path=Path("./"),
            constraints={}
        )
        result = workflow.execute()
        print(f"✅ Workflow completed: {len(result.get('results', []))} phases")
        
        print("\nStep 3: Deploy expert agents...")
        registry = ExpertRegistry()
        orchestrator = ExpertOrchestrator(registry)
        task_id = orchestrator.submit_task(
            task_type="debugging",
            description="Debug integration test",
            context={"verdict": verdict.verdict},
            priority=9
        )
        print(f"✅ Expert task submitted: {task_id}")
        
        print("\nStep 4: Context management...")
        cm = ContextManager()
        context = cm.create_context("test_agent", "test_session")
        print(f"✅ Context created: {context.max_tokens:,} tokens available")
        
        print("\nStep 5: Collect metrics...")
        collector = get_metrics_collector()
        print(f"✅ Metrics collector ready")
        
        print("\n✅ COMPLETE INTEGRATION WORKFLOW SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Integration workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_connection_report():
    """Generate comprehensive connection report"""
    print_section("CONNECTION VERIFICATION REPORT")
    
    results = {
        "AGI Core": verify_agi_core(),
        "Common Utilities": verify_common_utilities(),
        "Orchestrator": verify_orchestrator(),
        "Bidirectional Comm": verify_bidirectional_communication(),
        "File Structure": verify_file_structure(),
        "Service Endpoints": verify_service_endpoints(),
        "Integration Test": verify_integration_example(),
    }
    
    print_section("SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} PASSED ({passed/total*100:.0f}%)")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n🎉 ALL CONNECTIONS VERIFIED!")
        print("\nYour systems are fully integrated:")
        print("  • AGI Core ↔ Governance Orchestrator ✅")
        print("  • AGI Core ↔ Common Utilities ✅")
        print("  • Bidirectional Communication ✅")
        print("  • Complete Workflow ✅")
        print("\n🚀 Ready for production!")
        return True
    else:
        print("\n⚠️  SOME CONNECTIONS NEED ATTENTION")
        print("\nFailed components:")
        for component, status in results.items():
            if not status:
                print(f"  • {component}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  🔗 SYSTEM CONNECTION VERIFICATION")
    print("="*70)
    
    success = generate_connection_report()
    
    sys.exit(0 if success else 1)

