#!/usr/bin/env bash
# 2-Minute Launch Checklist
# Verifies all systems operational

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Launch Checklist - All Systems                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

FAIL_COUNT=0

# Helper function
check_service() {
    local name="$1"
    local url="$2"
    local timeout="${3:-5}"
    
    if curl -sf --max-time "$timeout" "$url" >/dev/null 2>&1; then
        echo "✅ $name - OPERATIONAL"
        return 0
    else
        echo "❌ $name - NOT RUNNING"
        ((FAIL_COUNT++))
        return 1
    fi
}

echo "━━━ Core Services ━━━"
check_service "Assistant Broker     " "http://127.0.0.1:8080/v1/health"
check_service "Knowledge Gateway    " "http://127.0.0.1:8088/health"
check_service "Weaviate Vector DB   " "http://127.0.0.1:8090/v1/.well-known/ready"

echo ""
echo "━━━ Authentication ━━━"
if [ -f ~/.assistant-broker-token ]; then
    TOKEN=$(cat ~/.assistant-broker-token)
    if [ ${#TOKEN} -ge 32 ]; then
        echo "✅ Broker token found (${#TOKEN} chars)"
    else
        echo "⚠️  Broker token too short (${#TOKEN} chars, need 32+)"
        ((FAIL_COUNT++))
    fi
else
    echo "❌ No broker token at ~/.assistant-broker-token"
    echo "   Run: cd ~/Documents/GitHub/assistant-broker && make install-agent"
    ((FAIL_COUNT++))
fi

echo ""
echo "━━━ Build Tools ━━━"
command -v swift >/dev/null && echo "✅ Swift $(swift --version | head -1 | awk '{print $4}')" || { echo "❌ Swift not found"; ((FAIL_COUNT++)); }
command -v python3 >/dev/null && echo "✅ Python $(python3 -V | awk '{print $2}')" || { echo "❌ Python not found"; ((FAIL_COUNT++)); }
command -v docker >/dev/null && echo "✅ Docker $(docker -v | awk '{print $3}' | tr -d ',')" || echo "⚠️  Docker not found"

echo ""
echo "━━━ Scripts ━━━"
SCRIPT_DIR="$HOME/Documents/GitHub/scripts"
[ -x "$SCRIPT_DIR/deliver_app.sh" ] && echo "✅ deliver_app.sh ready" || { echo "❌ deliver_app.sh missing/not executable"; ((FAIL_COUNT++)); }
[ -x "$SCRIPT_DIR/broker_client.py" ] && echo "✅ broker_client.py ready" || { echo "❌ broker_client.py missing/not executable"; ((FAIL_COUNT++)); }
[ -x "$SCRIPT_DIR/knowledge_helper.py" ] && echo "✅ knowledge_helper.py ready" || { echo "❌ knowledge_helper.py missing/not executable"; ((FAIL_COUNT++)); }
[ -x "$SCRIPT_DIR/app_wizard.py" ] && echo "✅ app_wizard.py ready" || echo "⚠️  app_wizard.py missing"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 ALL SYSTEMS GO - Ready to build!"
    echo ""
    echo "Try: python3 scripts/knowledge_helper.py 'SwiftUI patterns'"
    exit 0
else
    echo "⚠️  $FAIL_COUNT issue(s) found"
    echo ""
    echo "Start missing services:"
    echo "  cd ~/Documents/GitHub/AI-Projects/universal-ai-tools"
    echo "  docker compose -f docker-compose.knowledge-grounding.yml up -d"
    exit 1
fi

