"""
Microsoft Azure AI MCP Server
Provides tools for Azure OpenAI and Cognitive Services
"""
import os
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("microsoft-azure", dependencies=["azure-ai-inference", "azure-search-documents"])

@mcp.tool()
def azure_openai_chat(
    messages: list,
    deployment: str = "gpt-4",
    endpoint: Optional[str] = None
) -> dict:
    """
    Chat with Azure OpenAI
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        deployment: Azure OpenAI deployment name
        endpoint: Azure OpenAI endpoint URL (optional, uses env var)
    
    Returns:
        Chat completion response
    """
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential

        endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_KEY")

        if not endpoint or not key:
            return {"error": "Azure OpenAI credentials not set"}

        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        response = client.complete(
            model=deployment,
            messages=messages
        )

        return {
            "content": response.choices[0].message.content,
            "model": deployment,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def azure_cognitive_search(
    query: str,
    index: str,
    endpoint: Optional[str] = None,
    top: int = 10
) -> dict:
    """
    Search using Azure Cognitive Search
    
    Args:
        query: Search query
        index: Search index name
        endpoint: Azure Search endpoint (optional, uses env var)
        top: Number of results to return
    
    Returns:
        Search results
    """
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient

        endpoint = endpoint or os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_KEY")

        if not endpoint or not key:
            return {"error": "Azure Search credentials not set"}

        client = SearchClient(
            endpoint=endpoint,
            index_name=index,
            credential=AzureKeyCredential(key)
        )

        results = client.search(query, top=top)

        return {
            "results": [
                {
                    "score": r.get("@search.score"),
                    "document": {k: v for k, v in r.items() if not k.startswith("@")}
                }
                for r in results
            ],
            "count": len(list(results)),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

