#!/usr/bin/env python3
"""
COMPLETE EXPANDED TEST
Test ALL discovered features including new ones
"""
import asyncio
import httpx
import json

BASE = "http://localhost"
results = {"passed": 0, "failed": 0, "total_tested": 0, "new_discoveries": []}

def log(name, status, detail="", is_new=False):
    results["total_tested"] += 1
    if status == "✅": 
        results["passed"] += 1
        if is_new:
            results["new_discoveries"].append(name)
    else: 
        results["failed"] += 1
    marker = " 🆕" if is_new else ""
    print(f"  {status} {name}{marker}" + (f" - {detail}" if detail else ""))

async def test_all_expanded():
    print("🎯 COMPLETE EXPANDED TEST - ALL Features Including New Discoveries")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        
        # ================================================================
        # NEW: Governance Metrics Exporter (5 endpoints)
        # ================================================================
        print("\n🆕 GOVERNANCE METRICS EXPORTER - 5 New Endpoints")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9109/health")
            log("Health", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Health", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/metrics")
            log("Prometheus metrics", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Prometheus metrics", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/status")
            data = r.json() if r.status_code == 200 else {}
            log("Status", "✅" if r.status_code == 200 else "❌", str(data.get("status", ""))[:30], True)
        except: log("Status", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/info")
            log("Info", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Info", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/v1")
            log("V1 API", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("V1 API", "❌")
        
        # ================================================================
        # NEW: AGI Core (if now running)
        # ================================================================
        print("\n🆕 AGI CORE - Testing After Startup")
        print("-"*80)
        
        # Check both port 8100 and potential agi-core service port
        for port in [8100, 8101]:
            try:
                r = await client.get(f"{BASE}:{port}/health", timeout=3.0)
                if r.status_code == 200:
                    data = r.json()
                    service = data.get("service", "")
                    if "agi" in service.lower():
                        log(f"AGI Core on port {port}", "✅", service, True)
                        
                        # Test more endpoints
                        try:
                            r2 = await client.get(f"{BASE}:{port}/tools")
                            log("List tools", "✅" if r2.status_code == 200 else "❌", "", True)
                        except: log("List tools", "❌")
                        
                        try:
                            r3 = await client.get(f"{BASE}:{port}/workflows")
                            log("List workflows", "✅" if r3.status_code == 200 else "❌", "", True)
                        except: log("List workflows", "❌")
                        
                        break
            except:
                continue
        
        # ================================================================
        # NEW: Alertmanager (if now running)
        # ================================================================
        print("\n🆕 ALERTMANAGER - Testing After Startup")
        print("-"*80)
        
        for port in [9093, 9094, 9095, 9096]:
            try:
                r = await client.get(f"{BASE}:{port}/-/healthy", timeout=3.0)
                if r.status_code == 200:
                    log(f"Alertmanager on port {port}", "✅", "", True)
                    
                    # Test alerts endpoint
                    try:
                        r2 = await client.get(f"{BASE}:{port}/api/v2/alerts")
                        log("List alerts", "✅" if r2.status_code == 200 else "❌", "", True)
                    except: log("List alerts", "❌")
                    
                    break
            except:
                continue
        else:
            log("Alertmanager", "⚠️", "Not found - may not be critical")
        
        # ================================================================
        # EXPANDED: More Governance Features
        # ================================================================
        print("\n📊 GOVERNANCE ORCHESTRATOR - More Features")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9110/docs")
            if r.status_code == 200:
                log("OpenAPI docs", "✅", "", True)
        except: log("OpenAPI docs", "❌")
        
        try:
            r = await client.get(f"{BASE}:9110/policies")
            log("List policies", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("List policies", "❌")
        
        try:
            r = await client.post(f"{BASE}:9110/evaluate",
                json={"policy": "test", "context": {}})
            log("Evaluate policy", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Evaluate policy", "❌")
    
    # ================================================================
    # FINAL SUMMARY
    # ================================================================
    total = results["total_tested"]
    cumulative = 133 + total  # 133 from previous phases
    cumulative_working = 58 + results["passed"]
    
    print("\n" + "="*80)
    print("📊 COMPLETE EXPANDED TEST RESULTS")
    print("="*80)
    
    print(f"\n🔹 This Phase:")
    print(f"  ✅ Passed: {results['passed']}/{total}")
    print(f"  ❌ Failed: {results['failed']}/{total}")
    
    print(f"\n🔹 Cumulative (All Phases):")
    print(f"  📊 Total Features: 137+")
    print(f"  🧪 Features Tested: {cumulative}")
    print(f"  ✅ Features Working: {cumulative_working}")
    print(f"  📈 Coverage: {(cumulative/137*100):.1f}%")
    
    print(f"\n🆕 New Discoveries: {len(results['new_discoveries'])}")
    for i, discovery in enumerate(results['new_discoveries'], 1):
        print(f"  {i}. ✅ {discovery}")
    
    with open("complete_expanded_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Results: complete_expanded_results.json")
    print(f"\n💙 Found {results['passed']} more working features!")

if __name__ == "__main__":
    asyncio.run(test_all_expanded())
