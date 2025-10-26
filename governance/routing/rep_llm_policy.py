"""
LLM-Based Sensitivity Calculator for REP

Uses local LLM reasoning to calculate sophisticated sensitivity signals
for complex multi-agent coordination scenarios.

This enables intelligent policy decisions beyond simple rule-based thresholds,
while maintaining ATHENA_NO_CLOUD=1 compliance by using only local models.
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional
import requests

from governance.routing.rep_protocol import (
    REPDecision,
    REPSensitivity,
    REPMessage,
    SystemState,
    SensitivityType
)

logger = logging.getLogger(__name__)


class LLMSensitivityCalculator:
    """
    LLM-based sensitivity calculator for complex scenarios
    
    Uses local LLM (via Athena router) to reason about coordination
    decisions in complex multi-agent scenarios.
    
    Features:
    - Considers second-order effects
    - Reasons about peer behavior
    - Multi-objective optimization
    - Explains decisions (for governance/audit)
    
    Compliance:
    - ATHENA_NO_CLOUD=1: Only uses local models
    - Routes through Athena's local-first router
    - No external API calls
    """
    
    def __init__(
        self,
        router_url: str = "http://127.0.0.1:8099",
        model: str = "qwen2.5-coder:7b",
        temperature: float = 0.2,
        max_tokens: int = 500,
        timeout_seconds: float = 2.0
    ):
        """
        Initialize LLM sensitivity calculator
        
        Args:
            router_url: Local Athena router URL
            model: Model to use for reasoning
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
            timeout_seconds: Request timeout
        """
        self.router_url = router_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        
        # Validate local-only
        self._validate_local_only()
        
        logger.info(
            f"LLM Sensitivity Calculator initialized: "
            f"router={router_url}, model={model}"
        )
    
    def _validate_local_only(self):
        """Ensure router URL is local (ATHENA_NO_CLOUD=1 compliance)"""
        import os
        if os.getenv('ATHENA_NO_CLOUD') == '1':
            if not any(host in self.router_url for host in ['127.0.0.1', 'localhost']):
                raise ValueError(
                    f"ATHENA_NO_CLOUD=1 but router URL is not local: {self.router_url}"
                )
    
    def calculate_sensitivities(
        self,
        decision: REPDecision,
        system_state: SystemState,
        peer_messages: List[REPMessage]
    ) -> List[REPSensitivity]:
        """
        Calculate sensitivities using LLM reasoning
        
        Args:
            decision: Current routing decision
            system_state: System state
            peer_messages: Recent peer messages
            
        Returns:
            List of sensitivities with reasoning
        """
        start_time = time.time()
        
        try:
            # Build context for LLM
            context = self._build_context(decision, system_state, peer_messages)
            
            # Get LLM reasoning
            response = self._query_llm(context)
            
            # Parse sensitivities from LLM response
            sensitivities = self._parse_llm_response(response, system_state)
            
            # Record latency
            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                f"LLM sensitivity calculation complete: {len(sensitivities)} sensitivities, "
                f"latency={latency_ms:.1f}ms"
            )
            
            return sensitivities
            
        except Exception as e:
            logger.error(f"LLM sensitivity calculation failed: {e}", exc_info=True)
            # Return conservative defaults on error
            return self._get_default_sensitivities(decision, system_state)
    
    def _build_context(
        self,
        decision: REPDecision,
        system_state: SystemState,
        peer_messages: List[REPMessage]
    ) -> str:
        """
        Build context prompt for LLM reasoning
        
        Creates a structured prompt that helps the LLM understand
        the coordination scenario and reason about sensitivities.
        """
        # Format peer information
        peer_summary = self._format_peer_summary(peer_messages)
        
        # Format system metrics
        system_summary = self._format_system_summary(system_state)
        
        context = f"""You are a multi-agent coordination system analyzing routing decisions.

CURRENT DECISION:
- Model: {decision.model}
- Confidence: {decision.confidence:.2f}
- Domain: {decision.domain}

