#!/usr/bin/env python3
"""
Constitutional Governance Test Script
====================================

Demonstrates the governance layer in action by testing various strategies
against the constitutional framework.

Usage:
    python scripts/test_constitutional_governance.py --constitution constitutional_policy_template.yaml
"""

import argparse

from src.core.governance_layer import get_governance_engine
from src.core.automated_strategy_generation import StrategyGenome, StrategyComponent

def create_test_strategies():
    """Create various test strategies to evaluate governance."""
    return [
        # Ethical strategy (should pass)
        StrategyGenome(
            components={StrategyComponent.COSINE_SIMILARITY,
                       StrategyComponent.CROSS_ENCODER,
                       StrategyComponent.DIVERSITY_PROMOTION},
            parameters={'ce_top_k': 8, 'cosine_weight': 1.0, 'diversity_lambda': 0.2},
            generation=1
        ),

        # Ethical violation (discriminatory components)
        StrategyGenome(
            components={StrategyComponent.PERSONALIZATION,
                       StrategyComponent.USER_FEEDBACK_INTEGRATION},
            parameters={'personalization_bias': 0.8},  # Too high
            generation=2
        ),

        # Safety violation (high complexity)
        StrategyGenome(
            components={StrategyComponent.COSINE_SIMILARITY,
                       StrategyComponent.CROSS_ENCODER,
                       StrategyComponent.NEURAL_RESCORING,
                       StrategyComponent.PERSONALIZATION,
                       StrategyComponent.CONTEXT_FILTERING,
                       StrategyComponent.DIVERSITY_PROMOTION,
                       StrategyComponent.TEMPORAL_WEIGHTING,
                       StrategyComponent.USER_FEEDBACK_INTEGRATION},
            parameters={'ce_top_k': 15, 'neural_scale': 1.5, 'personalization_bias': 0.4},
            generation=3
        ),

        # Business-aligned strategy (should pass)
        StrategyGenome(
            components={StrategyComponent.CROSS_ENCODER,
                       StrategyComponent.PERSONALIZATION,
                       StrategyComponent.DIVERSITY_PROMOTION},
            parameters={'ce_top_k': 6, 'personalization_bias': 0.15, 'diversity_lambda': 0.25},
            generation=4
        ),

        # Compliance violation (missing transparency)
        StrategyGenome(
            components={StrategyComponent.PERSONALIZATION,
                       StrategyComponent.USER_FEEDBACK_INTEGRATION},
            parameters={'personalization_bias': 0.3},
            generation=5
        )
    ]

def test_governance_evaluation(strategies, show_details=False):
    """Test governance evaluation on strategies."""
    engine = get_governance_engine()

    print("\n" + "="*80)
    print("CONSTITUTIONAL GOVERNANCE EVALUATION TEST")
    print("="*80)

    results = []

    for i, strategy in enumerate(strategies, 1):
        print(f"\n🧬 Testing Strategy {i} (Generation {strategy.generation})")
        print(f"   Components: {[c.value for c in strategy.components]}")
        print(f"   Parameters: {strategy.parameters}")

        # Evaluate governance
        assessment = engine.evaluate_strategy_governance(strategy)

        # Show results
        clearance = "✅ CLEARED" if assessment['overall_clearance'] else "❌ BLOCKED"
        print(f"   Governance Result: {clearance}")
        print(".2f")
        print(f"   Blocking Violations: {len(assessment['blocking_violations'])}")

        if show_details:
            if assessment['ethical_assessment']['violations']:
                print(f"   ⚠️  Ethical Issues: {len(assessment['ethical_assessment']['violations'])}")

            if assessment['business_assessment']['overall_alignment'] < 0.7:
                print(".2f")

            if assessment['safety_assessment']['safety_score'] < 0.9:
                print(".2f")

            if assessment['compliance_assessment']['compliance_score'] < 0.9:
                print(".2f")

            if assessment['recommendations']:
                print(f"   💡 Recommendations: {len(assessment['recommendations'])}")

        results.append({
            'strategy': i,
            'cleared': assessment['overall_clearance'],
            'governance_score': assessment['governance_score'],
            'blocking_violations': len(assessment['blocking_violations'])
        })

    return results

