"""
MLX Integration for Athena Router

Provides Apple Silicon-optimized inference using MLX framework.
MLX offers significant performance improvements on M1/M2/M3 chips.

MLX vs Ollama:
- MLX: Optimized for Apple Silicon, faster inference, lower power
- Ollama: General-purpose, works on any hardware, more models

Architecture: MLX primary, Ollama fallback
"""

import logging
import time
from typing import Dict, Optional, Any, Tuple
import subprocess
import sys

logger = logging.getLogger(__name__)


class MLXModelManager:
    """Manages MLX models and inference."""

    def __init__(self):
        self.model_configs = {
            # Athena model ID -> MLX configuration
            "codellama-34b": {
                "mlx_model": "mlx-community/CodeLlama-34b-Instruct-hf-4bit-MLX",
                "max_tokens": 512,
                "temperature": 0.1
            },
            "gpt-4-turbo": {
                "mlx_model": "mlx-community/OpenHermes-2.5-Mistral-7B",
                "max_tokens": 1024,
                "temperature": 0.7
            },
            "gpt-3.5-turbo": {
                "mlx_model": "mlx-community/Phi-2-3B-4bit-mlx",
                "max_tokens": 512,
                "temperature": 0.7
            },
            "claude-3-opus": {
                "mlx_model": "mlx-community/Mistral-7B-Instruct-v0.2",
                "max_tokens": 1024,
                "temperature": 0.8
            }
        }

        # Check available models after configs are defined
        self.available_models = self._check_available_models()

    def _check_available_models(self) -> Dict[str, bool]:
        """Check which MLX models are available locally."""
        available = {}

        # Check if MLX is installed
        try:
            import mlx.core as mx
            logger.info("MLX framework available")
        except ImportError:
            logger.warning("MLX framework not installed - MLX models unavailable")
            return {}

        # Check for available models (simplified check)
        # In practice, you'd check actual model files/directories
        for model_id, config in self.model_configs.items():
            # For now, assume models are available if MLX is installed
            # In production, check actual model file existence
            available[model_id] = True

        logger.info(f"MLX models available: {list(available.keys())}")
        return available

    def has_model(self, athena_model_id: str) -> bool:
        """Check if MLX model is available."""
        return athena_model_id in self.available_models

    def infer_mlx(self, athena_model_id: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Execute inference using MLX model.

        Args:
            athena_model_id: Athena model identifier
            prompt: Input prompt
            **kwargs: Additional inference parameters

        Returns:
            Dict with inference results
        """
        if not self.has_model(athena_model_id):
            raise ValueError(f"MLX model {athena_model_id} not available")

        try:
            import mlx.core as mx
            import mlx.nn as nn

            start_time = time.time()

            # Get model configuration
            config = self.model_configs[athena_model_id]
            mlx_model_name = config["mlx_model"]

            # Load model (simplified - in practice, use proper MLX model loading)
            logger.info(f"Loading MLX model: {mlx_model_name}")

            # Placeholder for actual MLX inference
            # In production, this would:
            # 1. Load the MLX model
            # 2. Tokenize input
            # 3. Run inference
            # 4. Decode output

            # Simulate inference time and response
            inference_time = time.time() - start_time

            # Mock response for demonstration
            mock_responses = {
                "codellama-34b": "```python\ndef sort_list(arr):\n    return sorted(arr)\n```",
                "gpt-4-turbo": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                "gpt-3.5-turbo": "To sort a list in Python, you can use the `sorted()` function or the `list.sort()` method.",
                "claude-3-opus": "The user asked about machine learning. Let me provide a comprehensive explanation."
            }

            response = mock_responses.get(athena_model_id, "This is a mock MLX response.")

            return {
                "model": athena_model_id,
                "mlx_model": mlx_model_name,
                "response": response,
                "done": True,
                "inference_time": inference_time,
                "tokens_per_second": len(response.split()) / max(inference_time, 0.001),
                "backend": "mlx",
                "hardware": "apple_silicon"
            }

        except Exception as e:
            logger.error(f"MLX inference failed for {athena_model_id}: {e}")
            raise


class InferenceManager:
    """
    Manages inference backends with MLX primary, Ollama fallback.

    Priority order:
    1. MLX (Apple Silicon optimized)
    2. Ollama (general purpose)
    """

    def __init__(self):
        self.mlx_manager = MLXModelManager()
        self.ollama_manager = None  # Lazy load to avoid import errors

    def _get_ollama_manager(self):
        """Lazy load Ollama manager."""
        if self.ollama_manager is None:
            try:
                from .ollama_integration import ollama_manager
                self.ollama_manager = ollama_manager
            except ImportError:
                logger.warning("Ollama integration not available")
                self.ollama_manager = None
        return self.ollama_manager

    def infer(self, athena_model_id: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Execute inference with MLX primary, Ollama fallback.

        Args:
            athena_model_id: Athena model identifier
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Dict with inference results and backend info
        """
        # Try MLX first (primary)
        if self.mlx_manager.has_model(athena_model_id):
            try:
                logger.info(f"Using MLX for {athena_model_id}")
                result = self.mlx_manager.infer_mlx(athena_model_id, prompt, **kwargs)
                result["fallback_used"] = False
                return result

            except Exception as e:
                logger.warning(f"MLX inference failed for {athena_model_id}: {e}")

        # Fall back to Ollama
        ollama_mgr = self._get_ollama_manager()
        if ollama_mgr:
            try:
                logger.info(f"Falling back to Ollama for {athena_model_id}")
                result = ollama_mgr.infer_with_routing_result(
                    routing_result={
                        "model": athena_model_id,
                        "confidence": 0.5,  # Lower confidence for fallback
                        "domain": "general",
                        "latency_ms": 0.0,
                        "metadata": {"strategy": "mlx_fallback"}
                    },
                    prompt=prompt
                )
                result["fallback_used"] = True
                result["fallback_backend"] = "ollama"
                return result

            except Exception as e:
                logger.error(f"Ollama fallback also failed for {athena_model_id}: {e}")

        # Both backends failed
        raise RuntimeError(f"All inference backends failed for model {athena_model_id}")

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all available models across backends."""
        models = {}

        # MLX models (primary)
        for model_id in self.mlx_manager.available_models:
            config = self.mlx_manager.model_configs.get(model_id, {})
            models[model_id] = {
                "primary_backend": "mlx",
                "mlx_model": config.get("mlx_model"),
                "fallback_available": self._get_ollama_manager() is not None,
                "max_tokens": config.get("max_tokens", 512),
                "hardware_optimized": "apple_silicon"
            }

        # Ollama models (fallback only - not listed as primary)
        ollama_mgr = self._get_ollama_manager()
        if ollama_mgr:
            for ollama_name, info in ollama_mgr.get_available_models().items():
                athena_id = info.get("athena_model_id")
                if athena_id and athena_id not in models:
                    # Only add if not already available via MLX
                    models[athena_id] = {
                        "primary_backend": "ollama",
                        "ollama_model": ollama_name,
                        "fallback_available": False,
                        "hardware_optimized": "general"
                    }

        return models

    def health_check(self) -> Dict[str, Any]:
        """Check health of all inference backends."""
        return {
            "mlx": {
                "available": len(self.mlx_manager.available_models) > 0,
                "models": list(self.mlx_manager.available_models.keys())
            },
            "ollama": {
                "available": self._get_ollama_manager() is not None,
                "healthy": self._get_ollama_manager() and self._get_ollama_manager().client.health_check()
            },
            "inference_ready": len(self.get_available_models()) > 0
        }


# Global inference manager
inference_manager = InferenceManager()

