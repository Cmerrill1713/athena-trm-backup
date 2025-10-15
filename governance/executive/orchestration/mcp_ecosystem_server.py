#!/usr/bin/env python3
"""
MCP Ecosystem Server
Complete multi-tool MCP server with YouTube, arXiv, Wikipedia, Web Search, and more
"""
import json
import os
import subprocess
from typing import Any, Dict

import requests
from mcp.server.fastmcp import FastMCP, tool

# Initialize MCP server
mcp = FastMCP("mcp-ecosystem")

MCPSTORE_URL = os.getenv("MCPSTORE_URL", "http://athena-mcp-store:8411")

# ============================================================================
# YOUTUBE TOOLS (using yt-dlp-transcript)
# ============================================================================

@tool()
def youtube_get_transcript(url: str, language: str = "en"):
    """
    Get transcript from a YouTube video using yt-dlp-transcript.
    
    Args:
        url: YouTube video URL
        language: Subtitle language code (default: en)
    
    Returns:
        str: Video transcript text
    """
    try:
        from yt_dlp_transcript import yt_dlp_transcript
        transcript = yt_dlp_transcript(url, language=language)

        # Store result
        store_result("youtube", "transcript", "PASS",
                    f"Fetched transcript for {url[:50]}...",
                    {"url": url, "language": language, "length": len(transcript)})

        return {"transcript": transcript, "url": url, "language": language}
    except Exception as e:
        store_result("youtube", "transcript", "FAIL",
                    f"Failed to fetch transcript: {str(e)[:100]}",
                    {"url": url, "error": str(e)})
        return {"error": str(e), "url": url}

@tool()
def youtube_download_video(url: str, format: str = "best"):
    """
    Download YouTube video metadata and info using yt-dlp.
    
    Args:
        url: YouTube video URL
        format: Video format (default: best)
    
    Returns:
        dict: Video information and download status
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
                "url": url
            }
        else:
            return {"error": result.stderr, "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}

# ============================================================================
# RESEARCH TOOLS (arXiv, Wikipedia)
# ============================================================================

@tool()
def arxiv_search(query: str, max_results: int = 5):
    """
    Search arXiv for research papers.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 5)
    
    Returns:
        list: Research papers with title, authors, summary
    """
    try:
        import arxiv

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = []
        for result in search.results():
            papers.append({
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published": result.published.isoformat(),
                "pdf_url": result.pdf_url,
                "entry_id": result.entry_id
            })

        store_result("research", "arxiv", "PASS",
                    f"Found {len(papers)} papers for: {query[:50]}",
                    {"query": query, "results": len(papers)})

        return {"papers": papers, "count": len(papers)}
    except Exception as e:
        return {"error": str(e), "query": query}

@tool()
def wikipedia_search(query: str, sentences: int = 3):
    """
    Search Wikipedia and get summary.
    
    Args:
        query: Search query
        sentences: Number of sentences in summary (default: 3)
    
    Returns:
        dict: Wikipedia page summary and URL
    """
    try:
        import wikipedia

        # Search for the page
        pages = wikipedia.search(query, results=1)
        if not pages:
            return {"error": "No results found", "query": query}

        # Get summary
        page = wikipedia.page(pages[0])
        summary = wikipedia.summary(pages[0], sentences=sentences)

        store_result("research", "wikipedia", "PASS",
                    f"Retrieved: {page.title[:50]}",
                    {"query": query, "title": page.title})

        return {
            "title": page.title,
            "summary": summary,
            "url": page.url,
            "categories": page.categories[:5] if hasattr(page, 'categories') else []
        }
    except Exception as e:
        return {"error": str(e), "query": query}

# ============================================================================
# WEB SEARCH TOOLS
# ============================================================================

@tool()
def duckduckgo_search(query: str, max_results: int = 10):
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)
    
    Returns:
        list: Search results with title, snippet, URL
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "snippet": r.get("body"),
                    "url": r.get("href")
                })

        store_result("web-search", "duckduckgo", "PASS",
                    f"Found {len(results)} results for: {query[:50]}",
                    {"query": query, "results": len(results)})

        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "query": query}

@tool()
def web_scrape(url: str):
    """
    Scrape and extract text content from a web page.
    
    Args:
        url: Web page URL to scrape
    
    Returns:
        dict: Extracted text content
    """
    try:
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; MCP-Ecosystem/1.0)'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)

        return {
            "url": url,
            "content": text[:10000],  # Limit to 10k chars
            "length": len(text),
            "title": soup.title.string if soup.title else "No title"
        }
    except Exception as e:
        return {"error": str(e), "url": url}

# ============================================================================
# FILE & CONTENT TOOLS
# ============================================================================

@tool()
def fetch_url_content(url: str, format: str = "text"):
    """
    Fetch content from any URL.
    
    Args:
        url: URL to fetch
        format: Return format (text, json, raw)
    
    Returns:
        dict: Fetched content
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        if format == "json":
            content = response.json()
        elif format == "text":
            content = response.text
        else:
            content = response.content.decode('utf-8', errors='ignore')

        return {
            "url": url,
            "content": content,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type')
        }
    except Exception as e:
        return {"error": str(e), "url": url}

