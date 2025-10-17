#!/usr/bin/env python3
"""
SimHash-based near-duplicate detector for Swift/Python/Go/Rust code.
Normalizes code (removes comments, whitespace, strings) and hashes to find similar files.
"""
import ast
import glob
import hashlib
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


def normalize_code(code: str, language: str) -> str:
    """Normalize code by removing noise (comments, strings, whitespace)."""
    
    if language in ['swift', 'rust', 'go', 'typescript', 'javascript']:
        # Remove C-style comments
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    
    elif language == 'python':
        # Remove Python comments
        code = re.sub(r'#.*', '', code)
        # Remove docstrings
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
    
    # Remove all string literals
    code = re.sub(r'"[^"]*"', 'STR', code)
    code = re.sub(r"'[^']*'", 'STR', code)
    
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code)
    code = code.strip()
    
    return code


def get_language(filepath: str) -> str:
    """Determine language from file extension."""
    ext = Path(filepath).suffix
    mapping = {
        '.py': 'python',
        '.swift': 'swift',
        '.go': 'go',
        '.rs': 'rust',
        '.ts': 'typescript',
        '.js': 'javascript'
    }
    return mapping.get(ext, 'unknown')


def compute_hash(code: str) -> str:
    """Compute SHA1 hash of normalized code."""
    return hashlib.sha1(code.encode('utf-8', errors='ignore')).hexdigest()[:16]


def find_near_duplicates(
    patterns: List[str] = ['**/*.swift', '**/*.py', '**/*.go', '**/*.rs', '**/*.ts'],
    exclude_patterns: List[str] = [
        '**/node_modules/**',
        '**/build/**',
        '**/dist/**',
        '**/vendor/**',
        '**/.git/**',
        '**/archive/**',
        '**/governance/upstream/**',
        '**/pydantic-ai/**',
        '**/TinyRecursiveModels/**',
        '**/fastvlm/**'
    ]
) -> Dict[str, List[str]]:
    """Find near-duplicate files by content hash."""
    
    hash_to_files: Dict[str, List[str]] = defaultdict(list)
    
    for pattern in patterns:
        for filepath in glob.glob(pattern, recursive=True):
            # Skip excluded paths
            skip = False
            for exclude in exclude_patterns:
                if Path(filepath).match(exclude):
                    skip = True
                    break
            
            if skip:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                # Skip very small files (< 100 chars)
                if len(code) < 100:
                    continue
                
                language = get_language(filepath)
                if language == 'unknown':
                    continue
                
                normalized = normalize_code(code, language)
                
                # Skip if normalized code is tiny
                if len(normalized) < 50:
                    continue
                
                code_hash = compute_hash(normalized)
                hash_to_files[code_hash].append(filepath)
            
            except Exception as e:
                print(f"Error processing {filepath}: {e}", file=sys.stderr)
                continue
    
    # Filter to only duplicates
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    
    return duplicates


def find_exact_duplicates() -> List[Tuple[str, List[str]]]:
    """Find exact file duplicates using SHA256."""
    from subprocess import run, PIPE
    
    try:
        # Get all tracked files
        result = run(['git', 'ls-files'], capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
        
        # Compute hashes
        hash_to_files: Dict[str, List[str]] = defaultdict(list)
        
        for filepath in files:
            if not Path(filepath).exists():
                continue
            
            try:
                result = run(['shasum', '-a', '256', filepath], capture_output=True, text=True, check=True)
                file_hash = result.stdout.split()[0]
                hash_to_files[file_hash].append(filepath)
            except:
                continue
        
        # Filter to duplicates
        duplicates = [(h, files) for h, files in hash_to_files.items() if len(files) > 1]
        return duplicates
    
    except Exception as e:
        print(f"Error finding exact duplicates: {e}", file=sys.stderr)
        return []


def find_duplicate_names() -> Dict[str, List[str]]:
    """Find files with the same basename in different locations."""
    from subprocess import run
    
    try:
        result = run(['git', 'ls-files'], capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
        
        name_to_paths: Dict[str, List[str]] = defaultdict(list)
        
        for filepath in files:
            basename = Path(filepath).name
            
            # Skip very common names
            if basename in ['__init__.py', 'README.md', 'index.ts', 'main.go', 'test.py']:
                continue
            
            name_to_paths[basename].append(filepath)
        
        # Filter to duplicates
        duplicates = {name: paths for name, paths in name_to_paths.items() if len(paths) > 1}
        return duplicates
    
    except Exception as e:
        print(f"Error finding duplicate names: {e}", file=sys.stderr)
        return {}


def main():
    """Run duplicate detection and report results."""
    print("=" * 80)
    print("DUPLICATE CODE SCAN")
    print("=" * 80)
    print()
    
    # 1. Exact duplicates
    print("1. EXACT DUPLICATES (same content)")
    print("-" * 80)
    exact_dupes = find_exact_duplicates()
    
    if exact_dupes:
        for file_hash, files in exact_dupes:
            print(f"\nHash: {file_hash}")
            for f in files:
                print(f"  {f}")
        print(f"\nTotal: {len(exact_dupes)} exact duplicate groups")
    else:
        print("✅ No exact duplicates found")
    
    print()
    print()
    
    # 2. Near duplicates
    print("2. NEAR DUPLICATES (similar code)")
    print("-" * 80)
    near_dupes = find_near_duplicates()
    
    if near_dupes:
        for code_hash, files in sorted(near_dupes.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\nHash: {code_hash} ({len(files)} files)")
            for f in files:
                print(f"  {f}")
        print(f"\nTotal: {len(near_dupes)} near-duplicate groups")
    else:
        print("✅ No near duplicates found")
    
    print()
    print()
    
    # 3. Duplicate filenames
    print("3. DUPLICATE FILENAMES (same name, different paths)")
    print("-" * 80)
    name_dupes = find_duplicate_names()
    
    if name_dupes:
        # Focus on key files
        key_names = [
            'router', 'Router', 'ChatService', 'LatencyBadge', 
            'orchestrator', 'verdict', 'app.py', 'api.py',
            'ChatComposer', 'KeyCatchingTextEditor'
        ]
        
        found_key = False
        for name, paths in sorted(name_dupes.items()):
            # Check if it's a key name
            is_key = any(k in name for k in key_names)
            
            if is_key:
                found_key = True
                print(f"\n⚠️  {name} ({len(paths)} locations)")
                for p in paths:
                    print(f"  {p}")
        
        if not found_key:
            print("✅ No critical duplicate filenames found")
        
        print(f"\nTotal: {len(name_dupes)} duplicate filename groups")
    else:
        print("✅ No duplicate filenames found")
    
    print()
    print("=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

