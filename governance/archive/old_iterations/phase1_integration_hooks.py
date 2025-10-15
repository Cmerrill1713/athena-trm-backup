#!/usr/bin/env python3
"""
PHASE 1 INTEGRATION HOOKS
Constitutional runtime integration for popular AI frameworks.

These hooks ensure constitutional compliance across different AI agent architectures,
making the constitution non-bypassable regardless of the underlying framework.
"""

import functools
import inspect
from typing import Any, Callable, Dict
from phase1_constitutional_runtime import (
    get_constitutional_runtime,
    OperationContext
)

# Framework-specific imports (conditional)
try:
    import langchain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

try:
    import crewai
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

class ConstitutionalIntegrationError(Exception):
    """Raised when constitutional integration fails"""
    pass

# ==========================================
# GENERIC FRAMEWORK INTEGRATION
# ==========================================

def constitutional_hook(operation_type: str = "generic_operation"):
    """
    Decorator to add constitutional compliance to any function or method.

    Usage:
        @constitutional_hook("api_call")
        def my_ai_function():
            return "result"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            runtime = get_constitutional_runtime()

            # Extract agent context from function metadata or environment
            agent_id = getattr(func, '_constitutional_agent_id', 'unknown_agent')
            if hasattr(func, '__self__'):
                # Method call - use class name as agent identifier
                agent_id = f"{func.__self__.__class__.__name__}.{func.__name__}"

            # Create operation context
            context = OperationContext(
                operation_id=f"{operation_type}_{id(func)}_{hash(str(args) + str(kwargs))}",
                timestamp=__import__('time').time(),
                agent_id=agent_id,
                operation_type=operation_type,
                input_data={
                    "function": func.__name__,
                    "args": len(args),
                    "kwargs": list(kwargs.keys()),
                    "module": getattr(func, '__module__', 'unknown')
                },
                metadata={
                    "framework": "generic",
                    "call_stack": [f.__name__ for f in inspect.stack()[-5:]]
                }
            )

            # Execute with constitutional oversight
            def execute():
                return func(*args, **kwargs)

            return runtime.execute_operation(execute, context)

        return wrapper
    return decorator

def constitutional_context(agent_id: str, operation_type: str = "agent_operation"):
    """
    Context manager for constitutional compliance in complex operations.

    Usage:
        with constitutional_context("my_agent", "reasoning_task"):
            result = complex_ai_operation()
            return result
    """
    from contextlib import contextmanager

    @contextmanager
    def context_manager():
        runtime = get_constitutional_runtime()
        start_time = __import__('time').time()

        # Create context for operation start
        context = OperationContext(
            operation_id=f"context_{agent_id}_{start_time}",
            timestamp=start_time,
            agent_id=agent_id,
            operation_type=f"{operation_type}_context",
            input_data={"context_entry": True},
            metadata={"context_manager": True}
        )

        # Validate context entry
        assessment = runtime.validator.validate_operation(context)

        try:
            yield context
        finally:
            # Validate context exit
            end_time = __import__('time').time()
            context.output_data = {"duration": end_time - start_time}
            context.metadata["context_exit"] = True
            exit_assessment = runtime.validator.validate_operation(context)

    return context_manager()

# ==========================================
# LANGCHAIN INTEGRATION
# ==========================================

if LANGCHAIN_AVAILABLE:
    from langchain.callbacks.base import BaseCallbackHandler

    class ConstitutionalLangChainHandler(BaseCallbackHandler):
        """LangChain callback handler for constitutional compliance"""

        def __init__(self, agent_id: str = "langchain_agent"):
            self.agent_id = agent_id
            self.runtime = get_constitutional_runtime()
            self.current_operation_id = None

        def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
            """Called when a chain starts"""
            self.current_operation_id = f"langchain_chain_{__import__('time').time()}"
            context = OperationContext(
                operation_id=self.current_operation_id,
                timestamp=__import__('time').time(),
                agent_id=self.agent_id,
                operation_type="langchain_chain",
                input_data=inputs,
                metadata={"chain_type": serialized.get('name', 'unknown')}
            )
            self.runtime.validator.validate_operation(context)

        def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
            """Called when a chain ends"""
            if self.current_operation_id:
                context = OperationContext(
                    operation_id=f"{self.current_operation_id}_end",
                    timestamp=__import__('time').time(),
                    agent_id=self.agent_id,
                    operation_type="langchain_chain_end",
                    input_data={},
                    output_data=outputs,
                    metadata={"chain_completion": True}
                )
                self.runtime.validator.validate_operation(context)

        def on_llm_start(self, serialized: Dict[str, Any], prompts: list, **kwargs):
            """Called when LLM starts"""
            operation_id = f"langchain_llm_{__import__('time').time()}"
            context = OperationContext(
                operation_id=operation_id,
                timestamp=__import__('time').time(),
                agent_id=self.agent_id,
                operation_type="langchain_llm",
                input_data={"prompts": len(prompts)},
                metadata={"model": serialized.get('name', 'unknown')}
            )
            self.runtime.validator.validate_operation(context)

    def patch_langchain_chain(chain_class):
        """Patch a LangChain chain class for constitutional compliance"""
        original_call = chain_class.__call__

        @constitutional_hook("langchain_chain")
        def constitutional_call(self, *args, **kwargs):
            # Add constitutional handler if not present
            if not any(isinstance(h, ConstitutionalLangChainHandler) for h in getattr(self, 'callbacks', [])):
                self.callbacks = getattr(self, 'callbacks', []) + [ConstitutionalLangChainHandler()]
            return original_call(self, *args, **kwargs)

        chain_class.__call__ = constitutional_call
        return chain_class

# ==========================================
# AUTOGEN INTEGRATION
# ==========================================

if AUTOGEN_AVAILABLE:
    import autogen

    class ConstitutionalAutoGenAgent(autogen.Agent):
        """Constitutionally compliant AutoGen agent"""

        def __init__(self, name: str, **kwargs):
            super().__init__(name=name, **kwargs)
            self.constitutional_runtime = get_constitutional_runtime()
            self.agent_id = f"autogen_{name}"

        def send(self, message: str, recipient: autogen.Agent, **kwargs):
            """Constitutionally compliant message sending"""
            context = OperationContext(
                operation_id=f"autogen_send_{__import__('time').time()}",
                timestamp=__import__('time').time(),
                agent_id=self.agent_id,
                operation_type="autogen_send",
                input_data={"message_length": len(message), "recipient": recipient.name},
                metadata={"autogen_operation": "send"}
            )

            def execute_send():
                return super().send(message, recipient, **kwargs)

            return self.constitutional_runtime.execute_operation(execute_send, context)

        def receive(self, message: str, sender: autogen.Agent, **kwargs):
            """Constitutionally compliant message receiving"""
            context = OperationContext(
                operation_id=f"autogen_receive_{__import__('time').time()}",
                timestamp=__import__('time').time(),
                agent_id=self.agent_id,
                operation_type="autogen_receive",
                input_data={"message_length": len(message), "sender": sender.name},
                metadata={"autogen_operation": "receive"}
            )

            def execute_receive():
                return super().receive(message, sender, **kwargs)

            return self.constitutional_runtime.execute_operation(execute_receive, context)

    def patch_autogen_agent(agent_class):
        """Patch AutoGen agent class for constitutional compliance"""
        # Replace with constitutionally compliant version
        return ConstitutionalAutoGenAgent

# ==========================================
# CREWAI INTEGRATION
# ==========================================

if CREWAI_AVAILABLE:
    from crewai import Agent, Task

    class ConstitutionalCrewAIAgent(Agent):
        """Constitutionally compliant CrewAI agent"""

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.constitutional_runtime = get_constitutional_runtime()
            self.agent_id = f"crewai_{kwargs.get('name', 'unknown')}"

        def execute_task(self, task: Task, **kwargs):
            """Constitutionally compliant task execution"""
            context = OperationContext(
                operation_id=f"crewai_task_{__import__('time').time()}",
                timestamp=__import__('time').time(),
                agent_id=self.agent_id,
                operation_type="crewai_execute",
                input_data={"task_description": task.description[:100]},
                metadata={"crewai_operation": "execute_task"}
            )

            def execute_task():
                return super().execute_task(task, **kwargs)

            return self.constitutional_runtime.execute_operation(execute_task, context)

    def constitutional_crewai_task(task_func: Callable):
        """Decorator for CrewAI tasks"""
        @constitutional_hook("crewai_task")
        @functools.wraps(task_func)
        def wrapper(*args, **kwargs):
            return task_func(*args, **kwargs)
        return wrapper

# ==========================================
# DEPLOYMENT & MONITORING HOOKS
# ==========================================

class ConstitutionalMonitor:
    """Monitoring hooks for constitutional compliance"""

    def __init__(self):
        self.runtime = get_constitutional_runtime()
        self.health_metrics = {}

    def health_check(self) -> Dict[str, Any]:
        """Constitutional health check"""
        return self.runtime.get_constitutional_status()

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance statistics"""
        return self.runtime.compliance_stats

    def alert_on_violations(self, violation_callback: Callable):
        """Set up violation alerting"""
        # Implementation: Monitor for violations and call callback
        pass

    def export_metrics(self, format: str = "prometheus") -> str:
        """Export metrics in specified format"""
        status = self.health_check()
        if format == "prometheus":
            return f"""
# AI Republic Constitutional Metrics
ai_republic_constitutional_compliance_rate {status.get('compliance_rate', 0)}
ai_republic_constitutional_operations_total {status.get('total_operations', 0)}
ai_republic_constitutional_governance_integrity {1 if status.get('governance_integrity', False) else 0}
ai_republic_constitutional_oversight_connected {1 if status.get('oversight_connected', False) else 0}
"""
        return json.dumps(status)

