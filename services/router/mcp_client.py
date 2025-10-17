import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

class MCPClient:
    """Robust MCP client with proper error handling and timeouts."""
    
    def __init__(self, base="http://athena-mcp-ecosystem:8412", timeout=8.0):
        self.base = base
        self.timeout = timeout
        logger.info(f"MCP Client initialized: {base}")

    async def web_search(self, query: str):
        """Search the web using MCP web_search tool."""
        url = f"{self.base}/tool/web_search"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(url, json={"query": query})
                r.raise_for_status()
                result = r.json()
                logger.debug(f"MCP web_search result: {result}")
                return result
        except httpx.TimeoutException:
            logger.error(f"MCP web_search timeout for query: {query}")
            raise Exception("MCP web_search timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP web_search HTTP error: {e.response.status_code}")
            raise Exception(f"MCP web_search failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"MCP web_search error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check MCP service health."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base}/health")
                return r.status_code == 200
        except Exception as e:
            logger.debug(f"MCP health check failed: {e}")
            return False

# Tool name registry - keep in one place to avoid whack-a-mole
AVAILABLE_TOOLS = {
    "web_search": "/tool/web_search",
    "browser_search": "/tool/web_search",  # Alias
}

def get_tool_endpoint(tool_name: str) -> str:
    """Get the correct endpoint for a tool name."""
    return AVAILABLE_TOOLS.get(tool_name, f"/tool/{tool_name}")
