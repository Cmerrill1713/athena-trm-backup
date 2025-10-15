#!/usr/bin/env python3
"""
Example: Scout-Plan-Build Workflow

Demonstrates the most powerful agentic pattern:
1. Scout - Explore codebase
2. Plan - Create strategy
3. Build - Execute
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agi_core.workflows import ScoutPlanBuild, WorkflowOrchestrator


def main():
    print("🔍 Scout-Plan-Build Workflow Example\n")
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator()
    
    # Create Scout-Plan-Build workflow
    workflow = ScoutPlanBuild(
        workflow_id="example_spb_001",
        task_description="Add rate limiting middleware to API endpoints",
        codebase_path=Path("./"),
        constraints={
            "test_coverage": 0.85,
            "performance_impact": "minimal"
        }
    )
    
    # Register workflow
    orchestrator.register_workflow(workflow)
    
    print(f"📋 Workflow: {workflow.workflow_id}")
    print(f"📝 Task: {workflow.task_description}\n")
    
    # Execute workflow
    print("🚀 Executing workflow...\n")
    result = orchestrator.execute_workflow(workflow.workflow_id)
    
    # Display results
    print("✅ Workflow completed!\n")
    print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
    print(f"Phases: {result.get('phases_completed', 0)}")
    print(f"\nPhase Results:")
    
    for phase_result in result.get('results', []):
        phase = phase_result['phase']
        success = "✓" if phase_result['success'] else "✗"
        duration = phase_result['duration_seconds']
        tokens = phase_result['tokens_used']
        efficiency = phase_result['context_efficiency']
        
        print(f"  {success} {phase.upper()}: {duration:.2f}s, {tokens} tokens, {efficiency:.0%} efficient")
        
        # Show phase-specific output
        if phase == 'scout':
            output = phase_result['output']
            print(f"     Files: {len(output.get('relevant_files', []))}")
            print(f"     Complexity: {output.get('estimated_complexity', 'unknown')}")
        elif phase == 'plan':
            output = phase_result['output']
            print(f"     Steps: {len(output.get('steps', []))}")
            print(f"     Estimated time: {output.get('total_estimated_time', 'unknown')}")
        elif phase == 'build':
            output = phase_result['output']
            print(f"     Files created: {output.get('files_created', 0)}")
            print(f"     Files modified: {output.get('files_modified', 0)}")
            print(f"     Tests: {output.get('tests_passed', 0)}/{output.get('tests_added', 0)} passed")
    
    print(f"\n📊 Total tokens: {sum(r['tokens_used'] for r in result.get('results', []))}")
    print(f"📊 Avg efficiency: {sum(r['context_efficiency'] for r in result.get('results', [])) / len(result.get('results', [])):.0%}")


if __name__ == "__main__":
    main()

