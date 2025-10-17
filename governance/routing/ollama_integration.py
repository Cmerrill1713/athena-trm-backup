"""
Ollama Integration for Athena Router

Provides seamless integration with Ollama-hosted local models,
enabling the router to execute inference on routed queries.
"""

import logging
import time
from typing import Dict, Optional, Any
import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minute timeout for inference

    def list_models(self) -> list:
        """List all available Ollama models."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    def generate(self, model: str, prompt: str, options: Optional[Dict] = None) -> Dict:
        """
        Generate text using specified Ollama model.

        Args:
            model: Model name (e.g., 'qwen3-coder:30b')
            prompt: Input prompt
            options: Additional generation options

        Returns:
            Dict with 'response', 'done', and metadata
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False  # Non-streaming for simplicity
        }

        if options:
            payload.update(options)

        try:
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            inference_time = time.time() - start_time

            # Add timing metadata
            result['inference_time'] = inference_time
            result['tokens_per_second'] = len(result.get('response', '').split()) / inference_time

            logger.info(f"Ollama inference: {model} in {inference_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Ollama generation failed for {model}: {e}")
            return {
                "error": str(e),
                "model": model,
                "done": False,
                "inference_time": 0.0
            }

    def health_check(self) -> bool:
        """Check if Ollama service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False


class OllamaModelManager:
    """Manages mapping between Athena model profiles and Ollama models."""

    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client
        self.model_mapping = {
            # Athena model ID -> Ollama model name
            "codellama-34b": "qwen3-coder:30b",
            "gpt-4-turbo": "qwen2.5:14b",
            "gpt-3.5-turbo": "qwen2.5:7b",
            "claude-3-opus": "mistral:7b",
            "llama-3.2-3b": "llama3.2:3b",
            "gpt-oss-20b": "gpt-oss:20b"
        }

        # Athena domain -> preferred Ollama models
        self.domain_preferences = {
            "code": ["qwen3-coder:30b", "codellama:34b"],
            "general": ["qwen2.5:14b", "qwen2.5:7b", "mistral:7b"],
            "math": ["qwen2.5:14b", "qwen2.5:7b"],
            "embedding": ["qwen3-embedding:4b", "nomic-embed-text:latest"]
        }

    def get_ollama_model(self, athena_model_id: str) -> Optional[str]:
        """Get Ollama model name for Athena model ID."""
        return self.model_mapping.get(athena_model_id)

    def get_available_models(self) -> Dict[str, Any]:
        """Get all available Ollama models with Athena mapping."""
        ollama_models = self.client.list_models()
        available = {}

        for model in ollama_models:
            name = model['name']
            # Find which Athena model this corresponds to
            athena_id = None
            for athena, ollama in self.model_mapping.items():
                if ollama == name:
                    athena_id = athena
                    break

            available[name] = {
                "athena_model_id": athena_id,
                "size": model.get('size', 'unknown'),
                "modified": model.get('modified_at', 'unknown'),
                "digest": model.get('digest', '')[:16] + '...'
            }

        return available

    def infer_with_routing_result(self, routing_result: Dict, prompt: str) -> Dict:
        """
        Execute inference using routing result from Athena router.

        Args:
            routing_result: Result from /route endpoint
            prompt: The original user prompt

        Returns:
            Dict with inference result and routing metadata
        """
        model_id = routing_result.get('model')
        ollama_model = self.get_ollama_model(model_id)

        if not ollama_model:
            return {
                "error": f"No Ollama mapping for Athena model {model_id}",
                "routing_result": routing_result,
                "prompt": prompt
            }

        # Execute inference
        inference_result = self.client.generate(ollama_model, prompt)

        # Combine routing metadata with inference result
        result = {
            "routing": routing_result,
            "inference": inference_result,
            "ollama_model": ollama_model,
            "athena_model": model_id,
            "prompt": prompt,
            "response": inference_result.get('response', ''),
            "total_time": routing_result.get('latency_ms', 0) + inference_result.get('inference_time', 0)
        }

        logger.info(f"Executed routed inference: {model_id} -> {ollama_model} ({result['total_time']:.2f}s total)")

        return result


# Global instances
ollama_client = OllamaClient()
ollama_manager = OllamaModelManager(ollama_client)

