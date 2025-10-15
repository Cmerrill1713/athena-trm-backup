#!/bin/bash
# Quick run script for NeuroForge Swift UI

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 NeuroForge Swift UI${NC}"
echo ""

# Check backend
API_BASE="${API_BASE:-http://localhost:8014}"
echo -e "${YELLOW}Checking backend at ${API_BASE}...${NC}"

if curl -s -f -m 2 "${API_BASE}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend healthy${NC}"
else
    echo -e "${RED}⚠️  Backend not reachable at ${API_BASE}${NC}"
    echo "   Make sure your backend is running:"
    echo "   → make green"
    echo ""
fi

# Build and run
echo -e "${YELLOW}Building and launching app...${NC}"
echo ""

export API_BASE
swift run
