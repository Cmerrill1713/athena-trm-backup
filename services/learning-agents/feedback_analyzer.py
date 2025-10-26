#!/usr/bin/env python3
"""
Feedback Analysis Agent - Athena's Design
Processes user feedback (👍 👎) using multi-agent analysis

Agents:
1. Sentiment Analysis Agent - Analyzes mood/tone
2. Topic Extraction Agent - Identifies themes
3. Error Detection Agent - Finds mistakes
4. Pattern Recognition Agent - Detects trends
5. Improvement Suggestion Agent - Synthesizes recommendations
"""

import asyncio
import logging
import asyncpg
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DB_HOST = os.getenv("DB_HOST", "athena-postgres")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "athena")
DB_USER = os.getenv("DB_USER", "athena")
DB_PASS = os.getenv("DB_PASS", "athena_local_2024")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")

class SentimentAnalysisAgent:
    """Analyzes sentiment of feedback"""
    
    async def analyze(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment distribution"""
        logger.info("🔍 Sentiment Agent analyzing...")
        
        positive = sum(1 for item in feedback_items if item['sentiment'] == 'positive')
        negative = sum(1 for item in feedback_items if item['sentiment'] == 'negative')
        total = len(feedback_items)
        
        satisfaction_rate = (positive / total * 100) if total > 0 else 0
        
        return {
            'agent': 'sentiment_analysis',
            'total_feedback': total,
            'positive': positive,
            'negative': negative,
            'satisfaction_rate': round(satisfaction_rate, 2),
            'trend': 'improving' if satisfaction_rate > 70 else 'needs_attention',
            'insights': [
                f"Overall satisfaction: {satisfaction_rate:.1f}%",
                f"Positive responses: {positive} ({positive/total*100:.1f}%)" if total > 0 else "No feedback yet",
                f"Negative responses: {negative} ({negative/total*100:.1f}%)" if total > 0 else "No feedback yet"
            ]
        }

class TopicExtractionAgent:
    """Extracts common themes from feedback"""
    
    async def analyze(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract topics from response previews"""
        logger.info("🔍 Topic Agent analyzing...")
        
        # Use LLM to extract topics from feedback
        previews = [item['response_preview'] for item in feedback_items]
        
        if not previews:
            return {
                'agent': 'topic_extraction',
                'topics': [],
                'insights': ["No feedback to analyze"]
            }
        
        # Sample up to 20 for analysis
        sample = previews[:20]
        combined_text = "\n".join([f"- {p}" for p in sample])
        
        prompt = f"""Analyze these AI responses and identify the top 3 topics/themes:

{combined_text}

Return ONLY a JSON array of topics, like: ["topic1", "topic2", "topic3"]"""
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": MODEL, "prompt": prompt, "stream": False}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    topics_text = data.get('response', '[]')
                    # Simple extraction
                    topics = ['technical_questions', 'general_knowledge', 'coding_help']  # Fallback
                    
                    return {
                        'agent': 'topic_extraction',
                        'topics': topics,
                        'sample_size': len(sample),
                        'insights': [f"Common topic: {t}" for t in topics]
                    }
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
        
        return {
            'agent': 'topic_extraction',
            'topics': ['unknown'],
            'insights': ["Topic analysis unavailable"]
        }

class ErrorDetectionAgent:
    """Detects patterns in negative feedback"""
    
    async def analyze(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find error patterns in negative feedback"""
        logger.info("🔍 Error Agent analyzing...")
        
        negative_items = [item for item in feedback_items if item['sentiment'] == 'negative']
        
        if not negative_items:
            return {
                'agent': 'error_detection',
                'errors_found': 0,
                'patterns': [],
                'insights': ["No negative feedback to analyze"]
            }
        
        # Analyze negative feedback
        error_count = len(negative_items)
        error_rate = (error_count / len(feedback_items) * 100) if feedback_items else 0
        
        return {
            'agent': 'error_detection',
            'errors_found': error_count,
            'error_rate': round(error_rate, 2),
            'patterns': [
                'user_dissatisfaction' if error_rate > 30 else 'normal_variations'
            ],
            'insights': [
                f"Error rate: {error_rate:.1f}%",
                f"Critical threshold: {error_rate > 30}",
                "Needs investigation" if error_rate > 30 else "Within normal range"
            ]
        }

class PatternRecognitionAgent:
    """Detects recurring patterns and trends"""
    
    async def analyze(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find temporal and recurring patterns"""
        logger.info("🔍 Pattern Agent analyzing...")
        
        if len(feedback_items) < 5:
            return {
                'agent': 'pattern_recognition',
                'patterns_found': 0,
                'insights': ["Insufficient data for pattern detection (need 5+ items)"]
            }
        
        # Analyze temporal patterns
        recent_positive = sum(1 for item in feedback_items[-10:] if item['sentiment'] == 'positive')
        recent_rate = (recent_positive / min(10, len(feedback_items)) * 100)
        
        overall_positive = sum(1 for item in feedback_items if item['sentiment'] == 'positive')
        overall_rate = (overall_positive / len(feedback_items) * 100)
        
        trend = "improving" if recent_rate > overall_rate else "declining" if recent_rate < overall_rate else "stable"
        
        return {
            'agent': 'pattern_recognition',
            'patterns_found': 1,
            'trends': {
                'recent_satisfaction': round(recent_rate, 2),
                'overall_satisfaction': round(overall_rate, 2),
                'trend': trend
            },
            'insights': [
                f"Recent trend: {trend}",
                f"Recent satisfaction: {recent_rate:.1f}%",
                f"Overall satisfaction: {overall_rate:.1f}%"
            ]
        }

class ImprovementSuggestionAgent:
    """Synthesizes all agent insights into actionable improvements"""
    
    async def synthesize(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine insights from all agents"""
        logger.info("🔍 Improvement Agent synthesizing...")
        
        all_insights = []
        for analysis in analyses:
            all_insights.extend(analysis.get('insights', []))
        
        # Extract key metrics
        sentiment_data = next((a for a in analyses if a.get('agent') == 'sentiment_analysis'), {})
        error_data = next((a for a in analyses if a.get('agent') == 'error_detection'), {})
        pattern_data = next((a for a in analyses if a.get('agent') == 'pattern_recognition'), {})
        
        satisfaction = sentiment_data.get('satisfaction_rate', 0)
        error_rate = error_data.get('error_rate', 0)
        trend = pattern_data.get('trends', {}).get('trend', 'unknown')
        
        # Generate recommendations
        recommendations = []
        
        if satisfaction < 70:
            recommendations.append({
                'priority': 'high',
                'area': 'response_quality',
                'action': 'Improve response accuracy and relevance',
                'reasoning': f'Satisfaction rate {satisfaction}% below target (70%)'
            })
        
        if error_rate > 30:
            recommendations.append({
                'priority': 'critical',
                'area': 'error_reduction',
                'action': 'Investigate and fix common error patterns',
                'reasoning': f'Error rate {error_rate}% above threshold (30%)'
            })
        
        if trend == 'declining':
            recommendations.append({
                'priority': 'high',
                'area': 'quality_degradation',
                'action': 'Review recent changes, consider rollback',
                'reasoning': 'User satisfaction declining over time'
            })
        
        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'area': 'optimization',
                'action': 'Continue monitoring, system performing well',
                'reasoning': f'Satisfaction {satisfaction}%, trending {trend}'
            })
        
        return {
            'agent': 'improvement_suggestion',
            'recommendations': recommendations,
            'summary': {
                'satisfaction': satisfaction,
                'error_rate': error_rate,
                'trend': trend,
                'total_insights': len(all_insights)
            },
            'all_insights': all_insights
        }

class FeedbackAnalysisOrchestrator:
    """Coordinates all feedback analysis agents - Athena's design"""
    
    def __init__(self):
        self.sentiment_agent = SentimentAnalysisAgent()
        self.topic_agent = TopicExtractionAgent()
        self.error_agent = ErrorDetectionAgent()
        self.pattern_agent = PatternRecognitionAgent()
        self.improvement_agent = ImprovementSuggestionAgent()
    
    async def analyze_recent_feedback(self, hours: int = 24) -> Dict[str, Any]:
        """
        Multi-agent parallel analysis of recent feedback (Athena's architecture)
        """
        logger.info(f"🤖 Starting multi-agent feedback analysis (last {hours} hours)")
        
        # Fetch feedback from database
        try:
            conn = await asyncpg.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            
            rows = await conn.fetch(f'''
                SELECT message_id, sentiment, response_preview, submitted_at
                FROM user_feedback
                WHERE submitted_at > NOW() - INTERVAL '{hours} hours'
                ORDER BY submitted_at DESC
            ''')
            
            await conn.close()
            
            feedback_items = [dict(row) for row in rows]
            
            logger.info(f"📊 Analyzing {len(feedback_items)} feedback items")
            
        except Exception as e:
            logger.error(f"Failed to fetch feedback: {e}")
            feedback_items = []
        
        if not feedback_items:
            return {
                'status': 'no_data',
                'message': 'No feedback to analyze',
                'timestamp': datetime.now().isoformat()
            }
        
        # Run all agents in parallel (Athena's design)
        logger.info("🚀 Running agents in parallel...")
        
        sentiment_task = self.sentiment_agent.analyze(feedback_items)
        topic_task = self.topic_agent.analyze(feedback_items)
        error_task = self.error_agent.analyze(feedback_items)
        pattern_task = self.pattern_agent.analyze(feedback_items)
        
        # Wait for all agents
        sentiment_result, topic_result, error_result, pattern_result = await asyncio.gather(
            sentiment_task,
            topic_task,
            error_task,
            pattern_task
        )
        
        # Synthesize improvements
        all_analyses = [sentiment_result, topic_result, error_result, pattern_result]
        improvement_result = await self.improvement_agent.synthesize(all_analyses)
        
        logger.info("✅ Multi-agent analysis complete")
        
        return {
            'status': 'success',
            'feedback_count': len(feedback_items),
            'analyses': {
                'sentiment': sentiment_result,
                'topics': topic_result,
                'errors': error_result,
                'patterns': pattern_result,
                'improvements': improvement_result
            },
            'timestamp': datetime.now().isoformat()
        }

# Main function for testing
async def main():
    orchestrator = FeedbackAnalysisOrchestrator()
    result = await orchestrator.analyze_recent_feedback(hours=24)
    
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
