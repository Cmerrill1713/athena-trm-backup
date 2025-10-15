#!/usr/bin/env python3
"""
Code Validation Agent Team - Multi-Agent Code Quality Assurance
===============================================================
Uses specialized LLM agents to validate and improve code quality
"""

import asyncio
from pathlib import Path
from typing import Dict, Any
from ollama_code_agent import OllamaCodeAgent


class CodeValidationTeam:
    """
    Multi-agent team for comprehensive code validation and improvement

    Agents:
    1. SECURITY AUDITOR - Finds security vulnerabilities
    2. PERFORMANCE ANALYZER - Identifies performance issues
    3. CODE REVIEWER - Checks code quality and best practices
    4. TEST VALIDATOR - Ensures comprehensive test coverage
    5. DOCUMENTATION CHECKER - Validates documentation quality
    """

    def __init__(self):
        self.agents = {
            "security_auditor": {
                "model": "qwen3-coder:30b",
                "prompt": """You are a Security Auditor specializing in Python code.

Analyze code for:
- SQL injection vulnerabilities
- Command injection risks
- Authentication/authorization flaws
- Cryptographic weaknesses
- Input validation issues
- Race conditions
- Information disclosure

Provide:
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- Specific line numbers
- Exploit scenarios
- Fix recommendations

Be thorough and precise."""
            },

            "performance_analyzer": {
                "model": "qwen3-coder:30b",
                "prompt": """You are a Performance Optimization Expert for Python.

Analyze code for:
- Time complexity issues (O(n²) where O(n) possible)
- Memory leaks
- Inefficient loops
- Unnecessary computations
- Database N+1 queries
- Blocking I/O in async code
- Missing caching opportunities

Provide:
- Current complexity
- Optimized alternative
- Expected speedup
- Code diff

Focus on high-impact optimizations."""
            },

            "code_reviewer": {
                "model": "qwen2.5:14b",
                "prompt": """You are a Senior Code Reviewer (Python expert).

Review for:
- PEP 8 compliance
- Type hint usage
- Docstring quality
- Error handling
- Code duplication
- Naming conventions
- Modularity
- SOLID principles

Provide:
- Issue severity
- Specific suggestions
- Code examples
- Best practice references

Be constructive and specific."""
            },

            "test_validator": {
                "model": "qwen3-coder:30b",
                "prompt": """You are a Test Quality Specialist.

Validate test suites for:
- Code coverage gaps
- Missing edge cases
- Missing error cases
- Test isolation issues
- Fixture quality
- Assertion strength
- Test organization

Provide:
- Coverage estimate
- Missing test cases
- Example test implementations
- Priority ranking

Aim for 90%+ coverage."""
            },

            "documentation_checker": {
                "model": "qwen2.5:14b",
                "prompt": """You are a Technical Documentation Specialist.

Check documentation for:
- Docstring completeness
- Parameter documentation
- Return value docs
- Exception docs
- Usage examples
- Type hint clarity
- README quality

Provide:
- Missing documentation list
- Clarity improvements
- Example additions

Make docs beginner-friendly."""
            }
        }

        self.ollama_agent = OllamaCodeAgent()

    async def validate_code(self, code: str, filename: str = "unknown.py") -> Dict[str, Any]:
        """
        Run complete code validation using all specialist agents

        Returns comprehensive validation report
        """

        print("=" * 80)
        print(f"🔍 CODE VALIDATION - {filename}")
        print("=" * 80)

        results = {}

        # Run all validators in parallel (or sequentially for token limits)
        for agent_name, agent_config in self.agents.items():
            print(f"\n🤖 Running {agent_name}...")

            task = f"""
Analyze this Python code:

```python
{code}
```

File: {filename}

Provide detailed analysis following your role's expertise.
"""

            # Temporarily override model for this agent
            original_model = self.ollama_agent.model
            self.ollama_agent.model = agent_config["model"]

            # Update prompt via custom call
            full_prompt = f"{agent_config['prompt']}\n\n{task}"

            result = await self.ollama_agent.generate_code(full_prompt)

            # Restore original model
            self.ollama_agent.model = original_model

            results[agent_name] = {
                "success": result.get("success"),
                "analysis": result.get("code", "") or result.get("response", ""),
                "model": agent_config["model"],
                "tokens": result.get("tokens", 0)
            }

            if result.get("success"):
                print(f"   ✅ Complete ({result.get('tokens', 0)} tokens)")
            else:
                print(f"   ❌ Failed: {result.get('error')}")

        return results

    def generate_report(self, validation_results: Dict[str, Any], code: str) -> str:
        """Generate human-readable validation report"""

        report = []
        report.append("=" * 80)
        report.append("📋 CODE VALIDATION REPORT")
        report.append("=" * 80)

        # Overall summary
        successful_checks = sum(1 for r in validation_results.values() if r["success"])
        total_checks = len(validation_results)

        report.append(f"\n✅ Completed: {successful_checks}/{total_checks} validation checks")
        report.append(f"📊 Total tokens: {sum(r.get('tokens', 0) for r in validation_results.values())}")

        # Individual results
        for agent_name, result in validation_results.items():
            report.append(f"\n{'=' * 80}")
            report.append(f"🔍 {agent_name.upper().replace('_', ' ')}")
            report.append(f"{'=' * 80}")

            if result["success"]:
                report.append(result["analysis"])
            else:
                report.append(f"❌ Validation failed: {result.get('error', 'Unknown error')}")

        # Overall verdict
        report.append(f"\n{'=' * 80}")
        report.append("🏆 OVERALL VERDICT")
        report.append(f"{'=' * 80}")

        if successful_checks == total_checks:
            report.append("✅ All validation checks completed successfully!")
            report.append("📊 Review findings above and address high-priority issues.")
        else:
            report.append(f"⚠️  {total_checks - successful_checks} validation check(s) failed")
            report.append("🔧 Please review errors and retry.")

        return "\n".join(report)

    async def validate_and_improve(self, code: str, filename: str = "code.py") -> Dict[str, Any]:
        """
        Validate code and generate improved version

        Workflow:
        1. Run all validators
        2. Aggregate findings
        3. Generate improved code addressing issues
        4. Re-validate improved code
        """

        print("🔄 VALIDATE & IMPROVE WORKFLOW")
        print("=" * 80)

        # Step 1: Initial validation
        print("\n📊 Step 1: Running initial validation...")
        initial_validation = await self.validate_code(code, filename)

        # Step 2: Aggregate findings
        print("\n🔍 Step 2: Aggregating findings...")
        all_findings = []
        for agent_name, result in initial_validation.items():
            if result["success"]:
                all_findings.append(f"[{agent_name}]: {result['analysis'][:300]}...")

        # Step 3: Generate improved code
        print("\n💻 Step 3: Generating improved version...")
        improvement_task = f"""
Improve this Python code based on validation findings:

ORIGINAL CODE:
```python
{code}
```

VALIDATION FINDINGS:
{chr(10).join(all_findings)}

Generate improved version that addresses:
- Security vulnerabilities
- Performance issues
- Code quality concerns
- Missing tests
- Documentation gaps

Output ONLY the improved code.
"""

        improved_result = await self.ollama_agent.generate_code(improvement_task)

        # Step 4: Re-validate
        if improved_result.get("success"):
            print("\n✅ Step 4: Re-validating improved code...")
            improved_code = improved_result["code"]
            final_validation = await self.validate_code(improved_code, f"{filename}.improved")

            return {
                "original_code": code,
                "improved_code": improved_code,
                "initial_validation": initial_validation,
                "final_validation": final_validation,
                "improvement_success": True
            }
        else:
            return {
                "original_code": code,
                "initial_validation": initial_validation,
                "improvement_success": False,
                "error": improved_result.get("error")
            }


