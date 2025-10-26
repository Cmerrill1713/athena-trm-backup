"""
Knowledge Base Search Tool for AGI Agents

Provides agents with access to the 5.8GB DocsV2 corpus via RAG Gateway.
Agents can search for factual information, code examples, policies, and documentation.
"""

import os
import logging
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

RAG_GATEWAY_URL = os.getenv("RAG_GATEWAY_URL", "http://localhost:8088")

@dataclass
class KBSearchResult:
    """Structured knowledge base search result"""
    doc_id: str
    title: str
    chunk: str
    score: float
    source: str
    url: str

class KBSearchTool:
    """
    Knowledge Base Search Tool
    
    Allows agents to query the internal knowledge base for:
    - Documentation
    - Code examples
    - Research papers
    - Policies
    - FAQs
    - Technical guides
    """
    
    def __init__(self, gateway_url: str = RAG_GATEWAY_URL, timeout: float = 5.0):
        self.gateway_url = gateway_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "nearText"
    ) -> List[KBSearchResult]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return (default 5, max 20)
            mode: Search mode - "bm25", "nearText", or "hybrid"
        
        Returns:
            List of KBSearchResult objects with citations
        
        Raises:
            HTTPError: If RAG Gateway is unavailable
        """
        try:
            logger.info(f"KB Search: {query[:100]} (mode={mode}, top_k={top_k})")
            
            response = await self.client.post(
                f"{self.gateway_url}/kb/search",
                json={
                    "query": query,
                    "topK": min(top_k, 20),  # Cap at 20
                    "mode": mode,
                    "semanticEnabled": True
                }
            )
            response.raise_for_status()
            data = response.json()
            
            hits = data.get("hits", [])
            metrics = data.get("metrics", {})
            
            logger.info(f"KB Search returned {len(hits)} hits in {metrics.get('latency_ms', 0)}ms")
            
            results = [
                KBSearchResult(
                    doc_id=hit.get("doc_id", ""),
                    title=hit.get("title", "Untitled"),
                    chunk=hit.get("chunk", ""),
                    score=hit.get("score", 0.0),
                    source=hit.get("source", ""),
                    url=hit.get("url", "")
                )
                for hit in hits
            ]
            
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"KB Search failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in KB Search: {e}")
            raise
    
    def format_results_for_agent(self, results: List[KBSearchResult], max_context: int = 2000) -> str:
        """
        Format search results for agent consumption.
        
        Returns a compact string with citations that fits in agent context.
        """
        if not results:
            return "No relevant documentation found in knowledge base."
        
        formatted = []
        total_chars = 0
        
        for i, result in enumerate(results):
            if total_chars >= max_context:
                break
            
            citation = f"[{result.doc_id}:{result.title}]"
            chunk_preview = result.chunk[:300] + ("..." if len(result.chunk) > 300 else "")
            entry = f"{i+1}. {citation}\n   Score: {result.score:.3f}\n   {chunk_preview}\n"
            
            formatted.append(entry)
            total_chars += len(entry)
        
        return "\n".join(formatted)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Tool definition for OpenAI-style function calling
KB_SEARCH_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "kb_search",
        "description": "Search internal knowledge base for documentation, code examples, research papers, and policies. Returns snippets with citations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query. Be specific and include key terms."
                },
                "topK": {
                    "type": "integer",
                    "description": "Number of results to return (1-20)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "mode": {
                    "type": "string",
                    "enum": ["bm25", "nearText", "hybrid"],
                    "description": "Search mode: bm25 (keyword), nearText (semantic), hybrid (both)",
                    "default": "nearText"
                }
            },
            "required": ["query"]
        }
    }
}


# Convenience function for quick searches
async def kb_search(query: str, top_k: int = 5, mode: str = "nearText") -> List[KBSearchResult]:
    """
    Quick knowledge base search function.
    
    Usage:
        results = await kb_search("How to reset tokens?")
        for result in results:
            print(f"{result.title}: {result.chunk[:100]}")
    """
    tool = KBSearchTool()
    try:
        return await tool.search(query, top_k, mode)
    finally:
        await tool.close()


if __name__ == "__main__":
    import asyncio
    
    async def test():
        tool = KBSearchTool()
        try:
            # Test search
            results = await tool.search("How to train recursive models?", top_k=3, mode="hybrid")
            print(f"\nFound {len(results)} results:\n")
            print(tool.format_results_for_agent(results))
        finally:
            await tool.close()
    
    asyncio.run(test())