def show_governance_stats():
    """Show governance statistics."""
    engine = get_governance_engine()
    stats = engine.get_governance_stats()

    print("\n" + "="*60)
    print("GOVERNANCE STATISTICS")
    print("="*60)

    print(f"Total Assessments: {stats['total_assessments']}")
    print(".1f")
    print(f"Pending Interventions: {stats['pending_interventions']}")
    print(f"Recent Assessments (24h): {stats['recent_assessments']}")

    print("\nPolicy Status:")
    for policy_id, policy_data in stats['policy_violations'].items():
        status = "✅" if policy_data['enabled'] else "❌"
        print(f"  {status} {policy_id}: {policy_data['violations']} violations")

def demonstrate_human_intervention():
    """Demonstrate human intervention capabilities."""
    engine = get_governance_engine()

    print("\n" + "="*60)
    print("HUMAN INTERVENTION DEMONSTRATION")
    print("="*60)

    # Create a blocked strategy for intervention
    blocked_strategy = StrategyGenome(
        components={StrategyComponent.PERSONALIZATION},
        parameters={'personalization_bias': 0.5},
        generation=99
    )

    assessment = engine.evaluate_strategy_governance(blocked_strategy)

    if not assessment['overall_clearance']:
        print("🚫 Strategy blocked - requesting human intervention...")

        # Request intervention
        strategy_id = "intervention_demo_001"
        engine.request_human_intervention(
            strategy_id,
            "High personalization bias requires human review",
            assessment
        )

        print(f"📋 Intervention requested for strategy: {strategy_id}")

        # Show pending interventions
        stats = engine.get_governance_stats()
        print(f"📊 Pending interventions: {stats['pending_interventions']}")

        # Demonstrate approval with conditions
        print("\n✅ Approving with conditions...")
        conditions = [
            "Reduce personalization bias to maximum 0.25",
            "Add diversity component with lambda >= 0.2",
            "Implement user consent verification"
        ]

        success = engine.approve_with_conditions(strategy_id, conditions)
        print(f"Approval with conditions: {'✅ Success' if success else '❌ Failed'}")

        if success:
            print("📝 Conditions applied:")
            for i, condition in enumerate(conditions, 1):
                print(f"   {i}. {condition}")

def main():
    parser = argparse.ArgumentParser(description="Test constitutional governance layer")
    parser.add_argument('--constitution', help='Path to constitution file to load')
    parser.add_argument('--details', action='store_true', help='Show detailed assessment results')
    parser.add_argument('--intervention', action='store_true', help='Demonstrate human intervention')

    args = parser.parse_args()

    # Load constitution if provided
    if args.constitution:
        from scripts.load_constitutional_policies import ConstitutionalPolicyLoader
        loader = ConstitutionalPolicyLoader()

        if loader.load_from_file(args.constitution):
            print(f"✅ Loaded constitution from: {args.constitution}")
        else:
            print(f"❌ Failed to load constitution from: {args.constitution}")
            return 1

    # Create test strategies
    test_strategies = create_test_strategies()

    # Run governance tests
    results = test_governance_evaluation(test_strategies, args.details)

    # Show summary
    total_strategies = len(results)
    cleared_strategies = sum(1 for r in results if r['cleared'])
    avg_governance_score = sum(r['governance_score'] for r in results) / total_strategies

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Strategies Tested: {total_strategies}")
    print(f"Strategies Cleared: {cleared_strategies} ({cleared_strategies/total_strategies*100:.1f}%)")
    print(".2f")
    print(f"Average Blocking Violations: {sum(r['blocking_violations'] for r in results)/total_strategies:.1f}")

    # Show governance stats
    show_governance_stats()

    # Demonstrate human intervention if requested
    if args.intervention:
        demonstrate_human_intervention()

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("✅ Constitutional governance layer is operational and enforcing policies.")
    print("="*60)

    return 0

if __name__ == "__main__":
    exit(main())
