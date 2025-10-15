#!/usr/bin/env python3
"""
🧭 Governance Consolidation Script
Consolidates scattered iterations into clean tiered governance structure
"""

import os
import json
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

class GovernanceConsolidator:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.governance_dir = self.root_dir / "governance"
        self.iteration_log = []
        
    def create_governance_structure(self):
        """Create the governance directory structure"""
        structure = {
            "legislative": ["policy_compiler", "canary_rules"],
            "judicial": ["entropy_service.py", "evaluation", "calibration"],
            "executive": ["start_server.sh", "docker", "orchestration"],
            "devil_advocate": ["stress_tests", "red_team_sets"],
            "observability": ["prometheus.yml"],
            "archive": ["old_iterations"]
        }
        
        for branch, subdirs in structure.items():
            branch_dir = self.governance_dir / branch
            branch_dir.mkdir(parents=True, exist_ok=True)
            
            for subdir in subdirs:
                (branch_dir / subdir).mkdir(exist_ok=True)
                
        print("✅ Created governance structure")
        
    def analyze_codebase(self) -> Dict[str, List[Path]]:
        """Analyze codebase and categorize files"""
        categories = {
            "entropy": [],
            "evaluation": [],
            "stress_test": [],
            "policy": [],
            "orchestration": [],
            "monitoring": [],
            "learning": [],
            "other": []
        }
        
        # File patterns for each category
        patterns = {
            "entropy": ["entropy", "chaos", "drift", "stability"],
            "evaluation": ["eval", "test", "benchmark", "performance"],
            "stress_test": ["stress", "load", "chaos", "attack"],
            "policy": ["policy", "rule", "governance", "canary"],
            "orchestration": ["orchestr", "start", "deploy", "docker"],
            "monitoring": ["monitor", "prometheus", "grafana", "metrics"],
            "learning": ["learn", "train", "evolution", "agent"]
        }
        
        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in 
                [".git", "__pycache__", ".venv", "node_modules", "target"]):
                
                file_str = str(file_path).lower()
                
                categorized = False
                for category, keywords in patterns.items():
                    if any(keyword in file_str for keyword in keywords):
                        categories[category].append(file_path)
                        categorized = True
                        break
                        
                if not categorized:
                    categories["other"].append(file_path)
                    
        return categories
    
    def move_files_to_governance(self, categories: Dict[str, List[Path]]):
        """Move files to appropriate governance locations"""
        
        # Mapping from categories to governance structure
        category_mapping = {
            "entropy": "judicial/entropy_service.py",
            "evaluation": "judicial/evaluation", 
            "stress_test": "devil_advocate/stress_tests",
            "policy": "legislative/policy_compiler",
            "orchestration": "executive/orchestration",
            "monitoring": "observability",
            "learning": "judicial/calibration",
            "other": "archive/old_iterations"
        }
        
        moved_files = []
        
        for category, files in categories.items():
            target_dir = self.governance_dir / category_mapping[category]
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in files:
                try:
                    # Create relative path structure
                    relative_path = file_path.relative_to(self.root_dir)
                    target_path = target_dir / relative_path.name
                    
                    # Handle filename conflicts
                    counter = 1
                    original_target = target_path
                    while target_path.exists():
                        stem = original_target.stem
                        suffix = original_target.suffix
                        target_path = original_target.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(target_path))
                    moved_files.append({
                        "from": str(relative_path),
                        "to": str(target_path.relative_to(self.root_dir)),
                        "category": category
                    })
                    
                except Exception as e:
                    print(f"❌ Error moving {file_path}: {e}")
                    
        return moved_files
    
    def create_iteration_log(self, moved_files: List[Dict]):
        """Create iteration tracking log"""
        
        iteration_entry = {
            "version": "v1.0",
            "author": "GovernanceConsolidator",
            "date": datetime.now().isoformat(),
            "summary": "Initial governance consolidation - organized scattered iterations into tiered structure",
            "files_moved": len(moved_files),
            "categories": list(set(f["category"] for f in moved_files)),
            "moved_files": moved_files[:10],  # First 10 for summary
            "total_files": len(moved_files)
        }
        
        self.iteration_log.append(iteration_entry)
        
        # Save as YAML
        log_path = self.governance_dir / "iteration_log.yaml"
        with open(log_path, 'w') as f:
            yaml.dump(self.iteration_log, f, default_flow_style=False)
            
        print(f"✅ Created iteration log at {log_path}")
        
    def create_governance_manifest(self):
        """Create governance manifest"""
        
        manifest = {
            "governance_version": "v1.0",
            "created": datetime.now().isoformat(),
            "structure": {
                "legislative": {
                    "purpose": "Policy compilation and canary rules",
                    "components": ["policy_compiler", "canary_rules"]
                },
                "judicial": {
                    "purpose": "Entropy monitoring and evaluation",
                    "components": ["entropy_service.py", "evaluation", "calibration"]
                },
                "executive": {
                    "purpose": "System execution and orchestration", 
                    "components": ["start_server.sh", "docker", "orchestration"]
                },
                "devil_advocate": {
                    "purpose": "Stress testing and red teaming",
                    "components": ["stress_tests", "red_team_sets"]
                },
                "observability": {
                    "purpose": "Monitoring and metrics",
                    "components": ["prometheus.yml"]
                },
                "archive": {
                    "purpose": "Historical iterations",
                    "components": ["old_iterations"]
                }
            },
            "event_bus": {
                "enabled": True,
                "channels": ["policy_promotion", "entropy_drift", "calibration", "stress_test_results"]
            }
        }
        
        manifest_path = self.governance_dir / "governance_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"✅ Created governance manifest at {manifest_path}")
        
    def create_event_bus_config(self):
        """Create event bus configuration"""
        
        event_config = {
            "event_bus": {
                "version": "v1.0",
                "channels": {
                    "policy_promotion": {
                        "description": "New policies promoted to active",
                        "subscribers": ["executive", "judicial"]
                    },
                    "entropy_drift": {
                        "description": "Entropy levels changed",
                        "subscribers": ["observability", "devil_advocate"]
                    },
                    "calibration_complete": {
                        "description": "System calibration finished",
                        "subscribers": ["legislative", "executive"]
                    },
                    "stress_test_results": {
                        "description": "Stress test completed",
                        "subscribers": ["judicial", "observability"]
                    }
                }
            }
        }
        
        config_path = self.governance_dir / "event_bus_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(event_config, f, default_flow_style=False)
            
        print(f"✅ Created event bus config at {config_path}")
        
    def run_consolidation(self):
        """Run the full consolidation process"""
        print("🧭 Starting Governance Consolidation")
        print("=" * 50)
        
        # 1. Create structure
        self.create_governance_structure()
        
        # 2. Analyze codebase
        print("📊 Analyzing codebase...")
        categories = self.analyze_codebase()
        
        total_files = sum(len(files) for files in categories.values())
        print(f"📁 Found {total_files} files to organize")
        
        for category, files in categories.items():
            if files:
                print(f"  • {category}: {len(files)} files")
        
        # 3. Move files
        print("\n📦 Moving files to governance structure...")
        moved_files = self.move_files_to_governance(categories)
        print(f"✅ Moved {len(moved_files)} files")
        
        # 4. Create governance files
        self.create_iteration_log(moved_files)
        self.create_governance_manifest()
        self.create_event_bus_config()
        
        print("\n🎉 Consolidation complete!")
        print(f"📂 Governance structure created at: {self.governance_dir}")
        print("\n📋 Next steps:")
        print("  1. Review moved files in governance/ directory")
        print("  2. Update any broken imports/references")
        print("  3. Run: python governance/governance_manifest.json --validate")
        print("  4. Start using iteration_log.yaml for version tracking")

if __name__ == "__main__":
    consolidator = GovernanceConsolidator()
    consolidator.run_consolidation()
