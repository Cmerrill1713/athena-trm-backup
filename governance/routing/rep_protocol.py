"""
Ripple Effect Protocol (REP) Implementation for Athena

REP enables multi-agent coordination by sharing sensitivity signals,
allowing agents to anticipate and adapt to system changes.

Reference: https://arxiv.org/abs/2510.16572 (ICLR 2026 submission)

Key Concepts:
- Agents share BOTH decisions AND sensitivities
- Sensitivities indicate how decisions would change under different conditions
- Enables anticipatory coordination without central authority
- Local-first: All coordination happens via local pubsub (Redis)

Compliance:
- ATHENA_NO_CLOUD=1: All communication is local-only
- Zero external API calls
- Privacy-preserving: Sensitivities never leave infrastructure
"""

import json
import logging
import time
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class SensitivityType(str, Enum):
    """Types of sensitivities agents can signal"""
    # Resource-based sensitivities
    MODEL_QUEUE_DEPTH = "model_queue_depth"
    LATENCY_THRESHOLD = "latency_threshold"
    MEMORY_PRESSURE = "memory_pressure"
    
    # Cost-based sensitivities
    COST_PRESSURE = "cost_pressure"
    BUDGET_EXHAUSTION = "budget_exhaustion"
    
    # Coordination-based sensitivities
    PEER_CLUSTERING = "peer_clustering"
    LOAD_IMBALANCE = "load_imbalance"
    
    # Availability-based sensitivities
    MODEL_AVAILABILITY = "model_availability"
    FALLBACK_READINESS = "fallback_readiness"
    
    # Quality-based sensitivities
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    QUALITY_DEGRADATION = "quality_degradation"


