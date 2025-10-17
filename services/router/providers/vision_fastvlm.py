"""FastVLM Provider - Local vision model."""
import logging
import base64
import aiohttp
from typing import Dict, Any, Optional, List

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class FastVLMProvider(BaseProvider):
    """FastVLM provider for local vision analysis."""
    
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8088",
        timeout_ms: int = 1500
    ):
        super().__init__(endpoint, timeout_ms)
        logger.info(f"FastVLM provider initialized: {endpoint}")
    
    async def analyze(
        self,
        image_b64: str,
        prompt: str = "Describe the image in detail"
    ) -> Dict[str, Any]:
        """
        Analyze image using FastVLM.
        
        Returns:
            {
                "caption": str,
                "boxes": List[Dict],  # Optional bounding boxes
                "confidence": float,
                "modality": "vision"
            }
        """
        payload = {
            "image": image_b64,
            "prompt": prompt,
            "max_tokens": 256
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.endpoint}/analyze", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"FastVLM returned {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    return {
                        "caption": result.get("caption", result.get("description", "")),
                        "boxes": result.get("boxes", []),
                        "confidence": result.get("confidence", 0.9),
                        "modality": "vision"
                    }
        
        except Exception as e:
            logger.error(f"FastVLM analysis failed: {e}")
            raise
    
    async def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Not used for vision - use analyze() instead."""
        raise NotImplementedError("Use analyze() for vision tasks")
    
    async def health_check(self) -> bool:
        """Check FastVLM service health."""
        try:
            timeout = aiohttp.ClientTimeout(total=2.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoint}/health") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"FastVLM health check failed: {e}")
            return False

