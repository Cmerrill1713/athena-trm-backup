#!/bin/bash
# 60-second green run - NeuroForge UI Tests
# Usage: ./scripts/quick_green_run.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 NeuroForge 60-Second Green Run${NC}"
echo "================================="

# Check if we're in the right directory
if [ ! -f "NeuroForgeApp.xcworkspace" ]; then
    echo -e "${RED}❌ Error: NeuroForgeApp.xcworkspace not found${NC}"
    echo "Please run this script from the NeuroForgeApp directory"
    exit 1
fi

# Step 1: Quick backend health check
echo -e "${YELLOW}1. Checking backend health...${NC}"
cd ..
if make green > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend services healthy${NC}"
else
    echo -e "${RED}⚠️  Backend services not responding${NC}"
    echo "Please run 'make green' from repo root first"
    exit 1
fi

# Step 2: Warm up services
echo -e "${YELLOW}2. Warming up services...${NC}"
cd NeuroForgeApp
bash scripts/warmup_services.sh || true

# Step 3: Run UI tests
echo -e "${YELLOW}3. Running UI tests...${NC}"
echo "This should take ~60 seconds..."

# Create artifacts directory
mkdir -p artifacts

# Run tests with timeout
timeout 120 xcodebuild \
  -workspace NeuroForgeApp.xcworkspace \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -resultBundlePath artifacts/NeuroForgeUI.xcresult \
  -derivedDataPath DerivedData \
  test 2>&1 | tee artifacts/xcodebuild-ui-tests.log

TEST_EXIT_CODE=${PIPESTATUS[0]}

# Step 4: Collect artifacts
echo -e "${YELLOW}4. Collecting artifacts...${NC}"
/usr/bin/zip -qry artifacts/UITestArtifacts.zip \
  artifacts/NeuroForgeUI.xcresult \
  DerivedData/Logs || true

# Step 5: Report results
echo
echo "================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 GREEN RUN SUCCESS!${NC}"
    echo -e "${GREEN}✅ All UI tests passed${NC}"
    echo -e "${GREEN}✅ Artifacts collected${NC}"
    echo -e "${GREEN}✅ Ready for production${NC}"
else
    echo -e "${RED}❌ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo
    echo "Check artifacts for details:"
    echo "  📄 artifacts/xcodebuild-ui-tests.log"
    echo "  📦 artifacts/UITestArtifacts.zip"
fi

echo
echo "📁 Artifacts: artifacts/UITestArtifacts.zip"
echo "📊 Results: artifacts/NeuroForgeUI.xcresult"
echo "⏱️  Duration: ~60 seconds"

exit $TEST_EXIT_CODE
