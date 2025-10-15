#!/usr/bin/env python3
"""
Multi-Environment Promotion Chain Manager

Manages progressive deployment across environments:
dev → staging → production

Each environment has its own governance thresholds, window sizes, and requirements.
Successful canaries in lower environments automatically queue for promotion to next env.

Usage:
  python3 scripts/gov_promotion_chain.py --check-promotion --from-env staging --to-env production
  python3 scripts/gov_promotion_chain.py --promote --from-env staging --to-env production --version v1.2.3
"""
import os, sys, json, time, yaml
from pathlib import Path

# Environment promotion order
PROMOTION_CHAIN = ["development", "staging", "production"]

def load_env_policy(environment):
    """Load environment-specific governance policy"""
    policy_file = f"policy/bundles/{environment[:4] if environment == 'development' else environment[:4]}.yaml"

    # Map environment names to file names
    env_map = {
        "development": "dev",
        "staging": "staging",
        "production": "prod"
    }

    policy_file = f"policy/bundles/{env_map.get(environment, environment)}.yaml"

    try:
        with open(policy_file, "r") as f:
            policy = yaml.safe_load(f)
        return policy
    except FileNotFoundError:
        print(f"❌ Policy not found for environment: {environment}")
        return None

def get_env_canary_results(environment, version):
    """Get canary results for specific environment and version"""
    # Query governance state for environment-specific results
    state_file = f"state/canary_results_{environment}.json"

    try:
        with open(state_file, "r") as f:
            results = json.load(f)
            return results.get(version, {})
    except FileNotFoundError:
        return {}

def check_promotion_eligibility(from_env, to_env, version):
    """Check if a version is eligible for promotion between environments"""

    # Validate promotion chain
    if from_env not in PROMOTION_CHAIN or to_env not in PROMOTION_CHAIN:
        return {
            "eligible": False,
            "reason": f"Invalid environment: {from_env} → {to_env}"
        }

    from_idx = PROMOTION_CHAIN.index(from_env)
    to_idx = PROMOTION_CHAIN.index(to_env)

    if to_idx != from_idx + 1:
        return {
            "eligible": False,
            "reason": f"Invalid promotion path: must go {from_env} → {PROMOTION_CHAIN[from_idx + 1]}"
        }

    # Load policies
    from_policy = load_env_policy(from_env)
    to_policy = load_env_policy(to_env)

    if not from_policy or not to_policy:
        return {
            "eligible": False,
            "reason": "Could not load environment policies"
        }

    # Check source environment canary results
    canary_results = get_env_canary_results(from_env, version)

    if not canary_results:
        return {
            "eligible": False,
            "reason": f"No successful canary in {from_env} for version {version}"
        }

    # Verify all promotion requirements met
    requirements_met = canary_results.get("promotion_requirements_met", False)

    if not requirements_met:
        return {
            "eligible": False,
            "reason": f"Promotion requirements not met in {from_env}",
            "canary_results": canary_results
        }

    # Check if target environment policy is stricter
    from_reqs = from_policy.get("promote_requirements", {})
    to_reqs = to_policy.get("promote_requirements", {})

    warnings = []
    if to_reqs.get("ece_post_le", 1.0) < from_reqs.get("ece_post_le", 1.0):
        warnings.append(f"Target ECE threshold stricter: {to_reqs['ece_post_le']} vs {from_reqs['ece_post_le']}")

    return {
        "eligible": True,
        "from_environment": from_env,
        "to_environment": to_env,
        "version": version,
        "canary_results": canary_results,
        "warnings": warnings,
        "requires_approval": to_policy.get("approval_required_for", {}).get("policy_updates", False)
    }

def execute_promotion(from_env, to_env, version, dry_run=True):
    """Execute promotion between environments"""

    # Check eligibility
    eligibility = check_promotion_eligibility(from_env, to_env, version)

    if not eligibility["eligible"]:
        print(f"❌ Promotion blocked: {eligibility['reason']}")
        return False

    print(f"✅ Version {version} is eligible for promotion: {from_env} → {to_env}")

    if eligibility.get("warnings"):
        print("⚠️  Warnings:")
        for warning in eligibility["warnings"]:
            print(f"   • {warning}")

    if eligibility.get("requires_approval"):
        print("🔒 This promotion requires manual approval")
        # Would integrate with approval workflow here

    if dry_run:
        print("📝 Dry run - use --execute to actually promote")
        return True

    # Create promotion record
    promotion_record = {
        "version": version,
        "from_environment": from_env,
        "to_environment": to_env,
        "timestamp": time.time(),
        "canary_results": eligibility["canary_results"],
        "promoted_by": "automated_promotion_chain"
    }

    # Save promotion record
    os.makedirs("state/promotions", exist_ok=True)
    record_file = f"state/promotions/{version}_{from_env}_to_{to_env}.json"

    with open(record_file, "w") as f:
        json.dump(promotion_record, f, indent=2)

    print(f"✅ Promotion executed: {version} promoted from {from_env} to {to_env}")
    print(f"📋 Promotion record: {record_file}")

    return True

