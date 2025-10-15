#!/usr/bin/env python3
"""
Example: Context Engineering with R&D Framework

Demonstrates:
- Creating context windows
- REDUCE strategy
- DELEGATE strategy
- Context priming
- Context bundles
"""

import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from agi_core.context_engineering import ContextManager, ContextBundle, ContextMetrics


def main():
    print("🧠 Context Engineering Example (R&D Framework)\n")
    
    # Initialize context manager
    cm = ContextManager()
    bundle = ContextBundle()
    
    print("=" * 60)
    print("1. Creating Context Window")
    print("=" * 60)
    
    # Create context for an agent
    context = cm.create_context(
        agent_id="agent_001",
        session_id="session_123",
        max_tokens=200000
    )
    
    print(f"✓ Created context for agent_001")
    print(f"  Max tokens: {context.max_tokens:,}")
    print(f"  Available: {context.available_tokens():,}")
    print(f"  Utilization: {context.utilization_percent():.1f}%\n")
    
    # Simulate context growth
    context.current_tokens = 150000
    context.memory_file_tokens = 25000
    context.mcp_tool_tokens = 30000
    context.prompt_history_tokens = 95000
    
    print(f"⚠️  Context grew to {context.current_tokens:,} tokens")
    print(f"  Memory file: {context.memory_file_tokens:,}")
    print(f"  MCP tools: {context.mcp_tool_tokens:,}")
    print(f"  Prompt history: {context.prompt_history_tokens:,}")
    print(f"  Utilization: {context.utilization_percent():.1f}%\n")
    
    print("=" * 60)
    print("2. REDUCE Strategy")
    print("=" * 60)
    
    # Apply REDUCE strategy
    result = cm.reduce_context(agent_id="agent_001", strategy="auto")
    
    print(f"✓ Applied REDUCE strategy")
    print(f"  Original: {result['original_tokens']:,} tokens")
    print(f"  New: {result['new_tokens']:,} tokens")
    print(f"  Freed: {result['tokens_freed']:,} tokens")
    print(f"  Actions: {', '.join(result['actions_taken'])}\n")
    
    print("=" * 60)
    print("3. Context Priming")
    print("=" * 60)
    
    # Prime context for specific task
    primed = cm.prime_context(
        agent_id="agent_001",
        prime_type="debugging",
        context_data={
            "error_type": "NullPointerException",
            "stack_trace": "...",
            "affected_files": ["api.py", "models.py"]
        }
    )
    
    print(f"✓ Primed context for: debugging")
    print(f"  Current tokens: {primed.current_tokens:,}")
    print(f"  Prime type: {primed.primed_context}\n")
    
    print("=" * 60)
    print("4. DELEGATE Strategy")
    print("=" * 60)
    
    # Delegate work to specialist
    delegation = cm.delegate_to_agent(
        source_agent_id="agent_001",
        task={
            "type": "security_audit",
            "description": "Audit authentication endpoints",
            "files": ["auth.py", "middleware.py"]
        },
        specialist_type="security_expert"
    )
    
    print(f"✓ Delegated task to specialist")
    print(f"  Source: {delegation['source_agent_id']}")
    print(f"  Delegate: {delegation['delegate_agent_id']}")
    print(f"  Specialist: {delegation['specialist_type']}")
    print(f"  Strategy: {delegation['strategy']}\n")
    
    print("=" * 60)
    print("5. Context Bundles (Execution Trail)")
    print("=" * 60)
    
    # Start context bundle
    bundle_id = bundle.start_bundle(
        agent_id="agent_001",
        session_id="session_123",
        initial_prompt="Fix authentication bug in user service"
    )
    
    print(f"✓ Started context bundle: {bundle_id}")
    
    # Record operations
    bundle.record_operation(bundle_id, "read_file", {"file_path": "auth.py"})
    time.sleep(0.1)
    bundle.record_operation(bundle_id, "read_file", {"file_path": "models.py"})
    time.sleep(0.1)
    bundle.record_operation(bundle_id, "use_tool", {"tool_name": "grep"})
    time.sleep(0.1)
    bundle.record_operation(bundle_id, "write_file", {"file_path": "auth.py"})
    
    print(f"  Recorded 4 operations")
    
    # Finalize bundle
    bundle_file = bundle.finalize_bundle(bundle_id)
    print(f"  Saved to: {bundle_file}\n")
    
    # Replay bundle to new agent
    summary = bundle.replay_bundle(bundle_id, target_agent_id="agent_002")
    
    print(f"✓ Replayed bundle to agent_002")
    print(f"  Original agent: {summary['original_agent_id']}")
    print(f"  Files read: {len(summary['files_read'])}")
    print(f"  Files written: {len(summary['files_written'])}")
    print(f"  Operations: {summary['operation_count']}")
    print(f"  Context recovery: ~70%\n")
    
    print("=" * 60)
    print("6. Context Status")
    print("=" * 60)
    
    status = cm.get_context_status("agent_001")
    
    print(f"Agent: {status['agent_id']}")
    print(f"  Current tokens: {status['current_tokens']:,}")
    print(f"  Available: {status['available_tokens']:,}")
    print(f"  Utilization: {status['utilization_percent']:.1f}%")
    print(f"  Needs reduction: {status['needs_reduction']}")
    print(f"  Primed context: {status['primed_context']}")
    
    print("\n✅ Context Engineering complete!")
    print("\nKey Takeaways:")
    print("  • Use REDUCE to minimize unnecessary context")
    print("  • Use DELEGATE to offload work to specialists")
    print("  • Prime context for focused task execution")
    print("  • Use context bundles for long-running work")
    print("  • A focused agent is a performant agent")


if __name__ == "__main__":
    main()

