#!/bin/bash
# Athena Terminal Adapter
# Usage: athena-assist "explain why /kb/search failing"

ATHENA_URL="http://localhost:8765"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

query="$1"

if [ -z "$query" ]; then
    echo "Usage: athena-assist \"your question about the code\""
    echo "Example: athena-assist \"why is this function slow?\""
    exit 1
fi

# Get current context
repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
current_file=$(git ls-files --full-name "$(pwd)" 2>/dev/null | head -1 || echo "")

# Build request
request_json=$(cat << EOF
{
  "repoRoot": "$repo_root",
  "file": "$current_file",
  "query": "$query",
  "intent": "explain-and-fix"
}
EOF
)

echo -e "${BLUE}🤖 Athena is thinking...${NC}"
echo ""

# Call Athena
response=$(curl -s -X POST "$ATHENA_URL/assist" \
  -H "Content-Type: application/json" \
  -d "$request_json")

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Athena daemon not reachable${NC}"
    echo "Start with: make athena-up"
    exit 1
fi

# Parse response
summary=$(echo "$response" | jq -r '.summary' 2>/dev/null)
citations=$(echo "$response" | jq -r '.citations[]' 2>/dev/null)

if [ -z "$summary" ] || [ "$summary" = "null" ]; then
    echo -e "${YELLOW}⚠️  Athena returned no answer${NC}"
    echo "Response: $response"
    exit 1
fi

# Display result
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Athena's Answer:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "$summary"
echo ""

if [ ! -z "$citations" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Citations:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "$citations" | while read cite; do
        echo "  📎 $cite"
    done
    echo ""
fi

echo -e "${GREEN}✅ Done!${NC}"

