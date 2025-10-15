#!/bin/bash
# Complete UI test runner with proper error handling
# Usage: ./scripts/run_ui_tests.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 NeuroForge UI Test Runner${NC}"
echo "================================"

# Check if we're in the right directory
if [ ! -f "NeuroForgeApp.xcworkspace" ]; then
    echo -e "${RED}❌ Error: NeuroForgeApp.xcworkspace not found${NC}"
    echo "Please run this script from the NeuroForgeApp directory"
    exit 1
fi

# Step 1: Check backend health
echo -e "${YELLOW}1. Checking backend health...${NC}"
if ! curl -s -f -m 5 http://localhost:8014/health > /dev/null 2>&1; then
    echo -e "${RED}⚠️  Backend not responding at localhost:8014${NC}"
    echo "Please run 'make green' to start backend services"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Backend is healthy${NC}"
fi

# Step 2: Warm up services
echo -e "${YELLOW}2. Warming up services...${NC}"
bash scripts/warmup_services.sh || true

# Step 3: Create artifacts directory
echo -e "${YELLOW}3. Setting up artifacts...${NC}"
mkdir -p artifacts

# Step 4: Run UI tests
echo -e "${YELLOW}4. Running UI tests...${NC}"
echo "This may take 2-3 minutes..."

# Capture exit code for proper error handling
set +e
xcodebuild \
  -workspace NeuroForgeApp.xcworkspace \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -resultBundlePath artifacts/NeuroForgeUI.xcresult \
  -derivedDataPath DerivedData \
  test 2>&1 | tee artifacts/xcodebuild-ui-tests.log

TEST_EXIT_CODE=${PIPESTATUS[0]}
set -e

# Step 5: Collect artifacts regardless of test result
echo -e "${YELLOW}5. Collecting artifacts...${NC}"
/usr/bin/zip -qry artifacts/UITestArtifacts.zip \
  artifacts/NeuroForgeUI.xcresult \
  DerivedData/Logs || true

# Step 6: Report results
echo
echo "================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All UI tests passed!${NC}"
else
    echo -e "${RED}❌ Some UI tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo
    echo "Check the following for details:"
    echo "  📄 artifacts/xcodebuild-ui-tests.log"
    echo "  📦 artifacts/UITestArtifacts.zip"
    echo "  🖼️  artifacts/NeuroForgeUI.xcresult (open in Xcode)"
fi

echo
echo "📁 Artifacts location: artifacts/UITestArtifacts.zip"
echo "📊 Test results: artifacts/NeuroForgeUI.xcresult"
echo "📝 Build log: artifacts/xcodebuild-ui-tests.log"

# Exit with the test result code
exit $TEST_EXIT_CODE
