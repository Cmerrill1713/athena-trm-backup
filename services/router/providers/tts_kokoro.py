"""Kokoro-82M Provider - Local TTS model."""
import logging
import aiohttp
from typing import Dict, Any, Optional

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class KokoroTTSProvider(BaseProvider):
    """Kokoro-82M provider for local text-to-speech."""
    
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8091",
        voice: str = "en_US-female",
        timeout_ms: int = 350
    ):
        super().__init__(endpoint, timeout_ms)
        self.voice = voice
        logger.info(f"Kokoro TTS provider initialized: {endpoint}, voice={voice}")
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using Kokoro-82M.
        
        Returns:
            {
                "audio_b64": str,  # Base64-encoded WAV
                "duration_ms": int,
                "sample_rate": int,
                "modality": "voice"
            }
        """
        payload = {
            "text": text,
            "voice": voice or self.voice,
            "format": "wav"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.endpoint}/synthesize", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Kokoro returned {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    return {
                        "audio_b64": result.get("audio", result.get("audio_b64", "")),
                        "duration_ms": result.get("duration_ms", 0),
                        "sample_rate": result.get("sample_rate", 24000),
                        "modality": "voice"
                    }
        
        except Exception as e:
            logger.error(f"Kokoro TTS failed: {e}")
            raise
    
    async def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Not used for TTS - use synthesize() instead."""
        raise NotImplementedError("Use synthesize() for TTS tasks")
    
    async def health_check(self) -> bool:
        """Check Kokoro service health."""
        try:
            timeout = aiohttp.ClientTimeout(total=2.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoint}/health") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"Kokoro health check failed: {e}")
            return False

