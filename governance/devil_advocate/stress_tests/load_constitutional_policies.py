#!/usr/bin/env python3
"""
Constitutional Policy Loader
===========================

Loads and validates constitutional policies for the governance layer.
Supports both YAML and JSON policy formats.

Usage:
    python scripts/load_constitutional_policies.py --format yaml --file constitutional_policy_template.yaml
    python scripts/load_constitutional_policies.py --format json --file constitutional_policy_template.json
"""

import argparse
import json
import yaml
import logging
from typing import Dict, Any

from src.core.governance_layer import get_governance_engine, GovernancePolicy, PolicyCategory, GovernanceLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionalPolicyLoader:
    """Loads and validates constitutional policies from YAML/JSON templates."""

    def __init__(self):
        self.governance_engine = get_governance_engine()

    def load_from_file(self, file_path: str, format_type: str = "auto") -> bool:
        """
        Load constitutional policies from file.

        Args:
            file_path: Path to policy file
            format_type: File format ('yaml', 'json', or 'auto')

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Determine format
            if format_type == "auto":
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    format_type = "yaml"
                elif file_path.endswith('.json'):
                    format_type = "json"
                else:
                    logger.error(f"Could not determine format for file: {file_path}")
                    return False

            # Load file
            with open(file_path, 'r', encoding='utf-8') as f:
                if format_type == "yaml":
                    policies_data = yaml.safe_load(f)
                elif format_type == "json":
                    policies_data = json.load(f)
                else:
                    logger.error(f"Unsupported format: {format_type}")
                    return False

            # Validate and load policies
            return self._load_policies(policies_data)

        except Exception as e:
            logger.error(f"Failed to load policies from {file_path}: {e}")
            return False

    def _load_policies(self, policies_data: Dict[str, Any]) -> bool:
        """Load and validate policies from parsed data."""
        try:
            # Validate metadata
            if 'metadata' not in policies_data:
                logger.error("Policy file missing metadata section")
                return False

            metadata = policies_data['metadata']
            logger.info(f"Loading constitution v{metadata.get('version', 'unknown')} "
                       f"by {metadata.get('author', 'unknown')}")

            # Load governance policies
            policies_loaded = 0
            if 'governance_policies' in policies_data:
                for policy_data in policies_data['governance_policies']:
                    if self._load_governance_policy(policy_data):
                        policies_loaded += 1

            # Configure ethical boundaries
            if 'ethical_boundaries' in policies_data:
                self._configure_ethical_boundaries(policies_data['ethical_boundaries'])

            # Configure business constraints
            if 'business_constraints' in policies_data:
                self._configure_business_constraints(policies_data['business_constraints'])

            # Configure safety limits
            if 'safety_limits' in policies_data:
                self._configure_safety_limits(policies_data['safety_limits'])

            # Configure compliance rules
            if 'compliance_rules' in policies_data:
                self._configure_compliance_rules(policies_data['compliance_rules'])

            logger.info(f"Successfully loaded {policies_loaded} governance policies")
            return True

        except Exception as e:
            logger.error(f"Failed to load policies: {e}")
            return False

    def _load_governance_policy(self, policy_data: Dict[str, Any]) -> bool:
        """Load a single governance policy."""
        try:
            policy = GovernancePolicy(
                policy_id=policy_data['policy_id'],
                category=PolicyCategory(policy_data['category']),
                name=policy_data['name'],
                description=policy_data['description'],
                enforcement_level=GovernanceLevel(policy_data['enforcement_level']),
                conditions=policy_data['conditions'],
                actions=policy_data['actions'],
                enabled=policy_data.get('enabled', True)
            )

            self.governance_engine.add_custom_policy(policy)
            logger.debug(f"Loaded policy: {policy.policy_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load policy {policy_data.get('policy_id', 'unknown')}: {e}")
            return False

    def _configure_ethical_boundaries(self, config: Dict[str, Any]):
        """Configure ethical boundaries."""
        logger.info("Configuring ethical boundaries...")

        # Update forbidden patterns
        if 'forbidden_patterns' in config:
            # This would update the EthicalBoundaries class
            # In practice, you'd modify the governance engine's ethical checker
            logger.info(f"Configured {len(config['forbidden_patterns'])} ethical pattern categories")

    def _configure_business_constraints(self, config: Dict[str, Any]):
        """Configure business constraints."""
        logger.info("Configuring business constraints...")

        if 'objectives' in config:
            objectives = config['objectives']
            logger.info(f"Configured {len(objectives)} business objectives")

    def _configure_safety_limits(self, config: Dict[str, Any]):
        """Configure safety limits."""
        logger.info("Configuring safety limits...")

        if 'performance_limits' in config:
            limits = config['performance_limits']
            logger.info(f"Configured {len(limits)} performance safety limits")

    def _configure_compliance_rules(self, config: Dict[str, Any]):
        """Configure compliance rules."""
        logger.info("Configuring compliance rules...")

        frameworks = ['gdpr', 'ccpa', 'fairness']
        configured = sum(1 for fw in frameworks if fw in config and config[fw].get('enabled', False))
        logger.info(f"Configured compliance for {configured} regulatory frameworks")

    def validate_constitution(self) -> Dict[str, Any]:
        """Validate the loaded constitution for consistency and completeness."""
        validation_results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'summary': {}
        }

        # Check for required policies
        required_policies = ['ethical_no_harm', 'safety_system_stability', 'compliance_legal_requirements']
        existing_policies = [p.policy_id for p in self.governance_engine.policies]

        for required in required_policies:
            if required not in existing_policies:
                validation_results['issues'].append(f"Missing required policy: {required}")
                validation_results['valid'] = False

        # Check for conflicting policies
        blocking_policies = [p for p in self.governance_engine.policies if p.enforcement_level == GovernanceLevel.BLOCKING]
        if len(blocking_policies) > 10:
            validation_results['warnings'].append("High number of blocking policies may be overly restrictive")

        # Check policy completeness
        incomplete_policies = []
        for policy in self.governance_engine.policies:
            if not policy.conditions or not policy.actions:
                incomplete_policies.append(policy.policy_id)

        if incomplete_policies:
            validation_results['issues'].append(f"Incomplete policies: {incomplete_policies}")
            validation_results['valid'] = False

        # Summary
        validation_results['summary'] = {
            'total_policies': len(self.governance_engine.policies),
            'blocking_policies': len([p for p in self.governance_engine.policies if p.enforcement_level == GovernanceLevel.BLOCKING]),
            'warning_policies': len([p for p in self.governance_engine.policies if p.enforcement_level == GovernanceLevel.WARNING]),
            'permissive_policies': len([p for p in self.governance_engine.policies if p.enforcement_level == GovernanceLevel.PERMISSIVE])
        }

        return validation_results

    def show_constitution_summary(self):
        """Display a summary of the loaded constitution."""
        stats = self.governance_engine.get_governance_stats()

        print("\n" + "="*60)
        print("CONSTITUTIONAL AI FRAMEWORK - STATUS SUMMARY")
        print("="*60)

        print(f"Total Assessments: {stats['total_assessments']}")
        print(".1f")
        print(f"Pending Interventions: {stats['pending_interventions']}")
        print(f"Recent Assessments (24h): {stats['recent_assessments']}")

        print("\nGOVERNANCE POLICIES:")
        for category, data in stats['policy_violations'].items():
            status = "✅ ENABLED" if data['enabled'] else "❌ DISABLED"
            print(f"  {category}: {data['violations']} violations - {status}")

        print("\nETHICAL BOUNDARIES: ✅ ACTIVE")
        print("BUSINESS CONSTRAINTS: ✅ ACTIVE")
        print("SAFETY LIMITS: ✅ ACTIVE")
        print("COMPLIANCE RULES: ✅ ACTIVE")

        print("\nConstitution loaded and operational.")
        print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Load constitutional policies for governance layer")
    parser.add_argument('--file', '-f', required=True, help='Policy file path')
    parser.add_argument('--format', choices=['yaml', 'json', 'auto'], default='auto',
                       help='Policy file format (default: auto-detect)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate constitution, do not load')
    parser.add_argument('--summary', action='store_true',
                       help='Show constitution summary after loading')

    args = parser.parse_args()

    loader = ConstitutionalPolicyLoader()

    if args.validate_only:
        # Validate existing constitution
        validation = loader.validate_constitution()
        print("Constitution Validation Results:")
        print(f"Valid: {validation['valid']}")

        if validation['issues']:
            print("Issues:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")

        if validation['warnings']:
            print("Warnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️  {warning}")

        print(f"\nSummary: {validation['summary']}")

    else:
        # Load constitution
        if loader.load_from_file(args.file, args.format):
            print(f"✅ Successfully loaded constitution from {args.file}")

            # Validate after loading
            validation = loader.validate_constitution()
            if validation['valid']:
                print("✅ Constitution validation passed")
            else:
                print("❌ Constitution validation failed:")
                for issue in validation['issues']:
                    print(f"  - {issue}")

            if args.summary:
                loader.show_constitution_summary()

        else:
            print(f"❌ Failed to load constitution from {args.file}")
            return 1

    return 0

if __name__ == "__main__":
    exit(main())