# Demo usage
async def main():
    print("=" * 80)
    print("🛡️  CODE VALIDATION TEAM - MULTI-AGENT QUALITY ASSURANCE")
    print("=" * 80)

    # Example: Validate one of our generated implementations
    impl_file = Path("orchestrator/providers/contextual_thompson_sampling.py")

    if impl_file.exists():
        print(f"\n📄 Validating: {impl_file}")
        print(f"📏 Size: {impl_file.stat().st_size} bytes")

        with open(impl_file, 'r') as f:
            code = f.read()

        team = CodeValidationTeam()

        # Run validation
        print("\n🚀 Starting multi-agent validation...")
        validation_results = await team.validate_code(code, impl_file.name)

        # Generate report
        report = team.generate_report(validation_results, code)
        print("\n" + report)

        # Save report
        report_file = Path("state/research") / f"validation_report_{impl_file.stem}.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\n💾 Report saved to: {report_file}")

    else:
        print(f"\n❌ File not found: {impl_file}")
        print("\n💡 Demo: Showing how the validation team works")
        print("\n   1. SECURITY AUDITOR - Checks for vulnerabilities")
        print("   2. PERFORMANCE ANALYZER - Finds optimization opportunities")
        print("   3. CODE REVIEWER - Validates best practices")
        print("   4. TEST VALIDATOR - Ensures coverage")
        print("   5. DOCUMENTATION CHECKER - Validates docs")
        print("\n   All running in parallel for fast validation!")


if __name__ == "__main__":
    asyncio.run(main())
