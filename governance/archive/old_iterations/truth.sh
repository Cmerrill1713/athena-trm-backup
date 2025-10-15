#!/bin/bash
# Truth Serum - Reality check for stack services
# No vibes, just receipts

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  TRUTH SERUM - Stack Reality Check                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "=== WHO'S ON PORTS ==="
echo "Bridge (8014):"
lsof -n -iTCP:8014 -sTCP:LISTEN -P || echo "  (none)"
echo ""
echo "Athena (8090):"
lsof -n -iTCP:8090 -sTCP:LISTEN -P || echo "  (none)"
echo ""
echo "UAT (8181):"
lsof -n -iTCP:8181 -sTCP:LISTEN -P || echo "  (none)"
echo ""

echo "=== CURL HEADERS (BRIDGE) ==="
curl -s -D - http://127.0.0.1:8014/health -o /dev/null 2>&1 | sed -n '1,20p' || echo "Bridge not responding"
echo ""

echo "=== BRIDGE HEALTH BODY ==="
curl -s http://127.0.0.1:8014/health 2>/dev/null | jq . || echo "Bridge not responding or no jq"
echo ""

echo "=== ATHENA HEALTH ==="
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8090/health 2>/dev/null | jq . || echo "Athena not responding"
echo ""

echo "=== UAT HEALTH ==="
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/health 2>/dev/null | jq . || echo "UAT not responding"
echo ""

echo "=== PYTHON/PKG FINGERPRINTS (terminal) ==="
echo "Python location: $(command -v python3)"
echo "Python version: $(python3 -V)"
echo "Pytest location: $(command -v pytest 2>/dev/null || echo 'not found')"
if command -v pytest &>/dev/null; then
    echo "Pytest version: $(pytest --version 2>/dev/null || echo 'error')"
fi
python3 -c "import sys,site; print('sys.executable =', sys.executable); print('site packages  =', site.getsitepackages())"
echo ""

echo "=== ENV SNAPSHOT (.env.stack respected?) ==="
env | grep -E 'UAT_|ATH_|BRIDGE_|USE_MOCK|ENV=|PYTEST|VIRTUAL|PYENV' | sort || echo "(no matching env vars)"
echo ""

echo "=== PID FILES ==="
echo "Stack PIDs:"
for pid_file in .stack/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        name=$(basename "$pid_file" .pid)
        if ps -p "$pid" >/dev/null 2>&1; then
            echo "  ✓ $name: PID $pid (running)"
        else
            echo "  ✗ $name: PID $pid (STALE - process not found)"
        fi
    fi
done
echo ""

echo "=== GIT STATUS ==="
git_hash=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
git_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "Branch: $git_branch"
echo "Commit: $git_hash"
echo ""

echo "=== OPTIONAL SERVICES ==="
echo "Kokoro TTS (8020):"
lsof -n -iTCP:8020 -sTCP:LISTEN -P 2>/dev/null || echo "  ⚠️  Not running (start: make stack-voice)"
echo ""
echo "RAG Service (8015):"
lsof -n -iTCP:8015 -sTCP:LISTEN -P 2>/dev/null || echo "  ⚠️  Not running (start: make stack-rag)"
echo ""
echo "FastVLM (8811):"
lsof -n -iTCP:8811 -sTCP:LISTEN -P 2>/dev/null || echo "  ⚠️  Not running (start: make stack-vision)"
echo ""
echo "Vision RAG (8016):"
lsof -n -iTCP:8016 -sTCP:LISTEN -P 2>/dev/null || echo "  ⚠️  Not running (start: make stack-vision)"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  INTERPRETATION GUIDE                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🔍 Multiple PIDs per port → GHOSTS (kill with: make nuke-ports)"
echo "🔍 Missing x-service headers → OLD PROCESS or different binary"
echo "🔍 Python paths differ → Cursor using different environment"
echo "🔍 Stale PID files → Process died, run: make stack-down && make stack-up"
echo "🎚️  Optional services ⚠️  → Layer on: make stack-voice/rag/vision/full"
echo ""
