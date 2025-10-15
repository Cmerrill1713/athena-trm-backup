"""
Context Engineering - R&D Framework (Reduce & Delegate)

Implements IndyDevDan's core principle:
"A focused agent is a performant agent"

There are only two ways to manage context windows:
1. REDUCE - Minimize unnecessary context
2. DELEGATE - Distribute work to specialized agents
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict, field
from enum import Enum

# Sentry will be imported conditionally
try:
    import sentry_sdk as Sentry
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    class MockSentry:
        @staticmethod
        def capture_exception(e): pass
        @staticmethod
        def capture_message(msg, **kwargs): pass
    Sentry = MockSentry()

import logging
logger = logging.getLogger(__name__)

# Import metrics collector (lazy to avoid circular imports)
def _get_metrics_collector():
    """Lazy import of metrics collector"""
    try:
        from .evaluation_metrics import get_metrics_collector
        return get_metrics_collector()
    except ImportError:
        return None


class ContextStrategy(Enum):
    """Context management strategy"""
    REDUCE = "reduce"  # Minimize context in current agent
    DELEGATE = "delegate"  # Offload to another agent
    PRIME = "prime"  # Load focused context for task
    BUNDLE = "bundle"  # Save execution trail


@dataclass
class ContextMetrics:
    """Track context window usage and efficiency"""
    total_tokens: int = 0
    memory_tokens: int = 0
    tool_tokens: int = 0
    prompt_tokens: int = 0
    response_tokens: int = 0
    context_utilization: float = 0.0  # Percentage of context used
    wasted_tokens: int = 0  # Unused/unnecessary context
    timestamp: float = field(default_factory=time.time)
    
    def efficiency_score(self) -> float:
        """Calculate context efficiency (0-1, higher is better)"""
        if self.total_tokens == 0:
            return 1.0
        useful_tokens = self.total_tokens - self.wasted_tokens
        return useful_tokens / self.total_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContextWindow:
    """Represents an agent's context window state"""
    agent_id: str
    session_id: str
    max_tokens: int = 200000  # Claude 4.5 Sonnet context limit
    current_tokens: int = 0
    memory_file_tokens: int = 0
    mcp_tool_tokens: int = 0
    prompt_history_tokens: int = 0
    loaded_files: List[str] = field(default_factory=list)
    loaded_tools: List[str] = field(default_factory=list)
    primed_context: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def available_tokens(self) -> int:
        """Calculate available context window space"""
        return self.max_tokens - self.current_tokens
    
    def utilization_percent(self) -> float:
        """Context window usage percentage"""
        return (self.current_tokens / self.max_tokens) * 100
    
    def is_approaching_limit(self, threshold: float = 0.8) -> bool:
        """Check if approaching context limit"""
        return self.current_tokens >= (self.max_tokens * threshold)
    
    def needs_reduction(self) -> bool:
        """Determine if context reduction is needed"""
        return self.utilization_percent() > 75.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextManager:
    """
    R&D Framework Implementation
    Manages agent context windows using Reduce & Delegate strategies
    """
    
    def __init__(self, state_dir: Path = Path("./state/context")):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.active_contexts: Dict[str, ContextWindow] = {}
        self.metrics_history: List[ContextMetrics] = []
        
        logger.info(f"ContextManager initialized: state_dir={self.state_dir}, strategy=R&D Framework")
    
    def create_context(
        self,
        agent_id: str,
        session_id: str,
        max_tokens: int = 200000
    ) -> ContextWindow:
        """Create a new context window for an agent"""
        context = ContextWindow(
            agent_id=agent_id,
            session_id=session_id,
            max_tokens=max_tokens
        )
        
        self.active_contexts[agent_id] = context
        
        if SENTRY_AVAILABLE:
            with Sentry.start_span(op="context.create", description="Create Agent Context Window") as span:
                span.set_data("agent_id", agent_id)
                span.set_data("session_id", session_id)
                span.set_data("max_tokens", max_tokens)
        
        logger.info(f"Created context window for agent: {agent_id}, session={session_id}, max_tokens={max_tokens}")
        
        return context
    
    def reduce_context(
        self,
        agent_id: str,
        strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        REDUCE strategy: Minimize context in current agent
        
        Techniques:
        1. Remove unused MCP tools
        2. Trim memory file
        3. Archive old prompts
        4. Deduplicate loaded files
        """
        if agent_id not in self.active_contexts:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        context = self.active_contexts[agent_id]
        original_tokens = context.current_tokens
        
        actions_taken = []
        
        # 1. Reduce MCP tool context
        if context.mcp_tool_tokens > 5000:
            context.mcp_tool_tokens = min(context.mcp_tool_tokens, 2000)
            actions_taken.append("TRIM_MCP_TOOLS")
        
        # 2. Reduce memory file
        if context.memory_file_tokens > 1000:
            context.memory_file_tokens = min(context.memory_file_tokens, 500)
            actions_taken.append("TRIM_MEMORY_FILE")
        
        # 3. Archive old prompts
        if context.prompt_history_tokens > 10000:
            context.prompt_history_tokens = min(context.prompt_history_tokens, 5000)
            actions_taken.append("ARCHIVE_PROMPTS")
        
        # 4. Deduplicate files
        context.loaded_files = list(set(context.loaded_files))
        actions_taken.append("DEDUPE_FILES")
        
        # Recalculate total
        context.current_tokens = (
            context.memory_file_tokens +
            context.mcp_tool_tokens +
            context.prompt_history_tokens
        )
        
        tokens_freed = original_tokens - context.current_tokens
        
        # Calculate efficiency metrics
        efficiency_score = tokens_freed / original_tokens if original_tokens > 0 else 0
        
        logger.info(f"Reduced context for agent: {agent_id}, freed={tokens_freed} tokens, actions={actions_taken}")
        
        # Record metrics
        metrics_collector = _get_metrics_collector()
        if metrics_collector:
            metrics_collector.record_context_metrics(
                agent_id=agent_id,
                operation="reduce_context",
                metrics={
                    "original_tokens": original_tokens,
                    "new_tokens": context.current_tokens,
                    "tokens_freed": tokens_freed,
                    "efficiency_score": efficiency_score,
                    "actions_taken": actions_taken,
                    "strategy": strategy
                }
            )
        
        return {
            "agent_id": agent_id,
            "strategy": "REDUCE",
            "original_tokens": original_tokens,
            "new_tokens": context.current_tokens,
            "tokens_freed": tokens_freed,
            "efficiency_score": efficiency_score,
            "actions_taken": actions_taken,
            "timestamp": time.time()
        }
    
    def delegate_to_agent(
        self,
        source_agent_id: str,
        task: Dict[str, Any],
        specialist_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        DELEGATE strategy: Offload work to specialized agent
        
        Creates a new focused agent for the specific task,
        keeping source agent's context clean
        """
        # Create new session for delegated work
        delegate_session_id = f"{source_agent_id}_delegate_{int(time.time())}"
        delegate_agent_id = f"delegate_{hashlib.md5(delegate_session_id.encode()).hexdigest()[:8]}"
        
        # Create minimal context for delegated agent
        delegate_context = self.create_context(
            agent_id=delegate_agent_id,
            session_id=delegate_session_id,
            max_tokens=100000  # Smaller context for focused work
        )
        
        logger.info(f"Delegated task: {source_agent_id} -> {delegate_agent_id}, type={task.get('type', 'unknown')}, specialist={specialist_type}")
        
        # Record delegation metrics
        metrics_collector = _get_metrics_collector()
        if metrics_collector:
            source_context = self.active_contexts.get(source_agent_id)
            if source_context:
                metrics_collector.record_context_metrics(
                    agent_id=source_agent_id,
                    operation="delegate_to_agent",
                    metrics={
                        "delegate_agent_id": delegate_agent_id,
                        "task_type": task.get('type', 'unknown'),
                        "specialist_type": specialist_type,
                        "source_tokens": source_context.current_tokens,
                        "delegate_max_tokens": 100000
                    }
                )
        
        return {
            "source_agent_id": source_agent_id,
            "delegate_agent_id": delegate_agent_id,
            "delegate_session_id": delegate_session_id,
            "task": task,
            "specialist_type": specialist_type,
            "strategy": "DELEGATE",
            "timestamp": time.time()
        }
    
    def prime_context(
        self,
        agent_id: str,
        prime_type: str,
        context_data: Dict[str, Any]
    ) -> ContextWindow:
        """
        Context priming: Load focused, task-specific context
        
        Instead of always-on memory files, use dynamic priming:
        - prime_bug: For bug fixing
        - prime_feature: For feature development  
        - prime_refactor: For refactoring
        - prime_review: For code review
        """
        if agent_id not in self.active_contexts:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        context = self.active_contexts[agent_id]
        context.primed_context = prime_type
        
        # Add focused context based on prime type
        prime_tokens = len(json.dumps(context_data)) // 4  # Rough estimate
        context.current_tokens += prime_tokens
        
        logger.info(f"Primed context: agent={agent_id}, type={prime_type}, tokens_added={prime_tokens}, total={context.current_tokens}")
        
        # Record priming metrics
        metrics_collector = _get_metrics_collector()
        if metrics_collector:
            metrics_collector.record_context_metrics(
                agent_id=agent_id,
                operation="prime_context",
                metrics={
                    "prime_type": prime_type,
                    "tokens_added": prime_tokens,
                    "total_tokens": context.current_tokens,
                    "utilization_percent": context.utilization_percent()
                }
            )
        
        return context
    
    def get_context_status(self, agent_id: str) -> Dict[str, Any]:
        """Get current context status for an agent"""
        if agent_id not in self.active_contexts:
            return {"error": f"Agent {agent_id} not found"}
        
        context = self.active_contexts[agent_id]
        
        return {
            "agent_id": agent_id,
            "current_tokens": context.current_tokens,
            "max_tokens": context.max_tokens,
            "available_tokens": context.available_tokens(),
            "utilization_percent": context.utilization_percent(),
            "needs_reduction": context.needs_reduction(),
            "is_approaching_limit": context.is_approaching_limit(),
            "loaded_files_count": len(context.loaded_files),
            "loaded_tools_count": len(context.loaded_tools),
            "primed_context": context.primed_context,
            "timestamp": context.timestamp
        }
    
    def record_metrics(self, agent_id: str, metrics: ContextMetrics):
        """Record context metrics for monitoring"""
        self.metrics_history.append(metrics)
        
        # Keep last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Save to disk
        metrics_file = self.state_dir / f"{agent_id}_metrics.jsonl"
        with metrics_file.open("a") as f:
            f.write(json.dumps(metrics.to_dict()) + "\n")
        
        # Report metrics
        logger.info(f"Context metrics: agent={agent_id}, efficiency={metrics.efficiency_score():.2f}")


class ContextBundle:
    """
    Context Bundle: Execution trail for agent replay
    
    Captures the "story" of what an agent did:
    - Prompts issued
    - Files read/written
    - Tools used
    - Decisions made
    
    Enables ~70% accurate replay without full context
    """
    
    def __init__(self, bundle_dir: Path = Path("./state/context_bundles")):
        self.bundle_dir = Path(bundle_dir)
        self.bundle_dir.mkdir(parents=True, exist_ok=True)
        self.bundles: Dict[str, Dict[str, Any]] = {}
        
    def start_bundle(
        self,
        agent_id: str,
        session_id: str,
        initial_prompt: str
    ) -> str:
        """Start tracking a new context bundle"""
        bundle_id = f"{agent_id}_{session_id}_{int(time.time())}"
        
        self.bundles[bundle_id] = {
            "bundle_id": bundle_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "started_at": time.time(),
            "initial_prompt": initial_prompt,
            "operations": [],
            "files_read": [],
            "files_written": [],
            "tools_used": [],
            "prompts": [initial_prompt]
        }
        
        logger.info(f"Started context bundle: {bundle_id}")
        
        return bundle_id
    
    def record_operation(
        self,
        bundle_id: str,
        operation_type: str,
        details: Dict[str, Any]
    ):
        """Record an operation in the bundle"""
        if bundle_id not in self.bundles:
            raise ValueError(f"Unknown bundle: {bundle_id}")
        
        operation = {
            "type": operation_type,
            "timestamp": time.time(),
            "details": details
        }
        
        self.bundles[bundle_id]["operations"].append(operation)
        
        # Track specific operation types
        if operation_type == "read_file":
            self.bundles[bundle_id]["files_read"].append(details.get("file_path"))
        elif operation_type == "write_file":
            self.bundles[bundle_id]["files_written"].append(details.get("file_path"))
        elif operation_type == "use_tool":
            self.bundles[bundle_id]["tools_used"].append(details.get("tool_name"))
        elif operation_type == "prompt":
            self.bundles[bundle_id]["prompts"].append(details.get("prompt_text"))
    
    def finalize_bundle(self, bundle_id: str) -> Path:
        """Finalize and save bundle to disk"""
        if bundle_id not in self.bundles:
            raise ValueError(f"Unknown bundle: {bundle_id}")
        
        bundle = self.bundles[bundle_id]
        bundle["completed_at"] = time.time()
        bundle["duration_seconds"] = bundle["completed_at"] - bundle["started_at"]
        
        # Deduplicate files
        bundle["files_read"] = list(set(bundle["files_read"]))
        bundle["files_written"] = list(set(bundle["files_written"]))
        bundle["tools_used"] = list(set(bundle["tools_used"]))
        
        # Save to disk
        bundle_file = self.bundle_dir / f"{bundle_id}.json"
        with bundle_file.open("w") as f:
            json.dump(bundle, f, indent=2)
        
        logger.info(f"Finalized bundle: {bundle_id}, duration={bundle['duration_seconds']:.2f}s, ops={len(bundle['operations'])}")
        
        return bundle_file
    
    def load_bundle(self, bundle_path: Path) -> Dict[str, Any]:
        """Load a saved context bundle"""
        with bundle_path.open("r") as f:
            bundle = json.load(f)
        
        return bundle
    
    def replay_bundle(
        self,
        bundle_id: str,
        target_agent_id: str
    ) -> Dict[str, Any]:
        """
        Replay a context bundle to prime a new agent
        
        Returns summary that can be used to quickly bring
        new agent up to speed (~70% of context)
        """
        bundle_file = self.bundle_dir / f"{bundle_id}.json"
        
        if not bundle_file.exists():
            raise ValueError(f"Bundle not found: {bundle_id}")
        
        bundle = self.load_bundle(bundle_file)
        
        # Create replay summary
        summary = {
            "original_agent_id": bundle["agent_id"],
            "target_agent_id": target_agent_id,
            "initial_prompt": bundle["initial_prompt"],
            "files_read": bundle["files_read"],
            "files_written": bundle["files_written"],
            "tools_used": bundle["tools_used"],
            "operation_count": len(bundle["operations"]),
            "duration_seconds": bundle.get("duration_seconds", 0),
            "replay_timestamp": time.time()
        }
        
        logger.info(f"Replayed bundle: {bundle_id} -> agent {target_agent_id}")
        
        return summary

