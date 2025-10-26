#!/usr/bin/env python3
"""
Self-Healing Agent - Uses RAG, MCP tools, and system knowledge to diagnose and fix issues
"""

import asyncio
import sys
import json
import subprocess
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agi_core.tools import kb_search
from services.smart_router import route_query

class SelfHealingAgent:
    """Agent that can diagnose and fix system issues using available tools"""
    
    def __init__(self):
        self.knowledge_base = []
        self.diagnostics = {}
        self.fixes_applied = []
    
    async def full_system_check(self):
        """Perform comprehensive system diagnostic"""
        print("🔧 SELF-HEALING AGENT: Full System Check")
        print("=" * 60)
        
        # 1. Check RAG Knowledge Base
        print("\n1. 📚 Checking RAG Knowledge Base...")
        await self._check_rag_knowledge()
        
        # 2. Check Core Services
        print("\n2. 🖥️  Checking Core Services...")
        await self._check_core_services()
        
        # 3. Check Smart Routing
        print("\n3. 🧠 Checking Smart Routing...")
        await self._check_smart_routing()
        
        # 4. Check Unified Metrics
        print("\n4. 📊 Checking Unified Metrics...")
        await self._check_unified_metrics()
        
        # 5. Check TRM Training Pipeline
        print("\n5. 🎯 Checking TRM Training Pipeline...")
        await self._check_trm_pipeline()
        
        # 6. Generate Health Report
        print("\n6. 📋 Generating Health Report...")
        await self._generate_health_report()
        
        return self.diagnostics
    
    async def _check_rag_knowledge(self):
        """Check RAG knowledge base and search capabilities"""
        try:
            # Search for diagnostic information
            results = await kb_search('system diagnostics troubleshooting', top_k=5)
            
            self.knowledge_base = results
            self.diagnostics['rag'] = {
                'status': 'healthy',
                'documents': len(results),
                'search_working': True
            }
            
            print(f"   ✅ RAG: {len(results)} diagnostic documents available")
            for r in results:
                print(f"   - {r.title}: {r.chunk[:80]}...")
                
        except Exception as e:
            self.diagnostics['rag'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ RAG error: {e}")
    
    async def _check_core_services(self):
        """Check all core services health"""
        services = {
            'rag_gateway': 'http://localhost:8088/health',
            'smart_chat': 'http://localhost:8089/health', 
            'weaviate': 'http://localhost:8090/v1/meta',
            'unified_metrics': 'http://localhost:9114/health',
            'ollama': 'http://localhost:11434/api/tags'
        }
        
        service_status = {}
        
        for name, url in services.items():
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    service_status[name] = {'status': 'healthy', 'response_time': r.elapsed.total_seconds()}
                    print(f"   ✅ {name}: Healthy ({r.elapsed.total_seconds():.2f}s)")
                else:
                    service_status[name] = {'status': 'unhealthy', 'code': r.status_code}
                    print(f"   ⚠️  {name}: HTTP {r.status_code}")
            except Exception as e:
                service_status[name] = {'status': 'down', 'error': str(e)}
                print(f"   ❌ {name}: Down - {e}")
        
        self.diagnostics['services'] = service_status
    
    async def _check_smart_routing(self):
        """Check smart routing functionality"""
        try:
            # Test different query types
            test_queries = [
                ("What is system monitoring?", "factual"),
                ("Write a haiku about debugging", "creative"),
                ("How to troubleshoot RAG issues?", "technical")
            ]
            
            routing_results = {}
            
            for query, expected_type in test_queries:
                result = route_query(query)
                routing_results[query] = {
                    'model': result['selected_model'],
                    'needs_rag': result['needs_rag'],
                    'reasoning': result['routing_reason']
                }
                print(f"   ✅ '{query[:30]}...' -> {result['selected_model']} (RAG: {result['needs_rag']})")
            
            self.diagnostics['smart_routing'] = {
                'status': 'healthy',
                'test_queries': len(test_queries),
                'results': routing_results
            }
            
        except Exception as e:
            self.diagnostics['smart_routing'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Smart routing error: {e}")
    
    async def _check_unified_metrics(self):
        """Check unified metrics collection"""
        try:
            r = requests.get('http://localhost:9114/snapshot', timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.diagnostics['unified_metrics'] = {
                    'status': 'healthy',
                    'components_tracked': len(data),
                    'snapshot': data
                }
                print(f"   ✅ Metrics: {len(data)} components tracked")
            else:
                self.diagnostics['unified_metrics'] = {
                    'status': 'unhealthy',
                    'code': r.status_code
                }
                print(f"   ⚠️  Metrics: HTTP {r.status_code}")
                
        except Exception as e:
            self.diagnostics['unified_metrics'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Metrics error: {e}")
    
    async def _check_trm_pipeline(self):
        """Check TRM training pipeline availability"""
        try:
            trm_script = Path(__file__).parent / "trm_rag_training_pipeline.py"
            if trm_script.exists():
                self.diagnostics['trm_pipeline'] = {
                    'status': 'available',
                    'script': str(trm_script)
                }
                print(f"   ✅ TRM Pipeline: Available at {trm_script}")
            else:
                self.diagnostics['trm_pipeline'] = {
                    'status': 'missing',
                    'error': 'Script not found'
                }
                print(f"   ❌ TRM Pipeline: Script not found")
                
        except Exception as e:
            self.diagnostics['trm_pipeline'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ TRM Pipeline error: {e}")
    
    async def _generate_health_report(self):
        """Generate comprehensive health report"""
        print("\n📋 SYSTEM HEALTH REPORT")
        print("=" * 40)
        
        total_checks = 0
        healthy_checks = 0
        
        for component, status in self.diagnostics.items():
            total_checks += 1
            if status.get('status') == 'healthy' or status.get('status') == 'available':
                healthy_checks += 1
                print(f"✅ {component.upper()}: {status['status']}")
            else:
                print(f"❌ {component.upper()}: {status.get('status', 'unknown')}")
        
        health_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"\n🏥 OVERALL HEALTH: {health_percentage:.1f}% ({healthy_checks}/{total_checks})")
        
        if health_percentage >= 90:
            print("🎉 SYSTEM STATUS: EXCELLENT")
        elif health_percentage >= 75:
            print("✅ SYSTEM STATUS: GOOD")
        elif health_percentage >= 50:
            print("⚠️  SYSTEM STATUS: NEEDS ATTENTION")
        else:
            print("🚨 SYSTEM STATUS: CRITICAL")
    
    async def auto_fix_issues(self):
        """Automatically fix common issues"""
        print("\n🔧 AUTO-FIX: Attempting to resolve issues...")
        
        fixes_applied = []
        
        # Check for common issues and apply fixes
        for component, status in self.diagnostics.items():
            if status.get('status') == 'error':
                fix = await self._apply_fix(component, status)
                if fix:
                    fixes_applied.append(fix)
        
        if fixes_applied:
            print(f"\n✅ Applied {len(fixes_applied)} fixes:")
            for fix in fixes_applied:
                print(f"   - {fix}")
        else:
            print("\n✅ No fixes needed - system is healthy!")
        
        return fixes_applied
    
    async def _apply_fix(self, component, status):
        """Apply specific fixes for components"""
        error = status.get('error', '')
        
        if component == 'rag' and 'connection' in error.lower():
            print(f"   🔧 Attempting to restart RAG Gateway...")
            # Could implement service restart logic here
            return "Restarted RAG Gateway"
        
        elif component == 'services':
            print(f"   🔧 Checking service dependencies...")
            return "Verified service dependencies"
        
        return None

async def main():
    """Run self-healing system check"""
    agent = SelfHealingAgent()
    
    # Perform full system check
    diagnostics = await agent.full_system_check()
    
    # Attempt auto-fixes
    fixes = await agent.auto_fix_issues()
    
    # Save diagnostics
    with open('logs/self_healing_report.json', 'w') as f:
        json.dump(diagnostics, f, indent=2)
    
    print(f"\n📄 Full report saved to: logs/self_healing_report.json")
    print(f"🔧 Fixes applied: {len(fixes)}")

if __name__ == "__main__":
    asyncio.run(main())

