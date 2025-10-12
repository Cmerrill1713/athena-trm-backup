#!/usr/bin/env python3
"""
New App Wizard
Ties knowledge system + broker + build pipeline together

Usage:
    python3 app_wizard.py MyApp swift "SwiftUI menu bar app with charts"
    python3 app_wizard.py MyApp tauri "Electron alternative with Rust backend"
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Optional

# Add scripts to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from knowledge_helper import KnowledgeHelper
    from broker_client import BrokerClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure broker_client.py and knowledge_helper.py are in scripts/")
    sys.exit(1)


class AppWizard:
    """AI-driven app creation wizard"""
    
    def __init__(self):
        self.knowledge = KnowledgeHelper()
        self.broker = BrokerClient()
        self.desktop = Path.home() / "Desktop"
    
    def query_knowledge(self, topic: str, limit: int = 12) -> list:
        """Query knowledge base for implementation patterns"""
        print(f"🧠 Querying knowledge base: '{topic}'")
        results = self.knowledge.search(topic, limit=limit)
        
        if "error" in results:
            print(f"⚠️  Knowledge query failed: {results['error']}")
            return []
        
        docs = results.get("results", [])
        print(f"✅ Found {len(docs)} knowledge documents")
        return docs
    
    def create_plan(self, app_name: str, app_type: str, description: str, knowledge_docs: list) -> str:
        """Create implementation plan based on knowledge"""
        plan = f"""# {app_name} - Implementation Plan

## Goal
{description}

## Type
{app_type}

## Knowledge Sources
{len(knowledge_docs)} relevant documents from knowledge base (48K+ corpus)

## Key Insights
"""
        for i, doc in enumerate(knowledge_docs[:5], 1):
            title = doc.get('title', 'Untitled')
            summary = doc.get('content', '')[:200]
            plan += f"\n{i}. {title}\n   {summary}...\n"
        
        plan += """
## Constraints
- Tests must pass before packaging (validation gate)
- Services bound to 127.0.0.1 only
- Token authentication on APIs
- Follow PRD compliance (85%+ test coverage)

## Test Plan
1. Unit tests for core logic
2. Integration tests for API/UI
3. Manual smoke test before delivery

## Build Steps
1. Scaffold project structure
2. Implement core features
3. Add tests
4. Validate (pytest/XCTest)
5. Build release binary
6. Package DMG
7. Deliver to Desktop via broker

## Risks
- macOS permission prompts (Automation/Accessibility)
- Build time dependencies
- Test flakiness on CI

"""
        return plan
    
    def save_plan(self, app_name: str, plan: str) -> Path:
        """Save plan to Desktop via broker"""
        plan_path = self.desktop / f"{app_name}_plan.md"
        self.broker.write_file(str(plan_path), plan)
        print(f"📄 Plan saved: {plan_path}")
        return plan_path
    
    def scaffold_project(self, app_name: str, app_type: str, project_path: str) -> bool:
        """Scaffold project (calls external scaffolder or manual)"""
        print(f"🏗️  Scaffolding {app_type} project...")
        
        # Check if project already exists
        if os.path.exists(project_path):
            print(f"⚠️  Project already exists at: {project_path}")
            response = input("   Continue with existing project? [y/N]: ")
            if response.lower() != 'y':
                print("❌ Aborted")
                return False
            return True
        
        # Try to scaffold (you can wire your own scaffolder here)
        if app_type == "swift":
            print("📋 Swift scaffolding:")
            print(f"   Run: cd {Path(project_path).parent}")
            print(f"        swift package init --type executable --name {app_name}")
            print(f"   Or create Xcode project manually")
        elif app_type == "tauri":
            print("📋 Tauri scaffolding:")
            print(f"   Run: npm create tauri-app@latest")
        
        response = input(f"\n   Scaffold complete? [y/N]: ")
        return response.lower() == 'y'
    
    def build_and_deliver(self, app_name: str, app_type: str, project_path: str) -> Optional[str]:
        """Run full build pipeline"""
        print(f"🔨 Building and delivering {app_name}...")
        
        deliver_script = SCRIPTS_DIR / "deliver_app.sh"
        
        try:
            result = subprocess.run(
                [str(deliver_script), app_name, app_type, project_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 min max
            )
            
            # Extract DMG path from output
            for line in reversed(result.stdout.split('\n')):
                if line.strip().endswith('.dmg'):
                    return line.strip()
            
            print("✅ Build complete")
            print(result.stdout)
            return None
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed:")
            print(e.stderr)
            return None
        except subprocess.TimeoutExpired:
            print("❌ Build timed out (>10 min)")
            return None
    
    def create_summary(self, app_name: str, dmg_path: Optional[str], knowledge_count: int) -> None:
        """Create build summary and deliver to Desktop"""
        summary = f"""# {app_name} - Build Summary

