#!/usr/bin/env python3
"""
Auto-Diagnostic Script for Swift UI Typing Issue
Uses governance patterns to identify and remediate the problem
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

class SwiftTypingDiagnostic:
    """Governance-style diagnostic for Swift typing issues"""
    
    def __init__(self):
        self.metrics = {
            "checks_performed": 0,
            "issues_found": [],
            "remediations_suggested": []
        }
        self.verdict = "UNKNOWN"
        
    def log(self, msg, level="INFO"):
        """Governance-style logging"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] {msg}")
        
    def run_check(self, name, command, expected_contains=None):
        """Run a diagnostic check"""
        self.metrics["checks_performed"] += 1
        self.log(f"🔍 Running check: {name}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout + result.stderr
            
            if expected_contains:
                if expected_contains in output:
                    self.log(f"✅ {name}: PASS", "SUCCESS")
                    return True, output
                else:
                    self.log(f"❌ {name}: FAIL (missing '{expected_contains}')", "ERROR")
                    self.metrics["issues_found"].append({
                        "check": name,
                        "issue": f"Expected '{expected_contains}' not found",
                        "output": output[:500]
                    })
                    return False, output
            else:
                # Just return the output for analysis
                return result.returncode == 0, output
                
        except Exception as e:
            self.log(f"❌ {name}: EXCEPTION - {str(e)}", "ERROR")
            self.metrics["issues_found"].append({
                "check": name,
                "issue": str(e)
            })
            return False, str(e)
    
    def check_app_running(self):
        """Check if NeuroForgeApp is running"""
        success, output = self.run_check(
            "App Process Running",
            "ps aux | grep NeuroForgeApp | grep -v grep | grep -v tee"
        )
        if not success:
            self.metrics["issues_found"].append({
                "check": "app_running",
                "issue": "NeuroForgeApp not running",
                "remediation": "Launch the app with 'make run'"
            })
        return success
    
    def check_build_errors(self):
        """Check for Swift build errors"""
        self.log("🔍 Checking for build errors...")
        success, output = self.run_check(
            "Swift Build",
            "cd NeuroForgeApp && swift build 2>&1 | grep -i error || echo 'No errors'",
            expected_contains="No errors"
        )
        
        if not success and "error" in output.lower():
            self.metrics["issues_found"].append({
                "check": "build_errors",
                "issue": "Swift compilation errors detected",
                "details": output[:1000],
                "remediation": "Fix compilation errors before testing typing"
            })
        
        return success
    
    def check_focus_implementation(self):
        """Check if @FocusState is implemented"""
        success, output = self.run_check(
            "FocusState Implementation",
            "grep -r '@FocusState' NeuroForgeApp/Sources/ || echo 'Not found'"
        )
        
        if "Not found" in output:
            self.metrics["issues_found"].append({
                "check": "focus_state",
                "issue": "@FocusState not implemented in any view",
                "remediation": "Add @FocusState to TextField for proper focus management"
            })
            return False
        
        return True
    
    def check_textfield_usage(self):
        """Check TextField implementation"""
        success, output = self.run_check(
            "TextField Implementation",
            "grep -r 'TextField(' NeuroForgeApp/Sources/ | wc -l"
        )
        
        count = output.strip()
        self.log(f"Found {count} TextField usages")
        
        if int(count) == 0:
            self.metrics["issues_found"].append({
                "check": "textfield_usage",
                "issue": "No TextField found in source code",
                "remediation": "Implement TextField for text input"
            })
            return False
        
        return True
    
    def check_macos_permissions(self):
        """Check macOS permissions"""
        self.log("🔍 Checking macOS permissions...")
        
        # Check if app is sandboxed
        success, output = self.run_check(
            "Sandboxing Status",
            "codesign -d --entitlements - NeuroForgeApp/.build/debug/NeuroForgeApp 2>&1 || echo 'Not signed'"
        )
        
        if "sandbox" in output.lower():
            self.metrics["issues_found"].append({
                "check": "sandboxing",
                "issue": "App may be sandboxed, restricting keyboard access",
                "remediation": "Check entitlements or disable sandboxing for development"
            })
        
        return True
    
    def check_known_swiftui_bugs(self):
        """Check for known SwiftUI patterns that cause typing issues"""
        self.log("🔍 Checking for known SwiftUI bug patterns...")
        
        # Check for NSViewRepresentable usage (known to cause issues)
        success, output = self.run_check(
            "NSViewRepresentable Usage",
            "grep -r 'NSViewRepresentable' NeuroForgeApp/Sources/ | wc -l"
        )
        
        count = output.strip()
        if int(count) > 0:
            self.metrics["issues_found"].append({
                "check": "nsview_representable",
                "issue": f"Found {count} NSViewRepresentable implementations",
                "details": "NSViewRepresentable can cause keyboard focus issues on macOS",
                "remediation": "Replace NSViewRepresentable with pure SwiftUI TextField"
            })
        
        # Check for NavigationSplitView (known focus issues)
        success, output = self.run_check(
            "NavigationSplitView Usage",
            "grep -r 'NavigationSplitView' NeuroForgeApp/Sources/ | wc -l"
        )
        
        count = output.strip()
        if int(count) > 0:
            self.log(f"⚠️  Found {count} NavigationSplitView usages (known focus issues)")
            self.metrics["issues_found"].append({
                "check": "navigation_split_view",
                "issue": "NavigationSplitView has known focus issues on macOS",
                "details": "SwiftUI bug: TextField in NavigationSplitView detail view may not receive keyboard input",
                "remediation": "Use delayed focus (.onAppear with DispatchQueue.main.asyncAfter) or avoid NavigationSplitView"
            })
        
        return True
    
    def analyze_console_logs(self):
        """Analyze Console.app logs for errors"""
        self.log("🔍 Checking console logs...")
        
        success, output = self.run_check(
            "Console Logs",
            "log show --predicate 'process == \"NeuroForgeApp\"' --last 2m --style compact 2>/dev/null | tail -50 || echo 'No logs'"
        )
        
        if "error" in output.lower() or "exception" in output.lower():
            self.metrics["issues_found"].append({
                "check": "console_logs",
                "issue": "Errors detected in console logs",
                "details": output[:1000]
            })
        
        return True
    
    def determine_verdict(self):
        """Determine overall verdict governance-style"""
        issues_count = len(self.metrics["issues_found"])
        
        if issues_count == 0:
            self.verdict = "PASS"
        elif issues_count <= 2:
            self.verdict = "SOFT_FAIL"
        else:
            self.verdict = "HARD_FAIL"
        
        self.log(f"📊 Verdict: {self.verdict} ({issues_count} issues found)")
        
    def generate_remediation_plan(self):
        """Generate auto-remediation plan"""
        self.log("🔧 Generating remediation plan...")
        
        plan = {
            "timestamp": datetime.now().isoformat(),
            "verdict": self.verdict,
            "issues_found": len(self.metrics["issues_found"]),
            "remediation_steps": []
        }
        
        # Prioritize remediations
        for issue in self.metrics["issues_found"]:
            if "remediation" in issue:
                plan["remediation_steps"].append({
                    "issue": issue["issue"],
                    "action": issue["remediation"],
                    "priority": "HIGH" if "compilation" in issue["issue"].lower() else "MEDIUM"
                })
        
        # Add general recommendations
        if any("NavigationSplitView" in str(i) for i in self.metrics["issues_found"]):
            plan["remediation_steps"].append({
                "issue": "Known SwiftUI focus bug",
                "action": "Apply 0.3s delayed focus workaround with @FocusState",
                "priority": "HIGH",
                "code_example": """
@FocusState private var isFocused: Bool

TextField("...", text: $text)
    .focused($isFocused)
    .onAppear {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            isFocused = true
        }
    }
"""
            })
        
        return plan
    
    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        self.log("=" * 70)
        self.log("🚀 Starting Auto-Diagnostic for Swift UI Typing Issue")
        self.log("=" * 70)
        
        # Run all checks
        self.check_app_running()
        self.check_build_errors()
        self.check_focus_implementation()
        self.check_textfield_usage()
        self.check_known_swiftui_bugs()
        self.check_macos_permissions()
        self.analyze_console_logs()
        
        # Determine verdict
        self.determine_verdict()
        
        # Generate remediation plan
        plan = self.generate_remediation_plan()
        
        # Output results
        self.log("=" * 70)
        self.log("📊 DIAGNOSTIC RESULTS")
        self.log("=" * 70)
        self.log(f"Checks performed: {self.metrics['checks_performed']}")
        self.log(f"Issues found: {len(self.metrics['issues_found'])}")
        self.log(f"Verdict: {self.verdict}")
        self.log("")
        
        if self.metrics["issues_found"]:
            self.log("🔍 ISSUES DETECTED:")
            for i, issue in enumerate(self.metrics["issues_found"], 1):
                self.log(f"\n{i}. {issue['issue']}")
                if "remediation" in issue:
                    self.log(f"   → Fix: {issue['remediation']}")
        
        self.log("")
        self.log("=" * 70)
        self.log("🔧 REMEDIATION PLAN")
        self.log("=" * 70)
        
        for i, step in enumerate(plan["remediation_steps"], 1):
            self.log(f"\n{i}. [{step['priority']}] {step['issue']}")
            self.log(f"   Action: {step['action']}")
            if "code_example" in step:
                self.log(f"   Example:{step['code_example']}")
        
        # Save report
        report_path = Path("SWIFT_TYPING_DIAGNOSTIC.json")
        with open(report_path, "w") as f:
            json.dump({
                "metrics": self.metrics,
                "verdict": self.verdict,
                "remediation_plan": plan
            }, f, indent=2)
        
        self.log("")
        self.log(f"📄 Full report saved to: {report_path}")
        self.log("=" * 70)
        
        return self.verdict == "PASS"

if __name__ == "__main__":
    diagnostic = SwiftTypingDiagnostic()
    success = diagnostic.run_full_diagnostic()
    sys.exit(0 if success else 1)