SYSTEM STATE:
{system_summary}

PEER AGENTS:
{peer_summary}

TASK:
Analyze this coordination scenario and determine sensitivities - how likely this agent should be to switch models under different conditions.

Consider:
1. CLUSTERING RISK: Are too many peers using the same model? Would switching help or hurt?
2. RESOURCE PRESSURE: Are queues/latency/memory concerning? Is there capacity elsewhere?
3. COST EFFICIENCY: Is cost becoming a concern? Are there cheaper alternatives?
4. SECOND-ORDER EFFECTS: If this agent switches, what will peers do? Will it cascade?
5. COLLECTIVE GOOD: What decision best serves the overall system, not just this agent?

Return ONLY a valid JSON object with this structure:
{{
  "sensitivities": [
    {{
      "type": "PEER_CLUSTERING",
      "value": -0.7,
      "reasoning": "6 peers on same model, moderate clustering risk"
    }},
    {{
      "type": "LATENCY_THRESHOLD", 
      "value": -0.4,
      "reasoning": "Latency acceptable but trending up"
    }}
  ],
  "recommendation": "stay|switch",
  "confidence": 0.8,
  "reasoning": "Overall assessment of the situation"
}}

Values must be between -1.0 (definitely switch) and +1.0 (definitely stay).
Focus on the 5 key sensitivity types: PEER_CLUSTERING, MODEL_QUEUE_DEPTH, LATENCY_THRESHOLD, COST_PRESSURE, MODEL_AVAILABILITY.
"""
        
        return context
    
    def _format_peer_summary(self, peer_messages: List[REPMessage]) -> str:
        """Format peer messages into human-readable summary"""
        if not peer_messages:
            return "- No peer agents active"
        
        # Count peers per model
        model_counts = {}
        for msg in peer_messages:
            model = msg.decision.model
            model_counts[model] = model_counts.get(model, 0) + 1
        
        lines = [f"- Total peers: {len(peer_messages)}"]
        lines.append("- Model distribution:")
        for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  - {model}: {count} agents")
        
        # Sample recent peer sensitivities
        if peer_messages:
            recent = peer_messages[-3:]  # Last 3
            lines.append("- Recent peer sensitivities:")
            for msg in recent:
                sensitivities_str = ", ".join([
                    f"{s.type.value}={s.value:.2f}"
                    for s in msg.sensitivities[:2]  # Top 2
                ])
                lines.append(f"  - {msg.agent_id}: {sensitivities_str}")
        
        return "\n".join(lines)
    
    def _format_system_summary(self, system_state: SystemState) -> str:
        """Format system state into human-readable summary"""
        lines = []
        
        # Queue depths
        if system_state.queue_depths:
            lines.append("Queue Depths:")
            for model, depth in system_state.queue_depths.items():
                status = "⚠️ HIGH" if depth > 5 else "✓ OK"
                lines.append(f"  - {model}: {depth} ({status})")
        
        # Latencies
        if system_state.latencies_p95:
            lines.append("P95 Latencies:")
            for model, latency in system_state.latencies_p95.items():
                status = "⚠️ SLOW" if latency > 1000 else "✓ OK"
                lines.append(f"  - {model}: {latency:.0f}ms ({status})")
        
        # Cost
        budget_remaining = system_state.cost_budget_remaining()
        cost_status = "🔴 CRITICAL" if budget_remaining < 0.2 else "⚠️ HIGH" if budget_remaining < 0.5 else "✓ OK"
        lines.append(
            f"Cost: ${system_state.accumulated_cost:.2f} / "
            f"${system_state.cost_budget:.2f} "
            f"({budget_remaining*100:.0f}% remaining) ({cost_status})"
        )
        
        # Available models
        lines.append(f"Available Models: {len(system_state.available_models)}")
        if system_state.unavailable_models:
            lines.append(f"⚠️ Unavailable: {', '.join(system_state.unavailable_models)}")
        
        return "\n".join(lines)
    
    def _query_llm(self, context: str) -> str:
        """
        Query local LLM via Athena router
        
        Args:
            context: Prompt/context for LLM
            
        Returns:
            LLM response text
        """
        try:
            response = requests.post(
                f"{self.router_url}/route",
                json={
                    "query": context,
                    "domain": "reasoning",
                    "metadata": {
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "model": self.model
                    }
                },
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('response', '')
            
        except requests.Timeout:
            logger.error(f"LLM query timeout after {self.timeout_seconds}s")
            raise
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise
    
    def _parse_llm_response(
        self,
        response: str,
        system_state: SystemState
    ) -> List[REPSensitivity]:
        """
        Parse LLM JSON response into sensitivity objects
        
        Args:
            response: LLM response text
            system_state: System state (for threshold values)
            
        Returns:
            List of sensitivities
        """
        try:
            # Extract JSON from response (might have extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in LLM response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Parse sensitivities
            sensitivities = []
            for sens_data in data.get('sensitivities', []):
                try:
                    sens_type = SensitivityType(sens_data['type'])
                    value = float(sens_data['value'])
                    reasoning = sens_data.get('reasoning', '')
                    
                    # Clamp value to valid range
                    value = max(-1.0, min(1.0, value))
                    
                    sensitivity = REPSensitivity(
                        type=sens_type,
                        value=value,
                        threshold=self._get_threshold_for_type(sens_type, system_state),
                        metadata={
                            'source': 'llm',
                            'reasoning': reasoning,
                            'llm_confidence': data.get('confidence', 0.5)
                        }
                    )
                    sensitivities.append(sensitivity)
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse sensitivity: {e}")
                    continue
            
            if not sensitivities:
                logger.warning("No valid sensitivities parsed from LLM response")
                return self._get_default_sensitivities(None, system_state)
            
            logger.debug(
                f"Parsed {len(sensitivities)} sensitivities from LLM: "
                f"{[s.type.value for s in sensitivities]}"
            )
            
            return sensitivities
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"LLM response was: {response[:500]}")
            return self._get_default_sensitivities(None, system_state)
    
    def _get_threshold_for_type(
        self,
        sens_type: SensitivityType,
        system_state: SystemState
    ) -> Optional[float]:
        """Get appropriate threshold for sensitivity type"""
        thresholds = {
            SensitivityType.MODEL_QUEUE_DEPTH: 5.0,
            SensitivityType.LATENCY_THRESHOLD: 1000.0,
            SensitivityType.COST_PRESSURE: 0.8,
            SensitivityType.PEER_CLUSTERING: 3.0,
        }
        return thresholds.get(sens_type)
    
    def _get_default_sensitivities(
        self,
        decision: Optional[REPDecision],
        system_state: SystemState
    ) -> List[REPSensitivity]:
        """
        Get conservative default sensitivities if LLM fails
        
        Returns safe, conservative sensitivities that won't
        cause problems if LLM reasoning fails.
        """
        return [
            REPSensitivity(
                type=SensitivityType.MODEL_QUEUE_DEPTH,
                value=-0.5,
                threshold=5.0,
                metadata={'source': 'default', 'reason': 'llm_fallback'}
            ),
            REPSensitivity(
                type=SensitivityType.LATENCY_THRESHOLD,
                value=-0.5,
                threshold=1000.0,
                metadata={'source': 'default', 'reason': 'llm_fallback'}
            ),
            REPSensitivity(
                type=SensitivityType.COST_PRESSURE,
                value=-0.3,
                threshold=0.8,
                metadata={'source': 'default', 'reason': 'llm_fallback'}
            ),
            REPSensitivity(
                type=SensitivityType.PEER_CLUSTERING,
                value=-0.3,
                threshold=3.0,
                metadata={'source': 'default', 'reason': 'llm_fallback'}
            ),
        ]

