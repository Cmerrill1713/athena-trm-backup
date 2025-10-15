#!/usr/bin/env python3
"""
Research MCP Server (FastMCP)
Provides academic research tools: arXiv, Wikipedia
"""
import arxiv
import wikipedia
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("research")

@tool()
def search_arxiv(query: str, max_results: int = 5):
    """
    Search arXiv for research papers.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 5)
    
    Returns:
        list: Research papers with title, authors, summary, PDF URL
    """
    try:
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
                "entry_id": result.entry_id,
                "categories": result.categories
            })

        return {
            "status": "success",
            "papers": papers,
            "count": len(papers),
            "query": query
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "query": query}

@tool()
def search_wikipedia(query: str, sentences: int = 3):
    """
    Search Wikipedia and get summary.
    
    Args:
        query: Search query
        sentences: Number of sentences in summary (default: 3)
    
    Returns:
        dict: Wikipedia article summary, URL, and related info
    """
    try:
        # Search for pages
        pages = wikipedia.search(query, results=5)
        if not pages:
            return {"status": "error", "error": "No results found", "query": query}

        # Get first result
        page = wikipedia.page(pages[0], auto_suggest=False)
        summary = wikipedia.summary(pages[0], sentences=sentences, auto_suggest=False)

        return {
            "status": "success",
            "title": page.title,
            "summary": summary,
            "url": page.url,
            "categories": page.categories[:10] if hasattr(page, 'categories') else [],
            "links": page.links[:10] if hasattr(page, 'links') else [],
            "related_pages": pages[1:5]
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "status": "disambiguation",
            "options": e.options[:10],
            "query": query
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "query": query}

@tool()
def get_wikipedia_full_article(title: str):
    """
    Get full Wikipedia article content.
    
    Args:
        title: Exact Wikipedia article title
    
    Returns:
        dict: Full article content
    """
    try:
        page = wikipedia.page(title, auto_suggest=False)

        return {
            "status": "success",
            "title": page.title,
            "content": page.content,
            "url": page.url,
            "categories": page.categories if hasattr(page, 'categories') else [],
            "sections": page.sections if hasattr(page, 'sections') else []
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "title": title}

@tool()
def research_topic(topic: str, include_arxiv: bool = True, include_wikipedia: bool = True):
    """
    Comprehensive research on a topic using multiple sources.
    
    Args:
        topic: Topic to research
        include_arxiv: Include arXiv papers (default: True)
        include_wikipedia: Include Wikipedia (default: True)
    
    Returns:
        dict: Combined research from all sources
    """
    results = {"topic": topic, "sources": {}}

    if include_arxiv:
        results["sources"]["arxiv"] = search_arxiv(topic, max_results=3)

    if include_wikipedia:
        results["sources"]["wikipedia"] = search_wikipedia(topic, sentences=5)

    return results

if __name__ == "__main__":
    mcp.run()

