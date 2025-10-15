#!/usr/bin/env python3
"""
Automated Capability Assessment Runner

Runs comprehensive capability assessment prompts through Athena
and saves results for analysis and roadmap generation.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any
from capability_assessment_prompts import (
    CAPABILITY_DISCOVERY_PROMPT,
    DEPENDENCY_MAPPING_PROMPT,
    EVOLUTION_ROADMAP_PROMPT
)

# Configuration
BRIDGE_URL = "http://127.0.0.1:8014"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer supersecret"  # Default token
}

class AthenaCapabilityAssessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.results = {}

    def wait_for_service(self, max_attempts: int = 30) -> bool:
        """Wait for Athena/Bridge to be ready."""
        print("🔄 Waiting for services to be ready...")

        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{BRIDGE_URL}/health")
                if response.status_code == 200:
                    print("✅ Services ready!")
                    return True
            except requests.exceptions.RequestException:
                pass

            print(f"   Attempt {attempt + 1}/{max_attempts} - waiting...")
            time.sleep(2)

        print("❌ Services failed to start within timeout")
        return False

    def run_prompt(self, prompt: str, name: str) -> Dict[str, Any]:
        """Run a single prompt through Athena."""
        print(f"\n🧠 Running {name}...")

        payload = {
            "message": prompt,
            "stream": False
        }

        try:
            start_time = time.time()
            response = self.session.post(f"{BRIDGE_URL}/api/chat", json=payload, timeout=120)
            response_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                result['response_time'] = response_time
                result['timestamp'] = datetime.now().isoformat()
                result['prompt_name'] = name

                reply = result.get('response', '')
                print(f"   Response time: {response_time:.2f}s")
                print(f"   Response: {reply[:200]}...")

                return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                print(f"❌ Failed: {error_msg}")
                return {
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat(),
                    'prompt_name': name
                }

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"❌ Error: {error_msg}")
            return {
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'prompt_name': name
            }

    def run_all_assessments(self) -> Dict[str, Any]:
        """Run all capability assessment prompts."""
        assessments = [
            ("capability_discovery", CAPABILITY_DISCOVERY_PROMPT),
            ("dependency_mapping", DEPENDENCY_MAPPING_PROMPT),
            ("evolution_roadmap", EVOLUTION_ROADMAP_PROMPT)
        ]

        results = {
            'assessment_timestamp': datetime.now().isoformat(),
            'assessments': {}
        }

        for name, prompt in assessments:
            result = self.run_prompt(prompt, name)
            results['assessments'][name] = result

        return results

    def save_results(self, results: Dict[str, Any], output_dir: str = "docs/assessments/results"):
        """Save assessment results to files."""
        os.makedirs(output_dir, exist_ok=True)

        # Save complete results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_results_file = f"{output_dir}/capability_assessment_{timestamp}.json"

        with open(full_results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Saved full results to: {full_results_file}")

        # Save individual assessment summaries
        for name, result in results['assessments'].items():
            summary_file = f"{output_dir}/{name}_summary_{timestamp}.md"

            with open(summary_file, 'w') as f:
                f.write(f"# {name.replace('_', ' ').title()} Assessment\n\n")
                f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")

                if 'error' in result:
                    f.write(f"## Error\n\n{result['error']}\n")
                else:
                    f.write(f"**Response Time:** {result.get('response_time', 0):.2f}s\n\n")
                    f.write(f"**Latency:** {result.get('latency_ms', 0)}ms\n\n")

                    # Extract response content
                    response = result.get('response', '')
                    metadata = result.get('metadata', {})

                    f.write("## Response\n\n")
                    f.write(response)
                    f.write("\n\n## Metadata\n\n")
                    f.write(f"- Route: {metadata.get('route', 'N/A')}\n")
                    f.write(f"- Agent: {metadata.get('agent', 'N/A')}\n")
                    f.write(f"- Model: {metadata.get('model', 'N/A')}\n")
                    f.write(f"- Eval Enabled: {metadata.get('eval_enabled', 'N/A')}\n")

                    if metadata.get('eval_scores'):
                        scores = metadata['eval_scores']
                        f.write(f"- Helpfulness: {scores.get('helpfulness', 'N/A')}\n")
                        f.write(f"- Factuality: {scores.get('factuality', 'N/A')}\n")
                        f.write(f"- Clarity: {scores.get('clarity', 'N/A')}\n")

            print(f"💾 Saved {name} summary to: {summary_file}")

        return full_results_file

def main():
    """Run the complete capability assessment."""
    print("🧠 Athena Capability Self-Assessment")
    print("=" * 50)

    assessor = AthenaCapabilityAssessor()

    # Wait for services
    if not assessor.wait_for_service():
        sys.exit(1)

    # Run assessments
    print("\n🚀 Starting capability assessments...")
    results = assessor.run_all_assessments()

    # Save results
    results_file = assessor.save_results(results)

    print("\n🎉 Assessment complete!")
    print(f"📊 Results saved to: {results_file}")

    # Print summary
    print("\n📋 Summary:")
    for name, result in results['assessments'].items():
        status = "❌ Failed" if 'error' in result else f"✅ {result.get('response_time', 0):.1f}s"
        print(f"   {name.replace('_', ' ').title()}: {status}")

    print("\n💡 Next steps:")
    print("   1. Review the assessment results in docs/assessments/results/")
    print("   2. Analyze gaps and prioritize next implementations")
    print("   3. Use evolution roadmap for development planning")

if __name__ == "__main__":
    main()
