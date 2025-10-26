#!/usr/bin/env python3
"""
Normalize file permissions across the repository.

Makes shell scripts executable and removes execute bit from Python files
that lack a shebang (likely not meant to be scripts).

Usage:
    python3 scripts/normalize_perms.py [--dry-run] [--verbose]
    
Options:
    --dry-run    Show what would change without making changes
    --verbose    Show detailed output for each file processed
"""

import os
import stat
import sys
import argparse
from pathlib import Path


def has_shebang(path: Path) -> bool:
    """Check if a file starts with a shebang (#!)."""
    try:
        with open(path, 'rb') as f:
            head = f.read(64)
        return head.startswith(b'#!')
    except Exception:
        return False


def is_executable(path: Path) -> bool:
    """Check if a file has any execute bit set."""
    try:
        st = os.stat(path)
        return bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except FileNotFoundError:
        return False


def make_executable(path: Path, dry_run: bool = False) -> bool:
    """Add execute bits to a file."""
    try:
        st = os.stat(path)
        mode = st.st_mode
        new_mode = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        
        if dry_run:
            return True
        
        os.chmod(path, new_mode)
        return True
    except Exception as e:
        print(f"❌ Error making {path} executable: {e}", file=sys.stderr)
        return False


def remove_executable(path: Path, dry_run: bool = False) -> bool:
    """Remove execute bits from a file."""
    try:
        st = os.stat(path)
        mode = st.st_mode
        new_mode = mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH
        
        if dry_run:
            return True
        
        os.chmod(path, new_mode)
        return True
    except Exception as e:
        print(f"❌ Error removing execute from {path}: {e}", file=sys.stderr)
        return False


def normalize_permissions(root_dir: Path = Path('.'), dry_run: bool = False, verbose: bool = False):
    """
    Normalize permissions across the repository.
    
    Rules:
    - .sh files: Should be executable
    - .py files: Only executable if they have a shebang
    - Skip archive/ directory
    """
    
    stats = {
        'shell_made_exec': 0,
        'python_removed_exec': 0,
        'errors': 0
    }
    
    for root, dirs, files in os.walk(root_dir):
        root_path = Path(root)
        
        # Skip archive directory
        if 'archive' in root_path.parts:
            continue
        
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for name in files:
            file_path = root_path / name
            
            try:
                # Handle shell scripts
                if name.endswith('.sh'):
                    if not is_executable(file_path):
                        if verbose or dry_run:
                            action = "[DRY-RUN] Would make" if dry_run else "Making"
                            print(f"{action} executable: {file_path}")
                        
                        if make_executable(file_path, dry_run):
                            stats['shell_made_exec'] += 1
                        else:
                            stats['errors'] += 1
                
                # Handle Python files
                elif name.endswith('.py'):
                    if is_executable(file_path) and not has_shebang(file_path):
                        if verbose or dry_run:
                            action = "[DRY-RUN] Would remove" if dry_run else "Removing"
                            print(f"{action} executable bit: {file_path}")
                        
                        if remove_executable(file_path, dry_run):
                            stats['python_removed_exec'] += 1
                        else:
                            stats['errors'] += 1
            
            except FileNotFoundError:
                # File disappeared during walk (e.g., broken symlink)
                pass
            except Exception as e:
                if verbose:
                    print(f"⚠️  Error processing {file_path}: {e}", file=sys.stderr)
                stats['errors'] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Normalize file permissions across the repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run to see what would change
  python3 scripts/normalize_perms.py --dry-run
  
  # Apply changes with verbose output
  python3 scripts/normalize_perms.py --verbose
  
  # Just apply changes silently
  python3 scripts/normalize_perms.py
"""
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without making changes'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output for each file processed'
    )
    
    args = parser.parse_args()
    
    print("🔧 Normalizing file permissions...")
    if args.dry_run:
        print("   [DRY-RUN MODE - No changes will be made]")
    print()
    
    stats = normalize_permissions(
        root_dir=Path('.'),
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    print()
    print("=== Summary ===")
    print(f"Shell scripts made executable:  {stats['shell_made_exec']}")
    print(f"Python exec bits removed:       {stats['python_removed_exec']}")
    
    if stats['errors'] > 0:
        print(f"⚠️  Errors encountered:           {stats['errors']}")
        return 1
    
    if stats['shell_made_exec'] == 0 and stats['python_removed_exec'] == 0:
        print("✅ All files already have correct permissions!")
    else:
        if args.dry_run:
            print(f"🔍 Would fix {stats['shell_made_exec'] + stats['python_removed_exec']} files")
        else:
            print(f"✅ Fixed {stats['shell_made_exec'] + stats['python_removed_exec']} files")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

