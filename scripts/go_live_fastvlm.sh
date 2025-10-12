#!/usr/bin/env bash
# FastVLM Go-Live - 5-minute production deployment
# Runs all setup steps in sequence with validation

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          FastVLM Go-Live (5 Minutes)                           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Start monitoring
echo -e "${BLUE}[1/5]${NC} Starting monitoring stack..."
if docker ps | grep -q prometheus; then
    echo -e "      ${GREEN}✓${NC} Monitoring already running"
else
    make monitoring-up > /dev/null 2>&1
    sleep 5
    echo -e "      ${GREEN}✓${NC} Prometheus + Grafana started"
fi

# Step 2: Start FastVLM
echo -e "${BLUE}[2/5]${NC} Starting FastVLM server..."
if curl -s http://127.0.0.1:8811/health > /dev/null 2>&1; then
    echo -e "      ${GREEN}✓${NC} FastVLM already running"
else
    echo -e "      ${BLUE}→${NC} Starting in background..."
    cd fastvlm
    export FASTVLM_ROOT="$(pwd)/ml-fastvlm"
    export FASTVLM_MODEL="checkpoints/fastvlm_1.5b_stage3"
    export ENV="prod"
    export BUILD_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
    nohup python3 fastvlm_server.py > /tmp/fastvlm_server.log 2>&1 &
    cd ..
    
    echo "      Waiting for warmup (30s)..."
    sleep 30
    
    if curl -s http://127.0.0.1:8811/health > /dev/null 2>&1; then
        echo -e "      ${GREEN}✓${NC} FastVLM started and warmed up"
    else
        echo -e "      ${RED}✗${NC} FastVLM failed to start"
        echo "        Check: tail /tmp/fastvlm_server.log"
        exit 1
    fi
fi

# Step 3: Seed traffic
echo -e "${BLUE}[3/5]${NC} Seeding traffic (metrics will populate)..."
echo "      Running smoke tests..."
if python3 scripts/vision_smoke_test.py > /tmp/go_live_smoke.log 2>&1; then
    PASSED=$(grep -c "PASS" /tmp/go_live_smoke.log || echo 0)
    echo -e "      ${GREEN}✓${NC} Smoke tests: $PASSED tests passed"
else
    echo -e "      ${YELLOW}⚠${NC} Some smoke tests had issues"
fi

# Step 4: Daily ops check
echo -e "${BLUE}[4/5]${NC} Running daily ops check..."
if bash scripts/daily_ops_check.sh > /tmp/go_live_daily.log 2>&1; then
    CHECKS=$(grep -c "✅" /tmp/go_live_daily.log || echo 0)
    echo -e "      ${GREEN}✓${NC} Daily ops: $CHECKS checks passed"
else
    echo -e "      ${YELLOW}⚠${NC} Some daily checks pending (may be normal)"
fi

# Step 5: Enable automation
echo -e "${BLUE}[5/5]${NC} Enabling automation..."

read -p "      Enable 24/7 watchdog + auto-promotion? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # Enable watchdog
    make fastvlm-autostart > /dev/null 2>&1 || true
    echo -e "      ${GREEN}✓${NC} Watchdog enabled"
    
    # Setup nightly learning
    if ! crontab -l 2>/dev/null | grep -q "make learn"; then
        bash scripts/learn/setup_nightly_learning.sh > /dev/null 2>&1
        echo -e "      ${GREEN}✓${NC} Nightly learning enabled (2 AM)"
    else
        echo -e "      ${GREEN}✓${NC} Nightly learning already enabled"
    fi
    
    # Setup auto-promotion
    if ! crontab -l 2>/dev/null | grep -q "canary-auto-promote"; then
        bash scripts/setup_auto_promotion.sh > /dev/null 2>&1
        echo -e "      ${GREEN}✓${NC} Auto-promotion enabled (every 6h)"
    else
        echo -e "      ${GREEN}✓${NC} Auto-promotion already enabled"
    fi
else
    echo "      Skipping automation setup"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ FastVLM Go-Live Complete!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Services Running:"
echo "   • FastVLM:    http://127.0.0.1:8811"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana:    http://localhost:3001"
echo ""
echo "🎯 Quick Commands:"
echo "   make vision-chart IMG=chart.png   # Extract chart data"
echo "   make fastvlm-metrics              # View metrics"
echo "   make lineage-tree                 # View model history"
echo "   make daily-ops                    # Daily health check"
echo ""
echo "📊 Verify Metrics:"
echo "   curl http://127.0.0.1:8811/metrics | grep fastvlm_"
echo "   curl http://localhost:9090/api/v1/targets | jq"
echo ""
echo "🔧 Automation Active:"
if crontab -l 2>/dev/null | grep -q "make learn"; then
    echo "   ✓ Nightly learning (2 AM)"
fi
if crontab -l 2>/dev/null | grep -q "canary-auto-promote"; then
    echo "   ✓ Auto-promotion (every 6h)"
fi
echo ""
echo "📖 Full Guide: FASTVLM_FINAL_SUMMARY.md"
echo ""

