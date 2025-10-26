#!/bin/bash
# Start REP-Enhanced Router for Project Iceberg
#
# This script starts the Athena router with REP coordination enabled

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Project Iceberg - REP-Enhanced Router Startup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if Redis is running
echo -e "${YELLOW}Checking Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis not detected, attempting to start...${NC}"
    
    # Try to start Redis via Docker
    if command -v docker &> /dev/null; then
        if docker ps -a | grep -q athena-rep-redis; then
            docker start athena-rep-redis
        else
            docker run -d \
                --name athena-rep-redis \
                -p 127.0.0.1:6379:6379 \
                redis:7-alpine
        fi
        sleep 2
        echo -e "${GREEN}✓ Redis started via Docker${NC}"
    else
        echo -e "${YELLOW}⚠ Docker not found. Please start Redis manually:${NC}"
        echo "  brew services start redis  # macOS"
        echo "  or"
        echo "  docker run -d -p 6379:6379 redis:7-alpine"
        exit 1
    fi
fi

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
export ATHENA_REP_ENABLED=true
export ATHENA_REP_REDIS_URL=redis://127.0.0.1:6379
export ATHENA_REP_CHANNEL=athena:rep:routing
export ATHENA_REP_AGENT_ID=${ATHENA_REP_AGENT_ID:-"router_$(hostname)"}
export ATHENA_NO_CLOUD=1
export ATHENA_FAIL_CLOSED=1
export ROUTER_PORT=${ROUTER_PORT:-9113}
export ROUTER_HOST=${ROUTER_HOST:-0.0.0.0}

echo -e "${GREEN}✓ Environment configured${NC}"
echo "  Agent ID: $ATHENA_REP_AGENT_ID"
echo "  Redis: $ATHENA_REP_REDIS_URL"
echo "  Channel: $ATHENA_REP_CHANNEL"
echo "  Port: $ROUTER_PORT"

# Check if model profiles exist
PROFILES_PATH="governance/routing/model_profiles.json"
if [ ! -f "$PROFILES_PATH" ]; then
    echo -e "${YELLOW}⚠ Model profiles not found at $PROFILES_PATH${NC}"
    echo "  Creating minimal profiles..."
    
    cat > "$PROFILES_PATH" << 'EOF'
{
  "models": [
    {
      "model_id": "qwen2.5-coder:7b",
      "domain": "code",
      "domain_embedding": [0.1, 0.2, 0.3],
      "quality_score": 0.85,
      "cost": 0.0001,
      "latency_p50_ms": 50,
      "latency_p95_ms": 100,
      "is_approximate": false,
      "confidence": 0.9,
      "metadata": {"provider": "ollama"}
    },
    {
      "model_id": "llama3.1:8b",
      "domain": "general",
      "domain_embedding": [0.2, 0.3, 0.1],
      "quality_score": 0.80,
      "cost": 0.0002,
      "latency_p50_ms": 80,
      "latency_p95_ms": 150,
      "is_approximate": false,
      "confidence": 0.85,
      "metadata": {"provider": "ollama"}
    }
  ]
}
EOF
    echo -e "${GREEN}✓ Created minimal model profiles${NC}"
fi

# Start the router
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Starting REP-Enhanced Router...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$(dirname "$0")/../.."
python3 -m governance.routing.routing_api

# If script is stopped
echo ""
echo -e "${YELLOW}Router stopped.${NC}"

