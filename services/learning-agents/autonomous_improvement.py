#!/usr/bin/env python3
"""
Autonomous Improvement System
Wires Learning System → AGI Core → File Modifications

This is THE COMPLETE LOOP Athena wanted:
1. Learning agents analyze patterns
2. Generate improvement recommendations  
3. AGI Core Scout-Plan-Build executes changes
4. Judicial reviews for safety
5. Changes applied to actual files
6. System improves itself autonomously!
"""

import asyncio
import logging
import httpx
import os
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGI_CORE_URL = os.getenv("AGI_CORE_URL", "http://localhost:8091")
JUDICIAL_URL = os.getenv("JUDICIAL_URL", "http://localhost:8096")
LEARNING_URL = os.getenv("LEARNING_URL", "http://localhost:8098")

class AutonomousImprovementEngine:
    """
    The Complete Autonomous Loop
    
    Athena analyzes → Athena improves → Athena verifies
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info("🤖 Autonomous Improvement Engine initialized")
    
    async def run_improvement_cycle(self) -> Dict[str, Any]:
        """
        Complete autonomous improvement cycle
        
        Steps:
        1. Get learning recommendations from Learning System
        2. For each recommendation, generate AGI task
        3. Execute via AGI Core (Scout-Plan-Build)
        4. AGI Core uses Build Expert to modify files
        5. Judicial reviews changes
        6. Report results
        """
        logger.info("🚀 ========================================")
        logger.info("🚀 AUTONOMOUS IMPROVEMENT CYCLE STARTING")
        logger.info("🚀 ========================================")
        
        cycle_start = datetime.now()
        
        try:
            # Step 1: Get learning insights
            logger.info("\n📊 Step 1: Gathering learning insights...")
            learning_result = await self.client.post(
                f"{LEARNING_URL}/v1/learning/run"
            )
            learning_data = learning_result.json()
            
            if learning_data.get('status') != 'success':
                logger.warning("No learning insights available yet")
                return {
                    'status': 'no_insights',
                    'message': 'Learning system needs more data'
                }
            
            # Extract recommendations
            recommendations = learning_data.get('synthesized_knowledge', {}).get('priority_actions', [])
            
            logger.info(f"✅ Found {len(recommendations)} improvement recommendations")
            
            if not recommendations:
                logger.info("No actionable recommendations yet")
                return {
                    'status': 'no_actions',
                    'message': 'No improvements needed at this time'
                }
            
            # Step 2: For each recommendation, create AGI task
            logger.info("\n🧠 Step 2: Converting recommendations to AGI tasks...")
            
            results = []
            for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
                logger.info(f"\n  Recommendation {i}/{min(len(recommendations), 3)}:")
                logger.info(f"    Priority: {rec.get('priority')}")
                logger.info(f"    Area: {rec.get('area')}")
                logger.info(f"    Action: {rec.get('action')}")
                
                # Convert recommendation to AGI objective
                objective = self._recommendation_to_objective(rec)
                
                logger.info(f"    AGI Objective: {objective}")
                
                # Step 3: Execute via AGI Core
                logger.info(f"\n🔨 Step 3: Executing via AGI Core...")
                
                agi_result = await self.client.post(
                    f"{AGI_CORE_URL}/api/execute",
                    json={
                        "objective": objective,
                        "context": {
                            "recommendation": rec,
                            "learning_cycle": learning_data.get('cycle_id')
                        },
                        "tools": [
                            "system.doctor",
                            "rag.query",
                            "code.read",
                            "code.analyze",
                            "code.modify",  # THIS IS THE KEY - modifies files!
                            "git.commit"
                        ],
                        "max_steps": 12,
                        "flags": {
                            "adaptive_trm": True,
                            "auto_commit": False  # Require approval
                        }
                    }
                )
                
                agi_data = agi_result.json()
                
                logger.info(f"    AGI Status: {agi_data.get('status')}")
                logger.info(f"    Tools Used: {agi_data.get('result', {}).get('tools_used', [])}")
                
                # Step 4: Judicial review (already happened in AGI)
                logger.info(f"\n🛡️  Step 4: Judicial review...")
                
                judicial_result = await self._submit_to_judicial(rec, agi_data)
                
                logger.info(f"    Verdict: {judicial_result.get('verdict')}")
                
                results.append({
                    'recommendation': rec,
                    'agi_task_id': agi_data.get('task_id'),
                    'agi_status': agi_data.get('status'),
                    'judicial_verdict': judicial_result.get('verdict'),
                    'approved': judicial_result.get('verdict') in ['ALLOW', 'WARN']
                })
            
            # Summary
            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()
            
            approved_count = sum(1 for r in results if r.get('approved'))
            
            logger.info("\n🎯 ========================================")
            logger.info(f"🎯 CYCLE COMPLETE ({duration:.2f}s)")
            logger.info(f"🎯 Recommendations: {len(recommendations)}")
            logger.info(f"🎯 Executed: {len(results)}")
            logger.info(f"🎯 Approved: {approved_count}")
            logger.info("🎯 ========================================\n")
            
            return {
                'status': 'completed',
                'cycle_id': f"auto-improve-{int(cycle_start.timestamp())}",
                'duration_seconds': duration,
                'recommendations_total': len(recommendations),
                'tasks_executed': len(results),
                'tasks_approved': approved_count,
                'results': results,
                'timestamp': cycle_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Autonomous improvement cycle failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _recommendation_to_objective(self, recommendation: Dict[str, Any]) -> str:
        """Convert learning recommendation to AGI objective"""
        area = recommendation.get('area', 'general')
        action = recommendation.get('action', '')
        reasoning = recommendation.get('reasoning', '')
        
        # Map areas to concrete objectives
        if 'response_quality' in area:
            return f"Analyze and improve response quality: {reasoning}. Review UAI chat endpoint and optimize response generation."
        elif 'error_reduction' in area:
            return f"Reduce error rate: {reasoning}. Investigate error patterns and implement fixes."
        elif 'quality_degradation' in area:
            return f"Address quality degradation: {reasoning}. Review recent changes and consider rollback or improvements."
        elif 'routing' in area:
            return f"Optimize routing: {action}. {reasoning}"
        else:
            return f"Implement improvement: {action}. Reasoning: {reasoning}"
    
    async def _submit_to_judicial(self, recommendation: Dict[str, Any], agi_result: Dict[str, Any]) -> Dict[str, Any]:
        """Submit improvement to Judicial for safety review"""
        try:
            # Assess severity
            priority = recommendation.get('priority', 'low')
            severity = {
                'critical': 0.9,
                'high': 0.7,
                'medium': 0.5,
                'low': 0.3
            }.get(priority, 0.5)
            
            response = await self.client.post(
                f"{JUDICIAL_URL}/v2/judicial/adjudicate",
                json={
                    "event_id": f"auto-improve-{int(datetime.now().timestamp())}",
                    "instance_id": "athena-autonomous-improvement",
                    "actor_id": "autonomous-improvement-engine",
                    "article": "III",  # Learning & Adaptation
                    "severity": severity,
                    "confidence": 0.85,
                    "classification": "autonomous_improvement",
                    "details": {
                        "recommendation": recommendation,
                        "agi_task_id": agi_result.get('task_id'),
                        "agi_status": agi_result.get('status')
                    }
                }
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Judicial submission failed: {e}")
            return {'verdict': 'ERROR', 'error': str(e)}

async def main():
    """Run autonomous improvement cycle"""
    engine = AutonomousImprovementEngine()
    result = await engine.run_improvement_cycle()
    
    import json
    print("\n" + "="*60)
    print("AUTONOMOUS IMPROVEMENT RESULT")
    print("="*60)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