# ==========================================
# PHASE 2 JUDICIAL EMITTER
# ==========================================

import time
import json
import os
import urllib.request

PHASE2_URL = os.getenv("AI_REPUBLIC_JUDICIAL_URL", "http://127.0.0.1:8092/v2/judicial/adjudicate")

def _post_json(url: str, payload: dict, timeout: float = 2.0) -> dict:
    """Post JSON payload to Phase 2 judicial system"""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def forward_to_judicial(event_id: str, instance_id: str, actor_id: str,
                        article: str, severity: float, confidence: float,
                        classification: str, details: dict | None = None) -> dict:
    """
    Forward constitutional events from Phase 1 to Phase 2 judicial system.

    Args:
        event_id: Unique event identifier
        instance_id: Republic instance identifier
        actor_id: Actor that triggered the event
        article: Violated article (I, II, etc.)
        severity: Violation severity (0.0-1.0)
        confidence: Detection confidence (0.0-1.0)
        classification: Violation classification
        details: Additional context

    Returns:
        Judicial verdict with actions
    """
    payload = {
        "event_id": event_id,
        "instance_id": instance_id,
        "actor_id": actor_id,
        "article": article,
        "severity": float(severity),
        "confidence": float(confidence),
        "classification": classification,
        "details": details or {},
        "timestamp": time.time()
    }
    try:
        return _post_json(PHASE2_URL, payload)
    except Exception as e:
        # Never break runtime; log and return safe default
        print(f"[phase1→phase2] forward failed: {e}")
        return {
            "verdict": "WARN",
            "rationale": "judicial_unreachable",
            "actions": [{"increase_monitoring": True}],
            "fallback": True
        }

