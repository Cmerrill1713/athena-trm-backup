#!/usr/bin/env python3
"""
Integrate Historical Routing Data into Adaptive TRM
Load 50 routing decisions and feed into learning system
"""
import psycopg2
import json
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_routing_history():
    """Load historical routing decisions from PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="athena_db",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                prompt,
                selected_model,
                latency_ms,
                success,
                created_at
            FROM routing_outcomes
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        logger.info(f"✅ Loaded {len(rows)} historical routing decisions")
        
        return [
            {
                "id": row[0],
                "prompt": row[1],
                "model": row[2],
                "latency_ms": row[3],
                "success": row[4],
                "timestamp": str(row[5])
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Failed to load routing history: {e}")
        return []


def analyze_patterns(history):
    """Analyze patterns from historical data"""
    patterns = {
        "total_decisions": len(history),
        "success_rate": sum(1 for h in history if h["success"]) / len(history),
        "avg_latency": sum(h["latency_ms"] for h in history) / len(history),
        "model_distribution": {},
        "query_types": {}
    }
    
    # Model distribution
    for decision in history:
        model = decision["model"]
        if model not in patterns["model_distribution"]:
            patterns["model_distribution"][model] = {"count": 0, "successes": 0, "avg_latency": 0}
        
        patterns["model_distribution"][model]["count"] += 1
        if decision["success"]:
            patterns["model_distribution"][model]["successes"] += 1
        patterns["model_distribution"][model]["avg_latency"] += decision["latency_ms"]
    
    # Calculate averages
    for model, stats in patterns["model_distribution"].items():
        stats["success_rate"] = stats["successes"] / stats["count"]
        stats["avg_latency"] = stats["avg_latency"] / stats["count"]
    
    return patterns


def feed_into_adaptive_trm(history):
    """Feed historical data into Adaptive TRM learning system"""
    logger.info("🧠 Feeding historical data into Adaptive TRM...")
    
    successful_feeds = 0
    
    for decision in history:
        # Determine if this was a TRM-like task (reasoning)
        prompt_lower = decision["prompt"].lower()
        used_trm = any(keyword in prompt_lower for keyword in [
            "solve", "debug", "analyze", "calculate", "reason", "logic"
        ])
        
        try:
            # Send to autonomous orchestrator feedback endpoint
            response = requests.post(
                "http://localhost:9114/feedback",
                json={
                    "query_id": f"historical_{decision['id']}",
                    "query": decision["prompt"],
                    "used_trm": used_trm,
                    "success": decision["success"],
                    "latency_ms": decision["latency_ms"]
                },
                timeout=5
            )
            
            if response.status_code == 200:
                successful_feeds += 1
                
        except Exception as e:
            logger.warning(f"Failed to feed decision {decision['id']}: {e}")
    
    logger.info(f"✅ Fed {successful_feeds}/{len(history)} decisions into Adaptive TRM")
    return successful_feeds


if __name__ == "__main__":
    logger.info("🚀 Historical Routing Data Integration")
    logger.info("=" * 50)
    
    # Load history
    history = load_routing_history()
    
    if not history:
        logger.error("No historical data found")
        exit(1)
    
    # Analyze
    patterns = analyze_patterns(history)
    
    logger.info(f"\n📊 Historical Patterns:")
    logger.info(f"   Total decisions: {patterns['total_decisions']}")
    logger.info(f"   Overall success rate: {patterns['success_rate']:.1%}")
    logger.info(f"   Average latency: {patterns['avg_latency']:.0f}ms")
    logger.info(f"\n🎯 Model Performance:")
    
    for model, stats in sorted(patterns["model_distribution"].items(), 
                                key=lambda x: x[1]["success_rate"], 
                                reverse=True)[:5]:
        logger.info(f"   {model}: {stats['success_rate']:.1%} success, {stats['avg_latency']:.0f}ms avg")
    
    # Feed into Adaptive TRM
    print()
    fed = feed_into_adaptive_trm(history)
    
    # Get updated status
    try:
        status = requests.get("http://localhost:9114/status").json()
        logger.info(f"\n📈 Updated Adaptive TRM Status:")
        logger.info(f"   Total decisions: {status['adaptive_trm']['total_decisions']}")
        logger.info(f"   Trigger probability: {status['adaptive_trm']['trigger_probability']:.2%}")
        logger.info(f"   TRM success rate: {status['adaptive_trm']['trm_success_rate']:.2%}")
    except:
        pass
    
    logger.info("\n🎉 Historical data integration complete!")
