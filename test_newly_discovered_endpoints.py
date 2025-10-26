#!/usr/bin/env python3
"""
TEST NEWLY DISCOVERED ENDPOINTS
Found in OpenAPI specs that we haven't tested yet
"""
import asyncio
import httpx
import json

BASE = "http://localhost"
results = {"passed": 0, "failed": 0, "new_working": []}

def log(name, status, detail=""):
    if status == "✅": 
        results["passed"] += 1
        results["new_working"].append(name)
    else: 
        results["failed"] += 1
    print(f"  {status} {name}" + (f" - {detail}" if detail else ""))

async def test_new_endpoints():
    print("🆕 TESTING NEWLY DISCOVERED ENDPOINTS")
    print("Found in OpenAPI specs we haven't tested")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        
        # ================================================================
        # UAI - New Endpoints (3 untested)
        # ================================================================
        print("\n💬 UAI - 3 New Endpoints")
        print("-"*80)
        
        try:
            r = await client.post(f"{BASE}:8080/api/tts/speak",
                json={"text": "Test", "voice": "en_US-female"})
            log("TTS Speak endpoint", "✅" if r.status_code == 200 else "❌", f"{r.status_code}")
        except Exception as e:
            log("TTS Speak endpoint", "❌", str(e)[:30])
        
        try:
            r = await client.get(f"{BASE}:8080/api/tts/voices")
            voices = r.json() if r.status_code == 200 else []
            log("TTS Voices list", "✅" if r.status_code == 200 else "❌", f"{len(voices) if isinstance(voices, list) else 0} voices")
        except Exception as e:
            log("TTS Voices list", "❌", str(e)[:30])
        
        try:
            r = await client.get(f"{BASE}:8080/v1/feedback/stats")
            log("Feedback Stats", "✅" if r.status_code == 200 else "❌")
        except Exception as e:
            log("Feedback Stats", "❌", str(e)[:30])
        
        # ================================================================
        # Router - New Endpoints (5 untested)
        # ================================================================
        print("\n🔀 ROUTER - 5 New Endpoints")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9113/canary")
            log("Canary status", "✅" if r.status_code == 200 else "❌")
        except: log("Canary status", "❌")
        
        try:
            r = await client.get(f"{BASE}:9113/ready")
            log("Readiness check", "✅" if r.status_code == 200 else "❌")
        except: log("Readiness check", "❌")
        
        try:
            r = await client.post(f"{BASE}:9113/reload-policy")
            log("Reload policy", "✅" if r.status_code == 200 else "❌")
        except: log("Reload policy", "❌")
        
        try:
            r = await client.get(f"{BASE}:9113/version")
            version = r.json() if r.status_code == 200 else {}
            log("Version info", "✅" if r.status_code == 200 else "❌", str(version.get("version", ""))[:20])
        except: log("Version info", "❌")
        
        try:
            r = await client.post(f"{BASE}:9113/vision/analyze",
                json={"image": "test", "prompt": "test"})
            log("Vision proxy (Router)", "✅" if r.status_code == 200 else "❌")
        except: log("Vision proxy (Router)", "❌")
        
        # ================================================================
        # Federation - Advanced Features (15+ untested)
        # ================================================================
        print("\n⚖️ FEDERATION - 15+ Advanced Endpoints")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:8097/federation/disputes")
            log("List disputes", "✅" if r.status_code == 200 else "❌")
        except: log("List disputes", "❌")
        
        try:
            r = await client.get(f"{BASE}:8097/federation/onboard/challenges")
            log("Onboard challenges", "✅" if r.status_code == 200 else "❌")
        except: log("Onboard challenges", "❌")
        
        try:
            r = await client.get(f"{BASE}:8097/federation/evidence/query")
            log("Evidence query", "✅" if r.status_code == 200 else "❌")
        except: log("Evidence query", "❌")
        
        try:
            r = await client.post(f"{BASE}:8097/federation/onboard/initiate",
                json={"sovereign_id": "test", "capabilities": []})
            log("Initiate onboarding", "✅" if r.status_code in [200, 201] else "❌")
        except: log("Initiate onboarding", "❌")
        
        try:
            r = await client.post(f"{BASE}:8097/federation/evidence/prepare",
                json={"type": "test", "data": {}})
            log("Prepare evidence", "✅" if r.status_code in [200, 201] else "❌")
        except: log("Prepare evidence", "❌")
        
        # ================================================================
        # Judicial - New Endpoint Format
        # ================================================================
        print("\n⚖️ JUDICIAL - Testing Correct Endpoint")
        print("-"*80)
        
        try:
            r = await client.post(f"{BASE}:8096/v2/judicial/adjudicate",
                json={
                    "event_type": "test",
                    "instance_id": "test",
                    "decision": {},
                    "severity": "low"
                })
            log("Judicial adjudicate (correct path)", "✅" if r.status_code in [200, 201] else "❌", f"{r.status_code}")
        except Exception as e:
            log("Judicial adjudicate (correct path)", "❌", str(e)[:30])
        
        # ================================================================
        # MCP - Check /tools endpoint for more
        # ================================================================
        print("\n🔧 MCP - Detailed Tool Analysis")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:8412/tools")
            if r.status_code == 200:
                data = r.json()
                tools = data.get("tools", {})
                log("Tool inventory", "✅", f"{len(tools)} tools")
                
                # List all tool names
                print(f"\n     Available Tools:")
                for i, tool_name in enumerate(list(tools.keys())[:15], 1):
                    print(f"       {i}. {tool_name}")
        except: log("Tool inventory", "❌")
    
    # ================================================================
    # SUMMARY
    # ================================================================
    total = results["passed"] + results["failed"]
    cumulative_tested = 146 + total
    cumulative_working = 67 + results["passed"]
    
    print("\n" + "="*80)
    print("📊 NEWLY DISCOVERED ENDPOINTS - RESULTS")
    print("="*80)
    
    print(f"\n🔹 This Round:")
    print(f"  ✅ Passed: {results['passed']}/{total}")
    print(f"  ❌ Failed: {results['failed']}/{total}")
    
    print(f"\n🔹 Cumulative Total:")
    print(f"  📊 Features Tested: {cumulative_tested}")
    print(f"  ✅ Features Working: {cumulative_working}")
    print(f"  📈 Coverage: {(cumulative_tested/137*100):.1f}%")
    
    print(f"\n🆕 New Working Endpoints: {len(results['new_working'])}")
    for i, endpoint in enumerate(results['new_working'], 1):
        print(f"  {i}. ✅ {endpoint}")
    
    with open("newly_discovered_endpoints.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Results: newly_discovered_endpoints.json")
    print(f"\n💙 Found {results['passed']} more working features!")

if __name__ == "__main__":
    asyncio.run(test_new_endpoints())
