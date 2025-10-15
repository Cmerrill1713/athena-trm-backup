#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(pwd)}"
echo "╔════════════════════════════════════════╗"
echo "║   Workspace Health Check               ║"
echo "╚════════════════════════════════════════╝"
echo "Scanning: $ROOT"
echo "-----------------------------------------"

# Python projects
find "$ROOT" -maxdepth 3 -type d \
  \( -name ".git" -o -name "node_modules" -o -name ".venv" \) -prune -o -type f -name "pyproject.toml" -print | while read -r p; do
  proj="$(dirname "$p")"
  echo -e "\n🐍 Python project: $proj"
  (
    cd "$proj"
    if [ -d ".venv" ]; then 
      source .venv/bin/activate 2>/dev/null || true
      echo "  ✓ venv found and activated"
    else
      echo "  ⚠ no .venv (run: uv venv --python 3.11)"
    fi
    
    echo -n "  Python: "
    python3 -V 2>/dev/null || echo "NOT FOUND"
    
    echo -n "  pip: "
    pip -V 2>/dev/null | cut -d' ' -f1-2 || echo "NOT FOUND"
    
    # Check for requirements
    if [ -f requirements.txt ]; then
      echo "  ℹ requirements.txt present"
    fi
    
    # Try ruff
    if command -v ruff >/dev/null 2>&1; then
      echo -n "  ruff: "
      ruff --version 2>/dev/null || true
    else
      echo "  ⚠ ruff not installed"
    fi
    
    # Try pytest
    if command -v pytest >/dev/null 2>&1; then
      echo -n "  pytest: "
      pytest --version 2>/dev/null | head -1 || true
    else
      echo "  ⚠ pytest not installed"
    fi
  )
done

# Node projects
find "$ROOT" -maxdepth 3 -type d \
  \( -name ".git" -o -name "node_modules" -o -name ".venv" \) -prune -o -type f -name "package.json" -print | while read -r p; do
  proj="$(dirname "$p")"
  echo -e "\n📦 Node project: $proj"
  (
    cd "$proj"
    echo -n "  node: "
    node -v 2>/dev/null || echo "NOT FOUND"
    
    echo -n "  npm: "
    npm -v 2>/dev/null || echo "NOT FOUND"
    
    if [ -f package-lock.json ]; then
      echo "  ℹ using npm"
    elif [ -f pnpm-lock.yaml ]; then
      echo "  ℹ using pnpm"
    elif [ -f yarn.lock ]; then
      echo "  ℹ using yarn"
    fi
  )
done

# Rust projects
find "$ROOT" -maxdepth 2 -type d \
  \( -name ".git" -o -name "target" \) -prune -o -type f -name "Cargo.toml" -print | while read -r p; do
  proj="$(dirname "$p")"
  echo -e "\n🦀 Rust project: $proj"
  (
    cd "$proj"
    echo -n "  cargo: "
    cargo -V 2>/dev/null || echo "NOT FOUND"
  )
done

# Swift projects
find "$ROOT" -maxdepth 2 -type d \
  \( -name ".git" -o -name ".build" \) -prune -o -type f -name "Package.swift" -print | while read -r p; do
  proj="$(dirname "$p")"
  echo -e "\n🍎 Swift project: $proj"
  (
    cd "$proj"
    echo -n "  swift: "
    swift --version 2>/dev/null | head -1 || echo "NOT FOUND"
  )
done

echo -e "\n-----------------------------------------"
echo "✅ Workspace scan complete"

