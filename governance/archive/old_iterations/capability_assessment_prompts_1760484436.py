#!/usr/bin/env python3
"""
Capability Assessment & Dependency Mapping Prompts for Athena

These prompts make Athena self-analyze its intelligence level and identify
architectural dependencies for the next phase of autonomous evolution.
"""

# Main capability discovery prompt
CAPABILITY_DISCOVERY_PROMPT = """
🧠 Prompt to Athena: Capability Discovery & Gap Check

"List and describe all current self-learning, self-evaluation, and autonomous optimization capabilities active in this stack. Include:
    •   Active evaluation systems (LLM judge, feedback channels, scoring methods, etc.)
    •   Learning signal routing (bandit system, weighting logic, reward shaping)
    •   Optimization loops (auto-promotion/rollback, reranker tuning, nightly reporting)
    •   Governance and safety mechanisms (feature flags, rollback paths, thresholds)
    •   Telemetry and alerting (Prometheus metrics, Grafana dashboards, alerts)

Then, identify gaps or missing layers that would make the system fully autonomous end-to-end — especially in:
    •   Personalization and user-adaptive behavior
    •   Knowledge/RAG optimization
    •   Meta-learning or multi-agent orchestration
    •   Cross-deployment knowledge sharing

For each gap, recommend one high-leverage next step to close it."
"""

# Dependency mapping prompt
DEPENDENCY_MAPPING_PROMPT = """
🔗 Prompt to Athena: System Dependency Analysis & Upgrade Path Planning

"Analyze this entire platform as a dependency graph. For each major subsystem, identify:

1. **Input Dependencies**: What signals/data does this subsystem require to function?
2. **Output Signals**: What does this subsystem produce that feeds other systems?
3. **Critical Path Dependencies**: Which subsystems must be working for this one to be useful?
4. **Failure Impact**: What breaks if this subsystem fails?
5. **Upgrade Choke Points**: What single changes would unlock the most capability?

Map out these relationships for:
- Athena (core LLM + judge)
- Bandit System (prompt optimization)
- Auto-Promotion Engine
- Feedback Collection (Bridge)
- Evaluation System (LLM judge)
- Telemetry Stack (Prometheus/Grafana)
- Knowledge/RAG System
- Multi-Agent Orchestration

Then, identify the 3 most leveraged upgrade paths based on dependency analysis, prioritizing changes that:
- Unblock the most downstream capabilities
- Create the most positive feedback loops
- Have the lowest implementation risk"
"""

# Evolution roadmap prompt
EVOLUTION_ROADMAP_PROMPT = """
🚀 Prompt to Athena: Autonomous Evolution Roadmap

"Based on current capabilities and dependency analysis, design a 3-month evolution roadmap that transforms this platform from 'learning-enabled' to 'fully autonomous self-improving AI.'

Phase 1 (Month 1): Foundation Strengthening
- What immediate gaps need closing for reliable autonomy?
- Which feedback loops need completion?

Phase 2 (Month 2): Advanced Learning
- How to implement user personalization?
- What meta-learning capabilities to add?

Phase 3 (Month 3): Multi-Agent Intelligence
- How to evolve toward multi-agent orchestration?
- What cross-deployment learning to implement?

For each phase, specify:
- Prerequisites (what must work first)
- Key deliverables (concrete capabilities)
- Success metrics (how to measure progress)
- Risk mitigation (rollback plans)

Focus on evolutionary steps that build upon existing strengths rather than requiring complete rewrites."
"""

def save_prompts_to_file():
    """Save all prompts to markdown files for easy reference."""

    prompts = [
        ("capability_discovery.md", CAPABILITY_DISCOVERY_PROMPT),
        ("dependency_mapping.md", DEPENDENCY_MAPPING_PROMPT),
        ("evolution_roadmap.md", EVOLUTION_ROADMAP_PROMPT)
    ]

    for filename, content in prompts:
        filepath = f"docs/assessments/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            f.write(content)

        print(f"✅ Saved {filename}")

if __name__ == "__main__":
    import os

    print("🤖 Athena Capability Assessment Prompts")
    print("=" * 50)

    print("\n1. CAPABILITY DISCOVERY PROMPT")
    print("-" * 30)
    print(CAPABILITY_DISCOVERY_PROMPT.strip())

    print("\n2. DEPENDENCY MAPPING PROMPT")
    print("-" * 30)
    print(DEPENDENCY_MAPPING_PROMPT.strip())

    print("\n3. EVOLUTION ROADMAP PROMPT")
    print("-" * 30)
    print(EVOLUTION_ROADMAP_PROMPT.strip())

    print("\n💾 Saving prompts to docs/assessments/...")
    save_prompts_to_file()

    print("\n🎯 Ready to run through Athena!")
    print("   make enterprise-up  # if not already running")
    print("   curl -X POST http://127.0.0.1:8014/api/chat -d '{\"message\":\"[paste prompt here]\"}'")
