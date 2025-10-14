#!/usr/bin/env python3
"""
Model Lineage Builder

Reads logs/promotions.log and generates:
- ASCII tree (always works)
- SVG graph (if Graphviz installed)
- Markdown report with stats

Usage:
    python3 scripts/lineage/build_lineage.py
    or
    make lineage
"""

import json
import subprocess
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Inputs/Outputs
PROMOTIONS_LOG = Path("logs/promotions.log")
OUT_DIR = Path("artifacts/lineage")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SVG_PATH = OUT_DIR / "lineage.svg"
MD_PATH = OUT_DIR / "lineage.md"
TREE_PATH = OUT_DIR / "lineage.txt"


def read_promotions():
    """Read all promotion/rollback events from log"""
    events = []
    
    if not PROMOTIONS_LOG.exists():
        print(f"⚠️  No promotions log found: {PROMOTIONS_LOG}")
        return events
    
    with PROMOTIONS_LOG.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                rec = json.loads(line)
                if rec.get("event") in ("PROMOTION", "ROLLBACK"):
                    events.append(rec)
            except Exception as e:
                print(f"⚠️  Skipping malformed line: {e}")
    
    return events


def build_graph(events):
    """Build graph nodes and edges from events"""
    edges = []
    nodes = set()
    
    for e in events:
        frm = e.get("from")
        to = e.get("to")
        
        if not frm or not to:
            continue
        
        nodes |= {frm, to}
        
        # Build edge label
        label = e["event"]
        extra = []
        
        if e.get("improvement") is not None:
            extra.append(f"Δ={e['improvement']:+.3f}")
        if e.get("p_value") is not None:
            extra.append(f"p={e['p_value']:.3f}")
        if e.get("window_hours") is not None:
            extra.append(f"{int(e['window_hours'])}h")
        
        if extra:
            label += "\\n" + "  ".join(extra)
        
        edges.append((frm, to, label, e))
    
    return nodes, edges


def render_ascii_tree(edges):
    """Render ASCII tree of lineage (handles cycles)"""
    # Build adjacency list and indegree
    adj = defaultdict(list)
    indeg = defaultdict(int)
    
    for u, v, label, e in edges:
        adj[u].append((v, label, e))
        indeg[v] += 1
        indeg.setdefault(u, 0)
    
    # Find roots (nodes with indegree 0)
    roots = [n for n, d in indeg.items() if d == 0]
    
    if not roots and edges:
        # No clear root, just pick first
        roots = [edges[0][0]]
    
    lines = []
    visited = set()  # Track visited to prevent cycles
    
    def dfs(u, prefix="", depth=0):
        """DFS to build tree (cycle-aware)"""
        # Prevent infinite recursion
        if depth > 20 or u in visited:
            if u in visited:
                lines.append(prefix + u + " (cycle)")
            return
        
        visited.add(u)
        lines.append(prefix + u)
        kids = adj.get(u, [])
        
        for i, (k, label, e) in enumerate(kids):
            last = (i == len(kids) - 1)
            branch = "└─ " if last else "├─ "
            
            # Add event info
            event_type = e.get("event", "")
            info = []
            if e.get("improvement"):
                info.append(f"Δ={e['improvement']:+.1%}")
            if event_type == "ROLLBACK":
                info.append("ROLLBACK")
            
            event_line = f" ({', '.join(info)})" if info else ""
            lines.append(prefix + branch + event_line)
            
            dfs(k, prefix + ("   " if last else "│  "), depth + 1)
        
        visited.remove(u)  # Allow revisiting in different branches
    
    for r in roots:
        dfs(r)
    
    return "\n".join(lines) if lines else "(no lineage yet)"


