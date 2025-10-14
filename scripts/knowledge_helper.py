#!/usr/bin/env python3
"""
Knowledge System Helper
Integrates existing Weaviate knowledge base with Assistant Broker
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any, Optional

# Add scripts dir to path
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from broker_client import BrokerClient


class KnowledgeHelper:
    """Helper for querying existing knowledge system"""

    def __init__(
        self,
        knowledge_gateway: str = "http://localhost:8088",
        weaviate_url: str = "http://localhost:8090"
    ):
        self.knowledge_gateway = knowledge_gateway
        self.weaviate_url = weaviate_url
        self.broker = BrokerClient()

    def search(self, query: str, limit: int = 10, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search knowledge base via gateway"""
        payload = {
            "query": query,
            "limit": limit
        }
        if sources:
            payload["sources"] = sources

        try:
            resp = requests.post(
                f"{self.knowledge_gateway}/search",
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e), "results": []}

    def health_check(self) -> Dict[str, str]:
        """Check knowledge system health"""
        status = {}

        # Check Knowledge Gateway
        try:
            resp = requests.get(f"{self.knowledge_gateway}/health", timeout=5)
            status["knowledge_gateway"] = "✅ healthy" if resp.ok else "❌ unhealthy"
        except:
            status["knowledge_gateway"] = "❌ not running"

        # Check Weaviate
        try:
            resp = requests.get(f"{self.weaviate_url}/v1/.well-known/ready", timeout=5)
            status["weaviate"] = "✅ ready" if resp.ok else "❌ not ready"
        except:
            status["weaviate"] = "❌ not running"

        # Check Broker
        try:
            broker_status = self.broker.health()
            status["broker"] = "✅ operational" if broker_status.get("status") == "ok" else "❌ unhealthy"
        except:
            status["broker"] = "❌ not running"

        return status

    def save_search_results(self, query: str, results: List[Dict], filename: str = "search_results.json"):
        """Save search results to Desktop via broker"""

        output = {
            "query": query,
            "total_results": len(results),
            "results": results
        }

        desktop_path = f"/Users/{os.environ.get('USER', 'christianmerrill')}/Desktop/{filename}"

        self.broker.write_file(desktop_path, json.dumps(output, indent=2))
        self.broker.reveal_in_finder(desktop_path)

        return desktop_path


def search_and_deliver(query: str, limit: int = 5):
    """Quick helper: search knowledge and save to Desktop"""
    helper = KnowledgeHelper()

    # Check system health
    print("🩺 System Health:")
    for service, status in helper.health_check().items():
        print(f"   {service}: {status}")
    print()

    # Search
    print(f"🔍 Searching for: {query}")
    results = helper.search(query, limit=limit)

    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return

    print(f"✅ Found {len(results.get('results', []))} results")

    # Save and reveal
    saved_path = helper.save_search_results(query, results.get('results', []))
    print(f"📄 Results saved to: {saved_path}")


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        search_and_deliver(query)
    else:
        # Demo
        helper = KnowledgeHelper()
        status = helper.health_check()

        print("🧠 Knowledge System Status")
        print("==========================")
        for service, health in status.items():
            print(f"{service}: {health}")
