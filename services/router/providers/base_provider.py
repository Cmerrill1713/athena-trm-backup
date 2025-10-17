"""Base provider interface."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """Base class for all model providers."""
    
    def __init__(self, endpoint: str, timeout_ms: int = 2000):
        self.endpoint = endpoint
        self.timeout_ms = timeout_ms
        self.timeout_s = timeout_ms / 1000.0
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        pass


