#!/bin/bash
# validate_swift_app.sh - Validate NeuroForgeApp setup and runtime

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Swift App Validation - NeuroForgeApp                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Kill any ghost instances
echo "1️⃣  Checking for ghost instances..."
if pgrep -f "NeuroForgeApp" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Found running instance, stopping...${NC}"
    pkill -f "NeuroForgeApp" 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Stopped${NC}"
else
    echo -e "${GREEN}✅ No ghost instances${NC}"
fi
echo ""

# Step 2: Check source files exist
echo "2️⃣  Checking source files..."
cd "$(dirname "$0")/../NeuroForgeApp"

required_files=(
    "Sources/main.swift"
    "Sources/ChatInputBar.swift"
    "Sources/AuthInterceptor.swift"
    "Sources/Governance/GovernanceClient.swift"
    "Sources/Governance/GovernanceViewModel.swift"
)

all_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file (MISSING)"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo -e "\n${RED}❌ Some required files are missing!${NC}"
    exit 1
fi
echo ""

# Step 3: Clean build artifacts
echo "3️⃣  Cleaning build artifacts..."
if [ -d ".build" ]; then
    rm -rf .build
    echo -e "${GREEN}✅ Cleaned .build${NC}"
fi

if [ -d "~/Library/Developer/Xcode/DerivedData" ]; then
    echo -e "${YELLOW}ℹ️  Consider: rm -rf ~/Library/Developer/Xcode/DerivedData/*${NC}"
fi
echo ""

# Step 4: Build app
echo "4️⃣  Building app..."
if swift build 2>&1 | tee /tmp/swift_build.log; then
    echo -e "${GREEN}✅ Build successful${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    echo ""
    echo "Last 20 lines of build log:"
    tail -20 /tmp/swift_build.log
    exit 1
fi
echo ""

# Step 5: Check for warnings
echo "5️⃣  Checking for warnings..."
warning_count=$(grep -c "warning:" /tmp/swift_build.log || true)
if [ "$warning_count" -eq 0 ]; then
    echo -e "${GREEN}✅ Zero warnings${NC}"
else
    echo -e "${YELLOW}⚠️  $warning_count warning(s) found:${NC}"
    grep "warning:" /tmp/swift_build.log | head -5
fi
echo ""

# Step 6: Check binary exists
echo "6️⃣  Checking binary..."
if [ -f ".build/debug/NeuroForgeApp" ]; then
    echo -e "${GREEN}✅ Binary exists: .build/debug/NeuroForgeApp${NC}"
    ls -lh .build/debug/NeuroForgeApp | awk '{print "   Size: " $5}'
else
    echo -e "${RED}❌ Binary not found!${NC}"
    exit 1
fi
echo ""

# Step 7: Check governance backend
echo "7️⃣  Checking governance backend..."
if curl -sf --max-time 2 http://localhost:9110/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Orchestrator (9110) is up${NC}"
else
    echo -e "${YELLOW}⚠️  Orchestrator (9110) is down${NC}"
    echo "   Start with: docker-compose -f docker-compose.athena-governance.yml up -d"
fi
echo ""

# Step 8: Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Validation Summary                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Status:"
echo -e "  ${GREEN}✅${NC} Source files present"
echo -e "  ${GREEN}✅${NC} Build successful"
echo -e "  ${GREEN}✅${NC} Binary created"
if [ "$warning_count" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} Zero warnings"
else
    echo -e "  ${YELLOW}⚠️${NC}  $warning_count warning(s)"
fi
echo ""
echo "Ready to run:"
echo "  cd NeuroForgeApp && .build/debug/NeuroForgeApp"
echo ""
echo "Or use Makefile:"
echo "  make -f Makefile.ui ui-run"
echo ""

exit 0
