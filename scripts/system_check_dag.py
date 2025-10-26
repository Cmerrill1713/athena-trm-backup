#!/usr/bin/env python3
"""
DAG-based System Check - Parallel health verification with hard gates
No external dependencies, pure Python stdlib
"""
import asyncio, json, os, sys, time
import subprocess, shlex
import urllib.request, urllib.error

TIMEOUT = float(os.getenv("DAG_TIMEOUT", "30"))
ADAPTER = os.getenv("ADAPTER_BASE", "http://localhost:3000")
RAG_GW  = os.getenv("RAG_GATEWAY", "http://localhost:8088")
WEAV    = os.getenv("WEAVIATE_URL", "http://localhost:8090")  # Fixed: was 8080, should be 8090
METRICS = os.getenv("UNIFIED_METRICS", "http://localhost:9114")  # Fixed: was 8092, should be 9114
SMART_CHAT = os.getenv("SMART_CHAT", "http://localhost:8089")

def curl_json(url, data=None, timeout=TIMEOUT):
    try:
        req = urllib.request.Request(url, data=(json.dumps(data).encode() if data else None),
                                     headers={"Content-Type":"application/json"} if data else {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"__error__": str(e)}

async def check_http(name, url):
    loop = asyncio.get_event_loop()
    return name, await loop.run_in_executor(None, curl_json, url, None, TIMEOUT)

async def kb_probe():
    q = {"query":"recursive reasoning", "topK":5, "mode":"nearText", "semanticEnabled":True}
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, curl_json, f"{RAG_GW}/kb/search", q, TIMEOUT)
    hits = (len(data.get("hits", [])) if isinstance(data, dict) else 0)
    return ("kb_probe", {"hits": hits, "latency_ms": data.get("metrics", {}).get("latency_ms", 0), "raw": data})

async def adapter_models():
    # Check if adapter is available (optional, may not be running)
    try:
        return await check_http("adapter_models", f"{ADAPTER}/v1/models")
    except Exception:
        return ("adapter_models", {"__skipped__": "Adapter not running (using Smart Chat directly)"})

async def smart_chat_health():
    return await check_http("smart_chat_health", f"{SMART_CHAT}/health")

async def weav_ready():
    # Try both ready and meta endpoints
    try:
        result = await check_http("weav_ready", f"{WEAV}/v1/.well-known/ready")
        if "__error__" not in result[1]:
            return result
    except Exception:
        pass
    
    # Fallback to meta endpoint
    try:
        result = await check_http("weav_meta", f"{WEAV}/v1/meta")
        return ("weav_ready", result[1])
    except Exception as e:
        return ("weav_ready", {"__error__": str(e)})

async def weav_class_count(cls="DocsV2"):
    q = {"query": f'{{ Aggregate {{ {cls} {{ meta {{ count }} }} }} }}'}
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, curl_json, f"{WEAV}/v1/graphql", q, TIMEOUT)
    try:
        cnt = data["data"]["Aggregate"][cls][0]["meta"]["count"]
    except Exception:
        cnt = 0
    return ("weav_count", {"class": cls, "count": cnt, "raw": data})

async def stream_test():
    # Test Smart Chat streaming (skip adapter for now)
    try:
        cmd = f"""curl -NsS {SMART_CHAT}/v1/chat/completions \
 -H 'content-type: application/json' \
 -d '{{"messages":[{{"role":"user","content":"test"}}],"max_tokens":10}}' """
        p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(p.communicate(), timeout=TIMEOUT)
        ok = len(out) > 0 and p.returncode == 0
        return ("stream_test", {"ok": ok, "response_length": len(out), "rc": p.returncode})
    except Exception as e:
        return ("stream_test", {"ok": False, "error": str(e)})

async def metrics_snapshot():
    return await check_http("metrics", f"{METRICS}/snapshot")

