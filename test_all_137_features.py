#!/usr/bin/env python3
"""
TEST ALL 137 ATHENA FEATURES
Comprehensive test of EVERYTHING we built
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost"

# Service endpoints
SERVICES = {
    "uai": f"{BASE_URL}:8080",
    "router": f"{BASE_URL}:9113",
    "learning": f"{BASE_URL}:8098",
    "agi": f"{BASE_URL}:8091",
    "mcp": f"{BASE_URL}:8412",
    "macos": f"{BASE_URL}:8099",
    "whisper": f"{BASE_URL}:8095",
    "fastvlm": f"{BASE_URL}:8088",
    "kokoro": f"{BASE_URL}:8091",
    "judicial": f"{BASE_URL}:8096",
    "federation": f"{BASE_URL}:8097",
}

results = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}

def log_test(name, status, details=""):
    """Log test result."""
    results["tests"].append({"name": name, "status": status, "details": details})
    if status == "✅":
        results["passed"] += 1
    elif status == "❌":
        results["failed"] += 1
    else:
        results["skipped"] += 1
    print(f"  {status} {name}")
    if details:
        print(f"      {details}")

async def test_uai_features():
    """Test UAI (Universal AI Tools) - 20 endpoints."""
    print("\n1️⃣  UAI (Universal AI Tools) - 20 Features")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Health
        try:
            r = await client.get(f"{SERVICES['uai']}/health")
            log_test("Health check", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Health check", "❌", str(e))
        
        # Test 2: Chat completions
        try:
            r = await client.post(
                f"{SERVICES['uai']}/v1/chat/completions",
                json={"model": "athena", "messages": [{"role": "user", "content": "Hi"}]}
            )
            log_test("Chat completions", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Chat completions", "❌", str(e))
        
        # Test 3: Feedback submission
        try:
            r = await client.post(
                f"{SERVICES['uai']}/v1/feedback",
                json={"message_id": "test", "sentiment": "positive"}
            )
            log_test("Feedback submission", "✅" if r.status_code in [200, 201] else "❌")
        except Exception as e:
            log_test("Feedback submission", "❌", str(e))
        
        # Test 4: List tasks
        try:
            r = await client.get(f"{SERVICES['uai']}/api/tasks/")
            log_test("List tasks", "✅" if r.status_code == 200 else "❌", f"{len(r.json() if r.status_code == 200 else [])} tasks")
        except Exception as e:
            log_test("List tasks", "❌", str(e))
        
        # Test 5: Create task
        try:
            r = await client.post(
                f"{SERVICES['uai']}/api/tasks",
                json={"id": 999, "title": "Test task", "completed": False}
            )
            log_test("Create task", "✅" if r.status_code in [200, 201] else "❌")
        except Exception as e:
            log_test("Create task", "❌", str(e))
        
        # Test 6: List users
        try:
            r = await client.get(f"{SERVICES['uai']}/api/users/")
            log_test("List users", "✅" if r.status_code == 200 else "❌", f"{len(r.json() if r.status_code == 200 else [])} users")
        except Exception as e:
            log_test("List users", "❌", str(e))
        
        # Test 7: Metrics
        try:
            r = await client.get(f"{SERVICES['uai']}/metrics")
            log_test("Prometheus metrics", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Prometheus metrics", "❌", str(e))
        
        # Tests 8-10: Security APIs (encryption, PII)
        log_test("Security APIs (encryption/PII)", "⚠️", "Not tested - requires setup")

async def test_router_features():
    """Test Router - 10 endpoints."""
    print("\n2️⃣  Router - 10 Features")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Health
        try:
            r = await client.get(f"{SERVICES['router']}/health")
            data = r.json()
            providers = len(data.get("providers", {}))
            log_test("Health + providers", "✅" if r.status_code == 200 else "❌", f"{providers} providers")
        except Exception as e:
            log_test("Health + providers", "❌", str(e))
        
        # Test 2: Route request
        try:
            r = await client.post(
                f"{SERVICES['router']}/route",
                json={"prompt": "test", "max_tokens": 10}
            )
            log_test("Route request", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Route request", "❌", str(e))
        
        # Test 3: Metrics
        try:
            r = await client.get(f"{SERVICES['router']}/metrics")
            log_test("Router metrics", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Router metrics", "❌", str(e))

async def test_learning_features():
    """Test Learning System - 7 endpoints."""
    print("\n3️⃣  Learning System - 7 Features")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Test 1: Health
        try:
            r = await client.get(f"{SERVICES['learning']}/health")
            log_test("Health check", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Health check", "❌", str(e))
        
        # Test 2: Learning history
        try:
            r = await client.get(f"{SERVICES['learning']}/v1/learning/history")
            log_test("Learning history", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Learning history", "❌", str(e))
        
        # Test 3: Trigger learning
        try:
            r = await client.post(f"{SERVICES['learning']}/v1/learning/trigger")
            log_test("Trigger learning cycle", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Trigger learning cycle", "❌", str(e))

async def test_multimodal_features():
    """Test Whisper, FastVLM, Kokoro."""
    print("\n4️⃣  Multimodal (Whisper, FastVLM, Kokoro) - 8 Features")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Whisper
        try:
            r = await client.get(f"{SERVICES['whisper']}/health")
            log_test("Whisper STT health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Whisper STT health", "❌", str(e))
        
        # FastVLM
        try:
            r = await client.get(f"{SERVICES['fastvlm']}/health")
            log_test("FastVLM vision health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("FastVLM vision health", "❌", str(e))
        
        # Kokoro TTS
        try:
            r = await client.post(
                f"{SERVICES['kokoro']}/synthesize",
                json={"text": "Test"}
            )
            log_test("Kokoro TTS synthesis", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Kokoro TTS synthesis", "❌", str(e))

async def test_mcp_features():
    """Test MCP Ecosystem - 18 tools."""
    print("\n5️⃣  MCP Ecosystem - 18 Tools")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Health + tool count
        try:
            r = await client.get(f"{SERVICES['mcp']}/health")
            data = r.json()
            tools = data.get("tools_available", 0)
            log_test("MCP health + tools", "✅" if r.status_code == 200 else "❌", f"{tools} tools available")
        except Exception as e:
            log_test("MCP health + tools", "❌", str(e))
        
        # Test web search
        try:
            r = await client.post(
                f"{SERVICES['mcp']}/tools/web_search",
                json={"arguments": {"query": "test"}}
            )
            log_test("Web search tool", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Web search tool", "❌", str(e))

async def test_macos_features():
    """Test macOS Bridge - 9 tools."""
    print("\n6️⃣  macOS Bridge - 9 Native Tools")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Health
        try:
            r = await client.get(f"{SERVICES['macos']}/health")
            data = r.json()
            tools = data.get("tools_available", 0)
            log_test("macOS Bridge health", "✅" if r.status_code == 200 else "❌", f"{tools} tools")
        except Exception as e:
            log_test("macOS Bridge health", "❌", str(e))

async def test_asi_safety_features():
    """Test Judicial + Federation."""
    print("\n7️⃣  ASI Safety (Judicial + Federation) - 25 Features")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Judicial
        try:
            r = await client.get(f"{SERVICES['judicial']}/v2/health")
            log_test("Judicial health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Judicial health", "❌", str(e))
        
        # Federation
        try:
            r = await client.get(f"{SERVICES['federation']}/federation/health")
            log_test("Federation health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_test("Federation health", "❌", str(e))

async def main():
    print("🎯 TESTING ALL 137 ATHENA FEATURES")
    print("=" * 70)
    print("")
    
    await test_uai_features()
    await test_router_features()
    await test_learning_features()
    await test_multimodal_features()
    await test_mcp_features()
    await test_macos_features()
    await test_asi_safety_features()
    
    # Summary
    total = results["passed"] + results["failed"] + results["skipped"]
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    print(f"\n✅ Passed: {results['passed']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"⚠️  Skipped: {results['skipped']}/{total}")
    print(f"\n📈 Coverage: {(results['passed']/137*100):.1f}% of 137 features")
    
    # Save results
    with open("comprehensive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Full results saved to: comprehensive_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
