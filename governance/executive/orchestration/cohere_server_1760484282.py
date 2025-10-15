"""
Cohere AI MCP Server
Provides tools for Cohere's generation, embedding, and reranking
"""
import os
from typing import List

from fastmcp import FastMCP

mcp = FastMCP("cohere-ai", dependencies=["cohere"])

@mcp.tool()
def cohere_generate(
    prompt: str,
    model: str = "command",
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> dict:
    """
    Generate text using Cohere
    
    Args:
        prompt: Input prompt
        model: Cohere model (command, command-light, command-nightly)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Generated text
    """
    try:
        import cohere

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            return {"error": "COHERE_API_KEY not set"}

        co = cohere.Client(api_key)

        response = co.generate(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return {
            "text": response.generations[0].text,
            "likelihood": response.generations[0].likelihood,
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def cohere_embed(texts: List[str], model: str = "embed-english-v3.0") -> dict:
    """
    Generate embeddings using Cohere
    
    Args:
        texts: List of texts to embed
        model: Embedding model
    
    Returns:
        List of embeddings
    """
    try:
        import cohere

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            return {"error": "COHERE_API_KEY not set"}

        co = cohere.Client(api_key)

        response = co.embed(
            texts=texts,
            model=model
        )

        return {
            "embeddings": response.embeddings,
            "count": len(response.embeddings),
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def cohere_rerank(query: str, documents: List[str], top_n: int = 10) -> dict:
    """
    Rerank documents using Cohere
    
    Args:
        query: Search query
        documents: List of documents to rerank
        top_n: Number of top results to return
    
    Returns:
        Reranked documents with scores
    """
    try:
        import cohere

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            return {"error": "COHERE_API_KEY not set"}

        co = cohere.Client(api_key)

        response = co.rerank(
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents))
        )

        return {
            "results": [
                {
                    "index": r.index,
                    "score": r.relevance_score,
                    "document": r.document
                }
                for r in response.results
            ],
            "query": query,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

