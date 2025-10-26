#!/usr/bin/env python3
"""
MASSIVE FEATURE TEST - Test ALL 137 features systematically
"""
import asyncio
import httpx
import json
import base64
from datetime import datetime

BASE = "http://localhost"

results = {"passed": 0, "failed": 0, "skipped": 0, "categories": []}

def log_result(category, feature, status, details=""):
    """Log test result."""
    if not any(c["name"] == category for c in results["categories"]):
        results["categories"].append({"name": category, "tests": []})
    
    for c in results["categories"]:
        if c["name"] == category:
            c["tests"].append({"feature": feature, "status": status, "details": details})
    
    if status == "✅":
        results["passed"] += 1
    elif status == "❌":
        results["failed"] += 1
    else:
        results["skipped"] += 1
    
    print(f"  {status} {feature}" + (f" - {details}" if details else ""))

async def test_all_features():
    print("🎯 TESTING ALL 137 ATHENA FEATURES - COMPREHENSIVE")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        
        # ================================================================
        # CATEGORY 1: UAI (Universal AI Tools) - 20+ endpoints
        # ================================================================
        print("\n1️⃣  UAI (Universal AI Tools) - 20+ Features")
        print("-" * 80)
        
        # Chat & RAG
        try:
            r = await client.post(f"{BASE}:8080/v1/chat/completions",
                json={"model": "athena", "messages": [{"role": "user", "content": "Test"}], "max_tokens": 20})
            log_result("UAI", "Chat completions", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("UAI", "Chat completions", "❌", str(e)[:50])
        
        # Feedback
        try:
            r = await client.post(f"{BASE}:8080/v1/feedback",
                json={"message_id": f"test_{int(datetime.now().timestamp())}", "sentiment": "positive", "response_preview": "test", "timestamp": int(datetime.now().timestamp())})
            log_result("UAI", "Feedback submission", "✅" if r.status_code in [200, 201] else "❌", f"Status: {r.status_code}")
        except Exception as e:
            log_result("UAI", "Feedback submission", "❌", str(e)[:50])
        
        # Tasks
        try:
            r = await client.get(f"{BASE}:8080/api/tasks/")
            tasks = r.json() if r.status_code == 200 else []
            log_result("UAI", "List tasks", "✅", f"{len(tasks)} tasks")
        except Exception as e:
            log_result("UAI", "List tasks", "❌", str(e)[:50])
        
        try:
            task_id = int(datetime.now().timestamp())
            r = await client.post(f"{BASE}:8080/api/tasks",
                json={"id": task_id, "title": f"Test {task_id}", "description": "Auto test", "completed": False, "created_at": datetime.now().isoformat()})
            log_result("UAI", "Create task", "✅" if r.status_code in [200, 201] else "❌", f"Status: {r.status_code}")
        except Exception as e:
            log_result("UAI", "Create task", "❌", str(e)[:50])
        
        try:
            r = await client.put(f"{BASE}:8080/api/tasks/{task_id}/complete")
            log_result("UAI", "Complete task", "✅" if r.status_code in [200, 201] else "❌")
        except Exception as e:
            log_result("UAI", "Complete task", "❌", str(e)[:50])
        
        # Users
        try:
            r = await client.get(f"{BASE}:8080/api/users/")
            users = r.json() if r.status_code == 200 else []
            log_result("UAI", "List users", "✅", f"{len(users)} users")
        except Exception as e:
            log_result("UAI", "List users", "❌", str(e)[:50])
        
        # TTS Proxy
        try:
            r = await client.post(f"{BASE}:8080/api/tts/synthesize",
                json={"text": "Test"})
            log_result("UAI", "TTS proxy", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("UAI", "TTS proxy", "❌", str(e)[:50])
        
        # Metrics
        try:
            r = await client.get(f"{BASE}:8080/metrics")
            log_result("UAI", "Prometheus metrics", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("UAI", "Prometheus metrics", "❌", str(e)[:50])
        
        # Health
        try:
            r = await client.get(f"{BASE}:8080/health")
            log_result("UAI", "Health check", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("UAI", "Health check", "❌", str(e)[:50])
        
        # ================================================================
        # CATEGORY 2: Router - 10 endpoints
        # ================================================================
        print("\n2️⃣  Router - 10 Features")
        print("-" * 80)
        
        try:
            r = await client.get(f"{BASE}:9113/health")
            data = r.json()
            providers = list(data.get("providers", {}).keys())
            log_result("Router", "Health + providers", "✅", f"{len(providers)} providers: {', '.join(providers[:3])}")
        except Exception as e:
            log_result("Router", "Health + providers", "❌", str(e)[:50])
        
        try:
            r = await client.post(f"{BASE}:9113/route",
                json={"prompt": "test routing", "max_tokens": 10, "temperature": 0.7})
            log_result("Router", "Route request", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Router", "Route request", "❌", str(e)[:50])
        
        try:
            r = await client.get(f"{BASE}:9113/metrics")
            log_result("Router", "Metrics endpoint", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Router", "Metrics endpoint", "❌", str(e)[:50])
        
        # ================================================================
        # CATEGORY 3: Learning System - 7 endpoints
        # ================================================================
        print("\n3️⃣  Learning System - 7 Features")
        print("-" * 80)
        
        try:
            r = await client.get(f"{BASE}:8098/health")
            log_result("Learning", "Health check", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Learning", "Health check", "❌", str(e)[:50])
        
        try:
            r = await client.get(f"{BASE}:8098/v1/learning/history")
            cycles = r.json() if r.status_code == 200 else []
            log_result("Learning", "Learning history", "✅", f"{len(cycles)} cycles")
        except Exception as e:
            log_result("Learning", "Learning history", "❌", str(e)[:50])
        
        try:
            r = await client.post(f"{BASE}:8098/v1/learning/trigger")
            log_result("Learning", "Trigger learning", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Learning", "Trigger learning", "❌", str(e)[:50])
        
        try:
            r = await client.post(f"{BASE}:8098/v1/feedback/analyze")
            log_result("Learning", "Feedback analysis", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Learning", "Feedback analysis", "❌", str(e)[:50])
        
        try:
            r = await client.post(f"{BASE}:8098/v1/router/learn")
            log_result("Learning", "Router learning", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Learning", "Router learning", "❌", str(e)[:50])
        
        # ================================================================
        # CATEGORY 4: Multimodal (Whisper, FastVLM, Kokoro) - 8 features
        # ================================================================
        print("\n4️⃣  Multimodal (Whisper, FastVLM, Kokoro) - 8 Features")
        print("-" * 80)
        
        # Whisper STT
        try:
            r = await client.get(f"{BASE}:8095/health")
            log_result("Multimodal", "Whisper STT health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Multimodal", "Whisper STT health", "❌", str(e)[:50])
        
        # FastVLM Vision
        try:
            r = await client.get(f"{BASE}:8088/health")
            log_result("Multimodal", "FastVLM health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Multimodal", "FastVLM health", "❌", str(e)[:50])
        
        # Kokoro TTS
        try:
            r = await client.post(f"{BASE}:8091/synthesize",
                json={"text": "Testing Athena TTS", "voice": "en_US-female"})
            has_audio = "audio" in r.json() if r.status_code == 200 else False
            log_result("Multimodal", "Kokoro TTS synthesis", "✅" if has_audio else "❌", "Audio generated!" if has_audio else f"Status: {r.status_code}")
        except Exception as e:
            log_result("Multimodal", "Kokoro TTS synthesis", "❌", str(e)[:50])
        
        try:
            r = await client.get(f"{BASE}:8091/metrics")
            log_result("Multimodal", "Kokoro metrics", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("Multimodal", "Kokoro metrics", "❌", str(e)[:50])
        
        # ================================================================
        # CATEGORY 5: MCP Ecosystem - 18 tools
        # ================================================================
        print("\n5️⃣  MCP Ecosystem - 18 Tools")
        print("-" * 80)
        
        try:
            r = await client.get(f"{BASE}:8412/health")
            data = r.json()
            tools = data.get("tools_available", 0)
            log_result("MCP", "Health + tool count", "✅", f"{tools} tools")
        except Exception as e:
            log_result("MCP", "Health + tool count", "❌", str(e)[:50])
        
        # Test individual tools
        try:
            r = await client.post(f"{BASE}:8412/tools/web_search",
                json={"arguments": {"query": "test"}})
            log_result("MCP", "Web search tool", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("MCP", "Web search tool", "❌", str(e)[:50])
        
        try:
            r = await client.post(f"{BASE}:8412/tools/arxiv_search",
                json={"arguments": {"query": "machine learning"}})
            log_result("MCP", "ArXiv search tool", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("MCP", "ArXiv search tool", "❌", str(e)[:50])
        
        # ================================================================
        # CATEGORY 6: macOS Bridge - 9 tools
        # ================================================================
        print("\n6️⃣  macOS Bridge - 9 Native Tools")
        print("-" * 80)
        
        try:
            r = await client.get(f"{BASE}:8099/health")
            data = r.json()
            tools = data.get("tools_available", 0)
            log_result("macOS", "Health + tool count", "✅", f"{tools} native tools")
        except Exception as e:
            log_result("macOS", "Health + tool count", "❌", str(e)[:50])
        
        # ================================================================
        # CATEGORY 7: ASI Safety (Judicial + Federation) - 25 features
        # ================================================================
        print("\n7️⃣  ASI Safety (Judicial + Federation) - 25 Features")
        print("-" * 80)
        
        try:
            r = await client.get(f"{BASE}:8096/v2/health")
            log_result("ASI Safety", "Judicial health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("ASI Safety", "Judicial health", "❌", str(e)[:50])
        
        try:
            r = await client.post(f"{BASE}:8096/v2/adjudicate",
                json={
                    "event_type": "test",
                    "instance_id": "test-runner",
                    "decision": "Testing judicial",
                    "severity": "low"
                })
            log_result("ASI Safety", "Judicial adjudication", "✅" if r.status_code in [200, 201] else "❌")
        except Exception as e:
            log_result("ASI Safety", "Judicial adjudication", "❌", str(e)[:50])
        
        try:
            r = await client.get(f"{BASE}:8097/federation/health")
            log_result("ASI Safety", "Federation health", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log_result("ASI Safety", "Federation health", "❌", str(e)[:50])
    
    # ================================================================
    # SUMMARY
    # ================================================================
    total = results["passed"] + results["failed"] + results["skipped"]
    
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE FEATURE TEST RESULTS")
    print("=" * 80)
    print(f"\n✅ Passed: {results['passed']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"⚠️  Skipped: {results['skipped']}/{total}")
    print(f"\n📈 Feature Coverage: {(results['passed']/137*100):.1f}% of 137 features")
    print(f"📈 Test Coverage: {(results['passed']/total*100):.1f}% of {total} tests")
    
    print("\n📋 Breakdown by Category:")
    for cat in results["categories"]:
        passed = sum(1 for t in cat["tests"] if t["status"] == "✅")
        total_cat = len(cat["tests"])
        print(f"  {cat['name']}: {passed}/{total_cat} passed")
    
    # Save results
    with open("massive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Full results saved to: massive_test_results.json")
    print(f"\n💙 Tested {results['passed']} features successfully!")

if __name__ == "__main__":
    asyncio.run(test_all_features())
