"""
REP (Ripple Effect Protocol) Metrics for Athena

Prometheus metrics for REP coordination monitoring and observability.

Metrics Categories:
1. Message flow (sent/received)
2. Coordination decisions (adjustments/fallbacks)
3. Peer activity (peer count, model distribution)
4. Sensitivity signals (by type and value)
5. Performance (latency, throughput)
"""

import logging
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, Info

logger = logging.getLogger(__name__)

# ============================================================================
# Message Flow Metrics
# ============================================================================

rep_messages_sent_total = Counter(
    'athena_rep_messages_sent_total',
    'Total REP messages sent by this agent',
    ['agent_id', 'channel']
)

rep_messages_received_total = Counter(
    'athena_rep_messages_received_total',
    'Total REP messages received from peers',
    ['agent_id', 'channel']
)

rep_message_size_bytes = Histogram(
    'athena_rep_message_size_bytes',
    'Size of REP messages in bytes',
    ['agent_id', 'message_type'],
    buckets=[100, 500, 1000, 2000, 5000, 10000]
)

# ============================================================================
# Coordination Decision Metrics
# ============================================================================

rep_coordination_adjustments_total = Counter(
    'athena_rep_coordination_adjustments_total',
    'Number of routing decisions adjusted by REP coordination',
    ['agent_id', 'reason', 'from_model', 'to_model']
)

rep_fallbacks_avoided_total = Counter(
    'athena_rep_fallbacks_avoided_total',
    'Number of fallbacks avoided due to REP coordination',
    ['agent_id', 'model']
)

rep_clustering_prevented_total = Counter(
    'athena_rep_clustering_prevented_total',
    'Number of times peer clustering was prevented',
    ['agent_id', 'model']
)

# ============================================================================
# Peer Activity Metrics
# ============================================================================

rep_active_peers = Gauge(
    'athena_rep_active_peers',
    'Number of active peer agents in REP network',
    ['agent_id', 'channel']
)

rep_peer_model_distribution = Gauge(
    'athena_rep_peer_model_distribution',
    'Distribution of model choices across peers',
    ['agent_id', 'model']
)

rep_peer_avg_confidence = Gauge(
    'athena_rep_peer_avg_confidence',
    'Average confidence score across peer decisions',
    ['agent_id']
)

# ============================================================================
# Sensitivity Signal Metrics
# ============================================================================

rep_sensitivity_calculated_total = Counter(
    'athena_rep_sensitivity_calculated_total',
    'Total sensitivity signals calculated',
    ['agent_id', 'sensitivity_type']
)

