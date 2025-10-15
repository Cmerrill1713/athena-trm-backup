#!/usr/bin/env python3
"""
Web Tools MCP Server (FastMCP)
Provides web search, scraping, and content fetching
"""
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("web")

@tool()
def search_duckduckgo(query: str, max_results: int = 10):
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum results (default: 10)
    
    Returns:
        list: Search results with title, snippet, URL
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "snippet": r.get("body"),
                    "url": r.get("href"),
                    "source": "duckduckgo"
                })

        return {
            "status": "success",
            "results": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "query": query}

@tool()
def scrape_webpage(url: str, extract: str = "text"):
    """
    Scrape content from a web page.
    
    Args:
        url: Web page URL
        extract: What to extract (text, links, images, all)
    
    Returns:
        dict: Extracted content
    """
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; MCP-Ecosystem/1.0)'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        result = {"status": "success", "url": url}

        if extract in ["text", "all"]:
            # Remove script and style
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)

            result["text"] = text[:20000]  # Limit to 20k chars
            result["length"] = len(text)

        if extract in ["links", "all"]:
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            result["links"] = links[:100]

        if extract in ["images", "all"]:
            images = [img.get('src') for img in soup.find_all('img', src=True)]
            result["images"] = images[:50]

        result["title"] = soup.title.string if soup.title else "No title"

        return result
    except Exception as e:
        return {"status": "error", "error": str(e), "url": url}

@tool()
def fetch_url(url: str, format: str = "text"):
    """
    Fetch content from any URL.
    
    Args:
        url: URL to fetch
        format: Return format (text, json, html)
    
    Returns:
        dict: Fetched content
    """
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; MCP-Ecosystem/1.0)'
        })
        response.raise_for_status()

        if format == "json":
            content = response.json()
        elif format == "html":
            content = response.text
        else:  # text
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.get_text()

        return {
            "status": "success",
            "url": url,
            "content": content[:20000] if isinstance(content, str) else content,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type')
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "url": url}

@tool()
def search_news(query: str, max_results: int = 10):
    """
    Search for news articles.
    
    Args:
        query: Search query
        max_results: Maximum results (default: 10)
    
    Returns:
        list: News articles with title, snippet, URL
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "body": r.get("body"),
                    "url": r.get("url"),
                    "source": r.get("source"),
                    "date": r.get("date")
                })

        return {
            "status": "success",
            "results": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "query": query}

if __name__ == "__main__":
    mcp.run()

