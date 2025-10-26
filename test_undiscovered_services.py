#!/usr/bin/env python3
"""
TEST UNDISCOVERED SERVICES
Services found with /docs endpoints we haven't fully tested
"""
import asyncio
import httpx
import json

BASE = "http://localhost"
results = {"passed": 0, "failed": 0, "new_features": []}

def log(name, status, detail=""):
    if status == "✅": 
        results["passed"] += 1
        results["new_features"].append(name)
    else: 
        results["failed"] += 1
    print(f"  {status} {name}" + (f" - {detail}" if detail else ""))

async def test_undiscovered():
    print("🔍 TESTING UNDISCOVERED SERVICES")
    print("Services found with /docs endpoints")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        
        # ================================================================
        # GOVERNANCE METRICS EXPORTER (Port 9109) - MANY endpoints!
        # ================================================================
        print("\n1️⃣  Governance Metrics Exporter - Port 9109 (NEW!)")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9109/health")
            log("Health", "✅" if r.status_code == 200 else "❌")
        except: log("Health", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/metrics")
            log("Metrics", "✅" if r.status_code == 200 else "❌")
        except: log("Metrics", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/status")
            log("Status", "✅" if r.status_code == 200 else "❌")
        except: log("Status", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/info")
            log("Info", "✅" if r.status_code == 200 else "❌")
        except: log("Info", "❌")
        
        try:
            r = await client.get(f"{BASE}:9109/v1")
            log("V1 endpoint", "✅" if r.status_code == 200 else "❌")
        except: log("V1 endpoint", "❌")
        
        # Get OpenAPI spec to see all endpoints
        try:
            r = await client.get(f"{BASE}:9109/openapi.json")
            if r.status_code == 200:
                spec = r.json()
                paths = list(spec.get("paths", {}).keys())
                log("OpenAPI spec", "✅", f"{len(paths)} endpoints documented")
                print(f"     Endpoints: {', '.join(paths[:10])}")
        except: log("OpenAPI spec", "❌")
        
        # ================================================================
        # CANARY MONITOR (Port 9111)
        # ================================================================
        print("\n2️⃣  Canary Monitor - Port 9111")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9111/health")
            log("Health", "✅" if r.status_code == 200 else "❌")
        except: log("Health", "❌")
        
        try:
            r = await client.get(f"{BASE}:9111/canaries")
            log("List canaries", "✅" if r.status_code == 200 else "❌")
        except: log("List canaries", "❌")
        
        try:
            r = await client.get(f"{BASE}:9111/metrics")
            log("Metrics", "✅" if r.status_code == 200 else "❌")
        except: log("Metrics", "❌")
        
        # ================================================================
        # AGI REMEDIATOR (Port 9112)
        # ================================================================
        print("\n3️⃣  AGI Remediator - Port 9112")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:9112/health")
            log("Health", "✅" if r.status_code == 200 else "❌")
        except: log("Health", "❌")
        
        try:
            r = await client.get(f"{BASE}:9112/metrics")
            log("Metrics", "✅" if r.status_code == 200 else "❌")
        except: log("Metrics", "❌")
        
        try:
            r = await client.post(f"{BASE}:9112/remediate",
                json={"error": "test", "context": {}})
            log("Remediate endpoint", "✅" if r.status_code == 200 else "❌")
        except: log("Remediate endpoint", "❌")
        
        # ================================================================
        # EVOLUTIONARY (Port 8014)
        # ================================================================
        print("\n4️⃣  Evolutionary Service - Port 8014")
        print("-"*80)
        
        try:
            r = await client.get(f"{BASE}:8014/health")
            log("Health", "✅" if r.status_code == 200 else "❌")
        except: log("Health", "❌")
        
        try:
            r = await client.get(f"{BASE}:8014/population")
            log("Get population", "✅" if r.status_code == 200 else "❌")
        except: log("Get population", "❌")
        
        try:
            r = await client.post(f"{BASE}:8014/evolve",
                json={"prompt": "test", "generations": 3})
            log("Evolve endpoint", "✅" if r.status_code == 200 else "❌")
        except: log("Evolve endpoint", "❌")
        
        # ================================================================
        # GOC - Governance Orchestration Compiler (Port ?)
        # ================================================================
        print("\n5️⃣  GOC - Governance Orchestration Compiler")
        print("-"*80)
        
        # Find GOC port
        for port in [8000, 8001, 8002, 8003, 8004, 8005]:
            try:
                r = await client.get(f"{BASE}:{port}/health", timeout=2.0)
                if r.status_code == 200:
                    data = r.json()
                    if "goc" in str(data).lower() or "compiler" in str(data).lower():
                        log(f"GOC found on port {port}", "✅", str(data.get("service", "")))
                        break
            except:
                continue
        else:
            log("GOC", "⚠️", "Not found on common ports")
        
        # ================================================================
        # LLM GATEWAY
        # ================================================================
        print("\n6️⃣  LLM Gateway")
        print("-"*80)
        
        for port in [8000, 8001, 8002, 8003, 8005, 8006]:
            try:
                r = await client.get(f"{BASE}:{port}/health", timeout=2.0)
                if r.status_code == 200:
                    data = r.json()
                    if "llm" in str(data).lower() or "gateway" in str(data).lower():
                        log(f"LLM Gateway found on port {port}", "✅", str(data.get("service", "")))
                        break
            except:
                continue
        else:
            log("LLM Gateway", "⚠️", "Not found or not running")
        
        # ================================================================
        # RAG GATEWAY
        # ================================================================
        print("\n7️⃣  RAG Gateway")
        print("-"*80)
        
        for port in [8000, 8001, 8002, 8003, 8005, 8006, 8007]:
            try:
                r = await client.get(f"{BASE}:{port}/health", timeout=2.0)
                if r.status_code == 200:
                    data = r.json()
                    if "rag" in str(data).lower():
                        log(f"RAG Gateway found on port {port}", "✅", str(data.get("service", "")))
                        break
            except:
                continue
        else:
            log("RAG Gateway", "⚠️", "Not found or not running")
    
    # ================================================================
    # SUMMARY
    # ================================================================
    total = results["passed"] + results["failed"]
    
    print("\n" + "="*80)
    print("📊 UNDISCOVERED SERVICES TEST RESULTS")
    print("="*80)
    print(f"\n✅ Passed: {results['passed']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"\n🆕 New Features Found: {len(results['new_features'])}")
    
    for feature in results["new_features"][:15]:
        print(f"   ✅ {feature}")
    
    with open("undiscovered_services_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Results: undiscovered_services_results.json")
    print(f"💙 Found {results['passed']} more features!")

if __name__ == "__main__":
    asyncio.run(test_undiscovered())