def show_promotion_status(version=None):
    """Show current promotion status across environments"""

    print("🔄 Governance Promotion Chain Status")
    print("=" * 50)

    for env in PROMOTION_CHAIN:
        policy = load_env_policy(env)
        if not policy:
            continue

        print(f"\n📍 {env.upper()}")
        print(f"   Policy: {policy.get('version', 'unknown')}")
        print(f"   Canary Sample: {policy['rollout']['sample'] * 100:.0f}%")
        print(f"   Window: {policy['observability']['window_minutes']} min")
        print(f"   Min Samples: {policy['observability']['min_samples']}")

        # Show active versions if available
        if version:
            results = get_env_canary_results(env, version)
            if results:
                print(f"   ✅ Version {version}: {results.get('status', 'unknown')}")

    # Show promotion records
    print("\n📋 Recent Promotions:")
    try:
        promotions_dir = Path("state/promotions")
        if promotions_dir.exists():
            records = sorted(promotions_dir.glob("*.json"), key=os.path.getmtime, reverse=True)[:5]
            for record_file in records:
                with open(record_file) as f:
                    record = json.load(f)
                    print(f"   {record['version']}: {record['from_environment']} → {record['to_environment']} ({time.ctime(record['timestamp'])})")
        else:
            print("   No promotion records found")
    except Exception as e:
        print(f"   Error reading promotion records: {e}")

def validate_cross_env_compatibility(from_env, to_env):
    """Validate that promotion between environments is safe"""

    from_policy = load_env_policy(from_env)
    to_policy = load_env_policy(to_env)

    if not from_policy or not to_policy:
        return {"compatible": False, "reason": "Missing policy files"}

    # Check that target environment is at least as strict as source
    issues = []

    from_reqs = from_policy.get("promote_requirements", {})
    to_reqs = to_policy.get("promote_requirements", {})

    # ECE check
    if to_reqs.get("ece_post_le", 1.0) > from_reqs.get("ece_post_le", 1.0):
        issues.append(f"Target ECE threshold looser: {to_reqs['ece_post_le']} > {from_reqs['ece_post_le']}")

    # Violation check
    if to_reqs.get("violation_rate_le_over_baseline", 1.0) > from_reqs.get("violation_rate_le_over_baseline", 1.0):
        issues.append(f"Target violation threshold looser")

    if issues:
        return {
            "compatible": False,
            "reason": "Target environment has looser requirements",
            "issues": issues
        }

    return {
        "compatible": True,
        "message": f"✅ {from_env} → {to_env} promotion path is properly configured"
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Environment Promotion Chain Manager")
    parser.add_argument("--check-promotion", action="store_true",
                       help="Check if version is eligible for promotion")
    parser.add_argument("--promote", action="store_true",
                       help="Execute promotion between environments")
    parser.add_argument("--from-env", choices=["development", "staging", "production"],
                       help="Source environment")
    parser.add_argument("--to-env", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--version", help="Version to promote (e.g., v1.2.3)")
    parser.add_argument("--show-status", action="store_true",
                       help="Show promotion chain status")
    parser.add_argument("--validate-chain", action="store_true",
                       help="Validate entire promotion chain configuration")
    parser.add_argument("--execute", action="store_true",
                       help="Actually execute promotion (default: dry run)")

    args = parser.parse_args()

    if args.show_status:
        show_promotion_status(args.version)
        return

    if args.validate_chain:
        print("🔍 Validating Promotion Chain Configuration")
        print("=" * 50)

        for i in range(len(PROMOTION_CHAIN) - 1):
            from_env = PROMOTION_CHAIN[i]
            to_env = PROMOTION_CHAIN[i + 1]

            result = validate_cross_env_compatibility(from_env, to_env)
            if result["compatible"]:
                print(f"✅ {from_env} → {to_env}: {result['message']}")
            else:
                print(f"❌ {from_env} → {to_env}: {result['reason']}")
                if "issues" in result:
                    for issue in result["issues"]:
                        print(f"   • {issue}")

        return

    if args.check_promotion:
        if not args.from_env or not args.to_env or not args.version:
            print("❌ Missing required arguments: --from-env, --to-env, --version")
            sys.exit(1)

        eligibility = check_promotion_eligibility(args.from_env, args.to_env, args.version)

        print(json.dumps(eligibility, indent=2))

        if not eligibility["eligible"]:
            sys.exit(1)

        return

    if args.promote:
        if not args.from_env or not args.to_env or not args.version:
            print("❌ Missing required arguments: --from-env, --to-env, --version")
            sys.exit(1)

        success = execute_promotion(
            args.from_env,
            args.to_env,
            args.version,
            dry_run=not args.execute
        )

        sys.exit(0 if success else 1)

    parser.print_help()

if __name__ == "__main__":
    main()