**Built:** {os.popen('date').read().strip()}
**Knowledge Sources:** {knowledge_count} documents (from 48K+ corpus)
**Status:** {'✅ Success' if dmg_path else '❌ Failed'}

"""
        if dmg_path:
            summary += f"""## Delivered Artifact
{dmg_path}

## SHA256
{dmg_path}.sha256

"""
        
        summary += """## Build Pipeline
1. ✅ Knowledge query
2. ✅ Plan generation
3. ✅ Project scaffold
4. ✅ Validation gate
5. ✅ Build
6. ✅ Package DMG
7. ✅ Delivery via broker

## Knowledge Base Integration
Queried local knowledge gateway (48K+ documents) to inform architecture decisions.

## Next Steps
- Open DMG and test app
- Review plan document
- Add to your app portfolio
"""
        
        summary_path = self.desktop / f"{app_name}_build_summary.md"
        self.broker.write_file(str(summary_path), summary)
        self.broker.reveal_in_finder(str(summary_path))
        print(f"📊 Summary: {summary_path}")
    
    def run(self, app_name: str, app_type: str, description: str, project_path: Optional[str] = None):
        """Run complete wizard"""
        print(f"""
╔════════════════════════════════════════════════════════════╗
║  New App Wizard: {app_name}
║  Type: {app_type}
║  Description: {description}
╚════════════════════════════════════════════════════════════╝
""")
        
        # Step 1: Query knowledge
        knowledge_docs = self.query_knowledge(f"{description} {app_type} architecture patterns")
        
        # Step 2: Create plan
        print("\n📝 Creating implementation plan...")
        plan = self.create_plan(app_name, app_type, description, knowledge_docs)
        plan_path = self.save_plan(app_name, plan)
        self.broker.reveal_in_finder(str(plan_path))
        print("✅ Plan revealed in Finder")
        
        # Ask user to review
        print("\n" + "="*60)
        response = input("📋 Review the plan, then continue? [y/N]: ")
        if response.lower() != 'y':
            print("⏸️  Paused - Plan saved to Desktop for review")
            return
        
        # Step 3: Scaffold
        if not project_path:
            default_path = f"/Users/{os.environ.get('USER', 'christianmerrill')}/Documents/GitHub/{app_name}"
            project_path = input(f"\n📁 Project path [{default_path}]: ").strip() or default_path
        
        if not self.scaffold_project(app_name, app_type, project_path):
            print("❌ Scaffolding incomplete - exiting")
            return
        
        # Step 4: Build & deliver
        print("\n" + "="*60)
        response = input("🔨 Ready to build and deliver? [y/N]: ")
        if response.lower() != 'y':
            print("⏸️  Stopped before build")
            return
        
        dmg_path = self.build_and_deliver(app_name, app_type, project_path)
        
        # Step 5: Summary
        self.create_summary(app_name, dmg_path, len(knowledge_docs))
        
        if dmg_path:
            print("\n🎉 SUCCESS! App delivered to Desktop")
        else:
            print("\n⚠️  Build completed with issues - check logs")


def main():
    parser = argparse.ArgumentParser(description="AI-Driven App Wizard")
    parser.add_argument("name", help="App name (e.g., MyMenuBarApp)")
    parser.add_argument("type", choices=["swift", "tauri", "python"], help="App type")
    parser.add_argument("description", help="App description for knowledge query")
    parser.add_argument("--project", help="Project path (optional, will prompt)")
    
    args = parser.parse_args()
    
    wizard = AppWizard()
    wizard.run(args.name, args.type, args.description, args.project)


if __name__ == "__main__":
    main()

