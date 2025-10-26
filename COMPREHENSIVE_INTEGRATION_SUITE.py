#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite
Tests ALL discovered functionality and integrations
"""
import requests
import json
import time
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    def __init__(self):
        self.results = []
        self.services = {
            "uai": "http://localhost:8080",
            "router": "http://localhost:9113",
            "autonomous": "http://localhost:9114",
            "knowledge_gateway": "http://localhost:8093",
            "knowledge_context": "http://localhost:8092",
            "knowledge_sync": "http://localhost:8089",
            "fastvlm": "http://localhost:8088",
            "kokoro": "http://localhost:8091",
            "mcp": "http://localhost:8412",
            "governance": "http://localhost:9110",
            "prometheus": "http://localhost:9090",
            "grafana": "http://localhost:3001",
            "weaviate": "http://localhost:8090"
        }
    
    def test(self, name: str, method: str, url: str, data: Dict = None, expect_status: int = 200):
        """Run a single test"""
        try:
            if method == "GET":
                resp = requests.get(url, timeout=5)
            elif method == "POST":
                resp = requests.post(url, json=data, timeout=5)
            else:
                resp = requests.request(method, url, json=data, timeout=5)
            
            passed = resp.status_code == expect_status or (200 <= resp.status_code < 300)
            
            self.results.append({
                "name": name,
                "method": method,
                "url": url,
                "status": resp.status_code,
                "passed": passed
            })
            
            status = "✅ PASS" if passed else f"❌ FAIL ({resp.status_code})"
            logger.info(f"{status} - {name}")
            
            return passed, resp
            
        except Exception as e:
            logger.error(f"❌ ERROR - {name}: {e}")
            self.results.append({
                "name": name,
                "method": method,
                "url": url,
                "status": "ERROR",
                "passed": False
            })
            return False, None
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🧪 COMPREHENSIVE INTEGRATION TEST SUITE")
        logger.info("=" * 60)
        
        # UAI Tests
        logger.info("\n📍 UAI Service (8080)")
        logger.info("-" * 60)
        self.test("UAI Health", "GET", f"{self.services['uai']}/health")
        self.test("UAI Chat", "POST", f"{self.services['uai']}/v1/chat/completions", 
                  {"messages": [{"role": "user", "content": "Test"}], "max_tokens": 10})
        self.test("UAI Tasks List", "GET", f"{self.services['uai']}/api/tasks/")
        self.test("UAI Task Detail", "GET", f"{self.services['uai']}/api/tasks/1")
        self.test("UAI Users List", "GET", f"{self.services['uai']}/api/users/")
        self.test("UAI User Detail", "GET", f"{self.services['uai']}/api/users/1")
        self.test("UAI TTS Voices", "GET", f"{self.services['uai']}/api/tts/voices")
        self.test("UAI Metrics", "GET", f"{self.services['uai']}/metrics")
        
        # Router Tests
        logger.info("\n📍 Router Service (9113)")
        logger.info("-" * 60)
        self.test("Router Health", "GET", f"{self.services['router']}/health")
        self.test("Router Ready", "GET", f"{self.services['router']}/ready")
        self.test("Router Version", "GET", f"{self.services['router']}/version")
        self.test("Router Route", "POST", f"{self.services['router']}/route", 
                  {"prompt": "What is TRM?"})
        self.test("Router Respond", "POST", f"{self.services['router']}/respond",
                  {"message": "Hello"})
        self.test("Router Vision", "POST", f"{self.services['router']}/vision/analyze",
                  {"image_b64": "test", "prompt": "test"})
        self.test("Router TTS", "POST", f"{self.services['router']}/tts/synthesize",
                  {"text": "test", "voice": "en_US-female"})
        self.test("Router Policy Reload", "POST", f"{self.services['router']}/reload-policy")
        
        # Autonomous Orchestrator Tests
        logger.info("\n📍 Autonomous Orchestrator (9114)")
        logger.info("-" * 60)
        self.test("Autonomous Health", "GET", f"{self.services['autonomous']}/health")
        self.test("Autonomous Status", "GET", f"{self.services['autonomous']}/status")
        self.test("Adaptive TRM Decide", "POST", f"{self.services['autonomous']}/trm/decide",
                  {"query": "Solve sudoku"})
        self.test("Adaptive TRM Feedback", "POST", f"{self.services['autonomous']}/feedback",
                  {"query_id": "test", "query": "test", "used_trm": True, "success": True, "latency_ms": 100})
        self.test("Auto-Rollback Evaluate", "POST", f"{self.services['autonomous']}/rollback/evaluate")
        
        # Knowledge Services Tests
        logger.info("\n📍 Knowledge Services")
        logger.info("-" * 60)
        self.test("Knowledge Gateway Health", "GET", f"{self.services['knowledge_gateway']}/health")
        self.test("Knowledge Gateway Search", "POST", f"{self.services['knowledge_gateway']}/search",
                  {"query": "TRM", "limit": 3})
        self.test("Knowledge Context Health", "GET", f"{self.services['knowledge_context']}/health")
        self.test("Knowledge Sync Health", "GET", f"{self.services['knowledge_sync']}/health")
        
        # Multimodal Tests
        logger.info("\n📍 Multimodal Services")
        logger.info("-" * 60)
        self.test("FastVLM Health", "GET", f"{self.services['fastvlm']}/health")
        self.test("FastVLM Analyze", "POST", f"{self.services['fastvlm']}/analyze",
                  {"image": "test", "prompt": "test"})
        self.test("Kokoro Health", "GET", f"{self.services['kokoro']}/health")
        self.test("Kokoro Synthesize", "POST", f"{self.services['kokoro']}/synthesize",
                  {"text": "Integration test", "voice": "en_US-female"})
        
        # MCP Tools
        logger.info("\n📍 MCP Tools")
        logger.info("-" * 60)
        self.test("MCP Health", "GET", f"{self.services['mcp']}/health")
        self.test("MCP Web Search", "POST", f"{self.services['mcp']}/tool/web_search",
                  {"arguments": {"query": "AI"}})
        self.test("MCP arXiv Search", "POST", f"{self.services['mcp']}/tool/arxiv_search",
                  {"arguments": {"query": "transformers", "max_results": 2}})
        
        # Governance
        logger.info("\n📍 Governance")
        logger.info("-" * 60)
        self.test("Governance Health", "GET", f"{self.services['governance']}/health")
        self.test("Governance State", "GET", f"{self.services['governance']}/state")
        
        # Observability
        logger.info("\n📍 Observability")
        logger.info("-" * 60)
        self.test("Prometheus Status", "GET", f"{self.services['prometheus']}/api/v1/status/config")
        self.test("Grafana Health", "GET", f"{self.services['grafana']}/api/health")
        
        # Weaviate
        logger.info("\n📍 Weaviate")
        logger.info("-" * 60)
        self.test("Weaviate Meta", "GET", f"{self.services['weaviate']}/v1/meta")
        self.test("Weaviate Schema", "GET", f"{self.services['weaviate']}/v1/schema")
        self.test("Weaviate Objects", "GET", f"{self.services['weaviate']}/v1/objects?limit=5")
        
        # Results Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed} ✅")
        logger.info(f"Failed: {failed} ❌")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            logger.info("\n❌ Failed Tests:")
            for r in self.results:
                if not r["passed"]:
                    logger.info(f"   - {r['name']} ({r['method']} {r['url']}): {r['status']}")
        
        return passed, total

if __name__ == "__main__":
    suite = ComprehensiveTestSuite()
    passed, total = suite.run_all_tests()
    
    # Save results
    with open("test_results_comprehensive.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "results": suite.results
        }, f, indent=2)
    
    logger.info(f"\n💾 Results saved to test_results_comprehensive.json")
    logger.info(f"\n🎉 Comprehensive testing complete: {passed}/{total} passed")
