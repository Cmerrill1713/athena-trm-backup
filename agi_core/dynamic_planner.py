"""
Dynamic AGI Planner - Creates plans based on actual user objectives
No more hardcoded workflows!
"""
import re
from typing import List, Dict, Any


def create_dynamic_plan(objective: str, available_tools: List[str]) -> List[Dict[str, Any]]:
    """
    Creates a dynamic plan based on the user's actual objective.
    
    Args:
        objective: What the user wants to accomplish
        available_tools: List of tools we can use
    
    Returns:
        List of plan steps to execute
    """
    objective_lower = objective.lower()
    plan = []
    
    # System check / health check
    if any(kw in objective_lower for kw in ['system check', 'health check', 'status', 'services']):
        if 'system.doctor' in available_tools:
            plan.append({
                "agent": "diagnostics",
                "tool": "system.doctor",
                "payload": {},
                "timeout_s": 10.0,
                "retries": 1
            })
        return plan
    
    # Search / research / papers
    if any(kw in objective_lower for kw in ['search', 'research', 'paper', 'find', 'look up', 'article']):
        # Try RAG first
        if 'rag.query' in available_tools:
            plan.append({
                "agent": "researcher",
                "tool": "rag.query",
                "payload": {
                    "query": objective,
                    "top_k": 5
                },
                "timeout_s": 15.0,
                "retries": 1
            })
        
        # Then web search if available
        if 'mcp.web_search' in available_tools:
            plan.append({
                "agent": "researcher",
                "tool": "mcp.web_search",
                "payload": {
                    "query": objective,
                    "num_results": 5
                },
                "timeout_s": 20.0,
                "retries": 1
            })
        return plan
    
    # File operations
    if any(kw in objective_lower for kw in ['read file', 'show file', 'open file', 'view']):
        # Extract file path from objective
        match = re.search(r'[\/\w\-\.]+\.(py|js|ts|md|txt|json|yaml|yml)', objective)
        if match and 'mcp.fs.read' in available_tools:
            plan.append({
                "agent": "file_reader",
                "tool": "mcp.fs.read",
                "payload": {
                    "path": match.group(0)
                },
                "timeout_s": 10.0,
                "retries": 0
            })
        return plan
    
    # Code analysis
    if any(kw in objective_lower for kw in ['analyze', 'check code', 'review code', 'optimize', 'improve']):
        if 'system.doctor' in available_tools:
            plan.append({
                "agent": "analyzer",
                "tool": "system.doctor",
                "payload": {},
                "timeout_s": 10.0,
                "retries": 1
            })
        
        # Could add code analysis tools here
        return plan
    
    # Shell commands
    if any(kw in objective_lower for kw in ['run command', 'execute', 'shell', 'terminal']):
        if 'mcp.shell' in available_tools:
            # Extract command from objective
            cmd_match = re.search(r'(?:run|execute)\s+["\']?([^"\']+)["\']?', objective_lower)
            if cmd_match:
                plan.append({
                    "agent": "executor",
                    "tool": "mcp.shell",
                    "payload": {
                        "cmd": cmd_match.group(1)
                    },
                    "timeout_s": 30.0,
                    "retries": 0
                })
        return plan
    
    # Knowledge / information queries
    if any(kw in objective_lower for kw in ['what is', 'tell me', 'explain', 'how to', 'who', 'when', 'where']):
        if 'rag.query' in available_tools:
            plan.append({
                "agent": "knowledge_retriever",
                "tool": "rag.query",
                "payload": {
                    "query": objective,
                    "top_k": 3
                },
                "timeout_s": 15.0,
                "retries": 1
            })
        return plan
    
    # Default: Try system doctor as a fallback
    if 'system.doctor' in available_tools:
        plan.append({
            "agent": "default",
            "tool": "system.doctor",
            "payload": {},
            "timeout_s": 10.0,
            "retries": 1
        })
    
    return plan


def get_plan_summary(plan: List[Dict[str, Any]]) -> str:
    """Get a human-readable summary of the plan"""
    if not plan:
        return "No plan generated - no matching tools available"
    
    steps = []
    for i, step in enumerate(plan, 1):
        steps.append(f"{i}. {step['agent']} will use {step['tool']}")
    
    return "\n".join(steps)