# ============================================================================
# MCP STORE INTEGRATION
# ============================================================================

def store_result(agent: str, service: str, status: str, summary: str, details: Dict[str, Any]):
    """Store result in MCP Store (fire-and-forget)"""
    try:
        requests.post(
            f"{MCPSTORE_URL}/v1/store/results",
            json={
                "agent": f"mcp-ecosystem-{agent}",
                "service": service,
                "status": status,
                "summary": summary,
                "details": details
            },
            timeout=5
        )
    except:
        pass  # Don't fail if store is unavailable

@tool()
def ecosystem_health():
    """
    Check health of all MCP ecosystem tools.
    
    Returns:
        dict: Status of all available tools
    """
    tools = {
        "youtube": "yt-dlp-transcript",
        "arxiv": "arxiv library",
        "wikipedia": "wikipedia library",
        "duckduckgo": "duckduckgo-search",
        "web_scrape": "beautifulsoup4",
        "fetch": "requests"
    }

    return {
        "status": "healthy",
        "tools_available": list(tools.keys()),
        "total_tools": len(tools),
        "mcp_store": MCPSTORE_URL
    }

# ============================================================================
# BATCH OPERATIONS
# ============================================================================

@tool()
def batch_youtube_transcripts(urls: str, language: str = "en"):
    """
    Fetch transcripts from multiple YouTube videos.
    
    Args:
        urls: Comma-separated list of YouTube URLs
        language: Subtitle language (default: en)
    
    Returns:
        list: Transcripts for all videos
    """
    url_list = [u.strip() for u in urls.split(",")]
    results = []

    for url in url_list:
        result = youtube_get_transcript(url, language)
        results.append(result)

    return {
        "results": results,
        "total": len(url_list),
        "successful": sum(1 for r in results if "transcript" in r)
    }

@tool()
def research_topic(topic: str, sources: str = "arxiv,wikipedia"):
    """
    Research a topic across multiple sources.
    
    Args:
        topic: Topic to research
        sources: Comma-separated sources (arxiv, wikipedia, web)
    
    Returns:
        dict: Combined research from all sources
    """
    source_list = [s.strip() for s in sources.split(",")]
    research = {}

    if "arxiv" in source_list:
        research["arxiv"] = arxiv_search(topic, max_results=3)

    if "wikipedia" in source_list:
        research["wikipedia"] = wikipedia_search(topic, sentences=5)

    if "web" in source_list:
        research["web"] = duckduckgo_search(topic, max_results=5)

    return {
        "topic": topic,
        "sources": research,
        "timestamp": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()
    }

if __name__ == "__main__":
    mcp.run()

