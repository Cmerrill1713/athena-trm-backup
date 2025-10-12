"""
FastVLM Provider - Vision model provider for Athena routing system
Integrates Apple's FastVLM into the model selection infrastructure
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import Sentry for observability (follows user's Sentry rules)
try:
    import sentry_sdk as Sentry
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logging.warning("Sentry not available - vision operations won't be traced")

# Import Prometheus for metrics
try:
    from prometheus_client import Counter, Histogram
    
    VISION_ROUTING_DECISIONS = Counter(
        'routing_decisions_total',
        'Total routing decisions',
        ['model', 'env', 'build']
    )
    
    VISION_ROUTING_LATENCY = Histogram(
        'routing_latency_ms',
        'Vision routing latency',
        ['model', 'env', 'build'],
        buckets=[50, 100, 200, 500, 1000, 2000, 5000]
    )
    
    VISION_ROUTING_SUCCESS = Counter(
        'routing_success_total',
        'Successful vision routing',
        ['model', 'env', 'build']
    )
    
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


logger = logging.getLogger(__name__)

ENV = os.environ.get("ENV", "dev")
BUILD_SHA = os.environ.get("BUILD_SHA", "local")


class FastVLMProvider:
    """
    FastVLM model provider for vision tasks
    
    Capabilities: vision, ocr, chart_reading, screenshot_analysis
    """
    
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8811",
        model_name: str = "fastvlm-1.5b"
    ):
        """
        Initialize FastVLM provider
        
        Args:
            endpoint: FastVLM server endpoint
            model_name: Model identifier for metrics
        """
        self.endpoint = endpoint
        self.model_name = model_name
        self.logger = logger.getChild("FastVLMProvider")
    
    def get_capabilities(self) -> Dict[str, float]:
        """
        Return model capabilities with quality scores
        
        Returns:
            Dict mapping capability to quality score (0-1)
        """
        return {
            "vision": 0.85,
            "ocr": 0.82,
            "chart_reading": 0.78,
            "screenshot_analysis": 0.88,
            "ui_understanding": 0.80,
            "diagram_analysis": 0.75
        }
    
    def is_available(self) -> bool:
        """
        Check if FastVLM server is available
        
        Returns:
            True if server is healthy
        """
        try:
            # Import here to avoid circular dependency
            from fastvlm.fastvlm_client import get_client
            
            client = get_client(self.endpoint)
            return client.is_healthy()
        except Exception as e:
            self.logger.warning(f"FastVLM availability check failed: {e}")
            return False
    
    def call(
        self,
        image_path: str,
        prompt: str = "Describe the image.",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Call FastVLM vision model with Sentry tracing and metrics
        
        Args:
            image_path: Path to image file
            prompt: Vision prompt/question
            context: Optional context dict for tracing attributes
        
        Returns:
            Model output text
        
        Raises:
            Exception: If inference fails
        """
        import time
        
        # Import client
        try:
            from fastvlm.fastvlm_client import get_client
        except ImportError:
            raise ImportError(
                "FastVLM client not found. Ensure fastvlm package is in PYTHONPATH"
            )
        
        # Create span for vision operation (follows user's Sentry rules)
        if SENTRY_AVAILABLE:
            return Sentry.start_span(
                {
                    "op": "vision.inference",
                    "name": f"FastVLM: {Path(image_path).name}",
                },
                lambda span: self._call_with_span(
                    span, image_path, prompt, context
                )
            )
        else:
            return self._call_impl(image_path, prompt, context)
    
    def _call_with_span(
        self,
        span,
        image_path: str,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Call with Sentry span active"""
        # Add attributes (follows user's Sentry rules for span attributes)
        span.set_attribute("model", self.model_name)
        span.set_attribute("endpoint", self.endpoint)
        span.set_attribute("image", Path(image_path).name)
        span.set_attribute("prompt_length", len(prompt))
        
        if context:
            for key, value in context.items():
                span.set_attribute(f"context.{key}", str(value))
        
        return self._call_impl(image_path, prompt, context)
    
    def _call_impl(
        self,
        image_path: str,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Actual call implementation with metrics + outcome logging"""
        import time
        from fastvlm.fastvlm_client import get_client
        
        start_time = time.time()
        success = False
        error_msg = None
        
        try:
            # Record routing decision
            if METRICS_AVAILABLE:
                VISION_ROUTING_DECISIONS.labels(
                    model=self.model_name,
                    env=ENV,
                    build=BUILD_SHA
                ).inc()
            
            # Make the call
            client = get_client(self.endpoint)
            result = client.vision(image_path, prompt)
            
            # Record success and latency
            latency_ms = (time.time() - start_time) * 1000
            success = bool(result and result.get("text"))
            
            if METRICS_AVAILABLE:
                VISION_ROUTING_SUCCESS.labels(
                    model=self.model_name,
                    env=ENV,
                    build=BUILD_SHA
                ).inc()
                
                VISION_ROUTING_LATENCY.labels(
                    model=self.model_name,
                    env=ENV,
                    build=BUILD_SHA
                ).observe(latency_ms)
            
            self.logger.info(
                f"FastVLM inference complete: {latency_ms:.0f}ms "
                f"(server: {result.get('latency_ms', 0):.0f}ms)"
            )
            
            # Determine task type from prompt or context
            task_type = self._infer_task_type(prompt, context)
            
            # Log routing decision for autonomous learning
            self._log_outcome(
                prompt=f"[VISION] {prompt}",
                policy={"selected_model": self.model_name, "capabilities": {"vision": 1.0}},
                latency_ms=int(latency_ms),
                success=success,
                meta={
                    **(context or {}),
                    "task_type": task_type,
                    "task": "vision",
                    "channel": "prod"
                }
            )
            
            return result["text"]
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Log error with Sentry (follows user's exception catching rules)
            self.logger.error(f"FastVLM inference failed after {latency_ms:.0f}ms: {e}")
            
            if SENTRY_AVAILABLE:
                Sentry.capture_exception(e)
            
            # Determine task type
            task_type = self._infer_task_type(prompt, context)
            
            # Log failed outcome for learning
            self._log_outcome(
                prompt=f"[VISION] {prompt}",
                policy={"selected_model": self.model_name, "capabilities": {"vision": 1.0}},
                latency_ms=int(latency_ms),
                success=False,
                meta={
                    **(context or {}),
                    "task_type": task_type,
                    "error": error_msg,
                    "task": "vision",
                    "channel": "prod"
                }
            )
            
            raise
    
    def _infer_task_type(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Infer specific task type from prompt/context for grade isolation"""
        # Check context first
        if context and "task_type" in context:
            return context["task_type"]
        
        # Infer from prompt keywords
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["extract text", "ocr", "read text"]):
            return "ocr"
        elif any(kw in prompt_lower for kw in ["chart", "graph", "data", "plot"]):
            return "chart"
        elif any(kw in prompt_lower for kw in ["ui", "interface", "button", "screen"]):
            return "ui"
        elif any(kw in prompt_lower for kw in ["diagram", "architecture", "flow"]):
            return "diagram"
        elif any(kw in prompt_lower for kw in ["whiteboard", "handwriting", "notes"]):
            return "whiteboard"
        else:
            return "vision"  # General vision
    
    def _log_outcome(
        self,
        prompt: str,
        policy: Dict[str, Any],
        latency_ms: int,
        success: bool,
        meta: Optional[Dict[str, Any]] = None
    ):
        """Log routing outcome for autonomous learning (fail-safe)"""
        try:
            from scripts.learn.outcome_logger import log_routing_decision
            
            log_routing_decision(
                prompt=prompt,
                policy=policy,
                selected_model=self.model_name,
                latency_ms=latency_ms,
                success=success,
                user_feedback=None,
                meta=meta
            )
        except Exception as e:
            # Never let logging break inference
            self.logger.debug(f"Outcome logging failed (non-fatal): {e}")


# Registry entry for model selector
FASTVLM_REGISTRY_ENTRY = {
    "name": "fastvlm-1.5b",
    "provider": "fastvlm",
    "caps": {"vision", "ocr", "chart_reading", "screenshot_analysis"},
    "quality": 0.85,  # Baseline; router will adjust based on outcomes
    "context": 4096,
    "latency_ms": 500,  # Expected latency
    "cost_tier": "free",  # Running locally
    "local": True,
    "endpoint": "http://127.0.0.1:8811"
}


def register_fastvlm_models(registry: List[Dict[str, Any]]) -> None:
    """
    Register FastVLM models in the routing registry
    
    Args:
        registry: Model registry to update
    """
    # Check if FastVLM is available
    try:
        from fastvlm.fastvlm_client import get_client
        client = get_client()
        
        if client.is_healthy():
            logger.info("FastVLM is available, registering models")
            registry.append(FASTVLM_REGISTRY_ENTRY)
        else:
            logger.warning("FastVLM server not healthy, skipping registration")
    except Exception as e:
        logger.warning(f"FastVLM not available: {e}")


# Singleton provider instance
_provider_instance: Optional[FastVLMProvider] = None


def get_provider(endpoint: Optional[str] = None) -> FastVLMProvider:
    """
    Get or create singleton FastVLM provider
    
    Args:
        endpoint: Optional endpoint override
    
    Returns:
        FastVLM provider instance
    """
    global _provider_instance
    
    if endpoint is None:
        endpoint = os.environ.get("FASTVLM_ENDPOINT", "http://127.0.0.1:8811")
    
    if _provider_instance is None or _provider_instance.endpoint != endpoint:
        _provider_instance = FastVLMProvider(endpoint)
    
    return _provider_instance

