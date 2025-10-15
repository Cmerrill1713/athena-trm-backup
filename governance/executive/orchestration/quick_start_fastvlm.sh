#!/usr/bin/env bash
# Quick Start FastVLM - Run this to get everything up and validated
# Usage: bash scripts/quick_start_fastvlm.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║              FastVLM Quick Start                               ║"
echo "║           Zero to Working in ~5 Minutes                        ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo -e "${RED}❌ Error: Run this from the workspace root${NC}"
    echo "   cd /Users/christianmerrill/Documents/GitHub"
    exit 1
fi

# Step 1: Check if FastVLM is set up
echo -e "${BLUE}[1/5]${NC} Checking FastVLM setup..."
if [ -d "fastvlm/ml-fastvlm" ] && [ -d "fastvlm/ml-fastvlm/checkpoints" ]; then
    echo -e "      ${GREEN}✓${NC} FastVLM already set up"
else
    echo -e "      ${YELLOW}⚠${NC} FastVLM not set up yet"
    echo ""
    read -p "      Download FastVLM model (~2GB, takes 3-5 min)? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "      ${BLUE}→${NC} Running setup..."
        make fastvlm-setup
        echo -e "      ${GREEN}✓${NC} Setup complete"
    else
        echo -e "      ${RED}✗${NC} Cannot proceed without setup"
        echo ""
        echo "      Run manually: make fastvlm-setup"
        exit 1
    fi
fi

# Step 2: Start monitoring stack
echo -e "${BLUE}[2/5]${NC} Starting monitoring stack..."
if docker ps | grep -q prometheus; then
    echo -e "      ${GREEN}✓${NC} Monitoring already running"
else
    echo -e "      ${BLUE}→${NC} Starting Prometheus + Grafana..."
    make monitoring-up > /dev/null 2>&1
    sleep 5
    echo -e "      ${GREEN}✓${NC} Monitoring started"
    echo "        • Prometheus: http://localhost:9090"
    echo "        • Grafana:    http://localhost:3001"
fi

# Step 3: Start FastVLM server
echo -e "${BLUE}[3/5]${NC} Starting FastVLM server..."
if curl -s http://127.0.0.1:8811/health > /dev/null 2>&1; then
    echo -e "      ${GREEN}✓${NC} Server already running"
else
    echo -e "      ${BLUE}→${NC} Starting server (will run in background)..."
    
    # Start server in background
    cd fastvlm
    export FASTVLM_ROOT="$(pwd)/ml-fastvlm"
    export FASTVLM_MODEL="checkpoints/fastvlm_1.5b_stage3"
    nohup python3 fastvlm_server.py > /tmp/fastvlm_server.log 2>&1 &
    SERVER_PID=$!
    cd ..
    
    echo "        PID: $SERVER_PID"
    echo "        Logs: /tmp/fastvlm_server.log"
    
    # Wait for warmup
    echo -e "      ${BLUE}→${NC} Waiting for warmup (30 seconds)..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8811/health > /dev/null 2>&1; then
            echo -e "      ${GREEN}✓${NC} Server ready (warmed up in ${i}s)"
            break
        fi
        sleep 1
    done
    
    if ! curl -s http://127.0.0.1:8811/health > /dev/null 2>&1; then
        echo -e "      ${RED}✗${NC} Server failed to start"
        echo "        Check logs: tail /tmp/fastvlm_server.log"
        exit 1
    fi
fi

# Step 4: Run validation
echo -e "${BLUE}[4/5]${NC} Running validation..."
if bash scripts/fastvlm_validation.sh > /tmp/fastvlm_validation.log 2>&1; then
    echo -e "      ${GREEN}✓${NC} Validation passed"
else
    echo -e "      ${YELLOW}⚠${NC} Some checks didn't pass (may be normal if fresh install)"
    echo "        See: /tmp/fastvlm_validation.log"
fi

# Step 5: Create test image and run demo
echo -e "${BLUE}[5/5]${NC} Running demo..."

# Check if we have a test image
if [ -f ~/Desktop/screenshot.png ] || [ -f ~/Desktop/test.png ]; then
    TEST_IMG=$(ls ~/Desktop/screenshot.png ~/Desktop/test.png 2>/dev/null | head -1)
    echo -e "      ${GREEN}✓${NC} Found test image: $TEST_IMG"
    
    read -p "      Run vision analysis on this image? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo -e "      ${BLUE}→${NC} Analyzing image..."
        python3 scripts/athena_vision.py "$TEST_IMG" \
          "Describe this image in 2 sentences" \
          2>&1 | tail -5
    fi
else
    echo -e "      ${YELLOW}⚠${NC} No test image found"
    echo "        Create one: screencapture ~/Desktop/test.png"
    echo "        Then run: make vision IMG=~/Desktop/test.png PROMPT='describe this'"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ FastVLM Quick Start Complete!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Services Running:"
echo "   • FastVLM:    http://127.0.0.1:8811"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana:    http://localhost:3001"
echo ""
echo "🔍 Try These Commands:"
echo "   make vision-chart IMG=chart.png      # Extract chart data"
echo "   make vision-ocr IMG=doc.png          # Extract text"
echo "   make fastvlm-smoke                   # Run 6-image test suite"
echo "   make fastvlm-metrics                 # View live metrics"
echo ""
echo "📊 Check Health:"
echo "   make fastvlm-validate                # 90-second validation"
echo "   curl http://127.0.0.1:8811/health    # Server health"
echo ""
echo "🛑 Stop Services:"
echo "   make fastvlm-down                    # Stop FastVLM"
echo "   make monitoring-down                 # Stop monitoring"
echo ""
echo "📖 Full Guide: FASTVLM_GO_LIVE_GUIDE.md"
echo ""