@dataclass
class REPSensitivity:
    """
    A sensitivity signal indicating how an agent's decision would change
    
    Attributes:
        type: Type of sensitivity
        value: Gradient/magnitude (-1.0 to 1.0)
            Negative = would switch away
            Positive = would stay/increase
        threshold: Condition value at which sensitivity activates
        metadata: Additional context
    """
    type: SensitivityType
    value: float  # -1.0 to 1.0
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate sensitivity value"""
        if not -1.0 <= self.value <= 1.0:
            raise ValueError(f"Sensitivity value must be in [-1.0, 1.0], got {self.value}")
    
    def would_switch(self, current_value: float) -> bool:
        """
        Determine if agent would switch given current condition value
        
        Args:
            current_value: Current value of the condition
            
        Returns:
            True if agent would switch based on sensitivity
        """
        if self.threshold is None:
            return self.value < -0.5  # Strong negative sensitivity
        
        # Check if current value exceeds threshold
        return current_value > self.threshold and self.value < 0


@dataclass
class REPDecision:
    """
    An agent's decision (e.g., which model to route to)
    """
    model: str
    confidence: float
    domain: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class REPMessage:
    """
    Complete REP protocol message
    
    Contains both the decision and sensitivity signals
    """
    agent_id: str
    timestamp: float
    decision: REPDecision
    sensitivities: List[REPSensitivity]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'agent_id': self.agent_id,
            'timestamp': self.timestamp,
            'decision': asdict(self.decision),
            'sensitivities': [
                {
                    'type': s.type.value,
                    'value': s.value,
                    'threshold': s.threshold,
                    'metadata': s.metadata
                }
                for s in self.sensitivities
            ],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'REPMessage':
        """Create from dictionary"""
        return cls(
            agent_id=data['agent_id'],
            timestamp=data['timestamp'],
            decision=REPDecision(**data['decision']),
            sensitivities=[
                REPSensitivity(
                    type=SensitivityType(s['type']),
                    value=s['value'],
                    threshold=s.get('threshold'),
                    metadata=s.get('metadata', {})
                )
                for s in data['sensitivities']
            ],
            metadata=data.get('metadata', {})
        )


@dataclass
class SystemState:
    """
    Current system state for sensitivity calculations
    """
    # Model metrics
    queue_depths: Dict[str, int] = field(default_factory=dict)
    latencies_p95: Dict[str, float] = field(default_factory=dict)
    memory_usage: Dict[str, float] = field(default_factory=dict)
    
    # Cost metrics
    accumulated_cost: float = 0.0
    cost_budget: float = 100.0
    
    # Availability metrics
    available_models: List[str] = field(default_factory=list)
    unavailable_models: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    
    def get_queue_depth(self, model: str) -> int:
        """Get queue depth for a model"""
        return self.queue_depths.get(model, 0)
    
    def get_latency_p95(self, model: str) -> float:
        """Get P95 latency for a model"""
        return self.latencies_p95.get(model, 0.0)
    
    def is_model_available(self, model: str) -> bool:
        """Check if model is available"""
        return model in self.available_models
    
    def cost_budget_remaining(self) -> float:
        """Get remaining cost budget percentage"""
        if self.cost_budget == 0:
            return 0.0
        return max(0.0, (self.cost_budget - self.accumulated_cost) / self.cost_budget)


class SensitivityCalculator:
    """
    Calculates sensitivity signals based on system state and decision
    
    Each calculator implements domain-specific sensitivity logic
    """
    
    def __init__(
        self,
        queue_depth_threshold: int = 5,
        latency_threshold_ms: float = 1000.0,
        cost_budget_threshold: float = 0.8,
        clustering_threshold: int = 3
    ):
        self.queue_depth_threshold = queue_depth_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.cost_budget_threshold = cost_budget_threshold
        self.clustering_threshold = clustering_threshold
    
    def calculate_all(
        self,
        decision: REPDecision,
        system_state: SystemState,
        peer_messages: List[REPMessage]
    ) -> List[REPSensitivity]:
        """
        Calculate all relevant sensitivities
        
        Args:
            decision: The routing decision made
            system_state: Current system state
            peer_messages: Recent peer messages
            
        Returns:
            List of sensitivity signals
        """
        sensitivities = []
        
        # Queue depth sensitivity
        sensitivities.append(
            self._calculate_queue_sensitivity(decision, system_state)
        )
        
        # Latency sensitivity
        sensitivities.append(
            self._calculate_latency_sensitivity(decision, system_state)
        )
        
        # Cost sensitivity
        sensitivities.append(
            self._calculate_cost_sensitivity(decision, system_state)
        )
        
        # Peer clustering sensitivity
        sensitivities.append(
            self._calculate_clustering_sensitivity(decision, peer_messages)
        )
        
        # Model availability sensitivity
        sensitivities.append(
            self._calculate_availability_sensitivity(decision, system_state)
        )
        
        return sensitivities
    
    def _calculate_queue_sensitivity(
        self,
        decision: REPDecision,
        system_state: SystemState
    ) -> REPSensitivity:
        """
        Calculate sensitivity to model queue depth
        
        High queue = high likelihood to switch to alternative
        """
        queue_depth = system_state.get_queue_depth(decision.model)
        
        if queue_depth > self.queue_depth_threshold:
            # High queue = strong negative sensitivity (would switch)
            normalized = min(1.0, queue_depth / (self.queue_depth_threshold * 2))
            value = -normalized  # More queue = more negative
        else:
            # Low queue = slight negative sensitivity
            value = -0.3
        
        return REPSensitivity(
            type=SensitivityType.MODEL_QUEUE_DEPTH,
            value=value,
            threshold=self.queue_depth_threshold,
            metadata={'current_queue': queue_depth}
        )
    
    def _calculate_latency_sensitivity(
        self,
        decision: REPDecision,
        system_state: SystemState
    ) -> REPSensitivity:
        """
        Calculate sensitivity to model latency
        
        High latency = high likelihood to fallback
        """
        latency_p95 = system_state.get_latency_p95(decision.model)
        
        if latency_p95 > self.latency_threshold_ms:
            # High latency = strong negative sensitivity
            excess = latency_p95 - self.latency_threshold_ms
            normalized = min(1.0, excess / self.latency_threshold_ms)
            value = -normalized
        else:
            # Good latency = slight negative sensitivity
            value = -0.2
        
        return REPSensitivity(
            type=SensitivityType.LATENCY_THRESHOLD,
            value=value,
            threshold=self.latency_threshold_ms,
            metadata={'current_latency_p95': latency_p95}
        )
    
    def _calculate_cost_sensitivity(
        self,
        decision: REPDecision,
        system_state: SystemState
    ) -> REPSensitivity:
        """
        Calculate sensitivity to cost pressure
        
        High cost accumulation = high likelihood to use cheaper models
        """
        budget_remaining = system_state.cost_budget_remaining()
        
        if budget_remaining < (1.0 - self.cost_budget_threshold):
            # Low budget = strong negative sensitivity (switch to cheaper)
            value = -0.9
        elif budget_remaining < 0.5:
            value = -0.6
        else:
            value = -0.1
        
        return REPSensitivity(
            type=SensitivityType.COST_PRESSURE,
            value=value,
            threshold=self.cost_budget_threshold,
            metadata={
                'budget_remaining_pct': budget_remaining,
                'accumulated_cost': system_state.accumulated_cost
            }
        )
    
    def _calculate_clustering_sensitivity(
        self,
        decision: REPDecision,
        peer_messages: List[REPMessage]
    ) -> REPSensitivity:
        """
        Calculate sensitivity to peer clustering
        
        Many peers using same model = avoid clustering
        """
        if not peer_messages:
            return REPSensitivity(
                type=SensitivityType.PEER_CLUSTERING,
                value=-0.1,
                threshold=self.clustering_threshold,
                metadata={'peer_count': 0}
            )
        
        # Count peers using same model
        same_model_count = sum(
            1 for msg in peer_messages
            if msg.decision.model == decision.model
        )
        
        if same_model_count >= self.clustering_threshold:
            # High clustering = strong negative sensitivity
            normalized = min(1.0, same_model_count / (self.clustering_threshold * 2))
            value = -normalized
        else:
            value = -0.1
        
        return REPSensitivity(
            type=SensitivityType.PEER_CLUSTERING,
            value=value,
            threshold=self.clustering_threshold,
            metadata={
                'peer_count': len(peer_messages),
                'same_model_count': same_model_count
            }
        )
    
    def _calculate_availability_sensitivity(
        self,
        decision: REPDecision,
        system_state: SystemState
    ) -> REPSensitivity:
        """
        Calculate sensitivity to model availability changes
        
        Model unavailable = immediate switch
        """
        is_available = system_state.is_model_available(decision.model)
        
        if not is_available:
            # Model unavailable = must switch immediately
            value = -1.0
        else:
            # Model available = slight positive (stay)
            value = 0.2
        
        return REPSensitivity(
            type=SensitivityType.MODEL_AVAILABILITY,
            value=value,
            metadata={
                'is_available': is_available,
                'available_models': len(system_state.available_models)
            }
        )


class REPCoordinator:
    """
    Base REP coordinator for multi-agent coordination
    
    Responsibilities:
    1. Calculate sensitivity signals
    2. Broadcast messages to peers
    3. Receive and process peer messages
    4. Coordinate decisions based on sensitivities
    
    Local-first: All communication via local Redis pubsub
    """
    
    def __init__(
        self,
        agent_id: str,
        channel: str = "athena:rep:routing",
        redis_url: str = "redis://127.0.0.1:6379",
        message_ttl_seconds: int = 60,
        sensitivity_calculator: Optional[SensitivityCalculator] = None
    ):
        """
        Initialize REP coordinator
        
        Args:
            agent_id: Unique identifier for this agent
            channel: Redis pubsub channel for REP messages
            redis_url: Local Redis URL (must be localhost/127.0.0.1)
            message_ttl_seconds: How long to keep peer messages
            sensitivity_calculator: Custom sensitivity calculator
        """
        self.agent_id = agent_id
        self.channel = channel
        self.redis_url = redis_url
        self.message_ttl_seconds = message_ttl_seconds
        self.sensitivity_calculator = sensitivity_calculator or SensitivityCalculator()
        
        # Validate local-only
        self._validate_local_only()
        
        # Redis client (lazy init)
        self._redis = None
        self._pubsub = None
        
        # Peer message cache
        self.peer_messages: List[REPMessage] = []
        self.last_cleanup = time.time()
        
        logger.info(
            f"REP Coordinator initialized: agent={agent_id}, "
            f"channel={channel}, redis={redis_url}"
        )
    
    def _validate_local_only(self):
        """Ensure Redis URL is local-only (ATHENA_NO_CLOUD=1 compliance)"""
        if os.getenv('ATHENA_NO_CLOUD') == '1':
            if not any(host in self.redis_url for host in ['127.0.0.1', 'localhost']):
                raise ValueError(
                    f"ATHENA_NO_CLOUD=1 but Redis URL is not local: {self.redis_url}"
                )
    
    @property
    def redis(self):
        """Lazy Redis connection"""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self.redis_url)
                logger.info(f"Connected to Redis at {self.redis_url}")
            except ImportError:
                logger.warning("redis-py not installed, REP coordination disabled")
                self._redis = None
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None
        return self._redis
    
    def broadcast_message(
        self,
        decision: REPDecision,
        system_state: SystemState
    ) -> Optional[REPMessage]:
        """
        Calculate sensitivities and broadcast REP message to peers
        
        Args:
            decision: The routing decision made
            system_state: Current system state
            
        Returns:
            The broadcasted message, or None if failed
        """
        try:
            # Calculate sensitivities
            sensitivities = self.sensitivity_calculator.calculate_all(
                decision,
                system_state,
                self.peer_messages
            )
            
            # Create REP message
            message = REPMessage(
                agent_id=self.agent_id,
                timestamp=time.time(),
                decision=decision,
                sensitivities=sensitivities,
                metadata={}
            )
            
            # Broadcast to peers
            if self.redis:
                self.redis.publish(
                    self.channel,
                    json.dumps(message.to_dict())
                )
                logger.debug(f"Broadcasted REP message: {self.agent_id} -> {decision.model}")
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to broadcast REP message: {e}")
            return None
    
    def receive_messages(self, timeout: float = 0.001) -> List[REPMessage]:
        """
        Receive new peer messages (non-blocking)
        
        Args:
            timeout: Timeout in seconds (default 1ms for low latency)
            
        Returns:
            List of new peer messages
        """
        if not self.redis:
            return []
        
        try:
            # Initialize pubsub if needed
            if self._pubsub is None:
                self._pubsub = self.redis.pubsub()
                self._pubsub.subscribe(self.channel)
                logger.info(f"Subscribed to REP channel: {self.channel}")
            
            # Get messages (non-blocking)
            new_messages = []
            message = self._pubsub.get_message(timeout=timeout)
            
            while message:
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        rep_msg = REPMessage.from_dict(data)
                        
                        # Ignore own messages
                        if rep_msg.agent_id != self.agent_id:
                            new_messages.append(rep_msg)
                            self.peer_messages.append(rep_msg)
                    except Exception as e:
                        logger.warning(f"Failed to parse REP message: {e}")
                
                message = self._pubsub.get_message(timeout=timeout)
            
            # Cleanup old messages
            self._cleanup_old_messages()
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Failed to receive REP messages: {e}")
            return []
    
    def _cleanup_old_messages(self):
        """Remove messages older than TTL"""
        now = time.time()
        
        # Only cleanup every 10 seconds
        if now - self.last_cleanup < 10:
            return
        
        cutoff = now - self.message_ttl_seconds
        self.peer_messages = [
            msg for msg in self.peer_messages
            if msg.timestamp > cutoff
        ]
        self.last_cleanup = now
        
        logger.debug(f"Cleaned up old messages, {len(self.peer_messages)} remaining")
    
    def coordinate_decision(
        self,
        base_decision: REPDecision,
        system_state: SystemState,
        alternative_models: Optional[List[str]] = None
    ) -> REPDecision:
        """
        Coordinate decision based on peer sensitivities
        
        This implements the core REP coordination logic:
        1. Check own sensitivities
        2. Check peer sensitivities
        3. Adjust decision if needed
        
        Args:
            base_decision: Initial routing decision
            system_state: Current system state
            alternative_models: Alternative models to consider
            
        Returns:
            Adjusted decision (may be same as base_decision)
        """
        # Receive latest peer messages
        self.receive_messages()
        
        # Calculate our sensitivities
        my_sensitivities = self.sensitivity_calculator.calculate_all(
            base_decision,
            system_state,
            self.peer_messages
        )
        
        # Check if we should adjust based on sensitivities
        for sensitivity in my_sensitivities:
            # Peer clustering check
            if sensitivity.type == SensitivityType.PEER_CLUSTERING:
                if sensitivity.value < -0.5:  # Strong negative
                    # Find alternative model with less clustering
                    alternative = self._find_less_clustered_model(
                        base_decision.model,
                        alternative_models or []
                    )
                    if alternative:
                        logger.info(
                            f"REP coordination: Switching from {base_decision.model} "
                            f"to {alternative} (peer clustering detected)"
                        )
                        return REPDecision(
                            model=alternative,
                            confidence=base_decision.confidence * 0.95,
                            domain=base_decision.domain,
                            metadata={
                                'rep_coordination': True,
                                'reason': 'peer_clustering_avoidance',
                                'original_model': base_decision.model
                            }
                        )
            
            # Queue depth check
            elif sensitivity.type == SensitivityType.MODEL_QUEUE_DEPTH:
                if sensitivity.value < -0.7:  # Very high queue
                    logger.info(
                        f"REP coordination: High queue detected for {base_decision.model}"
                    )
                    # Could trigger fallback here
            
            # Latency check
            elif sensitivity.type == SensitivityType.LATENCY_THRESHOLD:
                if sensitivity.value < -0.7:  # Very high latency
                    logger.warning(
                        f"REP coordination: High latency detected for {base_decision.model}"
                    )
                    # Could trigger fallback here
        
        # No adjustment needed
        return base_decision
    
    def _find_less_clustered_model(
        self,
        current_model: str,
        alternatives: List[str]
    ) -> Optional[str]:
        """
        Find alternative model with less peer clustering
        
        Args:
            current_model: Current model choice
            alternatives: Alternative models to consider
            
        Returns:
            Less clustered alternative, or None
        """
        if not alternatives or not self.peer_messages:
            return None
        
        # Count peer usage per model
        model_counts = {}
        for msg in self.peer_messages:
            model = msg.decision.model
            model_counts[model] = model_counts.get(model, 0) + 1
        
        # Find least used alternative
        current_count = model_counts.get(current_model, 0)
        
        least_used_model = None
        least_used_count = float('inf')
        
        for model in alternatives:
            if model == current_model:
                continue
            count = model_counts.get(model, 0)
            if count < least_used_count:
                least_used_count = count
                least_used_model = model
        
        # Only switch if significantly less clustered
        if least_used_model and least_used_count < current_count * 0.5:
            return least_used_model
        
        return None
    
    def get_peer_summary(self) -> Dict[str, Any]:
        """
        Get summary of peer activity
        
        Returns:
            Summary statistics about peer messages
        """
        if not self.peer_messages:
            return {
                'peer_count': 0,
                'model_distribution': {},
                'avg_confidence': 0.0
            }
        
        model_counts = {}
        total_confidence = 0.0
        
        for msg in self.peer_messages:
            model = msg.decision.model
            model_counts[model] = model_counts.get(model, 0) + 1
            total_confidence += msg.decision.confidence
        
        return {
            'peer_count': len(self.peer_messages),
            'model_distribution': model_counts,
            'avg_confidence': total_confidence / len(self.peer_messages),
            'message_age_seconds': time.time() - min(
                msg.timestamp for msg in self.peer_messages
            )
        }
    
    def shutdown(self):
        """Clean shutdown of REP coordinator"""
        if self._pubsub:
            self._pubsub.unsubscribe()
            self._pubsub.close()
        if self._redis:
            self._redis.close()
        logger.info(f"REP Coordinator shutdown: {self.agent_id}")

