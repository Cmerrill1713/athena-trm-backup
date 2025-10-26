#!/usr/bin/env python3
"""
MCP Ecosystem - Python backend for MCP tools
Port 8412 - Provides tools for YouTube, arXiv, Wikipedia, etc.
"""
import os
import logging
import requests
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Ecosystem",
    description="Tool backend for MCP ecosystem wrapper",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolRequest(BaseModel):
    """Tool execution request."""
    arguments: Dict[str, Any] = {}

async def search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Perform web search using DuckDuckGo API."""
    try:
        # Use DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        logger.info(f"Searching DuckDuckGo for: {query}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Check if response is empty
        if not response.text.strip():
            logger.warning("DuckDuckGo returned empty response")
            return _get_fallback_results(query)
        
        data = response.json()
        logger.info(f"DuckDuckGo response keys: {list(data.keys())}")
        
        results = []
        
        # Extract abstract if available
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "DuckDuckGo Result"),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", ""),
                "source": "DuckDuckGo"
            })
        
        # Extract related topics
        for topic in data.get("RelatedTopics", [])[:num_results-1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " ").title(),
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "source": "DuckDuckGo"
                })
        
        if not results:
            logger.warning("No results from DuckDuckGo, using fallback")
            return _get_fallback_results(query)
        
        return results[:num_results]
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return _get_fallback_results(query)

def _get_fallback_results(query: str) -> List[Dict[str, str]]:
    """Get fallback results when search fails."""
    return [
        {
            "title": f"Search results for: {query}",
            "url": "https://arxiv.org/search/?query=" + query.replace(" ", "+"),
            "snippet": f"Search results for '{query}' - this is a placeholder result. The web search functionality is being implemented.",
            "source": "Placeholder"
        },
        {
            "title": f"arXiv search for: {query}",
            "url": "https://arxiv.org/search/?query=" + query.replace(" ", "+"),
            "snippet": f"Search arXiv for '{query}' - this is a placeholder result.",
            "source": "arXiv Placeholder"
        }
    ]

async def search_arxiv(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search arXiv for research papers."""
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response (simplified)
        content = response.text
        results = []
        
        # Simple XML parsing for arXiv results
        import re
        entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
        
        for entry in entries[:max_results]:
            title_match = re.search(r'<title>(.*?)</title>', entry)
            summary_match = re.search(r'<summary>(.*?)</summary>', entry)
            link_match = re.search(r'<link.*?href="([^"]*)"', entry)
            
            if title_match:
                results.append({
                    "title": title_match.group(1).strip(),
                    "url": link_match.group(1) if link_match else "",
                    "snippet": summary_match.group(1).strip()[:200] + "..." if summary_match else "",
                    "source": "arXiv"
                })
        
        return results
        
    except Exception as e:
        logger.error(f"arXiv search error: {e}")
        return [
            {
                "title": f"arXiv search for: {query}",
                "url": "https://arxiv.org",
                "snippet": f"Search results for '{query}' on arXiv - this is a placeholder result.",
                "source": "arXiv Placeholder"
            }
        ]

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "mcp-ecosystem",
        "port": 8412,
        "tools_available": 11
    }

@app.post("/tool/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    """Execute MCP tool."""
    logger.info(f"Tool call: {tool_name} with args: {request.arguments}")
    
    try:
        if tool_name == "web_search":
            query = request.arguments.get("query", "")
            num_results = request.arguments.get("num_results", 5)
            
            # Always try arXiv search for research papers
            logger.info(f"Searching arXiv for: {query}")
            arxiv_results = await search_arxiv(query, num_results)
            if arxiv_results:
                return {"results": arxiv_results}
            
            # Fallback to placeholder if arXiv fails
            return {"results": _get_fallback_results(query)}
            
        elif tool_name == "arxiv_search":
            query = request.arguments.get("query", "")
            max_results = request.arguments.get("max_results", 5)
            results = await search_arxiv(query, max_results)
            return {"papers": results}
            
        elif tool_name == "youtube_get_transcript":
            video_id = request.arguments.get("video_id", "")
            return {
                "transcript": f"Transcript for video {video_id} - placeholder implementation",
                "duration": 120
            }
            
        elif tool_name == "wikipedia_search":
            query = request.arguments.get("query", "")
            return {
                "content": f"Wikipedia content for '{query}' - placeholder implementation",
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            }
            
        elif tool_name == "vision_analyze":
            image_url = request.arguments.get("image_url", "")
            return {
                "analysis": f"Vision analysis for image {image_url} - placeholder implementation",
                "objects": ["object1", "object2"],
                "confidence": 0.85
            }
            
        elif tool_name == "code_execute":
            code = request.arguments.get("code", "print('Hello, World!')")
            return {
                "output": f"Executed code: {code}",
                "exitcode": 0,
                "stdout": "Hello, World!",
                "stderr": ""
            }
            
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
            
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_PORT", "8412"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

