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
    
    def _extract_search_query(self, prompt: str) -> str:
        """Extract search terms from browser requests."""
        prompt_lower = prompt.lower()
        
        # Common browser request patterns
        browser_patterns = [
            "open a browser and look up",
            "search for",
            "look up",
            "find information about",
            "research",
            "browse",
            "search",
            "look for"
        ]
        
        # Remove browser request language and extract the actual search terms
        search_query = prompt
        for pattern in browser_patterns:
            if pattern in prompt_lower:
                # Extract everything after the pattern
                parts = prompt_lower.split(pattern, 1)
                if len(parts) > 1:
                    search_query = parts[1].strip()
                    break
        
        # Clean up the search query
        search_query = search_query.replace("research papers", "").replace("papers", "").strip()
        
        # If no specific search terms found, use common research topics
        if not search_query or len(search_query) < 3:
            search_query = "artificial intelligence research"
        
        logger.info(f"Extracted search query: '{search_query}' from prompt: '{prompt}'")
        return search_query
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using MCP browser tools."""
        if not self.enabled:
            raise Exception("MCP Browser provider is disabled")
        
        # Extract search terms from browser requests
        search_query = self._extract_search_query(prompt)
        
        payload = {
            "arguments": {
                "query": search_query,
                "num_results": 5
            }
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
                    logger.info(f"MCP Browser result: {result}")
                    
                    # Extract search results and format as text
                    if "results" in result:
                        results = result["results"]
                        if results and len(results) > 0:
                            # Format results nicely
                            formatted_results = []
                            for r in results[:3]:
                                title = r.get("title", "Untitled")
                                snippet = r.get("snippet", "")[:100] + "..." if len(r.get("snippet", "")) > 100 else r.get("snippet", "")
                                url = r.get("url", "")
                                source = r.get("source", "")
                                formatted_results.append(f"• {title} ({source})\n  {snippet}\n  {url}")
                            
                            return f"Search results for '{prompt}':\n\n" + "\n\n".join(formatted_results)
                        else:
                            return f"No search results found for '{prompt}'."
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