rep_sensitivity_value = Histogram(
    'athena_rep_sensitivity_value',
    'Distribution of sensitivity values (-1.0 to 1.0)',
    ['agent_id', 'sensitivity_type'],
    buckets=[-1.0, -0.9, -0.7, -0.5, -0.3, -0.1, 0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
)

rep_critical_sensitivities_total = Counter(
    'athena_rep_critical_sensitivities_total',
    'Number of critical sensitivities (value < -0.9) detected',
    ['agent_id', 'sensitivity_type']
)

# ============================================================================
# Performance Metrics
# ============================================================================

rep_coordination_latency_seconds = Histogram(
    'athena_rep_coordination_latency_seconds',
    'Latency of REP coordination operations',
    ['agent_id', 'operation'],
    buckets=[0.001, 0.005, 0.010, 0.020, 0.050, 0.100, 0.200, 0.500]
)

rep_redis_latency_seconds = Histogram(
    'athena_rep_redis_latency_seconds',
    'Latency of Redis operations (pubsub)',
    ['agent_id', 'operation'],
    buckets=[0.001, 0.002, 0.005, 0.010, 0.020, 0.050]
)

rep_message_processing_duration_seconds = Histogram(
    'athena_rep_message_processing_duration_seconds',
    'Duration to process incoming REP messages',
    ['agent_id'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.010, 0.020]
)

# ============================================================================
# System State Metrics
# ============================================================================

rep_system_queue_depth = Gauge(
    'athena_rep_system_queue_depth',
    'Current queue depth for each model',
    ['agent_id', 'model']
)

rep_system_latency_p95_ms = Gauge(
    'athena_rep_system_latency_p95_ms',
    'P95 latency for each model (milliseconds)',
    ['agent_id', 'model']
)

rep_system_cost_accumulated = Gauge(
    'athena_rep_system_cost_accumulated',
    'Accumulated cost across system',
    ['agent_id']
)

rep_system_cost_budget_remaining_pct = Gauge(
    'athena_rep_system_cost_budget_remaining_pct',
    'Remaining cost budget percentage',
    ['agent_id']
)

rep_system_available_models = Gauge(
    'athena_rep_system_available_models',
    'Number of available models',
    ['agent_id']
)

# ============================================================================
# Error Metrics
# ============================================================================

rep_errors_total = Counter(
    'athena_rep_errors_total',
    'Total REP errors encountered',
    ['agent_id', 'error_type', 'operation']
)

rep_redis_connection_failures_total = Counter(
    'athena_rep_redis_connection_failures_total',
    'Total Redis connection failures',
    ['agent_id']
)

rep_message_parse_errors_total = Counter(
    'athena_rep_message_parse_errors_total',
    'Total message parsing errors',
    ['agent_id']
)

# ============================================================================
# Hybrid Calculator Metrics (LLM vs Rules)
# ============================================================================

rep_calculation_mode_total = Counter(
    'athena_rep_calculation_mode_total',
    'Total calculations by mode (rule_based, llm, hybrid)',
    ['agent_id', 'mode']
)

rep_scenario_complexity_total = Counter(
    'athena_rep_scenario_complexity_total',
    'Total scenarios by complexity (simple, complex, critical)',
    ['agent_id', 'complexity']
)

rep_llm_calculations_total = Counter(
    'athena_rep_llm_calculations_total',
    'Total LLM-based calculations',
    ['agent_id', 'status']  # success | failure | timeout
)

rep_llm_calculation_latency_seconds = Histogram(
    'athena_rep_llm_calculation_latency_seconds',
    'Latency of LLM-based calculations',
    ['agent_id'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

rep_rule_vs_llm_agreement_total = Counter(
    'athena_rep_rule_vs_llm_agreement_total',
    'Agreement between rule-based and LLM calculations',
    ['agent_id', 'agreement']  # agree | disagree
)

rep_llm_confidence_score = Histogram(
    'athena_rep_llm_confidence_score',
    'LLM confidence scores',
    ['agent_id'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

rep_calculation_fallback_total = Counter(
    'athena_rep_calculation_fallback_total',
    'Number of fallbacks from LLM to rules',
    ['agent_id', 'reason']  # timeout | error | low_confidence
)

rep_policy_mode = Gauge(
    'athena_rep_policy_mode',
    'Current policy mode (0=rules, 1=llm, 2=hybrid)',
    ['agent_id']
)

# ============================================================================
# Info Metrics
# ============================================================================

rep_agent_info = Info(
    'athena_rep_agent_info',
    'REP agent configuration and metadata'
)


# ============================================================================
# Helper Class for Recording Metrics
# ============================================================================

class REPMetrics:
    """
    Helper class for recording REP metrics
    
    Simplifies metric recording with sensible defaults and error handling.
    """
    
    def __init__(self, agent_id: str, channel: str = "athena:rep:routing"):
        self.agent_id = agent_id
        self.channel = channel
        
        # Set agent info
        rep_agent_info.info({
            'agent_id': agent_id,
            'channel': channel
        })
    
    def record_message_sent(self):
        """Record a sent REP message"""
        rep_messages_sent_total.labels(
            agent_id=self.agent_id,
            channel=self.channel
        ).inc()
    
    def record_message_received(self):
        """Record a received REP message"""
        rep_messages_received_total.labels(
            agent_id=self.agent_id,
            channel=self.channel
        ).inc()
    
    def record_message_size(self, size_bytes: int, message_type: str = "standard"):
        """Record message size"""
        rep_message_size_bytes.labels(
            agent_id=self.agent_id,
            message_type=message_type
        ).observe(size_bytes)
    
    def record_coordination_adjustment(
        self,
        reason: str,
        from_model: str,
        to_model: str
    ):
        """Record a coordination adjustment"""
        rep_coordination_adjustments_total.labels(
            agent_id=self.agent_id,
            reason=reason,
            from_model=from_model,
            to_model=to_model
        ).inc()
    
    def record_clustering_prevented(self, model: str):
        """Record prevented clustering"""
        rep_clustering_prevented_total.labels(
            agent_id=self.agent_id,
            model=model
        ).inc()
    
    def record_active_peers(self, count: int):
        """Record number of active peers"""
        rep_active_peers.labels(
            agent_id=self.agent_id,
            channel=self.channel
        ).set(count)
    
    def record_peer_model_distribution(self, model: str, count: int):
        """Record peer model distribution"""
        rep_peer_model_distribution.labels(
            agent_id=self.agent_id,
            model=model
        ).set(count)
    
    def record_peer_avg_confidence(self, confidence: float):
        """Record average peer confidence"""
        rep_peer_avg_confidence.labels(
            agent_id=self.agent_id
        ).set(confidence)
    
    def record_sensitivity_calculated(self, sensitivity_type: str, value: float):
        """Record calculated sensitivity"""
        rep_sensitivity_calculated_total.labels(
            agent_id=self.agent_id,
            sensitivity_type=sensitivity_type
        ).inc()
        
        rep_sensitivity_value.labels(
            agent_id=self.agent_id,
            sensitivity_type=sensitivity_type
        ).observe(value)
        
        # Track critical sensitivities
        if value < -0.9:
            rep_critical_sensitivities_total.labels(
                agent_id=self.agent_id,
                sensitivity_type=sensitivity_type
            ).inc()
    
    def record_coordination_latency(self, operation: str, duration_seconds: float):
        """Record coordination operation latency"""
        rep_coordination_latency_seconds.labels(
            agent_id=self.agent_id,
            operation=operation
        ).observe(duration_seconds)
    
    def record_redis_latency(self, operation: str, duration_seconds: float):
        """Record Redis operation latency"""
        rep_redis_latency_seconds.labels(
            agent_id=self.agent_id,
            operation=operation
        ).observe(duration_seconds)
    
    def record_message_processing_duration(self, duration_seconds: float):
        """Record message processing duration"""
        rep_message_processing_duration_seconds.labels(
            agent_id=self.agent_id
        ).observe(duration_seconds)
    
    def record_system_state(
        self,
        queue_depths: dict,
        latencies_p95: dict,
        cost_accumulated: float,
        cost_budget: float,
        available_models: int
    ):
        """Record system state metrics"""
        # Queue depths
        for model, depth in queue_depths.items():
            rep_system_queue_depth.labels(
                agent_id=self.agent_id,
                model=model
            ).set(depth)
        
        # Latencies
        for model, latency in latencies_p95.items():
            rep_system_latency_p95_ms.labels(
                agent_id=self.agent_id,
                model=model
            ).set(latency)
        
        # Cost
        rep_system_cost_accumulated.labels(
            agent_id=self.agent_id
        ).set(cost_accumulated)
        
        if cost_budget > 0:
            budget_remaining_pct = ((cost_budget - cost_accumulated) / cost_budget) * 100
            rep_system_cost_budget_remaining_pct.labels(
                agent_id=self.agent_id
            ).set(budget_remaining_pct)
        
        # Available models
        rep_system_available_models.labels(
            agent_id=self.agent_id
        ).set(available_models)
    
    def record_error(self, error_type: str, operation: str):
        """Record an error"""
        rep_errors_total.labels(
            agent_id=self.agent_id,
            error_type=error_type,
            operation=operation
        ).inc()
    
    def record_redis_connection_failure(self):
        """Record Redis connection failure"""
        rep_redis_connection_failures_total.labels(
            agent_id=self.agent_id
        ).inc()
    
    def record_message_parse_error(self):
        """Record message parse error"""
        rep_message_parse_errors_total.labels(
            agent_id=self.agent_id
        ).inc()
    
    # ========================================================================
    # Hybrid Calculator Metrics
    # ========================================================================
    
    def record_calculation_mode(self, mode: str):
        """
        Record calculation mode used
        
        Args:
            mode: rule_based | llm | hybrid | critical_hybrid
        """
        rep_calculation_mode_total.labels(
            agent_id=self.agent_id,
            mode=mode
        ).inc()
    
    def record_scenario_complexity(self, complexity: str):
        """
        Record scenario complexity
        
        Args:
            complexity: simple | complex | critical
        """
        rep_scenario_complexity_total.labels(
            agent_id=self.agent_id,
            complexity=complexity
        ).inc()
    
    def record_llm_calculation(self, status: str, latency_seconds: float = 0):
        """
        Record LLM calculation attempt
        
        Args:
            status: success | failure | timeout
            latency_seconds: Calculation latency
        """
        rep_llm_calculations_total.labels(
            agent_id=self.agent_id,
            status=status
        ).inc()
        
        if latency_seconds > 0:
            rep_llm_calculation_latency_seconds.labels(
                agent_id=self.agent_id
            ).observe(latency_seconds)
    
    def record_rule_llm_agreement(self, agreement: bool):
        """
        Record agreement between rule and LLM calculations
        
        Args:
            agreement: True if agree, False if disagree
        """
        rep_rule_vs_llm_agreement_total.labels(
            agent_id=self.agent_id,
            agreement='agree' if agreement else 'disagree'
        ).inc()
    
    def record_llm_confidence(self, confidence: float):
        """
        Record LLM confidence score
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
        """
        rep_llm_confidence_score.labels(
            agent_id=self.agent_id
        ).observe(confidence)
    
    def record_calculation_fallback(self, reason: str):
        """
        Record fallback from LLM to rules
        
        Args:
            reason: timeout | error | low_confidence
        """
        rep_calculation_fallback_total.labels(
            agent_id=self.agent_id,
            reason=reason
        ).inc()
    
    def set_policy_mode(self, mode: str):
        """
        Set current policy mode
        
        Args:
            mode: rules | llm | hybrid
        """
        mode_value = {
            'rules': 0,
            'rule_based': 0,
            'llm': 1,
            'llm_based': 1,
            'hybrid': 2
        }.get(mode, 0)
        
        rep_policy_mode.labels(
            agent_id=self.agent_id
        ).set(mode_value)


# ============================================================================
# Global Metrics Instance
# ============================================================================

# This will be initialized by the router
_metrics_instance: Optional[REPMetrics] = None


def get_rep_metrics(agent_id: Optional[str] = None) -> Optional[REPMetrics]:
    """
    Get or create REP metrics instance
    
    Args:
        agent_id: Agent identifier (required for first call)
        
    Returns:
        REPMetrics instance or None if not initialized
    """
    global _metrics_instance
    
    if _metrics_instance is None and agent_id:
        _metrics_instance = REPMetrics(agent_id)
    
    return _metrics_instance


def initialize_rep_metrics(agent_id: str, channel: str = "athena:rep:routing"):
    """
    Initialize global REP metrics instance
    
    Args:
        agent_id: Agent identifier
        channel: REP channel
    """
    global _metrics_instance
    _metrics_instance = REPMetrics(agent_id, channel)
    logger.info(f"REP metrics initialized for agent {agent_id}")

