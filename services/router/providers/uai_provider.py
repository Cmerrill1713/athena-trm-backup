"""UAI Provider - Universal AI Tools integration."""
import logging
import aiohttp
from typing import Optional, Dict, Any

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class UAIProvider(BaseProvider):
    """UAI provider for OpenAI-compatible chat completions."""
    
    def __init__(
        self,
        endpoint: str = "http://uai:8080",
        model: str = "qwen2.5:7b",
        timeout_ms: int = 30000
    ):
        super().__init__(endpoint, timeout_ms)
        self.model = model
        logger.info(f"UAI provider initialized: {endpoint}, model={model}")
    
    async def chat(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        """Generate chat completion using UAI."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.endpoint}/v1/chat/completions",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"UAI returned {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"UAI chat failed: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        """Generate text using UAI (converts to chat format)."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, max_tokens, temperature)
    
    async def health_check(self) -> bool:
        """Check UAI service health."""
        try:
            timeout = aiohttp.ClientTimeout(total=2.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoint}/health") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"UAI health check failed: {e}")
            return False
