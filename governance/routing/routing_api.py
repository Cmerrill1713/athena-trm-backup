#!/usr/bin/env python3
"""
Routing API - Athena model router endpoints with production hardening.

Features:
- HTTP API for intelligent model routing
- Bearer token authentication
- Rate limiting (configurable)
- SSL/TLS support
- Comprehensive metrics and monitoring

Environment variables:
- ATHENA_ROUTER_TOKEN: Required bearer token for auth
- ATHENA_ROUTER_RATE_LIMIT: Requests per minute (default: 1000)
- ATHENA_ROUTER_SSL_CERT: Path to SSL certificate
- ATHENA_ROUTER_SSL_KEY: Path to SSL private key
"""

import logging
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from threading import Lock
from typing import Dict, Any

from flask import Flask, jsonify, request, g
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from werkzeug.exceptions import TooManyRequests

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from governance.routing.basic_router import BasicRouter, RoutingRequest
from governance.routing.contrastive_router import ContrastiveRouter
from governance.routing.ab_testing import ab_test_manager, ABTestStrategy
from governance.routing.feature_flags import feature_flag_manager
from governance.routing.cost_optimizer import cost_optimizer, usage_analytics
from governance.routing.ollama_integration import ollama_client, ollama_manager
from governance.routing.mlx_integration import inference_manager
from governance.observability.routing_metrics import routing_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
REQUIRED_TOKEN = os.getenv('ATHENA_ROUTER_TOKEN')
RATE_LIMIT_RPM = int(os.getenv('ATHENA_ROUTER_RATE_LIMIT', '1000'))
SSL_CERT_PATH = os.getenv('ATHENA_ROUTER_SSL_CERT')
SSL_KEY_PATH = os.getenv('ATHENA_ROUTER_SSL_KEY')

# Rate limiting storage (thread-safe)
rate_limit_lock = Lock()
client_requests = defaultdict(list)  # client_ip -> [timestamps]

# Initialize router
PROFILES_PATH = Path(__file__).parent / "model_profiles.json"
router = BasicRouter(profiles_path=PROFILES_PATH)


def check_auth():
    """Check bearer token authentication."""
    if not REQUIRED_TOKEN:
        # No auth required if token not set (development mode)
        return

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        routing_metrics.record_agent_error(
            agent='auth',
            error_type='missing_token'
        )
        return jsonify({
            "error": "Authentication required",
            "message": "Provide Bearer token in Authorization header"
        }), 401

    token = auth_header[7:]  # Remove "Bearer " prefix
    if token != REQUIRED_TOKEN:
        routing_metrics.record_agent_error(
            agent='auth',
            error_type='invalid_token'
        )
        return jsonify({
            "error": "Authentication failed",
            "message": "Invalid token"
        }), 401


def classify_routing_failure(error: Exception) -> str:
    """Classify routing failure for better triage."""
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Model availability issues
    if 'model' in error_str and ('not found' in error_str or 'unavailable' in error_str):
        return 'model_unavailable'

    # Network/connectivity issues
    if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'socket']):
        return 'network_failure'

    # Configuration issues
    if 'config' in error_str or 'profile' in error_str:
        return 'config_error'

    # Embedding/domain issues
    if any(keyword in error_str for keyword in ['embedding', 'domain', 'similarity']):
        return 'domain_processing_error'

    # Resource issues
    if any(keyword in error_str for keyword in ['memory', 'resource', 'capacity']):
        return 'resource_exhaustion'

    # Authentication issues (though should be caught earlier)
    if 'auth' in error_str or 'token' in error_str:
        return 'auth_failure'

    # Fallback to error type
    return error_type.lower()


