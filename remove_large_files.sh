#!/bin/bash

echo "🗑️  REMOVING LARGE FILES FROM GIT"
echo "=================================="
echo ""

echo "Removing files > 100MB..."

# Remove the 5 files that exceed 100MB
git rm --cached "governance/archive/old_iterations/libtorch_cpu.dylib"
git rm --cached "governance/judicial/evaluation/grafana_grafana_latest.tar"
git rm --cached "governance/judicial/evaluation/prom_prometheus_latest.tar"
git rm --cached "governance/executive/orchestration/postgres_15-alpine.tar"
git rm --cached "archive/2025-10-17-dedupe-sweep/policy_compiler_dump.tar.gz"

echo ""
echo "Removing files > 50MB..."

# Remove large files > 50MB
git rm --cached ".rag_seed_state.json"
git rm --cached "agi_core/.rag_seed_state.json" 2>/dev/null || true
git rm --cached "agi_core/.dynamic_rag_seed_state.json" 2>/dev/null || true
git rm --cached "governance/judicial/evaluation/UITestArtifacts.zip"
git rm --cached "governance/judicial/evaluation/UITestArtifacts_2.zip"
git rm --cached "governance/judicial/evaluation/UITestArtifacts_3.zip"

echo ""
echo "✅ Large files removed from git index"

