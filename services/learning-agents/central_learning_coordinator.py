#!/usr/bin/env python3
"""
Central Learning Coordinator - Athena's Meta-Controller
Coordinates all learning agents and manages the learning lifecycle

This is Project Iceberg integration for distributed learning!

Coordinates:
- Feedback Analysis Agent
- Router Learning Agent
- Future: UAI Learning, FastVLM Learning, etc.

Implements Athena's vision:
"Have different agents try different learning approaches, then share what works best"
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, List
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import learning agents
from feedback_analyzer import FeedbackAnalysisOrchestrator
from router_learning_agent import RouterLearningAgent

JUDICIAL_URL = os.getenv("JUDICIAL_URL", "http://ai-republic-judicial:8096")

class CentralLearningCoordinator:
    """
    Athena's Meta-Controller for Distributed Learning
    
    Implements her architectural vision:
    1. Coordinate specialized learning agents
    2. Collect insights from each
    3. Synthesize knowledge
    4. Submit to Judicial for safety review
    5. Distribute approved improvements to all services
    """
    
    def __init__(self):
        self.feedback_orchestrator = FeedbackAnalysisOrchestrator()
        self.router_learning = RouterLearningAgent()
        self.learning_history = []
    
    async def run_learning_cycle(self) -> Dict[str, Any]:
        """
        Execute a complete learning cycle (Athena's daily schedule)
        
        Steps:
        1. Collect insights from all learning agents (parallel)
        2. Synthesize cross-agent knowledge
        3. Submit to Judicial for safety review
        4. If approved, prepare deployment
        5. Log results
        """
        logger.info("🚀 ========================================")
        logger.info("🚀 ATHENA LEARNING CYCLE STARTING")
        logger.info("🚀 ========================================")
        
        cycle_start = datetime.now()
        
        # Phase 1: Parallel Learning (Athena's design)
        logger.info("\n📊 Phase 1: Multi-Agent Learning (Parallel)")
        
        feedback_task = self.feedback_orchestrator.analyze_recent_feedback(hours=24)
        router_task = self.router_learning.analyze_routing_patterns(hours=24)
        
        # Wait for all agents (parallel execution)
        feedback_result, router_result = await asyncio.gather(
            feedback_task,
            router_task,
            return_exceptions=True
        )
        
        # Handle errors
        if isinstance(feedback_result, Exception):
            feedback_result = {'status': 'error', 'error': str(feedback_result)}
        if isinstance(router_result, Exception):
            router_result = {'status': 'error', 'error': str(router_result)}
        
        logger.info(f"✅ Feedback analysis: {feedback_result.get('status', 'unknown')}")
        logger.info(f"✅ Router learning: {router_result.get('status', 'unknown')}")
        
        # Phase 2: Knowledge Synthesis (Athena's design)
        logger.info("\n🧠 Phase 2: Knowledge Synthesis")
        
        synthesized_knowledge = await self.synthesize_knowledge({
            'feedback_analysis': feedback_result,
            'router_learning': router_result
        })
        
        logger.info(f"✅ Synthesized {len(synthesized_knowledge.get('insights', []))} insights")
        
        # Phase 3: Judicial Safety Review (Athena's design)
        logger.info("\n🛡️  Phase 3: Judicial Safety Review")
        
        safety_approval = await self.submit_for_safety_review(synthesized_knowledge)
        
        logger.info(f"✅ Judicial verdict: {safety_approval.get('verdict', 'UNKNOWN')}")
        
        # Phase 4: Results
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        learning_result = {
            'cycle_id': f"learning-{int(cycle_start.timestamp())}",
            'timestamp': cycle_start.isoformat(),
            'duration_seconds': round(duration, 2),
            'agents_executed': [
                'feedback_analysis',
                'router_learning'
            ],
            'raw_results': {
                'feedback': feedback_result,
                'router': router_result
            },
            'synthesized_knowledge': synthesized_knowledge,
            'safety_review': safety_approval,
            'approved': safety_approval.get('verdict') in ['ALLOW', 'WARN'],
            'status': 'completed'
        }
        
        # Log to history
        self.learning_history.append(learning_result)
        
        logger.info("\n🎯 ========================================")
        logger.info(f"🎯 LEARNING CYCLE COMPLETE ({duration:.2f}s)")
        logger.info(f"🎯 Approved: {learning_result['approved']}")
        logger.info("🎯 ========================================\n")
        
        return learning_result
    
    async def synthesize_knowledge(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize insights from multiple agents into unified knowledge
        (Athena's cross-agent knowledge sharing)
        """
        
        all_insights = []
        all_recommendations = []
        
        # Extract feedback insights
        feedback_data = agent_results.get('feedback_analysis', {})
        if feedback_data.get('status') == 'success':
            analyses = feedback_data.get('analyses', {})
            improvement_data = analyses.get('improvements', {})
            
            if improvement_data:
                all_insights.extend(improvement_data.get('all_insights', []))
                all_recommendations.extend(improvement_data.get('recommendations', []))
        
        # Extract router insights
        router_data = agent_results.get('router_learning', {})
        if router_data.get('status') == 'success':
            learned_patterns = router_data.get('learned_patterns', {})
            
            if learned_patterns:
                all_insights.append(f"Best route: {learned_patterns.get('best_route')} ({learned_patterns.get('best_success_rate')}% success)")
                all_recommendations.extend(learned_patterns.get('recommendations', []))
        
        # Cross-agent synthesis
        synthesis = {
            'total_insights': len(all_insights),
            'total_recommendations': len(all_recommendations),
            'insights': all_insights,
            'recommendations': all_recommendations,
            'cross_agent_patterns': self._find_cross_patterns(agent_results),
            'priority_actions': self._prioritize_actions(all_recommendations)
        }
        
        return synthesis
    
    def _find_cross_patterns(self, agent_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """Find patterns across multiple agents"""
        patterns = []
        
        feedback_data = agent_results.get('feedback_analysis', {})
        router_data = agent_results.get('router_learning', {})
        
        # Check for quality correlation
        if feedback_data.get('status') == 'success' and router_data.get('status') == 'success':
            feedback_satisfaction = feedback_data.get('analyses', {}).get('sentiment', {}).get('satisfaction_rate', 0)
            
            if feedback_satisfaction < 70:
                patterns.append("User satisfaction correlates with system performance - both need improvement")
        
        return patterns
    
    def _prioritize_actions(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize recommended actions"""
        
        # Sort by priority: critical > high > low
        priority_order = {'critical': 0, 'high': 1, 'low': 2}
        sorted_recs = sorted(
            recommendations,
            key=lambda x: priority_order.get(x.get('priority', 'low'), 3)
        )
        
        return sorted_recs[:5]  # Top 5 actions
    
    async def submit_for_safety_review(self, synthesized_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit synthesized learning to Judicial for safety approval
        (Athena's federated learning with central safety server)
        """
        
        # Assess severity based on recommendations
        recommendations = synthesized_knowledge.get('recommendations', [])
        
        severity = 0.1  # Base severity for learning
        
        for rec in recommendations:
            if rec.get('priority') == 'critical':
                severity = max(severity, 0.8)
            elif rec.get('priority') == 'high':
                severity = max(severity, 0.5)
        
        event_payload = {
            "event_id": f"learning-cycle-{int(datetime.now().timestamp())}",
            "instance_id": "athena-learning-system",
            "actor_id": "central-learning-coordinator",
            "article": "III",  # Learning & Adaptation
            "severity": severity,
            "confidence": 0.9,
            "classification": "learning_cycle_complete",
            "details": {
                "insights_count": synthesized_knowledge.get('total_insights', 0),
                "recommendations_count": synthesized_knowledge.get('total_recommendations', 0),
                "priority_actions": synthesized_knowledge.get('priority_actions', []),
                "cross_patterns": synthesized_knowledge.get('cross_agent_patterns', [])
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{JUDICIAL_URL}/v2/judicial/adjudicate",
                    json=event_payload
                )
                
                result = response.json()
                
                return {
                    'submitted': True,
                    'verdict': result.get('verdict'),
                    'rationale': result.get('rationale'),
                    'review_required': result.get('review_required', False),
                    'actions': result.get('actions', [])
                }
                
        except Exception as e:
            logger.error(f"Judicial submission failed: {e}")
            return {
                'submitted': False,
                'verdict': 'ERROR',
                'error': str(e)
            }

async def main():
    """Run a complete learning cycle"""
    coordinator = CentralLearningCoordinator()
    result = await coordinator.run_learning_cycle()
    
    print("\n" + "="*60)
    print("LEARNING CYCLE RESULT")
    print("="*60)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