def write_markdown(nodes, edges, events):
    """Generate markdown report"""
    events_sorted = sorted(events, key=lambda e: e.get("ts", ""))
    
    def fmt_pct(x):
        """Format as percentage"""
        if isinstance(x, (int, float)):
            return f"{x*100:.1f}%"
        return "-"
    
    # Build table rows
    rows = []
    for e in events_sorted:
        kind = e["event"]
        t = e.get("ts", "-")
        frm = e.get("from", "-")
        to = e.get("to", "-")
        reason = e.get("reason", "-")
        canary = fmt_pct(e.get("canary_success"))
        control = fmt_pct(e.get("control_success"))
        delta = f"{e['improvement']:+.1%}" if isinstance(e.get("improvement"), (int, float)) else "-"
        pval = f"{e['p_value']:.3f}" if isinstance(e.get("p_value"), (int, float)) else "-"
        
        rows.append(
            f"| {t} | {kind} | `{frm}` → `{to}` | {reason} | {canary} | {control} | {delta} | {pval} |"
        )
    
    # Build markdown
    md = [
        "# Model Lineage Report",
        "",
        f"- **Nodes**: {len(nodes)}",
        f"- **Edges**: {len(edges)}",
        f"- **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Promotion / Rollback History",
        "",
        "| Time (UTC) | Event | Transition | Reason | Canary | Control | Δ | p |",
        "|------------|-------|------------|--------|-------:|--------:|---:|---|",
        *(rows or ["| – | – | – | – | – | – | – | – |"]),
        "",
        "## Notes",
        "",
        "- **Δ**: Improvement (canary - control success rate)",
        "- **p**: Statistical p-value from Wilson intervals",
        "- **Canary/Control**: Success rates during evaluation",
        "- **PROMOTION**: Stat-sig win sustained for 48h",
        "- **ROLLBACK**: Stat-sig regression detected",
        "",
        "## Lineage Graph",
        "",
        "See `lineage.svg` for visual representation (requires Graphviz).",
        "",
        "Or ASCII tree in `lineage.txt`",
    ]
    
    MD_PATH.write_text("\n".join(md), encoding="utf-8")


def render_graphviz(nodes, edges):
    """Render SVG using Graphviz (if available)"""
    if not shutil.which("dot"):
        return False
    
    # Build DOT source
    dot = [
        'digraph G {',
        '  rankdir=LR;',
        '  splines=true;',
        '  overlap=false;',
        '  fontname="Inter";',
        '  node [shape=box, style="rounded,filled", fillcolor="#F3F4F6", fontname="Inter"];',
        '  edge [color="#9CA3AF", arrowsize=0.8];',
    ]
    
    # Add nodes
    for n in sorted(nodes):
        dot.append(f'  "{n}";')
    
    # Add edges
    for u, v, label, e in edges:
        color = "#10B981" if e["event"] == "PROMOTION" else "#EF4444"
        dot.append(f'  "{u}" -> "{v}" [label="{label}", color="{color}"];')
    
    dot.append('}')
    
    # Write DOT file
    dot_src = "\n".join(dot)
    tmp = OUT_DIR / "lineage.dot"
    tmp.write_text(dot_src, encoding="utf-8")
    
    # Render to SVG
    try:
        subprocess.run(
            ["dot", "-Tsvg", str(tmp), "-o", str(SVG_PATH)],
            check=True,
            capture_output=True
        )
        return SVG_PATH.exists()
    except Exception as e:
        print(f"⚠️  Graphviz rendering failed: {e}")
        return False


def main():
    """Main entry point"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          Model Lineage Builder                                 ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    # Read events
    events = read_promotions()
    print(f"📖 Read {len(events)} events from {PROMOTIONS_LOG}")
    
    if not events:
        print("\n⚠️  No lineage data yet")
        print("   Promotions will appear after first canary deployment\n")
        
        # Create empty files
        TREE_PATH.write_text("(no lineage yet)", encoding="utf-8")
        write_markdown(set(), [], [])
        
        print("✅ Empty lineage artifacts created:")
        print(f"   - {TREE_PATH}")
        print(f"   - {MD_PATH}\n")
        return
    
    # Build graph
    nodes, edges = build_graph(events)
    print(f"📊 Built graph: {len(nodes)} nodes, {len(edges)} edges\n")
    
    # Render ASCII tree
    print("🌳 Rendering ASCII tree...")
    tree = render_ascii_tree(edges)
    TREE_PATH.write_text(tree, encoding="utf-8")
    print(f"   ✓ {TREE_PATH}")
    
    # Render markdown
    print("📝 Rendering markdown report...")
    write_markdown(nodes, edges, events)
    print(f"   ✓ {MD_PATH}")
    
    # Render SVG (if Graphviz available)
    print("🎨 Rendering SVG graph...")
    svg_ok = render_graphviz(nodes, edges)
    
    if svg_ok:
        print(f"   ✓ {SVG_PATH}")
    else:
        print("   ⊘ Graphviz not installed (install with: brew install graphviz)")
    
    # Summary
    print("\n" + "="*68)
    print("✅ Lineage Artifacts Generated")
    print("="*68)
    print("\n📄 Reports:")
    print(f"   - ASCII:  {TREE_PATH}")
    print(f"   - Report: {MD_PATH}")
    if svg_ok:
        print(f"   - Graph:  {SVG_PATH}")
    
    print("\n🔧 Commands:")
    print(f"   cat {TREE_PATH}           # View tree")
    print(f"   open {MD_PATH}            # View report")
    if svg_ok:
        print(f"   open {SVG_PATH}           # View graph")
    print()


if __name__ == "__main__":
    main()

