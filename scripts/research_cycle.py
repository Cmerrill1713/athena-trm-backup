#!/usr/bin/env python3
"""
Research Cycle Runner - Scheduled autonomous research execution
===============================================================
Runs as part of nightly evolution to discover and implement papers
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from research_orchestrator import get_research_orchestrator, get_research_hunter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Run the research cycle"""

    logger.info("=" * 80)
    logger.info("🔬 AUTONOMOUS RESEARCH CYCLE STARTING")
    logger.info("=" * 80)

    orchestrator = get_research_orchestrator()

    try:
        # Run complete cycle
        results = await orchestrator.run_daily_cycle()

        # Save results
        output_dir = Path(__file__).parent.parent / "state" / "research"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"cycle_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"💾 Results saved to: {output_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("📊 RESEARCH CYCLE SUMMARY")
        print("=" * 80)
        print(f"Papers Discovered: {results['papers_discovered']}")
        print(f"Papers Analyzed: {results['papers_analyzed']}")
        print(f"Implementations Queued: {results['implementations_queued']}")
        print(f"Implementations Completed: {results['implementations_completed']}")
        print(f"Duration: {results['duration_seconds']:.2f}s")
        print("=" * 80)

        # Print top papers
        if results['papers_discovered'] > 0:
            print("\n📚 TOP PAPERS:")
            hunter = get_research_hunter()
            top_papers = await hunter.get_top_papers(limit=5)

            for i, paper in enumerate(top_papers, 1):
                print(f"\n{i}. {paper.title}")
                print(f"   Score: {paper.relevance_score:.2f}")
                print(f"   URL: {paper.url}")
                print(f"   Algorithms: {', '.join(paper.algorithms or ['Not yet extracted'])}")

        # Print implementation results
        if results['implementations_completed'] > 0:
            print("\n🔨 IMPLEMENTATION RESULTS:")
            for impl in results['results']:
                status_icon = "✅" if impl['status'] == "completed" else "❌"
                print(f"\n{status_icon} {impl['paper_title']}")
                print(f"   Status: {impl['status']}")
                if impl.get('test_results'):
                    tr = impl['test_results']
                    print(f"   Tests: {tr.get('passed', 0)}/{tr.get('total', 0)} passed")

        print("\n" + "=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Research cycle failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
