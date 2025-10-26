"""
REP-Enhanced Router for Athena

Integrates Ripple Effect Protocol with existing routing infrastructure
to enable multi-agent coordination with sensitivity-aware routing.

This router is a drop-in replacement for BasicRouter with added REP coordination.
"""

import logging
import time
from pathlib import Path
from typing import Optional, List

from governance.routing.basic_router import (
    BasicRouter,
    RoutingRequest,
    RoutingChoice
)
from governance.routing.rep_protocol import (
    REPCoordinator,
    REPDecision,
    SystemState,
    SensitivityCalculator
)
from governance.routing.rep_hybrid_calculator import HybridSensitivityCalculator
from governance.observability.routing_metrics import routing_metrics
from governance.observability.rep_metrics import get_rep_metrics

logger = logging.getLogger(__name__)


class REPEnhancedRouter(BasicRouter):
    """
    REP-Enhanced Router with multi-agent coordination
    
    Features:
    - All features of BasicRouter
    - Broadcasts routing decisions with sensitivity signals
    - Receives peer sensitivities for coordination
    - Adjusts routing based on peer behavior
    - Anti-clustering: Avoids thundering herd problems
    - Cost coordination: Respects collective budget constraints
    - Load distribution: Balances load across models
    
    Usage:
        # Drop-in replacement for BasicRouter
        router = REPEnhancedRouter(
            profiles_path=Path("model_profiles.json"),
            agent_id="router_1"
        )
        
        # Route with REP coordination
        choice = router.route(request)
    """
    
    def __init__(
        self,
        profiles_path: Path,
        agent_id: Optional[str] = None,
        fallback_threshold: float = 0.7,
        enable_rep: bool = True,
        redis_url: str = "redis://127.0.0.1:6379",
        rep_channel: str = "athena:rep:routing",
        calculator_mode: str = "hybrid"  # hybrid | rule_based | llm_based
    ):
        """
        Initialize REP-enhanced router
        
        Args:
            profiles_path: Path to model_profiles.json
            agent_id: Unique agent identifier (auto-generated if None)
            fallback_threshold: Confidence threshold for fallback
            enable_rep: Enable REP coordination (disable for testing)
            redis_url: Local Redis URL for REP pubsub
            rep_channel: Redis channel for REP messages
            calculator_mode: Calculation mode (hybrid | rule_based | llm_based)
        """
        super().__init__(profiles_path, fallback_threshold)
        
        # Generate agent ID if not provided
        self.agent_id = agent_id or f"router_{id(self)}"
        self.enable_rep = enable_rep
        self.calculator_mode = calculator_mode
        
        # Initialize REP coordinator with appropriate calculator
        if self.enable_rep:
            try:
                # Create sensitivity calculator based on mode
                if calculator_mode == "hybrid":
                    sensitivity_calculator = HybridSensitivityCalculator(
                        enable_llm=True
                    )
                    logger.info(f"Using hybrid calculator (rules + LLM)")
                elif calculator_mode == "llm_based":
                    from governance.routing.rep_llm_policy import LLMSensitivityCalculator
                    sensitivity_calculator = LLMSensitivityCalculator()
                    logger.info(f"Using LLM-based calculator")
                else:  # rule_based
                    sensitivity_calculator = SensitivityCalculator()
                    logger.info(f"Using rule-based calculator")
                
                self.rep_coordinator = REPCoordinator(
                    agent_id=self.agent_id,
                    channel=rep_channel,
                    redis_url=redis_url,
                    sensitivity_calculator=sensitivity_calculator
                )
                
                # Initialize metrics
                rep_metrics = get_rep_metrics(self.agent_id)
                if rep_metrics:
                    rep_metrics.set_policy_mode(calculator_mode)
                
                logger.info(
                    f"REP coordination enabled for agent {self.agent_id} "
                    f"with {calculator_mode} calculator"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize REP coordinator: {e}. "
                    "Falling back to non-REP mode."
                )
                self.enable_rep = False
                self.rep_coordinator = None
        else:
            self.rep_coordinator = None
            logger.info(
                f"REP coordination disabled for agent {self.agent_id}"
            )
        
        # System state tracking
        self.system_state = SystemState()
        self.last_state_update = time.time()
    
    def route(self, request: RoutingRequest) -> RoutingChoice:
        """
        Route with REP coordination
        
        Flow:
        1. Get base routing decision
        2. Update system state
        3. Calculate sensitivities
        4. Check peer sensitivities
        5. Adjust decision if needed
        6. Broadcast our decision + sensitivities
        7. Return final choice
        
        Args:
            request: Routing request
            
        Returns:
            Routing choice (potentially adjusted by REP)
        """
        start_time = time.time()
        
        # Step 1: Get base routing decision
        base_choice = super().route(request)
        
        # If REP disabled, return base choice
        if not self.enable_rep or not self.rep_coordinator:
            return base_choice
        
        try:
            # Step 2: Update system state
            self._update_system_state()
            
            # Step 3: Convert to REP decision
            base_decision = REPDecision(
                model=base_choice.model,
                confidence=base_choice.confidence,
                domain=base_choice.domain,
                metadata=base_choice.metadata
            )
            
            # Step 4: Get alternative models for coordination
            alternatives = self._get_alternative_models(request.domain)
            
            # Step 5: Coordinate with peers (may adjust decision)
            coordinated_decision = self.rep_coordinator.coordinate_decision(
                base_decision,
                self.system_state,
                alternatives
            )
            
            # Step 6: Broadcast our decision + sensitivities
            self.rep_coordinator.broadcast_message(
                coordinated_decision,
                self.system_state
            )
            
            # Step 7: Convert back to RoutingChoice
            final_choice = RoutingChoice(
                model=coordinated_decision.model,
                confidence=coordinated_decision.confidence,
                domain=coordinated_decision.domain,
                latency_ms=(time.time() - start_time) * 1000,
                metadata={
                    **coordinated_decision.metadata,
                    'rep_enabled': True,
                    'agent_id': self.agent_id
                }
            )
            
            # Record metrics
            if coordinated_decision.model != base_choice.model:
                routing_metrics.record_fallback(
                    reason='rep_coordination',
                    from_model=base_choice.model,
                    to_model=coordinated_decision.model
                )
                logger.info(
                    f"REP coordination changed routing: "
                    f"{base_choice.model} -> {coordinated_decision.model}"
                )
            
            return final_choice
            
        except Exception as e:
            logger.error(f"REP coordination failed: {e}", exc_info=True)
            # Fallback to base choice on error
            return base_choice
    
    def _update_system_state(self):
        """
        Update system state for sensitivity calculations
        
        Fetches metrics from Prometheus/local monitoring
        """
        now = time.time()
        
        # Only update every 5 seconds to reduce overhead
        if now - self.last_state_update < 5:
            return
        
        try:
            # Update queue depths (from metrics)
            self.system_state.queue_depths = self._get_queue_depths()
            
            # Update latencies (from metrics)
            self.system_state.latencies_p95 = self._get_latencies()
            
            # Update available models
            self.system_state.available_models = [m.model_id for m in self.models]
            
            # Update cost tracking
            self.system_state.accumulated_cost = self._get_accumulated_cost()
            
            self.last_state_update = now
            
        except Exception as e:
            logger.error(f"Failed to update system state: {e}")
    
    def _get_queue_depths(self) -> dict:
        """
        Get current queue depths for each model
        
        In production, this would query actual queue metrics.
        For now, returns empty dict (no queuing).
        """
        # TODO: Integrate with actual queue metrics
        return {}
    
    def _get_latencies(self) -> dict:
        """
        Get P95 latencies for each model
        
        In production, this would query Prometheus metrics.
        For now, uses model profile latencies.
        """
        latencies = {}
        for model in self.models:
            latencies[model.model_id] = model.latency_p95_ms
        return latencies
    
    def _get_accumulated_cost(self) -> float:
        """
        Get accumulated cost across all agents
        
        In production, this would query cost tracking metrics.
        For now, returns 0.
        """
        # TODO: Integrate with cost tracking
        return 0.0
    
    def _get_alternative_models(self, domain: str) -> List[str]:
        """
        Get alternative models for a domain
        
        Args:
            domain: Domain to get alternatives for
            
        Returns:
            List of model IDs in the domain
        """
        return [
            m.model_id for m in self.models
            if m.domain == domain
        ]
    
    def get_rep_stats(self) -> dict:
        """
        Get REP coordination statistics
        
        Returns:
            Statistics about REP coordination
        """
        if not self.enable_rep or not self.rep_coordinator:
            return {
                'enabled': False,
                'agent_id': self.agent_id
            }
        
        peer_summary = self.rep_coordinator.get_peer_summary()
        
        stats = {
            'enabled': True,
            'agent_id': self.agent_id,
            'calculator_mode': self.calculator_mode,
            'peer_count': peer_summary['peer_count'],
            'peer_model_distribution': peer_summary['model_distribution'],
            'peer_avg_confidence': peer_summary['avg_confidence'],
            'system_state': {
                'available_models': len(self.system_state.available_models),
                'accumulated_cost': self.system_state.accumulated_cost,
                'cost_budget': self.system_state.cost_budget,
                'budget_remaining_pct': self.system_state.cost_budget_remaining()
            }
        }
        
        # Add hybrid calculator stats if available
        if self.calculator_mode == "hybrid":
            calc = self.rep_coordinator.sensitivity_calculator
            if hasattr(calc, 'get_stats'):
                stats['calculator_stats'] = calc.get_stats()
        
        return stats
    
    def shutdown(self):
        """Clean shutdown of router and REP coordinator"""
        if self.rep_coordinator:
            self.rep_coordinator.shutdown()
        logger.info(f"REP-enhanced router shutdown: {self.agent_id}")


# Convenience function for backward compatibility
def create_router(
    profiles_path: Path,
    enable_rep: bool = True,
    **kwargs
) -> BasicRouter:
    """
    Create router with optional REP coordination
    
    Args:
        profiles_path: Path to model profiles
        enable_rep: Enable REP coordination
        **kwargs: Additional arguments for router
        
    Returns:
        Router instance (REP-enhanced if enabled)
    """
    if enable_rep:
        return REPEnhancedRouter(profiles_path=profiles_path, **kwargs)
    else:
        return BasicRouter(profiles_path=profiles_path)

