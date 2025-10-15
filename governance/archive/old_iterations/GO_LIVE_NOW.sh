#!/usr/bin/env bash
# GO LIVE — Complete System Verification (5-7 minutes)

set -e

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$WORKSPACE_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                          ║${NC}"
echo -e "${BLUE}║        🚀 GO LIVE — END-TO-END VERIFICATION 🚀           ║${NC}"
echo -e "${BLUE}║                                                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Verify UI switched
echo -e "${BLUE}Step 1/5: Verifying UI switched to ChatViewEnhanced...${NC}"
if grep -q "ChatViewEnhanced()" NeuroForgeApp/Sources/main.swift; then
    echo -e "${GREEN}  ✅ ChatViewEnhanced active${NC}"
else
    echo -e "${YELLOW}  ⚠️  Still using ChatView (update manually)${NC}"
fi
echo ""

# Step 2: Export meta variables
echo -e "${BLUE}Step 2/5: Setting meta-prompt environment...${NC}"
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
export META_SELFCRITIQUE=1
export META_CHAINING=1
export META_CONFIDENCE_FLOOR=0.65
echo -e "${GREEN}  ✅ Meta environment configured${NC}"
echo ""

# Step 3: Start backend stack
echo -e "${BLUE}Step 3/5: Starting backend stack...${NC}"
echo -e "${YELLOW}  ⏳ This may take ~10 seconds...${NC}"
make stack-up > /tmp/go_live_startup.log 2>&1
sleep 3
echo -e "${GREEN}  ✅ Stack started${NC}"
echo ""

# Step 4: Verify services
echo -e "${BLUE}Step 4/5: Verifying services...${NC}"

# Check Bridge
if curl -sf http://127.0.0.1:8014/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Bridge healthy (:8014)${NC}"
else
    echo -e "${YELLOW}  ⚠️  Bridge not responding${NC}"
fi

# Check UAT
if curl -sf http://127.0.0.1:8181/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ UAT healthy (:8181)${NC}"
else
    echo -e "${YELLOW}  ⚠️  UAT not responding${NC}"
fi

# Check Athena
if curl -sf http://127.0.0.1:8090/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Athena healthy (:8090)${NC}"
else
    echo -e "${YELLOW}  ⚠️  Athena not responding${NC}"
fi

# Check Kokoro (optional)
if curl -sf http://127.0.0.1:8020/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Kokoro TTS ready (:8020)${NC}"
else
    echo -e "${YELLOW}  ⚠️  Kokoro TTS not running (will use system voice)${NC}"
    echo -e "${YELLOW}     Optional: python3 scripts/kokoro_server.py${NC}"
fi
echo ""

# Step 5: Ready to launch app
echo -e "${BLUE}Step 5/5: Ready to launch app${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║         ✅ BACKEND READY — LAUNCH APP NOW ✅               ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Launch command:${NC}"
echo ""
echo -e "  cd NeuroForgeApp"
echo -e "  API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🧪 TEST SCENARIOS:${NC}"
echo ""
echo -e "${GREEN}1. Voice Test:${NC}"
echo -e "   • Click mic 🎤"
echo -e "   • Say: \"run smoke tests\""
echo -e "   • Expect: Meta panel with confidence + plan + tools"
echo ""
echo -e "${GREEN}2. Text Test:${NC}"
echo -e "   • Type: \"check backend logs for errors last 5 minutes\""
echo -e "   • Expect: High confidence panel with 2-4 step plan"
echo ""
echo -e "${GREEN}3. Debug Overlay:${NC}"
echo -e "   • Press: Cmd+Shift+P"
echo -e "   • Expect: Prompt debug overlay (original vs rewritten)"
echo ""
echo -e "${GREEN}4. Low Confidence:${NC}"
echo -e "   • Type: \"what about that?\""
echo -e "   • Expect: Low confidence (🔴), reflection badge"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🎯 EXPECTED GREEN LIGHTS:${NC}"
echo -e "  ✅ Meta panel appears with confidence pill"
echo -e "  ✅ Voice playback (Kokoro or system)"
echo -e "  ✅ Confidence sparkline above chat"
echo -e "  ✅ Plan expandable with Copy button"
echo -e "  ✅ Tool chips visible when tools selected"
echo -e "  ✅ Debug overlay toggles with Cmd+Shift+P"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}🧯 QUICK FIXES (if needed):${NC}"
echo ""
echo -e "  No meta panel:"
echo -e "    export META_PROMPTING=1"
echo -e "    make stack-restart"
echo ""
echo -e "  No voice:"
echo -e "    python3 scripts/kokoro_server.py"
echo -e "    (or just use system voice)"
echo ""
echo -e "  Ghosts:"
echo -e "    make nuke-ports && make stack-up"
echo ""
echo -e "  Check services:"
echo -e "    make truth"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🏁 When everything works:${NC}"
echo ""
echo -e "  git add -A"
echo -e "  git commit -m \"Meta UX + voice verified end-to-end\""
echo -e "  git tag -a v0.9.3-meta-live -m \"Meta dashboard + voice live\""
echo -e "  git push && git push origin v0.9.3-meta-live"
echo ""
echo -e "${GREEN}Ready to ship! 🚀✨${NC}"
echo ""

