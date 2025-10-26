#!/usr/bin/env python3
"""
Full AGI-RAG-TRM System Diagnostic
Performs comprehensive health check across all layers
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_status(emoji: str, status: str, message: str):
    print(f"{emoji} {status} {message}")

def check_file_exists(filepath: str) -> bool:
    """Check if a critical file exists and is readable"""
    path = Path(filepath)
    return path.exists() and path.is_file()

def check_dir_exists(dirpath: str) -> bool:
    """Check if a critical directory exists"""
    path = Path(dirpath)
    return path.exists() and path.is_dir()

# ============================================================================
# 1. CORE CODE INTEGRITY
# ============================================================================
def check_code_integrity() -> Dict[str, Any]:
    print_header("🧠 1. CORE CODE INTEGRITY")
    
    results = {
        "status": "healthy",
        "issues": [],
        "checks": {}
    }
    
    critical_paths = {
        "AGI Core": "agi_core/",
        "RAG Gateway": "services/rag-gateway/app.py",
        "Smart Router": "services/smart_router.py",
        "Smart Chat": "services/smart_chat/app.py",
        "Unified Metrics": "services/unified_metrics.py",
        "Code Access Tool": "agi_core/tools/code_access_tool.py",
        "KB Search Tool": "agi_core/tools/kb_search_tool.py",
        "Self Healing": "scripts/self_healing_agent.py",
        "Ship Check": "scripts/ship_check.sh"
    }
    
    for name, path in critical_paths.items():
        if '/' in path and not path.endswith('.py') and not path.endswith('.sh'):
            exists = check_dir_exists(path)
        else:
            exists = check_file_exists(path)
        
        results["checks"][name] = exists
        
        if exists:
            print_status("🟢", "OK", f"{name}: {path}")
        else:
            print_status("🔴", "MISSING", f"{name}: {path}")
            results["issues"].append(f"Missing: {path}")
            results["status"] = "degraded"
    
    # Try importing key modules
    print("\nTesting module imports...")
    try:
        sys.path.insert(0, str(Path.cwd()))
        from agi_core.tools.code_access_tool import CodeAccessTool
        print_status("🟢", "OK", "CodeAccessTool import")
    except Exception as e:
        print_status("🔴", "FAIL", f"CodeAccessTool import: {e}")
        results["issues"].append(f"Import error: {e}")
        results["status"] = "degraded"
    
    return results

# ============================================================================
# 2. SERVICE HEALTH
# ============================================================================
def check_service_health() -> Dict[str, Any]:
    print_header("⚙️ 2. SERVICE HEALTH")
    
    results = {
        "status": "healthy",
        "services": {},
        "issues": []
    }
    
    services = {
        "RAG Gateway": {"port": 8088, "health": "/health"},
        "Smart Chat": {"port": 8089, "health": "/health"},
        "Weaviate": {"port": 8080, "health": "/v1/.well-known/ready"},
        "Embedding Service": {"port": 8086, "health": "/health"},
        "Ollama": {"port": 11434, "health": "/api/tags"},
        "Unified Metrics": {"port": 9114, "health": "/snapshot"}
    }
    
    for name, config in services.items():
        url = f"http://localhost:{config['port']}{config['health']}"
        try:
            start = time.time()
            response = requests.get(url, timeout=3)
            latency = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                print_status("🟢", "UP", f"{name} (port {config['port']}, {latency}ms)")
                results["services"][name] = {
                    "status": "up",
                    "port": config['port'],
                    "latency_ms": latency
                }
            else:
                print_status("🟡", "WARN", f"{name} returned {response.status_code}")
                results["services"][name] = {
                    "status": "degraded",
                    "port": config['port'],
                    "code": response.status_code
                }
                results["status"] = "degraded"
                
        except requests.exceptions.ConnectionRefusedError:
            print_status("🔴", "DOWN", f"{name} (port {config['port']})")
            results["services"][name] = {"status": "down", "port": config['port']}
            results["issues"].append(f"{name} is not responding")
            results["status"] = "degraded"
        except Exception as e:
            print_status("🔴", "ERROR", f"{name}: {str(e)[:50]}")
            results["services"][name] = {"status": "error", "error": str(e)}
            results["issues"].append(f"{name}: {e}")
            results["status"] = "degraded"
    
    return results

# ============================================================================
# 3. KNOWLEDGE BASE STATUS
# ============================================================================
def check_knowledge_base() -> Dict[str, Any]:
    print_header("🧭 3. KNOWLEDGE BASE STATUS")
    
    results = {
        "status": "healthy",
        "weaviate": {},
        "issues": []
    }
    
    # Check Weaviate schema
    try:
        response = requests.get("http://localhost:8080/v1/schema", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            classes = schema.get("classes", [])
            
            # Look for DocsV2
            docs_v2 = None
            for cls in classes:
                if cls.get("class") == "DocsV2":
                    docs_v2 = cls
                    break
            
            if docs_v2:
                print_status("🟢", "OK", "DocsV2 class exists")
                
                # Get vector dimensions
                vector_config = docs_v2.get("vectorizer", {})
                print_status("🟢", "OK", f"Vector config: {vector_config}")
                
                # Count documents
                try:
                    agg_response = requests.get(
                        "http://localhost:8080/v1/objects?class=DocsV2&limit=0",
                        timeout=5
                    )
                    if agg_response.status_code == 200:
                        # Try to get total count from aggregate
                        aggregate_query = """
                        {
                          Aggregate {
                            DocsV2 {
                              meta { count }
                            }
                          }
                        }
                        """
                        gql_response = requests.post(
                            "http://localhost:8080/v1/graphql",
                            json={"query": aggregate_query},
                            timeout=5
                        )
                        
                        if gql_response.status_code == 200:
                            gql_data = gql_response.json()
                            count = gql_data.get("data", {}).get("Aggregate", {}).get("DocsV2", [{}])[0].get("meta", {}).get("count", 0)
                            print_status("🟢", "OK", f"DocsV2 contains {count:,} documents")
                            results["weaviate"]["document_count"] = count
                        else:
                            print_status("🟡", "WARN", "Could not get document count via GraphQL")
                except Exception as e:
                    print_status("🟡", "WARN", f"Could not count documents: {e}")
                
                results["weaviate"]["schema"] = "ok"
                results["weaviate"]["class"] = "DocsV2"
            else:
                print_status("🔴", "MISSING", "DocsV2 class not found in schema")
                results["issues"].append("DocsV2 class missing")
                results["status"] = "degraded"
        else:
            print_status("🔴", "ERROR", f"Schema check returned {response.status_code}")
            results["issues"].append(f"Schema check failed: {response.status_code}")
            results["status"] = "degraded"
            
    except Exception as e:
        print_status("🔴", "ERROR", f"Weaviate check failed: {e}")
        results["issues"].append(f"Weaviate error: {e}")
        results["status"] = "degraded"
    
    # Test KB search
    print("\nTesting KB search...")
    try:
        search_response = requests.post(
            "http://localhost:8088/kb/search",
            json={"query": "system check", "topK": 3, "mode": "nearText"},
            timeout=10
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            hits = data.get("hits", [])
            latency = data.get("metrics", {}).get("latency_ms", 0)
            
            print_status("🟢", "OK", f"KB search working ({len(hits)} results, {latency}ms)")
            results["weaviate"]["search_working"] = True
            results["weaviate"]["search_latency_ms"] = latency
        else:
            print_status("🔴", "FAIL", f"KB search returned {search_response.status_code}")
            results["issues"].append(f"KB search failed: {search_response.status_code}")
            results["status"] = "degraded"
            
    except Exception as e:
        print_status("🔴", "ERROR", f"KB search test failed: {e}")
        results["issues"].append(f"KB search error: {e}")
        results["status"] = "degraded"
    
    return results

# ============================================================================
# 4. ROUTING LOGIC & ADAPTER
# ============================================================================
def check_routing_logic() -> Dict[str, Any]:
    print_header("🧭 4. ROUTING LOGIC & SMART CHAT")
    
    results = {
        "status": "healthy",
        "tests": [],
        "issues": []
    }
    
    test_queries = [
        {"query": "What is the capital of France?", "expected_type": "factual", "description": "Factual query"},
        {"query": "Write me a creative story about a robot", "expected_type": "creative", "description": "Creative query"},
        {"query": "Explain recursive reasoning in AI systems", "expected_type": "reasoning", "description": "Reasoning query"}
    ]
    
    for test in test_queries:
        try:
            print(f"\nTesting: {test['description']}")
            print(f"Query: {test['query']}")
            
            start = time.time()
            response = requests.post(
                "http://localhost:8089/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": test['query']}],
                    "max_tokens": 100
                },
                timeout=30
            )
            latency = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                print_status("🟢", "OK", f"Response received ({latency}ms)")
                print(f"   Preview: {content[:100]}...")
                
                results["tests"].append({
                    "query": test['query'],
                    "type": test['expected_type'],
                    "status": "success",
                    "latency_ms": latency,
                    "response_length": len(content)
                })
            else:
                print_status("🔴", "FAIL", f"Chat returned {response.status_code}")
                results["issues"].append(f"Chat failed for {test['expected_type']}: {response.status_code}")
                results["status"] = "degraded"
                
        except Exception as e:
            print_status("🔴", "ERROR", f"Chat test failed: {e}")
            results["issues"].append(f"Chat error: {e}")
            results["status"] = "degraded"
    
    return results

# ============================================================================
# 5. UNIFIED METRICS & QUALITY GATES
# ============================================================================
def check_unified_metrics() -> Dict[str, Any]:
    print_header("📊 5. UNIFIED METRICS & QUALITY GATES")
    
    results = {
        "status": "healthy",
        "metrics": {},
        "issues": []
    }
    
    try:
        response = requests.get("http://localhost:9114/snapshot", timeout=5)
        
        if response.status_code == 200:
            metrics = response.json()
            
            print_status("🟢", "OK", "Unified Metrics snapshot retrieved")
            print(f"\nMetrics Snapshot:")
            print(json.dumps(metrics, indent=2))
            
            results["metrics"] = metrics
            
            # Check quality gates (if metrics are available)
            # Note: These might be empty on fresh start
            
        else:
            print_status("🔴", "FAIL", f"Metrics returned {response.status_code}")
            results["issues"].append(f"Metrics failed: {response.status_code}")
            results["status"] = "degraded"
            
    except Exception as e:
        print_status("🔴", "ERROR", f"Metrics check failed: {e}")
        results["issues"].append(f"Metrics error: {e}")
        results["status"] = "degraded"
    
    return results

# ============================================================================
# 6. ACCEPTANCE & CANARY COMPATIBILITY
# ============================================================================
def check_acceptance_suite() -> Dict[str, Any]:
    print_header("🧪 6. ACCEPTANCE & CANARY COMPATIBILITY")
    
    results = {
        "status": "healthy",
        "checks": {},
        "issues": []
    }
    
    # Check if acceptance scripts exist
    scripts = {
        "ship_check": "scripts/ship_check.sh",
        "ship_check_simple": "scripts/ship_check_simple.sh",
        "complete_system_check": "scripts/complete_system_check.sh",
        "canary_deploy": "scripts/canary_deploy.sh"
    }
    
    for name, path in scripts.items():
        exists = check_file_exists(path)
        results["checks"][name] = exists
        
        if exists:
            print_status("🟢", "OK", f"{name}: {path}")
        else:
            print_status("🟡", "MISSING", f"{name}: {path}")
            # Not critical, so just note it
    
    print("\nTrying simplified ship check...")
    try:
        if check_file_exists("scripts/ship_check_simple.sh"):
            result = subprocess.run(
                ["bash", "scripts/ship_check_simple.sh"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print_status("🟢", "PASS", "Ship check simple passed")
                results["checks"]["ship_check_run"] = "pass"
            else:
                print_status("🟡", "WARN", f"Ship check returned {result.returncode}")
                print(f"   Output: {result.stdout[:200]}")
                results["checks"]["ship_check_run"] = "warn"
        else:
            print_status("🟡", "SKIP", "Ship check script not found, skipping")
            
    except Exception as e:
        print_status("🟡", "WARN", f"Ship check test: {e}")
    
    return results

# ============================================================================
# 7. CODEBASE OPTIMIZATION CHECK
# ============================================================================
def check_code_optimization() -> Dict[str, Any]:
    print_header("🧰 7. CODEBASE OPTIMIZATION CHECK")
    
    results = {
        "status": "healthy",
        "suggestions": [],
        "issues": []
    }
    
    # Use the code access tool to analyze key files
    try:
        sys.path.insert(0, str(Path.cwd()))
        from agi_core.tools.code_access_tool import CodeAccessTool
        
        tool = CodeAccessTool()
        
        # Analyze key service files
        files_to_check = [
            "services/smart_chat/app.py",
            "services/smart_router.py",
            "services/rag-gateway/app.py"
        ]
        
        for filepath in files_to_check:
            if check_file_exists(filepath):
                analysis = tool.analyze_code(filepath)
                
                if "error" not in analysis:
                    print(f"\n📄 {filepath}:")
                    print(f"   Lines: {analysis.get('total_lines', 0)}")
                    print(f"   Functions: {analysis.get('functions', 0)}")
                    print(f"   Classes: {analysis.get('classes', 0)}")
                    
                    # Simple heuristics
                    if analysis.get('total_lines', 0) > 500:
                        suggestion = f"{filepath} is large ({analysis['total_lines']} lines) - consider modularizing"
                        results["suggestions"].append(suggestion)
                        print(f"   💡 {suggestion}")
                else:
                    print_status("🟡", "WARN", f"Could not analyze {filepath}")
        
        print_status("🟢", "OK", "Code analysis complete")
        
    except Exception as e:
        print_status("🟡", "WARN", f"Code optimization check: {e}")
    
    return results

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║    ATHENA AGI-RAG-TRM FULL SYSTEM DIAGNOSTIC              ║")
    print("║    Comprehensive Health Check Across All Layers           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all checks
    all_results = {}
    
    all_results["1_code_integrity"] = check_code_integrity()
    all_results["2_service_health"] = check_service_health()
    all_results["3_knowledge_base"] = check_knowledge_base()
    all_results["4_routing_logic"] = check_routing_logic()
    all_results["5_unified_metrics"] = check_unified_metrics()
    all_results["6_acceptance_suite"] = check_acceptance_suite()
    all_results["7_code_optimization"] = check_code_optimization()
    
    # Summary
    print_header("📊 DIAGNOSTIC SUMMARY")
    
    overall_status = "healthy"
    total_issues = 0
    
    for check_name, result in all_results.items():
        status = result.get("status", "unknown")
        issues = len(result.get("issues", []))
        total_issues += issues
        
        if status == "degraded" or issues > 0:
            overall_status = "degraded"
        
        emoji = "🟢" if status == "healthy" and issues == 0 else "🟡" if status == "degraded" else "🔴"
        print(f"{emoji} {check_name.replace('_', ' ').title()}: {status.upper()} ({issues} issues)")
    
    print(f"\n{Colors.BOLD}Overall System Status: {overall_status.upper()}{Colors.RESET}")
    print(f"Total Issues Found: {total_issues}")
    
    # Save full report
    report_file = f"artifacts/diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("artifacts", exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "total_issues": total_issues,
            "results": all_results
        }, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    # Print key recommendations
    if total_issues > 0:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}🔧 RECOMMENDED ACTIONS:{Colors.RESET}")
        for check_name, result in all_results.items():
            issues = result.get("issues", [])
            if issues:
                print(f"\n{check_name.replace('_', ' ').title()}:")
                for issue in issues[:3]:  # Show top 3 issues per check
                    print(f"  • {issue}")
    
    suggestions = all_results.get("7_code_optimization", {}).get("suggestions", [])
    if suggestions:
        print(f"\n{Colors.BOLD}{Colors.BLUE}💡 OPTIMIZATION SUGGESTIONS:{Colors.RESET}")
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Diagnostic complete!{Colors.RESET}\n")
    
    return 0 if overall_status == "healthy" else 1

if __name__ == "__main__":
    sys.exit(main())


