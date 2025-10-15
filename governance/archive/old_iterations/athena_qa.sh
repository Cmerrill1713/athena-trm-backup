#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Athena QA sweep =="

# ---- Guards (optional paths, adjust to your repo) ----
SWIFT_DIR="NeuroForgeApp"
SRC_DIRS=("NeuroForgeApp/Sources" "scripts" "src" "prometheus" "sql" "docker")
PROM_RULES_DIR="prometheus"      # where your *.yml alert/rule files live
SQL_DIR="sql"                    # where *.sql lives
DOCKERFILE="Dockerfile*"
PY_DIRS=("scripts" "src")
SHELL_DIRS=("scripts")
YAML_DIRS=(".")


# ---- Swift Lint/Format (check) ----
if [ -d "$SWIFT_DIR" ]; then
  echo "• SwiftLint"
  swiftlint --strict || true     # non-blocking? change to without || true to make blocking

  echo "• SwiftFormat (lint only)"
  swiftformat --lint "$SWIFT_DIR/Sources" || true
fi

# ---- Swift static analysis & tests (Debug) ----
if [ -d "$SWIFT_DIR" ]; then
  echo "• Swift build (Debug)"
  cd "$SWIFT_DIR" && swift build 2>&1 | tail -10 || true
  cd "$ROOT"
fi

# ---- Python QA ----
if compgen -G "scripts/*.py" > /dev/null || compgen -G "src/*.py" > /dev/null; then
  echo "• ruff (lint)"
  ruff check scripts src || true

  echo "• mypy (types)"
  mypy scripts src --ignore-missing-imports || true

  echo "• bandit (security)"
  bandit -r scripts src -q || true
fi

# ---- Shell QA ----
if [ -d "scripts" ]; then
  echo "• shellcheck"
  find "${SHELL_DIRS[@]}" -type f -name "*.sh" -print0 2>/dev/null | xargs -0 -I{} shellcheck -x {} || true
fi

# ---- YAML/TOML/JSON sanity ----
echo "• yamllint"
yamllint -s "${YAML_DIRS[@]}" || true

echo "• JSON sanity (package files & configs)"
find . -type f \( -name "*.json" -o -name "*.settings" \) -not -path "./build/*" -not -path "./DerivedData/*" -not -path "./.build/*" \
  -exec sh -c 'jq empty "{}" 2>/dev/null || echo "  ⚠️  Invalid JSON: {}"' \; || true

# ---- SQL ----
if [ -d "$SQL_DIR" ]; then
  echo "• sqlfluff"
  sqlfluff lint "$SQL_DIR" || true
fi

# ---- Prometheus Rules/Alerts ----
if [ -d "$PROM_RULES_DIR" ]; then
  if command -v promtool >/dev/null 2>&1; then
    echo "• promtool check rules"
    find "$PROM_RULES_DIR" -type f \( -name "*.yml" -o -name "*.yaml" \) \
      -exec promtool check rules {} \; || true
  else
    echo "• promtool not installed (skip). Install from Prometheus releases if you want this check."
  fi
fi

# ---- Dockerfile ----
if compgen -G "$DOCKERFILE" > /dev/null; then
  echo "• hadolint"
  for f in $DOCKERFILE; do
    echo "  Checking $f..."
    hadolint "$f" || true
  done
fi

# ---- Markdown (optional) ----
if command -v markdownlint >/dev/null 2>&1; then
  echo "• markdownlint"
  markdownlint '**/*.md' --ignore build --ignore DerivedData --ignore .build --ignore node_modules || true
fi

echo "✅ QA sweep finished"
