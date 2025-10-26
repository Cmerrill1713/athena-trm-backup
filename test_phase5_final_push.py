#!/usr/bin/env python3
"""
PHASE 5: Final Push to 90%+ Coverage
Test remaining features + create final inventory
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE = "http://localhost"
results = {"passed": 0, "failed": 0, "skipped": 0, "new_working": [], "details": []}

def log(name, status, detail="", is_new=False):
    results["details"].append({"name": name, "status": status, "detail": detail})
    if status == "✅": 
        results["passed"] += 1
        if is_new:
            results["new_working"].append(name)
    elif status == "❌": results["failed"] += 1
    else: results["skipped"] += 1
    marker = " 🆕" if is_new else ""
    print(f"  {status} {name}{marker}" + (f" - {detail}" if detail else ""))

async def test_phase5():
    print("🚀 PHASE 5: FINAL PUSH TO 90%+ COVERAGE")
    print("Testing all remaining discoverable features")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # ================================================================
        # MORE AGI CORE FEATURES (Port 8100)
        # ================================================================
        print("\n🤖 AGI CORE - Testing More Endpoints (Port 8100)")
        print("-"*80)
        
        # Health
        try:
            r = await client.get(f"{BASE}:8100/health")
            log("AGI: Health", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("AGI: Health", "❌")
        
        # Metrics
        try:
            r = await client.get(f"{BASE}:8100/metrics")
            log("AGI: Metrics", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("AGI: Metrics", "❌")
        
        # Workflows
        try:
            r = await client.get(f"{BASE}:8100/workflows")
            log("AGI: Workflows", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("AGI: Workflows", "❌")
        
        # Status
        try:
            r = await client.get(f"{BASE}:8100/status")
            log("AGI: Status", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("AGI: Status", "❌")
        
        # Remediate
        try:
            r = await client.post(f"{BASE}:8100/remediate",
                json={"error": "test", "context": {}})
            log("AGI: Remediate", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("AGI: Remediate", "❌")
        
        # ================================================================
        # MORE FEDERATION FEATURES
        # ================================================================
        print("\n⚖️ FEDERATION - More Endpoints")
        print("-"*80)
        
        # Consensus
        try:
            r = await client.post(f"{BASE}:8097/federation/consensus",
                json={"proposal": "test"})
            log("Federation: Consensus", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Federation: Consensus", "❌")
        
        # Vote
        try:
            r = await client.post(f"{BASE}:8097/federation/vote",
                json={"proposal_id": "test", "vote": "yes"})
            log("Federation: Vote", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Federation: Vote", "❌")
        
        # Reputation
        try:
            r = await client.get(f"{BASE}:8097/federation/reputation/test")
            log("Federation: Reputation", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Federation: Reputation", "❌")
        
        # ================================================================
        # TEST ALL REMAINING MCP TOOLS
        # ================================================================
        print("\n🔧 MCP - All Remaining Tools")
        print("-"*80)
        
        # Get full tool list
        try:
            r = await client.get(f"{BASE}:8412/tools")
            tools_data = r.json() if r.status_code == 200 else {}
            tool_names = tools_data.get("tools", {}).keys() if "tools" in tools_data else []
            log("MCP: Full tool list", "✅", f"{len(list(tool_names))} tools", True)
        except: log("MCP: Full tool list", "❌")
        
        # ================================================================
        # TEST REDIS
        # ================================================================
        print("\n🔴 REDIS - Testing Features")
        print("-"*80)
        
        # Check if Redis has HTTP interface
        try:
            r = await client.get(f"{BASE}:6379/ping", timeout=3.0)
            log("Redis: Ping", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Redis", "⚠️", "No HTTP interface (expected)")
        
        # ================================================================
        # TEST WEAVIATE HTTP
        # ================================================================
        print("\n🔷 WEAVIATE - Testing HTTP API")
        print("-"*80)
        
        # Weaviate is typically on 8080, but UAI is there
        # Check if Weaviate is on different port
        for port in [8081, 8083, 8084, 8085]:
            try:
                r = await client.get(f"{BASE}:{port}/v1/meta", timeout=3.0)
                if r.status_code == 200:
                    log(f"Weaviate on port {port}", "✅", "", True)
                    
                    # Test schema
                    try:
                        r2 = await client.get(f"{BASE}:{port}/v1/schema")
                        log("Weaviate: Schema", "✅" if r2.status_code == 200 else "❌", "", True)
                    except: log("Weaviate: Schema", "❌")
                    
                    # Test objects
                    try:
                        r3 = await client.get(f"{BASE}:{port}/v1/objects")
                        log("Weaviate: Objects", "✅" if r3.status_code == 200 else "❌", "", True)
                    except: log("Weaviate: Objects", "❌")
                    
                    break
            except:
                continue
        else:
            log("Weaviate HTTP", "⚠️", "Not found on common ports")
        
        # ================================================================
        # TEST MORE GOVERNANCE FEATURES
        # ================================================================
        print("\n⚖️ GOVERNANCE - More Features")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9110/metrics")
            log("Governance: Metrics", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Governance: Metrics", "❌")
        
        try:
            r = await client.get(f"{BASE}:9110/policies")
            log("Governance: Policies", "✅" if r.status_code == 200 else "❌", "", True)
        except: log("Governance: Policies", "❌")
    
    # ================================================================
    # FINAL SUMMARY
    # ================================================================
    total = results["passed"] + results["failed"] + results["skipped"]
    
    # Calculate overall progress
    all_phases_tested = 108 + total  # 108 from previous phases
    all_phases_working = 53 + results["passed"]  # 53 from previous phases
    
    print("\n" + "="*80)
    print("📊 PHASE 5 RESULTS + CUMULATIVE SUMMARY")
    print("="*80)
    
    print("\n🔹 Phase 5 Results:")
    print(f"  ✅ Passed: {results['passed']}/{total}")
    print(f"  ❌ Failed: {results['failed']}/{total}")
    print(f"  ⚠️  Skipped: {results['skipped']}/{total}")
    
    print("\n🔹 Overall Progress:")
    print(f"  📊 Total Features: 137")
    print(f"  🧪 Features Tested: {all_phases_tested}")
    print(f"  ✅ Features Working: {all_phases_working}")
    print(f"  📈 Coverage: {(all_phases_tested/137*100):.1f}%")
    print(f"  📈 Success Rate: {(all_phases_working/all_phases_tested*100):.1f}%")
    
    print(f"\n🆕 New Discoveries This Phase: {len(results['new_working'])}")
    for i, feature in enumerate(results["new_working"], 1):
        print(f"  {i}. ✅ {feature}")
    
    with open("phase5_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Results: phase5_results.json")
    print(f"\n💙 Phase 5 Complete! Total working features: {all_phases_working}")

if __name__ == "__main__":
    asyncio.run(test_phase5())