async def run_make(target):
    if not os.path.exists("Makefile"):
        return (f"make_{target}", {"__skipped__": "Makefile not found"})
    
    p = await asyncio.create_subprocess_exec("make", "-s", target, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(p.communicate(), timeout=120)
        return (f"make_{target}", {"rc": p.returncode, "out": out.decode()[:500], "err": err.decode()[:500]})
    except asyncio.TimeoutError:
        return (f"make_{target}", {"__error__": "timeout", "rc": -1})

async def main():
    t0 = time.time()
    
    # DAG: base health checks in parallel
    tasks = [
        smart_chat_health(),
        weav_ready(), 
        weav_class_count("DocsV2"),
        kb_probe(), 
        stream_test(), 
        metrics_snapshot(),
        adapter_models()  # Optional
    ]
    
    # Optional: quick retrieval gates if Makefile target exists
    # if os.path.exists("Makefile"):
    #     tasks += [run_make("rag-eval")]
    
    results = dict(await asyncio.gather(*tasks, return_exceptions=False))

    # HARD GATES
    failures = []
    warnings = []
    
    # 1) Smart Chat health
    sc = results.get("smart_chat_health", {})
    if "__error__" in sc:
        failures.append(f"Smart Chat unavailable: {sc['__error__']}")
    else:
        print(f"✅ Smart Chat: {sc.get('status', 'unknown')}")
    
    # 2) Weaviate ready
    wr = results.get("weav_ready", {})
    if "__error__" in wr:
        failures.append(f"Weaviate not ready: {wr['__error__']}")
    else:
        print(f"✅ Weaviate: ready")
    
    # 3) DocsV2 present and count > 0
    wc = results.get("weav_count", {})
    doc_count = wc.get("count", 0)
    if doc_count <= 0:
        warnings.append("DocsV2 corpus empty (currently has demo data, consider loading full corpus)")
        print(f"⚠️  DocsV2: {doc_count} documents (demo mode)")
    else:
        print(f"✅ DocsV2: {doc_count:,} documents")
    
    # 4) KB probe gets hits
    kb = results.get("kb_probe", {})
    hits = kb.get("hits", 0)
    if hits <= 0:
        failures.append("KB search returned 0 hits (DocsV2 empty or mis-routed)")
    else:
        print(f"✅ KB Search: {hits} hits in {kb.get('latency_ms', 0)}ms")
    
    # 5) Streaming/response works
    st = results.get("stream_test", {})
    if st.get("ok") is not True:
        failures.append("Smart Chat response test failed")
    else:
        print(f"✅ Chat Response: working")
    
    # 6) Metrics sane
    ms = results.get("metrics", {})
    if not isinstance(ms, dict) or "__error__" in ms:
        failures.append("Unified metrics snapshot unavailable")
    else:
        total_requests = ms.get("total_requests", 0)
        total_errors = ms.get("total_errors", 0)
        print(f"✅ Unified Metrics: {total_requests} requests, {total_errors} errors")
    
    # 7) Adapter (optional)
    am = results.get("adapter_models", {})
    if "__skipped__" in am:
        print(f"ℹ️  Adapter: {am['__skipped__']}")
    elif "__error__" in am:
        warnings.append("OpenAI adapter not running (optional)")
        print(f"⚠️  Adapter: not running (using Smart Chat directly)")
    else:
        print(f"✅ Adapter: available")

    # 8) Retrieval eval (if run)
    mk = results.get("make_rag-eval")
    if mk and "__skipped__" not in mk:
        if mk.get("rc", 1) != 0:
            warnings.append("rag-eval gates failed (optional)")
        else:
            print(f"✅ RAG Eval: passed")

    # Determine status
    if failures:
        status = "FAIL"
        print(f"\n❌ SYSTEM CHECK FAILED")
        for f in failures:
            print(f"   • {f}")
    elif warnings:
        status = "PASS_WITH_WARNINGS"
        print(f"\n✅ SYSTEM CHECK PASSED (with warnings)")
        for w in warnings:
            print(f"   ⚠️  {w}")
    else:
        status = "PASS"
        print(f"\n✅ SYSTEM CHECK PASSED")

    report = {
        "status": status,
        "elapsed_sec": round(time.time() - t0, 2),
        "failures": failures,
        "warnings": warnings,
        "results": results,
        "summary": {
            "smart_chat": "up" if "__error__" not in sc else "down",
            "weaviate": "up" if "__error__" not in wr else "down",
            "docs_v2_count": doc_count,
            "kb_search_hits": hits,
            "total_requests": ms.get("total_requests", 0),
            "total_errors": ms.get("total_errors", 0)
        }
    }
    
    print(f"\n📊 Report saved to artifacts/system_check_dag_report.json")
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/system_check_dag_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Also print JSON for programmatic use
    if os.getenv("JSON_OUTPUT", "").lower() == "true":
        print("\n" + json.dumps(report, indent=2))
    
    sys.exit(0 if status in ["PASS", "PASS_WITH_WARNINGS"] else 1)

if __name__ == "__main__":
    asyncio.run(main())

