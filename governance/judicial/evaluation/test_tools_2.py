#!/usr/bin/env python3.11
"""Quick test of MCP ecosystem tools"""

print("🧪 Testing MCP Ecosystem Tools\n")

# Test 1: YouTube (yt-dlp-transcript)
print("1️⃣ Testing YouTube transcript...")
try:
    from yt_dlp_transcript import yt_dlp_transcript
    # Test with a known video (Rick Astley - Never Gonna Give You Up)
    result = yt_dlp_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ", language="en")
    print(f"   ✅ YouTube transcript: {len(result)} characters")
    print(f"   Preview: {result[:100]}...")
except Exception as e:
    print(f"   ❌ YouTube failed: {e}")

print()

# Test 2: arXiv search
print("2️⃣ Testing arXiv search...")
try:
    import arxiv
    search = arxiv.Search(query="machine learning", max_results=2)
    results = list(search.results())
    print(f"   ✅ arXiv search: Found {len(results)} papers")
    if results:
        print(f"   First paper: {results[0].title[:60]}...")
except Exception as e:
    print(f"   ❌ arXiv failed: {e}")

print()

# Test 3: Wikipedia
print("3️⃣ Testing Wikipedia...")
try:
    import wikipedia
    summary = wikipedia.summary("Artificial Intelligence", sentences=2)
    print(f"   ✅ Wikipedia: {len(summary)} characters")
    print(f"   Preview: {summary[:100]}...")
except Exception as e:
    print(f"   ❌ Wikipedia failed: {e}")

print()

# Test 4: Web Search
print("4️⃣ Testing DuckDuckGo search...")
try:
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text("MCP protocol", max_results=2))
    print(f"   ✅ DuckDuckGo: Found {len(results)} results")
    if results:
        print(f"   First result: {results[0].get('title', '')[:60]}...")
except Exception as e:
    print(f"   ❌ DuckDuckGo failed: {e}")

print()

# Test 5: Web Scraping
print("5️⃣ Testing web scraping...")
try:
    import requests
    from bs4 import BeautifulSoup
    response = requests.get("https://example.com", timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    print(f"   ✅ Web scraping: {len(text)} characters from example.com")
except Exception as e:
    print(f"   ❌ Web scraping failed: {e}")

print()
print("=" * 50)
print("🎉 Core tool testing complete!")
print("=" * 50)
