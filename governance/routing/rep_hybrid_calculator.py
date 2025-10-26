"""
Hybrid Sensitivity Calculator for REP

Combines fast rule-based calculations with intelligent LLM reasoning.

Strategy:
- Simple scenarios (95%): Use rule-based calculator (5-10ms)
- Complex scenarios (5%): Use LLM reasoning (50-200ms)
- Critical scenarios (1%): Use both and validate

This provides the best of both worlds: speed for common cases,
intelligence for complex coordination challenges.
"""

import logging
import time
from typing import List, Optional
from enum import Enum

from governance.routing.rep_protocol import (
    REPDecision,
    REPSensitivity,
    REPMessage,
    SystemState,
    SensitivityCalculator,
    SensitivityType
)
from governance.routing.rep_llm_policy import LLMSensitivityCalculator

logger = logging.getLogger(__name__)


class ScenarioComplexity(str, Enum):
    """Complexity classification for scenarios"""
    SIMPLE = "simple"      # Rule-based is sufficient
    COMPLEX = "complex"    # LLM reasoning helpful
    CRITICAL = "critical"  # Use both for validation


class HybridSensitivityCalculator:
    """
    Hybrid calculator combining rules and LLM reasoning
    
    Decision Flow:
    1. Assess scenario complexity
    2. Simple → Rule-based (fast path)
    3. Complex → LLM reasoning (smart path)
    4. Critical → Both + validation (safe path)
    
    Features:
    - Automatic complexity assessment
    - Fallback to rules if LLM fails
    - Configurable thresholds
    - Metrics for monitoring
    """
    
    def __init__(
        self,
        rule_calculator: Optional[SensitivityCalculator] = None,
        llm_calculator: Optional[LLMSensitivityCalculator] = None,
        enable_llm: bool = True,
        complexity_thresholds: Optional[dict] = None
    ):
        """
        Initialize hybrid calculator
        
        Args:
            rule_calculator: Rule-based calculator (created if None)
            llm_calculator: LLM calculator (created if None)
            enable_llm: Enable LLM reasoning (disable for testing)
            complexity_thresholds: Custom complexity thresholds
        """
        self.rule_calculator = rule_calculator or SensitivityCalculator()
        self.llm_calculator = llm_calculator or LLMSensitivityCalculator() if enable_llm else None
        self.enable_llm = enable_llm and self.llm_calculator is not None
        
        # Complexity thresholds
        self.thresholds = complexity_thresholds or {
            'simple': {
                'max_peers': 5,
                'min_budget_remaining': 0.5,
                'max_queue_depth': 10,
                'max_latency_p95': 2000,
            },
            'critical': {
                'min_budget_remaining': 0.1,
                'max_queue_depth': 50,
                'min_available_models': 2,
                'max_peer_clustering': 15,
            }
        }
        
        # Statistics
        self.stats = {
            'total_calculations': 0,
            'simple_count': 0,
            'complex_count': 0,
            'critical_count': 0,
            'llm_failures': 0,
            'llm_fallbacks': 0,
        }
        
        logger.info(
            f"Hybrid Sensitivity Calculator initialized: "
            f"llm_enabled={self.enable_llm}"
        )
    
    def calculate_all(
        self,
        decision: REPDecision,
        system_state: SystemState,
        peer_messages: List[REPMessage]
    ) -> List[REPSensitivity]:
        """
        Calculate sensitivities using hybrid approach
        
        Args:
            decision: Current routing decision
            system_state: System state
            peer_messages: Recent peer messages
            
        Returns:
            List of sensitivities (from rules or LLM)
        """
        start_time = time.time()
        self.stats['total_calculations'] += 1
        
        # Assess scenario complexity
        complexity = self._assess_complexity(system_state, peer_messages)
        
        # Route to appropriate calculator
        try:
            if complexity == ScenarioComplexity.SIMPLE:
                # Fast path: Rule-based
                self.stats['simple_count'] += 1
                sensitivities = self.rule_calculator.calculate_all(
                    decision, system_state, peer_messages
                )
                source = "rules"
                
            elif complexity == ScenarioComplexity.COMPLEX:
                # Smart path: LLM reasoning
                self.stats['complex_count'] += 1
                if self.enable_llm:
                    try:
                        sensitivities = self.llm_calculator.calculate_sensitivities(
                            decision, system_state, peer_messages
                        )
                        source = "llm"
                    except Exception as e:
                        logger.warning(f"LLM calculation failed, falling back to rules: {e}")
                        self.stats['llm_fallbacks'] += 1
                        sensitivities = self.rule_calculator.calculate_all(
                            decision, system_state, peer_messages
                        )
                        source = "rules_fallback"
                else:
                    # LLM disabled, use rules
                    sensitivities = self.rule_calculator.calculate_all(
                        decision, system_state, peer_messages
                    )
                    source = "rules"
                
            else:  # CRITICAL
                # Safe path: Use both and validate
                self.stats['critical_count'] += 1
                sensitivities = self._handle_critical_scenario(
                    decision, system_state, peer_messages
                )
                source = "critical_hybrid"
            
            # Add metadata
            for sens in sensitivities:
                sens.metadata['complexity'] = complexity.value
                sens.metadata['calculator'] = source
            
            # Log stats periodically
            if self.stats['total_calculations'] % 100 == 0:
                self._log_stats()
            
            latency_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Hybrid calculation complete: complexity={complexity.value}, "
                f"source={source}, latency={latency_ms:.1f}ms"
            )
            
            return sensitivities
            
        except Exception as e:
            logger.error(f"Hybrid calculation failed: {e}", exc_info=True)
            # Emergency fallback to rules
            return self.rule_calculator.calculate_all(
                decision, system_state, peer_messages
            )
    
    def _assess_complexity(
        self,
        system_state: SystemState,
        peer_messages: List[REPMessage]
    ) -> ScenarioComplexity:
        """
        Assess scenario complexity
        
        Uses heuristics to determine if situation is simple,
        complex, or critical.
        
        Args:
            system_state: Current system state
            peer_messages: Recent peer messages
            
        Returns:
            Complexity classification
        """
        peer_count = len(peer_messages)
        budget_remaining = system_state.cost_budget_remaining()
        
        # Get max queue depth
        max_queue = max(system_state.queue_depths.values()) if system_state.queue_depths else 0
        
        # Get max latency
        max_latency = max(system_state.latencies_p95.values()) if system_state.latencies_p95 else 0
        
        # Count peer clustering
        if peer_messages:
            model_counts = {}
            for msg in peer_messages:
                model = msg.decision.model
                model_counts[model] = model_counts.get(model, 0) + 1
            max_clustering = max(model_counts.values()) if model_counts else 0
        else:
            max_clustering = 0
        
        # Check for CRITICAL conditions
        critical_conditions = [
            budget_remaining < self.thresholds['critical']['min_budget_remaining'],
            max_queue > self.thresholds['critical']['max_queue_depth'],
            len(system_state.available_models) < self.thresholds['critical']['min_available_models'],
            max_clustering > self.thresholds['critical']['max_peer_clustering'],
            len(system_state.unavailable_models) > 0,  # Any model down = critical
        ]
        
        if any(critical_conditions):
            logger.debug(
                f"Critical scenario detected: budget={budget_remaining:.2f}, "
                f"max_queue={max_queue}, available_models={len(system_state.available_models)}, "
                f"max_clustering={max_clustering}"
            )
            return ScenarioComplexity.CRITICAL
        
        # Check for SIMPLE conditions (all must be true)
        simple_conditions = [
            peer_count <= self.thresholds['simple']['max_peers'],
            budget_remaining >= self.thresholds['simple']['min_budget_remaining'],
            max_queue <= self.thresholds['simple']['max_queue_depth'],
            max_latency <= self.thresholds['simple']['max_latency_p95'],
        ]
        
        if all(simple_conditions):
            logger.debug(f"Simple scenario: peers={peer_count}, budget={budget_remaining:.2f}")
            return ScenarioComplexity.SIMPLE
        
        # Otherwise COMPLEX
        logger.debug(
            f"Complex scenario: peers={peer_count}, budget={budget_remaining:.2f}, "
            f"max_queue={max_queue}, max_latency={max_latency}"
        )
        return ScenarioComplexity.COMPLEX
    
    def _handle_critical_scenario(
        self,
        decision: REPDecision,
        system_state: SystemState,
        peer_messages: List[REPMessage]
    ) -> List[REPSensitivity]:
        """
        Handle critical scenarios with dual validation
        
        In critical situations, we use both rule-based and LLM
        calculations and compare them for safety.
        
        Args:
            decision: Current routing decision
            system_state: System state
            peer_messages: Recent peer messages
            
        Returns:
            Validated sensitivities
        """
        # Always get rule-based as baseline
        rule_sensitivities = self.rule_calculator.calculate_all(
            decision, system_state, peer_messages
        )
        
        # Try LLM if enabled
        if self.enable_llm:
            try:
                llm_sensitivities = self.llm_calculator.calculate_sensitivities(
                    decision, system_state, peer_messages
                )
                
                # Validate agreement
                if self._validate_agreement(rule_sensitivities, llm_sensitivities):
                    logger.info("Critical scenario: Rule and LLM agree, using LLM")
                    # Use LLM (potentially more nuanced)
                    for sens in llm_sensitivities:
                        sens.metadata['validated_by'] = 'rules'
                    return llm_sensitivities
                else:
                    logger.warning(
                        "Critical scenario: Rule and LLM disagree, using conservative (rules)"
                    )
                    self._log_disagreement(rule_sensitivities, llm_sensitivities)
                    # Use rules (more conservative in disagreement)
                    for sens in rule_sensitivities:
                        sens.metadata['llm_disagreement'] = True
                    return rule_sensitivities
                    
            except Exception as e:
                logger.error(f"LLM failed in critical scenario: {e}")
                self.stats['llm_failures'] += 1
                return rule_sensitivities
        else:
            # LLM disabled, use rules
            return rule_sensitivities
    
    def _validate_agreement(
        self,
        rule_sens: List[REPSensitivity],
        llm_sens: List[REPSensitivity]
    ) -> bool:
        """
        Validate that rule and LLM calculations agree
        
        Checks if both calculators recommend similar actions.
        
        Args:
            rule_sens: Rule-based sensitivities
            llm_sens: LLM sensitivities
            
        Returns:
            True if calculators agree
        """
        # Group by type
        rule_by_type = {s.type: s for s in rule_sens}
        llm_by_type = {s.type: s for s in llm_sens}
        
        # Check common types
        common_types = set(rule_by_type.keys()) & set(llm_by_type.keys())
        
        if not common_types:
            logger.warning("No common sensitivity types between rule and LLM")
            return False
        
        agreements = 0
        disagreements = 0
        
        for sens_type in common_types:
            rule_value = rule_by_type[sens_type].value
            llm_value = llm_by_type[sens_type].value
            
            # Check if both recommend same direction (sign)
            # and magnitude is within 0.3 (reasonable agreement)
            same_direction = (rule_value * llm_value) >= 0
            magnitude_diff = abs(rule_value - llm_value)
            
            if same_direction and magnitude_diff <= 0.3:
                agreements += 1
            else:
                disagreements += 1
        
        # Agree if majority consensus
        agreement_ratio = agreements / (agreements + disagreements)
        return agreement_ratio >= 0.7  # 70% agreement threshold
    
    def _log_disagreement(
        self,
        rule_sens: List[REPSensitivity],
        llm_sens: List[REPSensitivity]
    ):
        """Log disagreement between rule and LLM for analysis"""
        rule_by_type = {s.type: s for s in rule_sens}
        llm_by_type = {s.type: s for s in llm_sens}
        
        common_types = set(rule_by_type.keys()) & set(llm_by_type.keys())
        
        for sens_type in common_types:
            rule_value = rule_by_type[sens_type].value
            llm_value = llm_by_type[sens_type].value
            
            if abs(rule_value - llm_value) > 0.3:
                logger.warning(
                    f"Sensitivity disagreement on {sens_type.value}: "
                    f"rule={rule_value:.2f}, llm={llm_value:.2f}, "
                    f"llm_reasoning={llm_by_type[sens_type].metadata.get('reasoning', 'N/A')}"
                )
    
    def _log_stats(self):
        """Log usage statistics"""
        total = self.stats['total_calculations']
        if total == 0:
            return
        
        simple_pct = (self.stats['simple_count'] / total) * 100
        complex_pct = (self.stats['complex_count'] / total) * 100
        critical_pct = (self.stats['critical_count'] / total) * 100
        
        logger.info(
            f"Hybrid Calculator Stats (n={total}): "
            f"simple={simple_pct:.1f}%, complex={complex_pct:.1f}%, "
            f"critical={critical_pct:.1f}%, llm_failures={self.stats['llm_failures']}, "
            f"llm_fallbacks={self.stats['llm_fallbacks']}"
        )
    
    def get_stats(self) -> dict:
        """Get statistics about calculator usage"""
        total = self.stats['total_calculations']
        if total == 0:
            return {**self.stats, 'percentages': {}}
        
        return {
            **self.stats,
            'percentages': {
                'simple': (self.stats['simple_count'] / total) * 100,
                'complex': (self.stats['complex_count'] / total) * 100,
                'critical': (self.stats['critical_count'] / total) * 100,
            }
        }

