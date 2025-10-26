#!/usr/bin/env python3
"""
Router Learning Agent - Athena's Design
Learns optimal routing patterns from historical decisions

Analyzes:
- Which routes work best for different query types
- Latency patterns
- Failover effectiveness
- ECE (Energy-Compute Efficiency) optimization

Shares insights with Router via Project Iceberg coordination
"""

import asyncio
import logging
import asyncpg
import os
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "athena-postgres")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "athena")
DB_USER = os.getenv("DB_USER", "athena")
DB_PASS = os.getenv("DB_PASS", "athena_local_2024")

JUDICIAL_URL = "http://ai-republic-judicial:8096"

class RouterLearningAgent:
    """Learns from routing decisions to optimize future routing"""
    
    async def analyze_routing_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze routing decisions and learn patterns"""
        logger.info(f"🧠 Router Learning Agent analyzing last {hours} hours...")
        
        try:
            conn = await asyncpg.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            
            # Get routing decisions
            rows = await conn.fetch(f'''
                SELECT route, latency_ms, success, tokens_generated, ece_estimate
                FROM routing_decisions
                WHERE timestamp > NOW() - INTERVAL '{hours} hours'
                ORDER BY timestamp DESC
                LIMIT 1000
            ''')
            
            await conn.close()
            
            decisions = [dict(row) for row in rows]
            
            if not decisions:
                return {'status': 'no_data', 'message': 'No routing data to analyze'}
            
            logger.info(f"📊 Analyzing {len(decisions)} routing decisions")
            
            # Analyze by route
            route_stats = {}
            for decision in decisions:
                route = decision['route']
                if route not in route_stats:
                    route_stats[route] = {
                        'count': 0,
                        'total_latency': 0,
                        'success_count': 0,
                        'total_ece': 0
                    }
                
                route_stats[route]['count'] += 1
                route_stats[route]['total_latency'] += decision.get('latency_ms', 0) or 0
                route_stats[route]['success_count'] += 1 if decision.get('success') else 0
                route_stats[route]['total_ece'] += decision.get('ece_estimate', 0) or 0
            
            # Calculate metrics
            insights = []
            for route, stats in route_stats.items():
                avg_latency = stats['total_latency'] / stats['count']
                success_rate = (stats['success_count'] / stats['count'] * 100)
                avg_ece = stats['total_ece'] / stats['count'] if stats['count'] > 0 else 0
                
                insights.append({
                    'route': route,
                    'usage_count': stats['count'],
                    'avg_latency_ms': round(avg_latency, 2),
                    'success_rate': round(success_rate, 2),
                    'avg_ece': round(avg_ece, 4),
                    'performance': 'excellent' if success_rate > 95 else 'good' if success_rate > 80 else 'needs_improvement'
                })
            
            # Find best route
            best_route = max(insights, key=lambda x: x['success_rate'])
            
            # Generate learning insights
            learned_patterns = {
                'best_route': best_route['route'],
                'best_success_rate': best_route['success_rate'],
                'fastest_route': min(insights, key=lambda x: x['avg_latency_ms'])['route'],
                'most_efficient_route': max(insights, key=lambda x: x['avg_ece'])['route'],
                'recommendations': []
            }
            
            # Generate recommendations
            for insight in insights:
                if insight['success_rate'] < 80:
                    learned_patterns['recommendations'].append({
                        'route': insight['route'],
                        'issue': 'low_success_rate',
                        'current': insight['success_rate'],
                        'action': 'Consider deprioritizing this route or investigating failures'
                    })
                
                if insight['avg_latency_ms'] > 1000:
                    learned_patterns['recommendations'].append({
                        'route': insight['route'],
                        'issue': 'high_latency',
                        'current': insight['avg_latency_ms'],
                        'action': 'Optimize or add timeout limits'
                    })
            
            return {
                'agent': 'router_learning',
                'status': 'success',
                'analyzed_decisions': len(decisions),
                'route_insights': insights,
                'learned_patterns': learned_patterns,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Router learning failed: {e}")
            return {
                'agent': 'router_learning',
                'status': 'error',
                'error': str(e)
            }
    
    async def submit_learning_for_approval(self, learned_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Submit learned routing patterns to Judicial for safety review"""
        logger.info("🛡️ Submitting routing learning to Judicial...")
        
        # Assess severity based on proposed changes
        severity = 0.3  # Base severity for routing optimization
        
        if learned_patterns.get('recommendations'):
            severity = 0.5  # Higher if making changes
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{JUDICIAL_URL}/v2/judicial/adjudicate",
                    json={
                        "event_id": f"router-learning-{int(datetime.now().timestamp())}",
                        "instance_id": "athena-learning-system",
                        "actor_id": "router-learning-agent",
                        "article": "III",
                        "severity": severity,
                        "confidence": 0.85,
                        "classification": "learning_routing_optimization",
                        "details": learned_patterns
                    }
                )
                
                verdict = response.json()
                logger.info(f"Judicial verdict: {verdict['verdict']}")
                
                return {
                    'approved': verdict['verdict'] in ['ALLOW', 'WARN'],
                    'verdict': verdict,
                    'learning_patterns': learned_patterns
                }
                
        except Exception as e:
            logger.error(f"Judicial submission failed: {e}")
            return {
                'approved': False,
                'error': str(e)
            }

async def main():
    agent = RouterLearningAgent()
    
    # Analyze routing patterns
    result = await agent.analyze_routing_patterns(hours=24)
    print(json.dumps(result, indent=2))
    
    # If learned something, submit for approval
    if result.get('status') == 'success':
        learned = result.get('learned_patterns', {})
        if learned.get('recommendations'):
            approval = await agent.submit_learning_for_approval(learned)
            print("\n=== Judicial Review ===")
            print(json.dumps(approval, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
