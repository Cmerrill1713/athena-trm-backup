#!/usr/bin/env python3
"""
Self-Learning Capability Gap Analysis
========================================

This script processes the output of a self-learning audit and identifies gaps
in the system's autonomous learning capabilities.

Usage:
    python3 scripts/self_learning_gap_analysis.py <audit_output_file>

Or pipe audit results:
    echo "audit results here" | python3 scripts/self_learning_gap_analysis.py

The script will output:
1. Summary of implemented capabilities
2. Identified gaps with priority scores
3. Specific implementation recommendations
4. Action plan for closing gaps
"""

import sys
import re
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class LearningCapability:
    name: str
    learning_method: str
    triggers: List[str]
    scope: str
    governance_constraints: List[str]
    autonomy_level: str
    pipeline_location: str

@dataclass
class GapAnalysis:
    gap_id: str
    description: str
    priority: int  # 1-10 scale
    missing_capabilities: List[str]
    implementation_complexity: str
    expected_impact: str
    prerequisites: List[str]

class SelfLearningGapAnalyzer:
    def __init__(self):
        self.implemented_capabilities: List[LearningCapability] = []
        self.confidence_score = 0

        # Define the complete self-learning topology that should exist
        self.required_capabilities = self._define_required_capabilities()

    def _define_required_capabilities(self) -> Dict[str, Dict]:
        """Define the complete set of self-learning capabilities that should exist."""
        return {
            # Core optimization learning
            "neural_context_encoder": {
                "description": "Neural network for query intent and context analysis",
                "learning_methods": ["gradient_descent", "backpropagation"],
                "pipeline_locations": ["routing", "context_analysis"],
                "required_triggers": ["new_queries", "performance_feedback", "federated_updates"],
                "required_scope": ["local", "federated"],
                "governance_constraints": ["privacy_budget", "bias_limits", "drift_detection"],
                "autonomy_level": "full_auto"
            },
            "hierarchical_bandit": {
                "description": "Multi-level bandit for strategy and variant selection",
                "learning_methods": ["thompson_sampling", "beta_priors", "exponential_decay"],
                "pipeline_locations": ["routing", "strategy_selection"],
                "required_triggers": ["reward_signals", "user_feedback", "performance_metrics"],
                "required_scope": ["local"],
                "governance_constraints": ["exploration_floor", "variant_limits", "rollback_safety"],
                "autonomy_level": "full_auto"
            },
            "reward_shaper": {
                "description": "Adaptive reward signal blending and calibration",
                "learning_methods": ["drift_correction", "confidence_weighting", "z_score_normalization"],
                "pipeline_locations": ["feedback_processing", "signal_calibration"],
                "required_triggers": ["judge_drift", "feedback_patterns", "quality_metrics"],
                "required_scope": ["local", "federated"],
                "governance_constraints": ["signal_integrity", "bias_detection"],
                "autonomy_level": "semi_auto"
            },
            "rag_reranker": {
                "description": "Adaptive document reranking with threshold tuning",
                "learning_methods": ["grid_search", "statistical_optimization", "nightly_tuning"],
                "pipeline_locations": ["retrieval", "reranking"],
                "required_triggers": ["performance_data", "hourly_schedule", "quality_drift"],
                "required_scope": ["local"],
                "governance_constraints": ["overfilter_protection", "min_docs_guarantee"],
                "autonomy_level": "full_auto"
            },
            "personalization_engine": {
                "description": "User-adaptive retrieval and tone optimization",
                "learning_methods": ["rolling_histograms", "preference_learning", "decay_based"],
                "pipeline_locations": ["personalization", "tone_adjustment"],
                "required_triggers": ["user_feedback", "acceptance_signals", "preference_patterns"],
                "required_scope": ["local"],
                "governance_constraints": ["privacy_limits", "opt_out_respect", "ttl_enforcement"],
                "autonomy_level": "full_auto"
            },

            # Federated and distributed learning
            "federated_context_encoder": {
                "description": "Privacy-preserving neural model training across deployments",
                "learning_methods": ["fedavg", "differential_privacy", "secure_aggregation"],
                "pipeline_locations": ["context_analysis", "model_training"],
                "required_triggers": ["round_completion", "privacy_budget_available", "performance_uplift"],
                "required_scope": ["federated"],
                "governance_constraints": ["epsilon_budget", "reputation_weighting", "secure_channels"],
                "autonomy_level": "semi_auto"
            },
            "adaptive_federated_scheduling": {
                "description": "Economic optimization of federated participation",
                "learning_methods": ["cost_benefit_analysis", "uplift_prediction", "budget_optimization"],
                "pipeline_locations": ["federation_scheduling", "privacy_management"],
                "required_triggers": ["round_opportunities", "performance_history", "privacy_costs"],
                "required_scope": ["local"],
                "governance_constraints": ["privacy_economics", "performance_guarantees"],
                "autonomy_level": "full_auto"
            },

            # Evolutionary and generative learning
            "automated_strategy_generation": {
                "description": "Evolutionary algorithm for creating new optimization strategies",
                "learning_methods": ["genetic_algorithm", "meta_learning", "fitness_evaluation"],
                "pipeline_locations": ["strategy_creation", "optimization_innovation"],
                "required_triggers": ["performance_patterns", "historical_data", "evolutionary_pressure"],
                "required_scope": ["local"],
                "governance_constraints": ["constitutional_screening", "safety_validation", "deployment_limits"],
                "autonomy_level": "semi_auto"
            },
            "constitutional_weighting": {
                "description": "Adaptive governance priority adjustment based on system state",
                "learning_methods": ["state_detection", "weight_optimization", "performance_feedback"],
                "pipeline_locations": ["governance", "policy_adaptation"],
                "required_triggers": ["system_state_changes", "performance_metrics", "violation_patterns"],
                "required_scope": ["local"],
                "governance_constraints": ["meta_governance", "stability_limits", "human_override"],
                "autonomy_level": "semi_auto"
            },

            # Missing capabilities that should be added
            "retrieval_filter_learning": {
                "description": "Adaptive filtering of retrieved documents based on quality patterns",
                "learning_methods": ["quality_prediction", "filter_optimization", "feedback_loops"],
                "pipeline_locations": ["retrieval", "filtering"],
                "required_triggers": ["retrieval_quality", "user_satisfaction", "performance_data"],
                "required_scope": ["local", "federated"],
                "governance_constraints": ["overfilter_protection", "diversity_guarantees"],
                "autonomy_level": "full_auto"
            },
            "latency_adaptive_routing": {
                "description": "Dynamic routing based on predicted latency vs quality tradeoffs",
                "learning_methods": ["latency_prediction", "tradeoff_optimization", "real_time_adjustment"],
                "pipeline_locations": ["routing", "latency_management"],
                "required_triggers": ["latency_measurements", "quality_requirements", "system_load"],
                "required_scope": ["local"],
                "governance_constraints": ["latency_slas", "quality_floors"],
                "autonomy_level": "full_auto"
            },
            "governance_drift_detection": {
                "description": "Automatic detection and correction of governance policy drift",
                "learning_methods": ["anomaly_detection", "policy_validation", "drift_correction"],
                "pipeline_locations": ["governance", "policy_monitoring"],
                "required_triggers": ["policy_violations", "performance_changes", "system_behavior"],
                "required_scope": ["local"],
                "governance_constraints": ["meta_governance", "human_escalation"],
                "autonomy_level": "semi_auto"
            },
            "privacy_budget_optimization": {
                "description": "Dynamic optimization of differential privacy parameters",
                "learning_methods": ["budget_allocation", "utility_maximization", "privacy_utility_tradeoff"],
                "pipeline_locations": ["privacy_management", "federation"],
                "required_triggers": ["privacy_usage", "performance_needs", "federation_rounds"],
                "required_scope": ["local"],
                "governance_constraints": ["privacy_limits", "compliance_requirements"],
                "autonomy_level": "semi_auto"
            },
            "multi_modal_adaptation": {
                "description": "Adaptive handling of different content types and modalities",
                "learning_methods": ["modality_detection", "cross_modal_transfer", "type_specific_optimization"],
                "pipeline_locations": ["content_processing", "routing"],
                "required_triggers": ["content_patterns", "performance_by_type", "user_preferences"],
                "required_scope": ["local", "federated"],
                "governance_constraints": ["modality_safety", "content_filtering"],
                "autonomy_level": "full_auto"
            }
        }

    def parse_audit_output(self, audit_text: str) -> None:
        """Parse the audit output to extract implemented capabilities."""
        # Extract confidence score
        confidence_match = re.search(r'confidence score.*?(\d+)%', audit_text, re.IGNORECASE)
        if confidence_match:
            self.confidence_score = int(confidence_match.group(1))

        # Parse each capability
        capability_blocks = re.split(r'•\s*Name the mechanism:', audit_text)[1:]

        for block in capability_blocks:
            try:
                lines = [line.strip() for line in block.split('\n') if line.strip() and not line.startswith('•')]

                capability = LearningCapability(
                    name=self._extract_field(lines, "Name the mechanism"),
                    learning_method=self._extract_field(lines, "how it learns"),
                    triggers=self._extract_list_field(lines, "triggers adaptation"),
                    scope=self._extract_field(lines, "scope of impact"),
                    governance_constraints=self._extract_list_field(lines, "governance.*constraints"),
                    autonomy_level=self._extract_field(lines, "level of autonomy"),
                    pipeline_location=self._extract_field(lines, "pipeline.*applied")
                )

                if capability.name:
                    self.implemented_capabilities.append(capability)

            except Exception as e:
                print(f"Warning: Could not parse capability block: {e}")
                continue

    def _extract_field(self, lines: List[str], pattern: str) -> str:
        """Extract a field value from audit lines."""
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                # Extract everything after the pattern
                match = re.search(rf'.*{pattern}.*?[:\-]?\s*(.+)', line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return ""

    def _extract_list_field(self, lines: List[str], pattern: str) -> List[str]:
        """Extract a list field from audit lines."""
        result = []
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                # Extract and split on common separators
                match = re.search(rf'.*{pattern}.*?[:\-]?\s*(.+)', line, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Split on commas, semicolons, or 'and'
                    items = re.split(r'[;,]| and ', value)
                    result.extend([item.strip() for item in items if item.strip()])
        return result

    def analyze_gaps(self) -> List[GapAnalysis]:
        """Analyze gaps between implemented and required capabilities."""
        gaps = []
        implemented_names = {cap.name.lower() for cap in self.implemented_capabilities}

        for req_name, req_config in self.required_capabilities.items():
            if req_name not in implemented_names:
                # Check for partial matches or synonyms
                partial_match = any(req_name in cap.name.lower() or
                                  cap.name.lower() in req_name
                                  for cap in self.implemented_capabilities)

                if not partial_match:
                    gap = self._create_gap_analysis(req_name, req_config)
                    gaps.append(gap)

        return sorted(gaps, key=lambda x: x.priority, reverse=True)

    def _create_gap_analysis(self, gap_name: str, config: Dict) -> GapAnalysis:
        """Create a gap analysis entry for a missing capability."""
        complexity_map = {
            "retrieval_filter_learning": "medium",
            "latency_adaptive_routing": "low",
            "governance_drift_detection": "high",
            "privacy_budget_optimization": "high",
            "multi_modal_adaptation": "high"
        }

        priority_map = {
            "retrieval_filter_learning": 8,
            "latency_adaptive_routing": 7,
            "governance_drift_detection": 9,
            "privacy_budget_optimization": 6,
            "multi_modal_adaptation": 5
        }

        impact_map = {
            "retrieval_filter_learning": "High - Improved retrieval quality and reduced noise",
            "latency_adaptive_routing": "Medium - Better latency vs quality tradeoffs",
            "governance_drift_detection": "Critical - Prevents governance failures",
            "privacy_budget_optimization": "Medium - Better privacy-utility balance",
            "multi_modal_adaptation": "Low - Enhanced multi-modal handling"
        }

        return GapAnalysis(
            gap_id=gap_name,
            description=config["description"],
            priority=priority_map.get(gap_name, 5),
            missing_capabilities=[config["learning_methods"][0] if config["learning_methods"] else "unspecified"],
            implementation_complexity=complexity_map.get(gap_name, "medium"),
            expected_impact=impact_map.get(gap_name, "Medium impact on system performance"),
            prerequisites=config.get("prerequisites", [])
        )

    def generate_report(self) -> str:
        """Generate the complete gap analysis report."""
        report = []

        # Header
        report.append("=" * 80)
        report.append("SELF-LEARNING CAPABILITY GAP ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Implemented Capabilities: {len(self.implemented_capabilities)}")
        report.append(f"Identified Gaps: {len(self.analyze_gaps())}")
        report.append(f"Audit Confidence Score: {self.confidence_score}%")
        report.append("")

        # Implemented Capabilities
        report.append("✅ IMPLEMENTED CAPABILITIES")
        report.append("-" * 40)
        for cap in self.implemented_capabilities:
            report.append(f"• {cap.name}")
            report.append(f"  - Location: {cap.pipeline_location}")
            report.append(f"  - Scope: {cap.scope}")
            report.append(f"  - Autonomy: {cap.autonomy_level}")
            report.append("")

        # Gap Analysis
        gaps = self.analyze_gaps()
        report.append("❌ IDENTIFIED GAPS")
        report.append("-" * 40)

        for gap in gaps:
            report.append(f"🔴 PRIORITY {gap.priority}/10: {gap.gap_id}")
            report.append(f"   Description: {gap.description}")
            report.append(f"   Complexity: {gap.implementation_complexity}")
            report.append(f"   Expected Impact: {gap.expected_impact}")
            report.append("")

        # Action Plan
        report.append("🎯 ACTION PLAN")
        report.append("-" * 40)

        high_priority = [g for g in gaps if g.priority >= 8]
        medium_priority = [g for g in gaps if 5 <= g.priority < 8]
        low_priority = [g for g in gaps if g.priority < 5]

        if high_priority:
            report.append("🚨 HIGH PRIORITY (Immediate - Next Sprint):")
            for gap in high_priority:
                report.append(f"   • {gap.gap_id} - {gap.expected_impact}")
            report.append("")

        if medium_priority:
            report.append("⚠️ MEDIUM PRIORITY (Next Month):")
            for gap in medium_priority:
                report.append(f"   • {gap.gap_id} - {gap.expected_impact}")
            report.append("")

        if low_priority:
            report.append("📅 LOW PRIORITY (Future Enhancement):")
            for gap in low_priority:
                report.append(f"   • {gap.gap_id} - {gap.expected_impact}")
            report.append("")

        # Recommendations
        report.append("💡 IMPLEMENTATION RECOMMENDATIONS")
        report.append("-" * 40)
        report.append("1. Start with governance_drift_detection - highest safety impact")
        report.append("2. Add retrieval_filter_learning - direct quality improvement")
        report.append("3. Implement latency_adaptive_routing - performance optimization")
        report.append("4. Consider privacy_budget_optimization for compliance")
        report.append("5. Evaluate multi_modal_adaptation based on use cases")
        report.append("")
        report.append("Each implementation should include:")
        report.append("• Mathematical validation (like existing capabilities)")
        report.append("• Governance constraints and safety bounds")
        report.append("• Automated testing and rollback mechanisms")
        report.append("• Performance monitoring and alerting")

        return "\n".join(report)

def main():
    """Main entry point."""
    analyzer = SelfLearningGapAnalyzer()

    # Get input from file or stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            audit_output = f.read()
    else:
        audit_output = sys.stdin.read()

    # Parse and analyze
    analyzer.parse_audit_output(audit_output)
    gaps = analyzer.analyze_gaps()

    # Generate and print report
    report = analyzer.generate_report()
    print(report)

    # Exit with status based on gaps
    critical_gaps = len([g for g in gaps if g.priority >= 8])
    if critical_gaps > 0:
        print(f"\n⚠️  Found {critical_gaps} high-priority gaps requiring immediate attention")
        sys.exit(1)
    else:
        print("\n✅ No critical gaps identified - system learning capabilities are comprehensive")
        sys.exit(0)

if __name__ == "__main__":
    main()
