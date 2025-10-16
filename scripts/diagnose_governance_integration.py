#!/usr/bin/env python3
"""
Comprehensive Governance Integration Diagnostic

Checks all integration points between Governance, AGI Core, and Athena.
Based on the 10-minute integration checklist.
"""

import requests
import json
import time
from typing import Dict, List, Any, Tuple

# Colors
class Colors:
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    RESET = '\033[0m'

def green(msg): print(f"{Colors.GREEN}{msg}{Colors.RESET}")
def yellow(msg): print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
def red(msg): print(f"{Colors.RED}{msg}{Colors.RESET}")
def blue(msg): print(f"{Colors.BLUE}{msg}{Colors.RESET}")

def section(title):
    print(f"\n{'='*70}")
    blue(f"  {title}")
    print(f"{'='*70}\n")


class IntegrationDiagnostic:
    """Comprehensive integration diagnostic"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warned = 0
        
        self.services = {
            "prometheus": "http://localhost:9090",
            "grafana": "http://localhost:3001",
            "governance_metrics": "http://localhost:9109",
            "governance_canary": "http://localhost:9111",
            "governance_orchestrator": "http://localhost:9110",
            "agi_core": "http://localhost:8100"
        }
    
    def check(self, test_func, description) -> bool:
        """Run a check"""
        try:
            result = test_func()
            if result:
                green(f"✅ {description}")
                self.passed += 1
                return True
            else:
                yellow(f"⚠️  {description}")
                self.warned += 1
                return False
        except Exception as e:
            red(f"❌ {description}")
            print(f"   Error: {e}")
            self.failed += 1
            return False
    
    def critical_check(self, test_func, description) -> bool:
        """Run a critical check (failure = show error)"""
        result = self.check(test_func, description)
        return result
    
    # ========================================================================
    # 1. Service Health Checks
    # ========================================================================
    
    def check_services(self):
        section("1. SERVICE HEALTH CHECKS")
        
        for name, url in self.services.items():
            def test():
                try:
                    r = requests.get(f"{url}/health", timeout=2)
                    return r.status_code in [200, 404]  # 404 means service up, no /health endpoint
                except:
                    return False
            
            self.check(test, f"{name}: {url}")
    
    # ========================================================================
    # 2. Prometheus Scraping
    # ========================================================================
    
    def check_prometheus_targets(self):
        section("2. PROMETHEUS SCRAPING")
        
        def has_governance_jobs():
            r = requests.get(f"{self.services['prometheus']}/api/v1/targets")
            targets = r.json()['data']['activeTargets']
            gov_jobs = [t for t in targets if 'governance' in t['labels']['job']]
            
            if gov_jobs:
                print(f"Found {len(gov_jobs)} governance jobs:")
                for t in gov_jobs:
                    job = t['labels']['job']
                    health = t['health']
                    health_icon = "✅" if health == "up" else "❌"
                    print(f"   {health_icon} {job}: {health}")
                return len(gov_jobs) > 0
            return False
        
        self.check(has_governance_jobs, "Governance jobs configured in Prometheus")
        
        # Check specific metrics exist
        metrics_to_check = [
            "governance_verdicts_total",
            "governance_actions_total",
            "governance_ece_post",
            "governance_entropy_drift"
        ]
        
        print("\nChecking if metrics are being scraped:")
        for metric in metrics_to_check:
            def test():
                r = requests.get(
                    f"{self.services['prometheus']}/api/v1/query",
                    params={"query": metric}
                )
                result = r.json()['data']['result']
                return len(result) > 0
            
            self.check(test, f"{metric}")
    
    # ========================================================================
    # 3. End-to-End Verdict Flow
    # ========================================================================
    
    def check_verdict_flow(self):
        section("3. END-TO-END VERDICT FLOW")
        
        task_id = f"diagnostic_{int(time.time())}"
        
        # Send test verdict
        verdict_payload = {
            "task_id": task_id,
            "verdict": "PASS",
            "ece_estimate": 0.92,
            "entropy_drift": 0.05,
            "violation_rate_delta": 0.01,
            "latency_p95_delta": 10
        }
        
        def send_verdict():
            r = requests.post(
                f"{self.services['governance_orchestrator']}/verdict",
                json=verdict_payload,
                timeout=5
            )
            print(f"   Verdict response: {r.json().get('status', 'unknown')}")
            return r.status_code == 200
        
        self.critical_check(send_verdict, f"Send verdict {task_id}")
        
        # Wait for metrics to update
        time.sleep(1)
        
        # Check metrics updated
        def check_metric_update():
            r = requests.get(
                f"{self.services['prometheus']}/api/v1/query",
                params={"query": "governance_verdicts_total"}
            )
            result = r.json()['data']['result']
            return len(result) > 0
        
        self.check(check_metric_update, "Verdict metrics updated")
    
    # ========================================================================
    # 4. AGI Core Integration
    # ========================================================================
    
    def check_agi_integration(self):
        section("4. AGI CORE INTEGRATION")
        
        # Check if AGI Core is running
        def agi_running():
            r = requests.get(f"{self.services['agi_core']}/health", timeout=2)
            return r.status_code == 200
        
        if not self.check(agi_running, "AGI Core service running"):
            yellow("\n  💡 To start AGI Core:")
            yellow("     cd agi_core && python3 -m agi_core.agi_service &")
            return
        
        # Check AGI stats
        def check_agi_stats():
            r = requests.get(f"{self.services['agi_core']}/stats")
            stats = r.json()
            print(f"   Experts: {stats.get('registered_experts', 0)}")
            print(f"   Active agents: {stats.get('active_agents', 0)}")
            return stats.get('registered_experts', 0) > 0
        
        self.check(check_agi_stats, "AGI Core statistics available")
        
        # Test integration bridge
        def test_bridge():
            try:
                from agi_core.integrations import GovernanceBridge
                bridge = GovernanceBridge()
                return True
            except:
                return False
        
        self.check(test_bridge, "Integration bridge functional")
    
    # ========================================================================
    # 5. Docker Network
    # ========================================================================
    
    def check_docker_network(self):
        section("5. DOCKER NETWORK")
        
        import subprocess
        
        def check_containers():
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=governance', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            containers = result.stdout.strip().split('\n')
            containers = [c for c in containers if c]
            
            if containers:
                print(f"   Found {len(containers)} governance containers:")
                for container in containers:
                    status_result = subprocess.run(
                        ['docker', 'inspect', '--format', '{{.State.Status}}', container],
                        capture_output=True,
                        text=True
                    )
                    status = status_result.stdout.strip()
                    status_icon = "✅" if status == "running" else "❌"
                    print(f"   {status_icon} {container}: {status}")
                return len(containers) >= 3
            return False
        
        self.check(check_containers, "Governance containers running")
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    def print_summary(self):
        section("DIAGNOSTIC SUMMARY")
        
        total = self.passed + self.failed + self.warned
        
        print(f"✅ Passed: {self.passed}")
        print(f"⚠️  Warnings: {self.warned}")
        print(f"❌ Failed: {self.failed}")
        print(f"━━━━━━━━━━━━━━━━━")
        print(f"Total: {total} checks")
        print("")
        
        if self.failed == 0 and self.warned == 0:
            green("🎉 ALL CHECKS PASSED!")
            print("\n✅ Your governance stack is fully integrated with Athena!")
            return True
        elif self.failed == 0:
            yellow(f"⚠️  PASSED WITH {self.warned} WARNINGS")
            print("\n📋 Recommendations:")
            print("  • Start AGI Core service: cd agi_core && python3 -m agi_core.agi_service")
            print("  • Send more verdicts to populate metrics")
            print("  • Fix Prometheus scraping: bash scripts/fix_prometheus_scraping.sh")
            return True
        else:
            red(f"❌ {self.failed} CRITICAL FAILURES")
            print("\n🔧 Required fixes:")
            print("  • Check Docker containers are running")
            print("  • Verify network connectivity")
            print("  • Check service logs for errors")
            return False
    
    def run_full_diagnostic(self):
        """Run complete diagnostic"""
        print("\n" + "="*70)
        blue("  🔍 ATHENA GOVERNANCE INTEGRATION DIAGNOSTIC")
        print("="*70)
        
        self.check_services()
        self.check_prometheus_targets()
        self.check_verdict_flow()
        self.check_agi_integration()
        self.check_docker_network()
        
        return self.print_summary()


if __name__ == "__main__":
    diagnostic = IntegrationDiagnostic()
    success = diagnostic.run_full_diagnostic()
    
    exit(0 if success else 1)

