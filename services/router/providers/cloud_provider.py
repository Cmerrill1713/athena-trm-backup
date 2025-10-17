"""Cloud Provider - Governed frontier access (BLOCKED by default)."""
import os
import logging
import aiohttp
from typing import Optional

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class CloudProvider(BaseProvider):
    """Cloud provider - BLOCKED unless governance allows."""
    
    def __init__(
        self,
        enabled: bool = False,
        timeout_ms: int = 5000
    ):
        super().__init__("https://api.openai.com", timeout_ms)
        self.enabled = enabled
        
        # Check for hard block
        self.hard_blocked = os.getenv("ATHENA_NO_CLOUD", "1") == "1"
        
        if self.hard_blocked:
            logger.warning("☁️  Cloud provider HARD BLOCKED by ATHENA_NO_CLOUD=1")
        elif not enabled:
            logger.info("☁️  Cloud provider disabled by policy")
        else:
            logger.warning("☁️  Cloud provider ENABLED (governance override)")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate text using cloud API (should be blocked)."""
        if self.hard_blocked:
            logger.error("🚫 BLOCKED: Cloud access attempted with ATHENA_NO_CLOUD=1")
            raise Exception("Cloud access BLOCKED by ATHENA_NO_CLOUD policy")
        
        if not self.enabled:
            logger.error("🚫 BLOCKED: Cloud access attempted without governance approval")
            raise Exception("Cloud access requires governance approval")
        
        # If we get here, governance has explicitly allowed cloud access
        logger.warning(f"☁️  CLOUD ACCESS (governed): {prompt[:50]}...")
        
        # This would call OpenAI/Anthropic/etc, but for safety we log and block
        raise Exception(
            "Cloud provider implementation intentionally blocked. "
            "Route through local models only."
        )
    
    async def health_check(self) -> bool:
        """Cloud is never considered 'healthy' for routing."""
        return False  # Never route here automatically


