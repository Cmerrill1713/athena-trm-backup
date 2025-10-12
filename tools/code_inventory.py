#!/usr/bin/env python3
"""
Code Inventory - Accurate Source Code Metrics
==============================================
Walks repo, submodules, and external paths
Excludes noise, outputs Markdown + JSON
"""

import os
import sys
import re
import json
import subprocess
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List

try:
    import yaml
except ImportError:
    yaml = None


DEFAULT_EXCLUDE_DIRS = {
    '.git', 'build', 'dist', 'node_modules', '__pycache__',
    'DerivedData', '.swiftpm', '.idea', '.vscode', '.pytest_cache', '.build'
}

DEFAULT_EXCLUDE_EXT = {
    '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.dmg',
    '.xcarchive', '.xcworkspace', '.xcodeproj'
}


def is_git_repo(path):
    """Check if path is a git repository"""
    return (pathlib.Path(path) / '.git').exists()


def git_rev(path):
    """Get short git revision for path"""
    try:
        return subprocess.check_output(
            ['git', '-C', path, 'rev-parse', '--short', 'HEAD'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def load_config(cfg_path):
    """Load configuration from YAML"""
    cfg = {
        "components": {},
        "external_components": {},
        "include_submodules": True,
        "exclude_dirs": list(DEFAULT_EXCLUDE_DIRS),
        "exclude_ext": list(DEFAULT_EXCLUDE_EXT),
        "lang_map": {}
    }

    if os.path.exists(cfg_path):
        if yaml is None:
            print("⚠️  PyYAML not installed; using defaults", file=sys.stderr)
        else:
            with open(cfg_path, 'r') as f:
                loaded = yaml.safe_load(f) or {}
                cfg.update(loaded)

    return cfg


@dataclass
class Totals:
    """Code totals tracker"""
    files: int = 0
    lines: int = 0
    by_lang: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def add(self, lang: str, lines: int):
        """Add file stats"""
        self.files += 1
        self.lines += lines
        d = self.by_lang.setdefault(lang, {"files": 0, "lines": 0})
        d["files"] += 1
        d["lines"] += lines


def count_lines(file_path):
    """Count lines in file"""
    try:
        with open(file_path, 'rb') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def ext_to_lang(ext, lang_map):
    """Map file extension to language"""
    return lang_map.get(ext, ext.lstrip('.').upper() if ext else 'OTHER')


def walk_component(root, exclude_dirs, exclude_ext, lang_map) -> Totals:
    """Walk directory tree and count code"""
    totals = Totals()
    root = os.path.abspath(root)

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for fname in filenames:
            ext = os.path.splitext(fname)[1]

            # Skip excluded extensions
            if ext in exclude_ext:
                continue

            fpath = os.path.join(dirpath, fname)

            # Skip large binaries (>5MB)
            try:
                if os.path.getsize(fpath) > 5_000_000:
                    continue
            except OSError:
                continue

            lang = ext_to_lang(ext, lang_map)
            lines = count_lines(fpath)
            totals.add(lang, lines)

    return totals


def list_submodules(repo_root):
    """Parse .gitmodules and list submodules"""
    gitmodules = os.path.join(repo_root, '.gitmodules')
    subs = {}

    if not os.path.exists(gitmodules):
        return subs

    pat_path = re.compile(r'path\s*=\s*(.*)')
    pat_url = re.compile(r'url\s*=\s*(.*)')
    current = None

    with open(gitmodules, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('[submodule '):
                current = {}
            elif current is not None and line.startswith('path'):
                m = pat_path.search(line)
                if m:
                    current['path'] = m.group(1)
            elif current is not None and line.startswith('url'):
                m = pat_url.search(line)
                if m:
                    current['url'] = m.group(1)
                    # Finalize on url
                    if 'path' in current:
                        subs[current['path']] = current
                        current = None

    return subs


def summarize_component(name, path, cfg):
    """Summarize a single component"""
    totals = walk_component(
        path,
        set(cfg["exclude_dirs"]),
        set(cfg["exclude_ext"]),
        cfg["lang_map"]
    )

    rev = git_rev(path) if is_git_repo(path) else None

    return {
        "component": name,
        "path": os.path.abspath(path),
        "git_rev": rev,
        "totals": totals.__dict__
    }


def main():
    """Main inventory function"""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    cfg_path = os.path.join(os.path.dirname(__file__), 'code_inventory.yaml')
    cfg = load_config(cfg_path)

    print("📊 NeuroForge Code Inventory")
    print("=" * 60)
    print(f"Repo: {repo_root}")
    print()

    # Gather components
    entries = []

    # Main components
    for name, rel in cfg.get("components", {}).items():
        path = os.path.abspath(os.path.join(repo_root, rel))
        if os.path.exists(path):
            print(f"Scanning: {name}...")
            entries.append(summarize_component(name, path, cfg))
        else:
            print(f"⚠️  Skipped: {name} (path not found)")

    # External components
    for name, extp in cfg.get("external_components", {}).items():
        path = os.path.abspath(os.path.join(repo_root, extp))
        if os.path.exists(path):
            print(f"Scanning: {name} (external)...")
            entries.append(summarize_component(name + " (external)", path, cfg))

    # Submodules
    if cfg.get("include_submodules", True):
        subs = list_submodules(repo_root)
        for rel, meta in subs.items():
            path = os.path.abspath(os.path.join(repo_root, rel))
            if os.path.exists(path):
                print(f"Scanning: submodule:{rel}...")
                entries.append(summarize_component(f"submodule:{rel}", path, cfg))

    # Calculate grand totals
    grand = Totals()
    by_component = []

    for e in entries:
        t = e["totals"]
        grand.files += t["files"]
        grand.lines += t["lines"]

        # Merge language totals
        for lang, d in t["by_lang"].items():
            g = grand.by_lang.setdefault(lang, {"files": 0, "lines": 0})
            g["files"] += d["files"]
            g["lines"] += d["lines"]

        by_component.append(e)

    # Output JSON
    out = {
        "grand_total": {
            "files": grand.files,
            "lines": grand.lines,
            "by_lang": grand.by_lang
        },
        "components": by_component,
    }

    os.makedirs("./state", exist_ok=True)
    with open("./state/code_inventory.json", "w") as f:
        json.dump(out, f, indent=2)

    # Output Markdown
    def fmtnum(n):
        return f"{n:,}"

    md = []
    md.append("# Code Inventory\n")
    md.append(f"**Repo:** {os.path.basename(repo_root)}\n\n")
    md.append("## Grand Total\n")
    md.append(f"- **Files:** {fmtnum(grand.files)}\n")
    md.append(f"- **Lines:** {fmtnum(grand.lines)}\n\n")

    md.append("### By Language\n")
    for lang, d in sorted(grand.by_lang.items(), key=lambda x: -x[1]["lines"]):
        md.append(f"- **{lang}**: {fmtnum(d['lines'])} lines in {fmtnum(d['files'])} files\n")

    md.append("\n## By Component\n\n")
    for e in sorted(by_component, key=lambda x: -x["totals"]["lines"]):
        t = e["totals"]
        rev = e.get("git_rev") or "—"
        md.append(f"### {e['component']}\n")
        md.append(f"- **Path:** `{e['path']}`\n")
        md.append(f"- **Git:** `{rev}`\n")
        md.append(f"- **Files:** {fmtnum(t['files'])}, **Lines:** {fmtnum(t['lines'])}\n")

        # Top 5 languages
        langs = sorted(t["by_lang"].items(), key=lambda x: -x[1]["lines"])[:5]
        if langs:
            lang_str = ", ".join(f"{k} ({fmtnum(v['lines'])})" for k, v in langs)
            md.append(f"- **Top languages:** {lang_str}\n")
        md.append("\n")

    with open("./CODE_INVENTORY.md", "w") as f:
        f.write("".join(md))

    print()
    print("=" * 60)
    print("✅ Inventory Complete")
    print("=" * 60)
    print(f"Total Files: {fmtnum(grand.files)}")
    print(f"Total Lines: {fmtnum(grand.lines)}")
    print()
    print("Output files:")
    print("  - CODE_INVENTORY.md")
    print("  - state/code_inventory.json")
    print()

    # Non-zero exit if nothing found
    if not entries:
        print("❌ No components found - check code_inventory.yaml")
        sys.exit(1)


if __name__ == "__main__":
    main()
