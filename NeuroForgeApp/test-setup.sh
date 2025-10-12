#!/bin/bash
# Validate NeuroForge Swift UI setup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🧪 NeuroForge Setup Validation${NC}"
echo ""

# Check 1: Package.swift exists
echo -n "1. Package.swift exists... "
if [ -f "Package.swift" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

# Check 2: Sources directory structure
echo -n "2. Sources directory structure... "
if [ -d "Sources/Config" ] && \
   [ -d "Sources/Network" ] && \
   [ -d "Sources/Routing" ] && \
   [ -d "Sources/Features" ] && \
   [ -d "Sources/Diagnostics" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

# Check 3: All source files present
echo -n "3. All source files present... "
files=(
    "Sources/main.swift"
    "Sources/Config/APIBase.swift"
    "Sources/Network/APIClient.swift"
    "Sources/Network/APIError.swift"
    "Sources/Routing/TaskClassifier.swift"
    "Sources/Features/ChatView.swift"
    "Sources/Features/KeyCatchingTextView.swift"
    "Sources/Diagnostics/HealthBanner.swift"
)
all_present=true
for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        all_present=false
        break
    fi
done
if $all_present; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ Missing: $file${NC}"
    exit 1
fi

# Check 4: Build succeeds
echo -n "4. Swift build succeeds... "
if swift build > /tmp/neuroforge_build.log 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo "Build log:"
    cat /tmp/neuroforge_build.log
    exit 1
fi

# Check 5: Backend health (optional)
echo -n "5. Backend health check... "
API_BASE="${API_BASE:-http://localhost:8014}"
if curl -s -f -m 2 "${API_BASE}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not running (optional)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 All checks passed!${NC}"
echo ""
echo "Next steps:"
echo "  ./run.sh                    # Launch the app"
echo "  make run                    # Alternative launcher"
echo "  make open                   # Open in Xcode"
echo ""
