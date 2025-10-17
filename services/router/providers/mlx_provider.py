"""MLX Provider - Apple Silicon optimized inference."""
import logging
import aiohttp
from typing import Optional

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class MLXProvider(BaseProvider):
    """MLX provider for Apple Silicon."""
    
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080",
        model: str = "qwen2.5-coder-7b",
        timeout_ms: int = 1500
    ):
        super().__init__(endpoint, timeout_ms)
        self.model = model
        logger.info(f"MLX provider initialized: {endpoint}, model={model}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate text using MLX model."""
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": self.model
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.endpoint}/generate", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"MLX returned {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    return result.get("text", result.get("response", ""))
        
        except Exception as e:
            logger.error(f"MLX generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check MLX service health."""
        try:
            timeout = aiohttp.ClientTimeout(total=2.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoint}/health") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"MLX health check failed: {e}")
            return False


