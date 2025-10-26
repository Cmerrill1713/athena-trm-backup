#!/bin/bash
# Warmup services for NeuroForge UI tests
# Cuts first-run latency by pre-warming endpoints

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 Warming up NeuroForge services...${NC}"

# Base URLs
API_BASE="${API_BASE:-http://localhost:8014}"
TTS_BASE="${TTS_BASE:-http://localhost:8888}"
FASTVLM_BASE="${FASTVLM_BASE:-http://localhost:8811}"
WEAVIATE_BASE="${WEAVIATE_BASE:-http://localhost:8090}"

# Function to warm up an endpoint
warmup_endpoint() {
    local url="$1"
    local name="$2"
    local timeout="${3:-5}"

    echo -n "  Warming $name ($url)... "

    if curl -s -f -m "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Not available${NC}"
        return 1
    fi
}

# Warm up main API
warmup_endpoint "$API_BASE/health" "Main API" 10

# Warm up TTS service
warmup_endpoint "$TTS_BASE/health" "TTS Service" 5

# Warm up FastVLM
warmup_endpoint "$FASTVLM_BASE/health" "FastVLM" 5

# Warm up Weaviate
warmup_endpoint "$WEAVIATE_BASE/v1/meta" "Weaviate" 5

# Optional: Warm up chat endpoint with a simple request
echo -n "  Warming chat endpoint... "
if curl -s -f -m 10 \
    -X POST "$API_BASE/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"kind":"smalltalk","text":"ping","imageBase64":null}' \
    > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️  Chat not responding${NC}"
fi

echo -e "${GREEN}🎉 Service warmup complete!${NC}"
