#!/usr/bin/env python3
"""
Deep File-Level Audit
Before deleting anything, audit every file in suspected directories
"""

import os
import subprocess
from pathlib import Path
import json

ROOT = Path.cwd()

def find_references(filepath_or_name, search_in=["*.py", "*.yml", "*.yaml", "*.sh", "Makefile*", "docker-compose*"]):
    """Find all references to a file or directory name"""
    references = []
    
    for pattern in search_in:
        try:
            result = subprocess.run(
                ["grep", "-r", "--include", pattern, "-l", filepath_or_name, "."],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and not line.startswith('./archive') and not line.startswith('./.git'):
                        references.append(line)
        except:
            pass
    
    return list(set(references))

def audit_directory(dirpath):
    """Audit all files in a directory"""
    p = ROOT / dirpath
    if not p.exists():
        return {"status": "missing", "files": []}
    
    files_info = []
    total_size = 0
    
    for f in p.rglob("*"):
        if f.is_file() and not str(f).startswith('.git'):
            relative = f.relative_to(ROOT)
            size = f.stat().st_size
            total_size += size
            
            # Check if referenced
            refs = find_references(f.name)
            
            files_info.append({
                "path": str(relative),
                "size": size,
                "referenced_by": refs[:5] if refs else []  # Limit to 5 refs
            })
    
    return {
        "status": "exists",
        "file_count": len(files_info),
        "total_size": total_size,
        "files": sorted(files_info, key=lambda x: x['size'], reverse=True)[:20]  # Top 20 by size
    }

# Directories to audit deeply
suspects = [
    "NeuroForgeApp_Clean",
    "Desktop-Projects",
    "ai_republic",
    "infra_snapshot"
]

print("=" * 80)
print("DEEP FILE-LEVEL AUDIT")
print("=" * 80)
print()

results = {}

for dirname in suspects:
    print(f"\n📁 Auditing: {dirname}/")
    print("-" * 80)
    
    audit = audit_directory(dirname)
    results[dirname] = audit
    
    if audit["status"] == "missing":
        print(f"   ✅ Already removed")
        continue
    
    print(f"   Files: {audit['file_count']}")
    print(f"   Total size: {audit['total_size']:,} bytes ({audit['total_size'] / 1024:.1f} KB)")
    print()
    
    if audit['file_count'] > 0:
        print(f"   Top files by size:")
        for f in audit['files'][:10]:
            refs = len(f['referenced_by'])
            ref_status = f"✅ {refs} refs" if refs > 0 else "⚠️  No refs"
            print(f"      {ref_status} - {f['path']} ({f['size']:,} bytes)")
            if f['referenced_by']:
                for ref in f['referenced_by'][:2]:
                    print(f"          → {ref}")

# Save detailed report
output_path = ROOT / "artifacts" / "wiring" / "deep_audit.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(results, indent=2))

print()
print("=" * 80)
print(f"📝 Detailed report saved: {output_path}")
print()

# Summary
total_referenced = sum(
    1 for d, data in results.items() 
    if data["status"] == "exists" 
    for f in data.get("files", []) 
    if f.get("referenced_by")
)

total_files = sum(
    data.get("file_count", 0) 
    for data in results.values() 
    if data["status"] == "exists"
)

print("📊 Summary:")
for dirname, data in results.items():
    if data["status"] == "missing":
        print(f"   ✅ {dirname}: Already removed")
    else:
        count = data['file_count']
        has_refs = any(f.get('referenced_by') for f in data.get('files', []))
        status = "🟡 KEEP" if has_refs else "⚠️  CAN DELETE"
        print(f"   {status} {dirname}: {count} files, {data['total_size']:,} bytes")

print()
if total_referenced > 0:
    print(f"⚠️  Found {total_referenced} referenced files - review before deleting!")
else:
    print(f"✅ No references found - safe to delete after manual review")

