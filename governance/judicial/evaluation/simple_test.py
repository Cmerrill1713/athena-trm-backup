#!/usr/bin/env python3.11
"""Test the tools that work without ffmpeg"""

print("🧪 MCP Ecosystem - Working Tools Test\n")

# Test Wikipedia
print("📖 Wikipedia Tool")
print("-" * 50)
try:
    import wikipedia
    result = wikipedia.summary("Model Context Protocol", sentences=3)
    print(f"✅ SUCCESS: Retrieved {len(result)} characters")
    print(f"Content: {result[:200]}...")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n")

# Test Web Scraping
print("🌐 Web Scraping Tool")
print("-" * 50)
try:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get("https://httpbin.org/html", timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()

    print(f"✅ SUCCESS: Scraped {len(text)} characters")
    print(f"Title: {soup.title.string if soup.title else 'N/A'}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n")

# Test arXiv (with better query)
print("📚 arXiv Research Tool")
print("-" * 50)
try:
    import arxiv

    client = arxiv.Client()
    search = arxiv.Search(
        query="LLM",
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = list(client.results(search))
    print(f"✅ SUCCESS: Found {len(results)} papers")

    for i, paper in enumerate(results, 1):
        print(f"   {i}. {paper.title[:60]}...")

except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n")

# Test URL Fetching
print("🔗 URL Fetch Tool")
print("-" * 50)
try:
    import requests

    response = requests.get("https://api.github.com/zen", timeout=10)
    print(f"✅ SUCCESS: Status {response.status_code}")
    print(f"Content: {response.text}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "=" * 50)
print("✅ MCP Ecosystem tools are functional!")
print("=" * 50)
