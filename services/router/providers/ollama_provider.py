"""Ollama Provider - Local model inference."""
import logging
import aiohttp
from typing import Optional

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama provider for local model inference."""
    
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5-coder:7b",
        timeout_ms: int = 2000
    ):
        super().__init__(endpoint, timeout_ms)
        self.model = model
        logger.info(f"Ollama provider initialized: {endpoint}, model={model}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate text using Ollama model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            },
            "stream": False
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.endpoint}/api/generate", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Ollama returned {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    return result.get("response", "")
        
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Ollama service health."""
        try:
            timeout = aiohttp.ClientTimeout(total=2.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Ollama has a /api/tags endpoint
                async with session.get(f"{self.endpoint}/api/tags") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False