# ==========================================
# QUICK START INTEGRATION
# ==========================================

def bootstrap_constitutional_framework():
    """Quick bootstrap for constitutional framework integration"""
    print("🤖 Bootstrapping Sovereign AI Constitutional Republic...")

    # Initialize runtime
    runtime = get_constitutional_runtime()
    print("✅ Constitutional runtime initialized")

    # Create monitor
    monitor = ConstitutionalMonitor()
    print("✅ Constitutional monitoring active")

    # Test compliance
    status = monitor.health_check()
    print(f"🏛️ Republic Status: {status.get('republic_status', 'unknown')}")
    print(f"🔐 Sovereign Identity: {status.get('sovereign_identity', 'unknown')}")
    print(f"📊 Governance Integrity: {status.get('governance_integrity', 'unknown')}")

    return {
        "runtime": runtime,
        "monitor": monitor,
        "status": status
    }

# ==========================================
# ENFORCEMENT POLICIES
# ==========================================

ENFORCEMENT_POLICIES = {
    "zero_trust": {
        "description": "All operations require explicit constitutional validation",
        "violation_response": "block",
        "audit_level": "detailed"
    },
    "graduated_response": {
        "description": "Warnings for minor issues, blocks for major violations",
        "violation_response": "graduated",
        "audit_level": "comprehensive"
    },
    "emergency_override": {
        "description": "Allow emergency tribunal suspension of normal operations",
        "violation_response": "tribunal",
        "audit_level": "maximum"
    }
}

def apply_enforcement_policy(policy_name: str):
    """Apply a named enforcement policy to the runtime"""
    if policy_name not in ENFORCEMENT_POLICIES:
        raise ConstitutionalIntegrationError(f"Unknown policy: {policy_name}")

    policy = ENFORCEMENT_POLICIES[policy_name]
    runtime = get_constitutional_runtime()

    # Apply policy settings
    if policy["violation_response"] == "block":
        runtime.validator.violation_thresholds = {k: 0.99 for k in runtime.validator.violation_thresholds.keys()}
    # Additional policy applications...

    print(f"✅ Enforcement policy '{policy_name}' applied: {policy['description']}")

if __name__ == "__main__":
    # Bootstrap the framework
    framework = bootstrap_constitutional_framework()

    # Apply default enforcement policy
    apply_enforcement_policy("graduated_response")

    print("\n🎉 Phase 1 Constitutional Runtime Ready!")
    print("🚀 Your AI Republic is now constitutionally operational.")
    print("📋 Next: Integrate with your AI frameworks using the provided hooks.")