def check_rate_limit():
    """Check rate limiting."""
    client_ip = request.remote_addr or 'unknown'
    now = time.time()

    with rate_limit_lock:
        # Clean old requests (older than 1 minute)
        client_requests[client_ip] = [
            ts for ts in client_requests[client_ip]
            if now - ts < 60
        ]

        # Check current request count
        if len(client_requests[client_ip]) >= RATE_LIMIT_RPM:
            routing_metrics.record_agent_error(
                agent='rate_limit',
                error_type='exceeded'
            )
            return jsonify({
                "error": "Rate limit exceeded",
                "message": f"Maximum {RATE_LIMIT_RPM} requests per minute",
                "retry_after": 60
            }), 429

        # Add current request
        client_requests[client_ip].append(now)


@app.before_request
def before_request():
    """Global middleware: auth and rate limiting."""
    # Skip auth/rate limiting for health and metrics
    if request.path in ['/health', '/metrics']:
        return

    # Check authentication
    auth_result = check_auth()
    if auth_result:
        return auth_result

    # Check rate limiting
    rate_result = check_rate_limit()
    if rate_result:
        return rate_result


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "athena-router",
        "models_loaded": len(router.models),
        "fallback_threshold": router.fallback_threshold,
        "authentication": REQUIRED_TOKEN is not None,
        "rate_limit_rpm": RATE_LIMIT_RPM,
        "ssl_enabled": SSL_CERT_PATH is not None and SSL_KEY_PATH is not None
    })


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/route', methods=['POST'])
def route():
    """
    Route a request to an appropriate model.
    
    Request body:
    {
        "query": "string",
        "domain": "general|code|math|...",
        "metadata": {...}
    }
    
    Response:
    {
        "model": "model-id",
        "confidence": 0.85,
        "domain": "code",
        "latency_ms": 12.5,
        "metadata": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query"
            }), 400
        
        # Create routing request
        routing_request = RoutingRequest(
            query=data['query'],
            domain=data.get('domain', 'general'),
            metadata=data.get('metadata', {})
        )
        
        # Route
        choice = router.route(routing_request)
        
        # Return choice
        return jsonify({
            "model": choice.model,
            "confidence": choice.confidence,
            "domain": choice.domain,
            "latency_ms": choice.latency_ms,
            "metadata": choice.metadata
        })
    
    except Exception as e:
        # Enhanced error logging for faster triage
        fail_reason = classify_routing_failure(e)
        logger.error(f"Routing error: {e} | FAIL_REASON={fail_reason}", exc_info=True)

        # Log to environment for monitoring
        os.environ['ATHENA_ROUTER_LAST_FAIL_REASON'] = fail_reason

        routing_metrics.record_agent_error(
            agent='routing_api',
            error_type=fail_reason
        )
        return jsonify({
            "error": str(e),
            "fail_reason": fail_reason
        }), 500


@app.route('/models', methods=['GET'])
def list_models():
    """List available models and their profiles."""
    return jsonify({
        "models": [
            {
                "model_id": m.model_id,
                "domain": m.domain,
                "quality_score": m.quality_score,
                "cost": m.cost,
                "latency_p50_ms": m.latency_p50_ms,
                "latency_p95_ms": m.latency_p95_ms,
                "is_approximate": m.is_approximate,
                "confidence": m.confidence,
                "metadata": m.metadata
            }
            for m in router.models
        ]
    })


@app.route('/reload', methods=['POST'])
def reload_profiles():
    """Reload model profiles from disk."""
    try:
        router._load_profiles()
        return jsonify({
            "status": "reloaded",
            "models_loaded": len(router.models)
        })
    except Exception as e:
        logger.error(f"Reload error: {e}", exc_info=True)
        return jsonify({
            "error": str(e)
        }), 500


# Advanced Features Endpoints

@app.route('/ab-test', methods=['POST'])
def create_ab_test():
    """Create an A/B test."""
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        strategy_name = data.get('strategy', 'basic_vs_contrastive')

        if not test_id:
            return jsonify({"error": "test_id required"}), 400

        strategy = ABTestStrategy(strategy_name)

        # For now, use the same router for both variants
        # In production, you'd have different router configurations
        contrastive_router = ContrastiveRouter(Path(__file__).parent / "model_profiles.json")

        ab_test = ab_test_manager.create_test(test_id, strategy, router, contrastive_router)

        return jsonify({
            "status": "created",
            "test_id": test_id,
            "strategy": strategy.value,
            "variants": [v.name for v in ab_test.variants]
        })

    except Exception as e:
        logger.error(f"A/B test creation error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/ab-test/<test_id>', methods=['GET'])
def get_ab_test_status(test_id):
    """Get A/B test status."""
    try:
        status = ab_test_manager.get_test_status(test_id)
        if not status:
            return jsonify({"error": "Test not found"}), 404

        return jsonify(status)

    except Exception as e:
        logger.error(f"A/B test status error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/ab-test/<test_id>/complete', methods=['POST'])
def complete_ab_test(test_id):
    """Complete an A/B test."""
    try:
        winner = ab_test_manager.complete_test(test_id)
        if not winner:
            return jsonify({"error": "Test not found or already completed"}), 404

        return jsonify({
            "status": "completed",
            "winner": winner.name,
            "metrics": {
                "requests": winner.metrics.requests,
                "success_rate": winner.metrics.success_rate,
                "avg_latency_ms": winner.metrics.avg_latency_ms
            }
        })

    except Exception as e:
        logger.error(f"A/B test completion error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/features', methods=['GET'])
def list_feature_flags():
    """List all feature flags."""
    try:
        flags = feature_flag_manager.list_flags()
        return jsonify({
            "flags": flags,
            "count": len(flags)
        })

    except Exception as e:
        logger.error(f"Feature flags list error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/features/<flag_name>', methods=['GET'])
def get_feature_flag(flag_name):
    """Get a specific feature flag."""
    try:
        flag = feature_flag_manager.get_flag(flag_name)
        if not flag:
            return jsonify({"error": "Feature flag not found"}), 404

        return jsonify({
            "name": flag.name,
            "enabled": flag.enabled,
            "value": flag.value,
            "description": flag.description,
            "rollout_percentage": flag.rollout_percentage
        })

    except Exception as e:
        logger.error(f"Feature flag get error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/features/<flag_name>', methods=['POST'])
def set_feature_flag(flag_name):
    """Set a feature flag."""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        value = data.get('value')
        description = data.get('description', '')
        rollout_percentage = data.get('rollout_percentage', 100.0)

        feature_flag_manager.set_flag(
            name=flag_name,
            enabled=enabled,
            value=value,
            description=description,
            rollout_percentage=rollout_percentage
        )

        return jsonify({
            "status": "updated",
            "flag": flag_name,
            "enabled": enabled,
            "rollout_percentage": rollout_percentage
        })

    except Exception as e:
        logger.error(f"Feature flag set error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/cost-report', methods=['GET'])
def get_cost_report():
    """Get cost optimization report."""
    try:
        report = cost_optimizer.get_cost_report()
        return jsonify(report)

    except Exception as e:
        logger.error(f"Cost report error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/usage-report', methods=['GET'])
def get_usage_report():
    """Get usage analytics report."""
    try:
        report = usage_analytics.get_usage_report()
        return jsonify(report)

    except Exception as e:
        logger.error(f"Usage report error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# REP (Ripple Effect Protocol) Coordination Endpoints - Project Iceberg
# ============================================================================

@app.route('/rep/stats', methods=['GET'])
def get_rep_stats():
    """
    Get REP coordination statistics
    
    Returns statistics about multi-agent coordination:
    - Active peer count
    - Model distribution across peers
    - System state metrics
    - Coordination adjustments
    """
    try:
        # Check if router supports REP
        if not hasattr(router, 'get_rep_stats'):
            return jsonify({
                "enabled": False,
                "message": "REP coordination not enabled on this router"
            }), 200
        
        stats = router.get_rep_stats()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"REP stats error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/rep/peers', methods=['GET'])
def get_rep_peers():
    """
    Get information about active REP peers
    
    Returns:
    - List of peer agent IDs
    - Their recent decisions
    - Sensitivity signals
    """
    try:
        if not hasattr(router, 'rep_coordinator') or not router.rep_coordinator:
            return jsonify({
                "enabled": False,
                "peers": []
            }), 200
        
        peer_summary = router.rep_coordinator.get_peer_summary()
        
        return jsonify({
            "enabled": True,
            "peer_count": peer_summary['peer_count'],
            "model_distribution": peer_summary['model_distribution'],
            "avg_confidence": peer_summary['avg_confidence']
        })
    
    except Exception as e:
        logger.error(f"REP peers error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/rep/sensitivities', methods=['GET'])
def get_rep_sensitivities():
    """
    Get current sensitivity calculations
    
    Shows how this agent would respond to system changes
    """
    try:
        if not hasattr(router, 'rep_coordinator') or not router.rep_coordinator:
            return jsonify({
                "enabled": False,
                "sensitivities": []
            }), 200
        
        # Get latest sensitivities from system state
        from governance.routing.rep_protocol import REPDecision
        
        # Mock decision for sensitivity calculation
        test_decision = REPDecision(
            model="qwen2.5-coder:7b",
            confidence=0.85,
            domain="code"
        )
        
        sensitivities = router.rep_coordinator.sensitivity_calculator.calculate_all(
            test_decision,
            router.system_state,
            router.rep_coordinator.peer_messages
        )
        
        return jsonify({
            "enabled": True,
            "sensitivities": [
                {
                    "type": s.type.value,
                    "value": s.value,
                    "threshold": s.threshold,
                    "metadata": s.metadata
                }
                for s in sensitivities
            ]
        })
    
    except Exception as e:
        logger.error(f"REP sensitivities error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/rep/config', methods=['GET'])
def get_rep_config():
    """
    Get REP configuration
    
    Returns:
    - Agent ID
    - Redis URL (masked for security)
    - Channel
    - Enabled status
    """
    try:
        if not hasattr(router, 'rep_coordinator') or not router.rep_coordinator:
            return jsonify({
                "enabled": False
            }), 200
        
        coordinator = router.rep_coordinator
        
        # Mask Redis URL for security
        redis_url = coordinator.redis_url
        if '@' in redis_url:
            # Mask password
            parts = redis_url.split('@')
            redis_url = f"{parts[0].split(':')[0]}://***@{parts[1]}"
        
        return jsonify({
            "enabled": True,
            "agent_id": coordinator.agent_id,
            "channel": coordinator.channel,
            "redis_url": redis_url,
            "message_ttl_seconds": coordinator.message_ttl_seconds,
            "peer_message_count": len(coordinator.peer_messages)
        })
    
    except Exception as e:
        logger.error(f"REP config error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/rep/metrics', methods=['GET'])
def get_rep_metrics():
    """
    Get REP-specific Prometheus metrics
    
    This is a convenience endpoint that filters Prometheus metrics
    to show only REP-related ones
    """
    try:
        from prometheus_client import REGISTRY
        
        rep_metrics = []
        for metric in REGISTRY.collect():
            if metric.name.startswith('athena_rep_'):
                rep_metrics.append({
                    "name": metric.name,
                    "documentation": metric.documentation,
                    "type": metric.type,
                    "samples": len(list(metric.samples))
                })
        
        return jsonify({
            "metrics": rep_metrics,
            "count": len(rep_metrics)
        })
    
    except Exception as e:
        logger.error(f"REP metrics error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/cost-weights', methods=['POST'])
def set_cost_weights():
    """Set cost optimization weights."""
    try:
        data = request.get_json()
        cost_weight = data.get('cost', 0.7)
        quality_weight = data.get('quality', 0.2)
        latency_weight = data.get('latency', 0.1)

        cost_optimizer.set_cost_weights(cost_weight, quality_weight, latency_weight)

        return jsonify({
            "status": "updated",
            "weights": {
                "cost": cost_weight,
                "quality": quality_weight,
                "latency": latency_weight
            }
        })

    except Exception as e:
        logger.error(f"Cost weights set error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Ollama Integration Endpoints

@app.route('/ollama/models', methods=['GET'])
def get_ollama_models():
    """Get available Ollama models with Athena mappings."""
    try:
        available_models = ollama_manager.get_available_models()
        ollama_health = ollama_client.health_check()

        return jsonify({
            "ollama_available": ollama_health,
            "models": available_models,
            "model_count": len(available_models),
            "athena_mappings": ollama_manager.model_mapping
        })

    except Exception as e:
        logger.error(f"Ollama models error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/ollama/generate', methods=['POST'])
def ollama_generate():
    """Generate text using Ollama model directly."""
    try:
        data = request.get_json()
        model = data.get('model')
        prompt = data.get('prompt')
        options = data.get('options', {})

        if not model or not prompt:
            return jsonify({"error": "model and prompt required"}), 400

        result = ollama_client.generate(model, prompt, options)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Ollama generate error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/infer', methods=['POST'])
def route_and_infer():
    """
    Route query to best model AND execute inference.

    This combines routing intelligence with actual model execution.
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query"
            }), 400

        # First, get routing decision
        routing_request = RoutingRequest(
            query=data['query'],
            domain=data.get('domain', 'general'),
            metadata=data.get('metadata', {})
        )

        start_time = time.time()
        choice = router.route(routing_request)
        routing_time = time.time() - start_time

        # Record routing metrics
        routing_metrics.record_request(
            model=choice.model,
            domain=choice.domain,
            status="success",
            latency_ms=routing_time * 1000,
            confidence=choice.confidence
        )

        # Now execute inference using Ollama
        inference_result = ollama_manager.infer_with_routing_result(
            routing_result={
                "model": choice.model,
                "confidence": choice.confidence,
                "domain": choice.domain,
                "latency_ms": routing_time * 1000,
                "metadata": choice.metadata
            },
            prompt=data['query']
        )

        return jsonify(inference_result)

    except Exception as e:
        logger.error(f"Route and infer error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def main():
    """Run the routing API server with production hardening."""
    port = int(os.getenv('ROUTER_PORT', '9113'))
    host = os.getenv('ROUTER_HOST', '0.0.0.0')

    # Security configuration summary
    security_features = []
    if REQUIRED_TOKEN:
        security_features.append("🔐 Authentication enabled")
    else:
        security_features.append("⚠️  No authentication (dev mode)")

    security_features.append(f"📊 Rate limit: {RATE_LIMIT_RPM} req/min")

    if SSL_CERT_PATH and SSL_KEY_PATH:
        security_features.append("🔒 SSL/TLS enabled")
    else:
        security_features.append("⚠️  No SSL/TLS")

    logger.info("=".join(["=" for _ in range(60)]))
    logger.info("🚀 Athena Router API - PRODUCTION HARDENED")
    logger.info("=".join(["=" for _ in range(60)]))
    logger.info(f"📍 Server: {host}:{port}")
    logger.info(f"🤖 Models: {len(router.models)} loaded")

    for feature in security_features:
        logger.info(feature)

    logger.info("📊 Metrics: /metrics (Prometheus)")
    logger.info("❤️  Health: /health")
    logger.info("🔀 Routing: POST /route")
    logger.info("=".join(["=" for _ in range(60)]))

    # Start server with SSL if configured
    if SSL_CERT_PATH and SSL_KEY_PATH:
        logger.info(f"🔒 Using SSL cert: {SSL_CERT_PATH}")
        app.run(
            host=host,
            port=port,
            debug=False,
            ssl_context=(SSL_CERT_PATH, SSL_KEY_PATH)
        )
    else:
        logger.warning("⚠️  Running without SSL - use only for development!")
        app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    import os
    main()

