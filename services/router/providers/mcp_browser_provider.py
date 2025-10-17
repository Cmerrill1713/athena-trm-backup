"""MCP Browser Provider - Tool-augmented fallback."""
import logging
import aiohttp
from typing import Optional
from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class MCPBrowserProvider(BaseProvider):
    """MCP Browser provider for tool-augmented responses."""
    
    def __init__(
        self,
        endpoint: str,
        enabled: bool = True,
        timeout_ms: int = 4000
    ):
        super().__init__(endpoint, timeout_ms)
        self.enabled = enabled
        logger.info(f"MCP Browser provider initialized: {endpoint}, enabled={enabled}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using MCP browser tools."""
        if not self.enabled:
            raise Exception("MCP Browser provider is disabled")
        
        payload = {
            "query": prompt,
            "max_results": 5
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Use the correct MCP tool endpoint
                async with session.post(f"{self.endpoint}/tool/web_search", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"MCP Browser returned {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    # Extract search results and format as text
                    if "results" in result:
                        results = result["results"]
                        if results:
                            titles = [r.get("title", "") for r in results[:3]]
                            return f"Search results: {', '.join(titles)}"
                        else:
                            return "No search results found."
                    return result.get("text", result.get("response", "Search completed."))
        
        except Exception as e:
            logger.error(f"MCP Browser generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check MCP Browser service health."""
        if not self.enabled:
            return False
        
        try:
            timeout = aiohttp.ClientTimeout(total=2.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoint}/health") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"MCP Browser health check failed: {e}")
            return False