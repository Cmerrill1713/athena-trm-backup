#!/usr/bin/env python3
"""
Athena MCP Server
=================

Model Context Protocol server for Cursor IDE integration.
Provides AI-powered tools for SwiftUI development, code analysis, and Athena system management.

Features:
- SwiftUI NavigationStack generation
- ViewModel pattern creation
- Async/await refactoring
- Code analysis and suggestions
- Athena system diagnostics
- Website crawling for Swift resources
"""

import asyncio
import sys
import json
import aiohttp
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    import uvicorn
except ImportError:
    print("Dependencies not installed. Install with: pip install fastapi uvicorn aiohttp beautifulsoup4")
    sys.exit(1)


@dataclass
class AthenaMCPServer:
    """MCP Server for Athena/Cursor integration"""

    def __init__(self):
        self.app = FastAPI(title="Athena MCP Server", version="1.0.0")

        self._setup_routes()

    def _setup_routes(self):
        """Set up FastAPI routes for HTTP transport"""

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "server": "athena-mcp"}

        @self.app.post("/crawl")
        async def crawl_website(request: Dict[str, Any]):
            """Crawl a website and return structured content"""
            url = request.get("url")
            max_pages = request.get("max_pages", 10)
            include_patterns = request.get("include_patterns", [])
            exclude_patterns = request.get("exclude_patterns", [])

            if not url:
                return {"error": "URL is required"}

            try:
                crawled_data = await crawl_website_async(url, max_pages, include_patterns, exclude_patterns)

                # Format the crawled data for Swift development context
                result = {
                    "source": url,
                    "pages_crawled": len(crawled_data),
                    "total_content_length": sum(len(content) for content in crawled_data.values()),
                    "content": {}
                }

                # Add content from each page
                for page_url, content in crawled_data.items():
                    # Extract code examples and Swift-related content
                    swift_content = _extract_swift_content(content)
                    if swift_content:
                        result["content"][page_url] = swift_content

                return result

            except Exception as e:
                return {"error": f"Error crawling website: {str(e)}"}


async def crawl_website_async(url: str, max_pages: int = 10,
                             include_patterns: List[str] = None,
                             exclude_patterns: List[str] = None) -> Dict[str, str]:
    """Crawl website and return content"""
    if include_patterns is None:
        include_patterns = []
    if exclude_patterns is None:
        exclude_patterns = []

    async with aiohttp.ClientSession() as session:
        return await _crawl_recursive_static(
            session, url, max_pages, set(), include_patterns, exclude_patterns
        )


async def _crawl_recursive_static(session, url: str, max_pages: int, visited: set,
                                 include_patterns: List[str], exclude_patterns: List[str]) -> Dict[str, str]:
        """Recursively crawl website pages"""
        if len(visited) >= max_pages or url in visited:
            return {}

        # Check include/exclude patterns
        if not _should_crawl_url(url, include_patterns, exclude_patterns):
            return {}

        visited.add(url)

        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract text content
                content = _extract_page_content(soup)

                # Find links for recursive crawling
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if _is_same_domain(url, full_url) and full_url not in visited:
                        links.append(full_url)

                # Crawl linked pages
                result = {url: content}
                for link in links[:3]:  # Limit recursive crawling
                    sub_results = await _crawl_recursive_static(
                        session, link, max_pages - len(visited), visited,
                        include_patterns, exclude_patterns
                    )
                    result.update(sub_results)

                return result

        except Exception as e:
            return {url: f"Error: {str(e)}"}

def _should_crawl_url(url: str, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
        """Check if URL should be crawled based on patterns"""
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return False

        # If no include patterns, allow everything
        if not include_patterns:
            return True

        # Check include patterns
        for pattern in include_patterns:
            if re.search(pattern, url):
                return True

        return False

def _is_same_domain(url1: str, url2: str) -> bool:
        """Check if URLs are on the same domain"""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False

def _extract_page_content(soup: BeautifulSoup) -> str:
        """Extract readable content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:2000]  # Limit content length

def _extract_swift_content(content: str) -> str:
        """Extract Swift-related content from page"""
        # Look for Swift code patterns, imports, or keywords
        swift_patterns = [
            r'import\s+SwiftUI',
            r'@State\b',
            r'@Published\b',
            r'struct\s+\w+:\s*View',
            r'func\s+\w+\([^)]*\)\s*->\s*some\s+View',
            r'NavigationStack',
            r'async\s+let',
            r'await\s+\w+',
        ]

        lines = content.split('\n')
        swift_lines = []

        for line in lines:
            for pattern in swift_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    swift_lines.append(line)
                    break

        return '\n'.join(swift_lines) if swift_lines else ""



async def crawl_website_async(url: str, max_pages: int = 10,
                             include_patterns: List[str] = None,
                             exclude_patterns: List[str] = None) -> Dict[str, str]:
    """Crawl website and return content"""
    if include_patterns is None:
        include_patterns = []
    if exclude_patterns is None:
        exclude_patterns = []

    async with aiohttp.ClientSession() as session:
        return await _crawl_recursive_static(
            session, url, max_pages, set(), include_patterns, exclude_patterns
        )


async def _crawl_recursive_static(session, url: str, max_pages: int, visited: set,
                                 include_patterns: List[str], exclude_patterns: List[str]) -> Dict[str, str]:
        """Recursively crawl website pages"""
        if len(visited) >= max_pages or url in visited:
            return {}

        # Check include/exclude patterns
        if not _should_crawl_url(url, include_patterns, exclude_patterns):
            return {}

        visited.add(url)

        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract text content
                content = _extract_page_content(soup)

                # Find links for recursive crawling
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if _is_same_domain(url, full_url) and full_url not in visited:
                        links.append(full_url)

                # Crawl linked pages
                result = {url: content}
                for link in links[:3]:  # Limit recursive crawling
                    sub_results = await _crawl_recursive_static(
                        session, link, max_pages - len(visited), visited,
                        include_patterns, exclude_patterns
                    )
                    result.update(sub_results)

                return result

        except Exception as e:
            return {url: f"Error: {str(e)}"}

def _should_crawl_url(url: str, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
        """Check if URL should be crawled based on patterns"""
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return False

        # If no include patterns, allow everything
        if not include_patterns:
            return True

        # Check include patterns
        for pattern in include_patterns:
            if re.search(pattern, url):
                return True

        return False

def _is_same_domain(url1: str, url2: str) -> bool:
        """Check if URLs are on the same domain"""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False

def _extract_page_content(soup: BeautifulSoup) -> str:
        """Extract readable content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:2000]  # Limit content length

def _extract_swift_content(content: str) -> str:
        """Extract Swift-related content from page"""
        # Look for Swift code patterns, imports, or keywords
        swift_patterns = [
            r'import\s+SwiftUI',
            r'@State\b',
            r'@Published\b',
            r'struct\s+\w+:\s*View',
            r'func\s+\w+\([^)]*\)\s*->\s*some\s+View',
            r'NavigationStack',
            r'async\s+let',
            r'await\s+\w+',
        ]

        lines = content.split('\n')
        swift_lines = []

        for line in lines:
            for pattern in swift_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    swift_lines.append(line)
                    break

        return '\n'.join(swift_lines) if swift_lines else ""

        def run_http(self, host: str = "0.0.0.0", port: int = 3333):
        """Run MCP server with HTTP transport"""
        uvicorn.run(self.app, host=host, port=port)

