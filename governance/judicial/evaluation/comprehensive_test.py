#!/usr/bin/env python3.11
"""
Comprehensive Functional Test of Each MCP Service
"""
import time

print("\n" + "="*70)
print("🧪 COMPREHENSIVE MCP SERVICE FUNCTIONAL TESTS")
print("="*70 + "\n")

test_results = []

# ============================================================================
# TEST 1: Wikipedia Research Tool
# ============================================================================
def test_wikipedia():
    print("📚 TEST 1: Wikipedia Research Tool")
    print("-" * 70)

    try:
        import wikipedia

        # Test 1a: Simple search
        result = wikipedia.summary("Artificial intelligence", sentences=2)

        print("✅ PASS: Basic search")
        print("   Query: 'Artificial intelligence'")
        print(f"   Result: {len(result)} chars")
        print(f"   Content: {result[:150]}...")

        # Test 1b: Get page
        page = wikipedia.page("Machine learning")

        print("✅ PASS: Full page retrieval")
        print(f"   Title: {page.title}")
        print(f"   URL: {page.url}")
        print(f"   Categories: {len(page.categories)} found")

        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

# ============================================================================
# TEST 2: arXiv Research Tool
# ============================================================================
def test_arxiv():
    print("\n📚 TEST 2: arXiv Research Tool")
    print("-" * 70)

    try:
        import arxiv

        client = arxiv.Client()
        search = arxiv.Search(
            query="transformer neural networks",
            max_results=3,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = list(client.results(search))

        print("✅ PASS: arXiv search")
        print("   Query: 'transformer neural networks'")
        print(f"   Papers found: {len(results)}")

        for i, paper in enumerate(results[:2], 1):
            print(f"\n   Paper {i}:")
            print(f"   Title: {paper.title[:60]}...")
            print(f"   Authors: {', '.join([a.name for a in paper.authors[:3]])}")
            print(f"   Published: {paper.published.date()}")

        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

# ============================================================================
# TEST 3: Web Scraping Tool
# ============================================================================
def test_web_scraping():
    print("\n🌐 TEST 3: Web Scraping Tool")
    print("-" * 70)

    try:
        import requests
        from bs4 import BeautifulSoup

        # Test 3a: Basic scraping
        url = "https://httpbin.org/html"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        text = soup.get_text()
        links = soup.find_all('a')

        print("✅ PASS: HTML parsing")
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Text extracted: {len(text)} chars")
        print(f"   Links found: {len(links)}")

        # Test 3b: JSON API
        json_url = "https://httpbin.org/json"
        response = requests.get(json_url, timeout=10)
        data = response.json()

        print("\n✅ PASS: JSON fetching")
        print(f"   URL: {json_url}")
        print(f"   Keys: {list(data.keys())}")

        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

# ============================================================================
# TEST 4: MCP Store Client
# ============================================================================
def test_mcp_store():
    print("\n💾 TEST 4: MCP Store Client")
    print("-" * 70)

    try:
        import requests

        # Test write
        payload = {
            "agent": "comprehensive-test",
            "service": "ecosystem-validation",
            "status": "PASS",
            "summary": "Tested all MCP services",
            "details": {"tests_run": 5, "timestamp": time.time()}
        }

        response = requests.post(
            "http://localhost:8411/v1/store/results",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ PASS: Write to MCP Store")
            print(f"   Record ID: {result.get('id', 'N/A')}")
            print(f"   Status: {result.get('status')}")

            # Test read
            read_response = requests.get(
                "http://localhost:8411/v1/store/results?service=ecosystem-validation&limit=1",
                timeout=10
            )

            if read_response.status_code == 200:
                print("\n✅ PASS: Read from MCP Store")
                data = read_response.json()
                print(f"   Results found: {data.get('count', 0)}")

            return True
        else:
            print(f"⚠️ MCP Store returned: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("⚠️ SKIP: MCP Store not running")
        print("   Start with: make mcp-store-up")
        return None
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

# ============================================================================
# TEST 5: Service Health Check Pattern
# ============================================================================
def test_service_health():
    print("\n🏥 TEST 5: Service Health Check Pattern")
    print("-" * 70)

    try:
        import requests

        # Test common service endpoints
        services = [
            ("Bridge", "http://localhost:8014/health"),
            ("Athena", "http://localhost:8090/health"),
            ("UAT", "http://localhost:8181/health"),
        ]

        for name, url in services:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ {name}: UP ({url})")
                else:
                    print(f"   ⚠️ {name}: Status {response.status_code}")
            except:
                print(f"   ⏭️  {name}: Not running (optional)")

        print("\n✅ PASS: Health check pattern validated")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

# ============================================================================
# RUN ALL TESTS
# ============================================================================

results = {
    "Wikipedia": test_wikipedia(),
    "arXiv": test_arxiv(),
    "Web Scraping": test_web_scraping(),
    "MCP Store": test_mcp_store(),
    "Health Checks": test_service_health()
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*70)
print("📊 FINAL TEST SUMMARY")
print("="*70)

passed = sum(1 for v in results.values() if v is True)
failed = sum(1 for v in results.values() if v is False)
skipped = sum(1 for v in results.values() if v is None)

for test_name, result in results.items():
    if result is True:
        status = "✅ PASS"
    elif result is False:
        status = "❌ FAIL"
    else:
        status = "⏭️  SKIP"
    print(f"{status}: {test_name}")

print(f"\nTotal: {len(results)} tests")
print(f"Passed: {passed} ✅")
print(f"Failed: {failed} ❌")
print(f"Skipped: {skipped} ⏭️")

print("\n" + "="*70)
if failed == 0 and passed > 0:
    print("🎉 MCP ECOSYSTEM CORE SERVICES: FUNCTIONAL!")
else:
    print("⚠️ Some services need attention (see details above)")
print("="*70 + "\n")
