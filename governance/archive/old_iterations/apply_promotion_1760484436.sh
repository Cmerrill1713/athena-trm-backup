#!/usr/bin/env bash
# Apply Promotion - Automatically apply canary promotion
# Triggered when auto_promote_canary.py returns exit code 42

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Auto-Apply Canary Promotion                           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Load promotion state
STATE_FILE="/tmp/fastvlm_canary_promotion_state.json"
if [ ! -f "$STATE_FILE" ]; then
    echo "❌ No promotion state found"
    echo "   Run: make canary-auto-promote"
    exit 1
fi

# Extract promoted models
PROMOTED_FROM=$(jq -r '.promoted_from // empty' "$STATE_FILE")
PROMOTED_TO=$(jq -r '.promoted_to // empty' "$STATE_FILE")
IMPROVEMENT=$(jq -r '.improvement // empty' "$STATE_FILE")
PROMOTED_AT=$(jq -r '.promoted_at // empty' "$STATE_FILE")

if [ -z "$PROMOTED_TO" ]; then
    echo "❌ No promotion in state"
    echo "   Promotion has not been triggered yet"
    exit 1
fi

echo -e "${BLUE}Promotion Details:${NC}"
echo "  From:        $PROMOTED_FROM"
echo "  To:          $PROMOTED_TO"
echo "  Improvement: $IMPROVEMENT"
echo "  Triggered:   $PROMOTED_AT"
echo ""

# Step 1: Update environment config
echo -e "${BLUE}[1/4]${NC} Updating .env.fastvlm..."
if [ -f ".env.fastvlm" ]; then
    # Backup
    cp .env.fastvlm .env.fastvlm.backup
    
    # Update CONTROL_MODEL if it exists
    if grep -q "^CONTROL_MODEL=" .env.fastvlm; then
        sed -i.bak "s|^CONTROL_MODEL=.*|CONTROL_MODEL=\"$PROMOTED_TO\"|" .env.fastvlm
        echo -e "      ${GREEN}✓${NC} Updated CONTROL_MODEL to $PROMOTED_TO"
    else
        echo "CONTROL_MODEL=\"$PROMOTED_TO\"" >> .env.fastvlm
        echo -e "      ${GREEN}✓${NC} Added CONTROL_MODEL=$PROMOTED_TO"
    fi
    
    # Clean up sed backup
    rm -f .env.fastvlm.bak
else
    echo -e "      ${YELLOW}⚠${NC} .env.fastvlm not found, creating..."
    cp fastvlm/env.template .env.fastvlm
    echo "CONTROL_MODEL=\"$PROMOTED_TO\"" >> .env.fastvlm
fi

# Step 2: Disable canary
echo -e "${BLUE}[2/4]${NC} Disabling canary..."
export CANARY_ENABLED=false
export CANARY_PERCENT=0
echo "export CANARY_ENABLED=false" > /tmp/canary.env
echo "export CANARY_PERCENT=0" >> /tmp/canary.env
echo -e "      ${GREEN}✓${NC} Canary disabled"

# Step 3: Log promotion event
echo -e "${BLUE}[3/4]${NC} Logging promotion event..."
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
PROMOTION_LOG="$LOG_DIR/promotions.log"

cat >> "$PROMOTION_LOG" <<EOF
[$(date '+%Y-%m-%d %H:%M:%S')] PROMOTION
  From: $PROMOTED_FROM
  To: $PROMOTED_TO
  Improvement: $IMPROVEMENT
  Triggered: $PROMOTED_AT
  Applied: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo -e "      ${GREEN}✓${NC} Logged to $PROMOTION_LOG"

# Step 4: Reload services (if running)
echo -e "${BLUE}[4/4]${NC} Reloading services..."
if pgrep -f fastvlm_server.py > /dev/null; then
    echo "      FastVLM server running, consider restart:"
    echo "        make fastvlm-down && make fastvlm-server"
else
    echo -e "      ${GREEN}✓${NC} No restart needed (server not running)"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Promotion Applied Successfully${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Changes:"
echo "   • Control model: $PROMOTED_FROM → $PROMOTED_TO"
echo "   • Canary: Disabled"
echo "   • Config: .env.fastvlm updated"
echo "   • Logged: $PROMOTION_LOG"
echo ""
echo "📋 Next Steps:"
echo "   1. Source new config: set -a; source .env.fastvlm; set +a"
echo "   2. Verify: make learn-verify"
echo "   3. Monitor: make fastvlm-confidence"
echo ""
echo "🔄 For next iteration:"
echo "   Deploy new canary: make canary-10 CANARY_MODEL=<next-model>"
echo ""

