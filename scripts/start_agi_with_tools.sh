#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  🧠 Starting AGI Core with Full Tool Access"
echo "════════════════════════════════════════════════════════════════"

cd /Users/christianmerrill/Documents/GitHub

# Kill existing AGI Core
kill $(cat /tmp/agi-core.pid 2>/dev/null) 2>/dev/null || true
sleep 2

# Set environment variables
export PYTHONPATH=/Users/christianmerrill/Documents/GitHub
export PYTHONUNBUFFERED=1

# Tool endpoints
export TOOL_FE_XCODE="http://localhost:8413/tool/xcode_build"
export TOOL_FE_LAUNCH="http://localhost:8413/tool/app_launch"
export TOOL_FE_PROBE="http://localhost:8413/tool/ui_typing_probe"
export TOOL_FE_REFLEX="http://localhost:8413/tool/swift_frontend_reflex"
export TOOL_GIT_PR="http://localhost:8412/tool/git_commit_push_pr"
export TOOL_MCP_WEB_SEARCH="http://localhost:8412/tool/web_search"
export TOOL_MCP_FS_READ="http://localhost:8412/tool/file_read"
export TOOL_MCP_FS_WRITE="http://localhost:8412/tool/file_write"
export TOOL_MCP_FS_PATCH="http://localhost:8412/tool/file_apply_patch"
export TOOL_MCP_SHELL="http://localhost:8412/tool/shell"
export TOOL_UAI_CHAT="http://localhost:8080/v1/chat/completions"

# Start AGI Core
python3 -m uvicorn agi_core.agi_service:app --host 0.0.0.0 --port 8000 > /tmp/agi-core.log 2>&1 &
echo $! > /tmp/agi-core.pid

echo "Waiting for AGI Core to start..."
sleep 8

# Test
if curl -fsS -X POST http://localhost:8000/api/execute \
    -H 'Content-Type: application/json' \
    -d '{"objective":"healthcheck","context":{},"tools":[],"max_steps":1}' >/dev/null 2>&1; then
    echo "✅ AGI Core started successfully (PID: $(cat /tmp/agi-core.pid))"
    echo ""
    echo "Ready for autonomous fixes!"
    echo "  make agi-fix-frontend"
else
    echo "❌ AGI Core failed to start"
    echo "Check logs: tail -f /tmp/agi-core.log"
    exit 1
fi
