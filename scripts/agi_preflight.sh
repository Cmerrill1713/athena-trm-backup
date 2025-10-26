#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🔍 AGI Autonomous Fix - Preflight Checks"
echo "════════════════════════════════════════════════════════════════"

FAILED=0

# 1. AGI Core
echo -n "AGI Core (8000)............... "
if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ HEALTHY"
else
    echo "❌ DOWN"
    FAILED=$((FAILED+1))
fi

# 2. Frontend MCP Tools
echo -n "Frontend Tools (8413)......... "
if curl -fsS http://localhost:8413/health >/dev/null 2>&1; then
    echo "✅ ONLINE"
else
    echo "⚠️  OFFLINE (optional, skipping)"
    # Not incrementing FAILED - this is optional
fi

# 3. LLM Path (Gateway or UAI)
echo -n "LLM Path (8015/8080).......... "
if curl -fsS http://localhost:8015/ready >/dev/null 2>&1 || curl -fsS http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ READY"
else
    echo "❌ DOWN"
    FAILED=$((FAILED+1))
fi

# 4. MCP Ecosystem
echo -n "MCP Ecosystem (8412).......... "
if curl -fsS http://localhost:8412/health >/dev/null 2>&1; then
    echo "✅ HEALTHY"
else
    echo "⚠️  DEGRADED (optional)"
fi

# 5. Check for lock
echo -n "Lock Check.................... "
if [ -f /tmp/agi_frontend_fix.lock ]; then
    echo "⚠️  Fix already running"
    FAILED=$((FAILED+1))
else
    echo "✅ CLEAR"
fi

# 6. Check git repo
echo -n "Git Repository................ "
if cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp 2>/dev/null && git rev-parse --git-dir >/dev/null 2>&1; then
    echo "✅ FOUND (branch: $(git branch --show-current))"
else
    echo "❌ NOT FOUND"
    FAILED=$((FAILED+1))
fi

echo "════════════════════════════════════════════════════════════════"

if [ $FAILED -gt 0 ]; then
    echo "❌ Preflight FAILED ($FAILED checks)"
    echo ""
    echo "Fix issues and retry. Common fixes:"
    echo "  • AGI Core:        docker compose up -d agi-core"
    echo "  • Frontend Tools:  docker compose up -d mcp-frontend-tools"
    echo "  • LLM Path:        docker compose up -d athena-api uai"
    echo ""
    exit 1
else
    echo "✅ Preflight PASSED - Ready to launch"
    echo ""
fi
