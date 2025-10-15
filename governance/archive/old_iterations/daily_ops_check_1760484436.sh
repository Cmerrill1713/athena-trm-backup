#!/usr/bin/env bash
# Daily Ops Check - 90-second operator checklist
# Run this every morning to verify system health

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Daily Ops Check (90 seconds)                          ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. FastVLM confidence
echo -e "${BLUE}[1/3]${NC} FastVLM confidence check..."
if make fastvlm-confidence > /tmp/daily_ops_fastvlm.log 2>&1; then
    # Count ✅ in output
    CHECKS=$(grep -c "✅" /tmp/daily_ops_fastvlm.log || echo 0)
    echo -e "      ${GREEN}✓${NC} FastVLM: $CHECKS/6 checks passed"
else
    echo -e "      ${RED}✗${NC} FastVLM confidence failed"
    echo "        Check: make fastvlm-logs"
fi

# 2. Canary evaluation
echo -e "${BLUE}[2/3]${NC} Canary evaluation..."
if python3 scripts/auto_promote_canary.py > /tmp/daily_ops_canary.log 2>&1; then
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 42 ]; then
        echo -e "      ${GREEN}🎉 PROMOTION READY!${NC}"
        echo "        Run: make canary-auto-promote"
    else
        # Check if tracking
        if grep -q "Started tracking" /tmp/daily_ops_canary.log; then
            HOURS=$(grep "hours" /tmp/daily_ops_canary.log | grep -oE "[0-9]+\.[0-9]+" | head -1)
            echo -e "      ${GREEN}✓${NC} Canary better, tracking (${HOURS}h/48h)"
        else
            echo -e "      ${GREEN}✓${NC} Canary monitoring (not better yet)"
        fi
    fi
else
    if grep -q "Insufficient" /tmp/daily_ops_canary.log; then
        echo -e "      ${YELLOW}ℹ${NC} Canary: insufficient data"
    else
        echo -e "      ${YELLOW}⚠${NC} Canary evaluation issues"
    fi
fi

# 3. Auto-promotion logs (last 50 lines)
echo -e "${BLUE}[3/3]${NC} Recent auto-promotion activity..."
if [ -f logs/auto_promotion.log ]; then
    LAST_RUN=$(tail -50 logs/auto_promotion.log | grep -m1 "Auto-promote" | sed 's/.*\[/[/' || echo "No recent runs")
    echo "      Last check: $LAST_RUN"
    
    # Check for promotion events
    PROMOTIONS=$(grep -c "PROMOTION" logs/auto_promotion.log 2>/dev/null || echo 0)
    if [ "$PROMOTIONS" -gt 0 ]; then
        LAST_PROMOTION=$(grep "PROMOTION" logs/auto_promotion.log | tail -1)
        echo -e "      ${GREEN}📊 Total promotions: $PROMOTIONS${NC}"
        echo "      Last: $LAST_PROMOTION"
    fi
else
    echo "      No auto-promotion logs yet"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Daily Ops Check Complete${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Quick stats
echo "📊 Quick Stats:"
if command -v psql &> /dev/null && [ -n "${DATABASE_URL:-}" ]; then
    # Requests today
    REQUESTS_TODAY=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM routing_outcomes WHERE created_at > CURRENT_DATE;" 2>/dev/null | tr -d ' ' || echo "N/A")
    echo "   Requests today: $REQUESTS_TODAY"
    
    # Success rate (7d)
    SUCCESS_RATE=$(psql "$DATABASE_URL" -t -c "
        SELECT ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM routing_outcomes
        WHERE created_at > NOW() - INTERVAL '7 days';
    " 2>/dev/null | tr -d ' ' || echo "N/A")
    echo "   Success rate (7d): ${SUCCESS_RATE}%"
fi

echo ""
echo "🔧 Commands:"
echo "   make fastvlm-metrics          # View live metrics"
echo "   make canary-eval              # Manual canary check"
echo "   make canary-promotion-status  # Promotion timer"
echo ""

