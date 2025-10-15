#!/usr/bin/env bash
# Athena Voice Control - One-Liner Installer
# Re-enables entire voice + mapping layer in one go

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKSPACE_ROOT"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🧠 Athena Voice Control - Setup                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================================================
# 1. Make Scripts Executable
# ============================================================================

echo "1️⃣  Making scripts executable..."
chmod +x athena_voice.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x .git/hooks/pre-push 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} Scripts executable"
echo ""

# ============================================================================
# 2. Check Dependencies
# ============================================================================

echo "2️⃣  Checking dependencies..."

check_dep() {
    local name=$1
    local cmd=$2
    local install=$3
    
    if command -v "$cmd" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "  ${YELLOW}⚠${NC}  $name (install: $install)"
        return 1
    fi
}

check_dep "jq" "jq" "brew install jq"
check_dep "sox/ffmpeg" "sox" "brew install sox" || \
check_dep "sox/ffmpeg" "ffmpeg" "brew install ffmpeg" || true
check_dep "whisper (optional)" "whisper" "pip install openai-whisper" || true
check_dep "Python 3" "python3" "already installed" || true

echo ""

# ============================================================================
# 3. Verify Voice Map
# ============================================================================

echo "3️⃣  Verifying voice command map..."
if [ -f "athena_voice_map.json" ]; then
    count=$(jq 'length' athena_voice_map.json)
    echo -e "  ${GREEN}✓${NC} $count commands mapped"
    echo "     Examples:"
    jq -r 'to_entries[] | "       \"\(.key)\" → \(.value)"' athena_voice_map.json | head -3
else
    echo -e "  ${YELLOW}⚠${NC}  athena_voice_map.json not found"
fi
echo ""

# ============================================================================
# 4. Verify Pre-Push Hook
# ============================================================================

echo "4️⃣  Checking pre-push gate..."
if [ -f ".git/hooks/pre-push" ] && [ -x ".git/hooks/pre-push" ]; then
    echo -e "  ${GREEN}✓${NC} Athena pre-push gate active"
    echo "     Blocks pushes if: health fails, tests fail, ghosts detected"
else
    echo -e "  ${YELLOW}⚠${NC}  Pre-push hook missing or not executable"
fi
echo ""

# ============================================================================
# 5. Verify Stack Tools
# ============================================================================

echo "5️⃣  Verifying stack tools..."
if [ -f "Makefile" ]; then
    targets=$(make -qp | grep -E '^[a-z-]+:' | cut -d: -f1 | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✓${NC} Makefile with $targets targets"
else
    echo -e "  ${YELLOW}⚠${NC}  Makefile not found"
fi

if [ -f "scripts/truth.sh" ] && [ -x "scripts/truth.sh" ]; then
    echo -e "  ${GREEN}✓${NC} Forensic debugging (truth.sh)"
else
    echo -e "  ${YELLOW}⚠${NC}  truth.sh missing"
fi

if [ -f "scripts/stack_watchdog.sh" ] && [ -x "scripts/stack_watchdog.sh" ]; then
    echo -e "  ${GREEN}✓${NC} Self-healing watchdog"
else
    echo -e "  ${YELLOW}⚠${NC}  stack_watchdog.sh missing"
fi
echo ""

# ============================================================================
# 6. Verify Common Library
# ============================================================================

echo "6️⃣  Verifying Tier 4 common library..."
if [ -f "common/ops.py" ]; then
    if python3 -c "from common.ops import wire_tracing" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} common/ops.py (tracing, guardrails, graceful shutdown)"
    else
        echo -e "  ${YELLOW}⚠${NC}  common/ops.py exists but imports fail (missing deps?)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC}  common/ops.py not found"
fi

if [ -f "common/secrets.py" ]; then
    echo -e "  ${GREEN}✓${NC} common/secrets.py (keychain integration)"
else
    echo -e "  ${YELLOW}⚠${NC}  common/secrets.py not found"
fi
echo ""

# ============================================================================
# 7. Quick Test (Optional)
# ============================================================================

echo "7️⃣  Quick sanity test..."
if [ -f "athena_voice_map.json" ]; then
    test_cmd=$(jq -r '."ghost check"' athena_voice_map.json 2>/dev/null || echo "")
    if [ "$test_cmd" == "make truth" ]; then
        echo -e "  ${GREEN}✓${NC} Voice mapping works (ghost check → make truth)"
    else
        echo -e "  ${YELLOW}⚠${NC}  Voice mapping might need repair"
    fi
fi
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Voice control setup complete!${NC}"
echo ""
echo "🎙️  Start voice control:"
echo "     ./athena_voice.sh"
echo ""
echo "🧠 Available commands:"
echo "     cat athena_voice_map.json | jq -r 'keys[]'"
echo ""
echo "🔍 Test manually:"
echo "     make truth"
echo "     make stack-up"
echo ""
echo "📚 Documentation:"
echo "     cat START_HERE.md"
echo "     cat OPERATIONAL_REFERENCE.md"
echo ""

