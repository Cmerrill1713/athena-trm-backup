#!/bin/bash
# Polished Athena System Startup Script
# Starts all services with health checks and validation

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
   ___  __  __                    
  / _ |/ /_/ /  ___ ___  ___ ___ _
 / __ / __/ _ \/ -_) _ \/ _ `/  ' \
/_/ |_\__/_//_/\__/_//_/\_,_/_/_/_/

Constitutional AI with Auto-Remediation
EOF
echo -e "${NC}"

# Check for required tools
echo -e "${BLUE}[1/5] Checking prerequisites...${NC}"
MISSING=""
for cmd in docker docker-compose jq curl; do
    if ! command -v $cmd &> /dev/null; then
        MISSING="$MISSING $cmd"
    fi
done

if [ -n "$MISSING" ]; then
    echo -e "${RED}✗ Missing required tools:$MISSING${NC}"
    echo "  Install with: brew install docker docker-compose jq"
    exit 1
fi
echo -e "${GREEN}✓ All prerequisites found${NC}"

# Check for API keys
echo -e "\n${BLUE}[2/5] Checking API configuration...${NC}"
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠ ANTHROPIC_API_KEY not set${NC}"
    echo "  Set with: export ANTHROPIC_API_KEY='your-key'"
    echo "  Continuing anyway (some features will be limited)"
else
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY configured${NC}"
fi

# Check for .env file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "  Consider copying: cp .env.example .env"
fi

# Start Docker services
echo -e "\n${BLUE}[3/5] Starting Docker services...${NC}"
echo "  This may take a few minutes on first run..."

if docker compose -f docker-compose.athena-governance.yml up -d; then
    echo -e "${GREEN}✓ Docker services started${NC}"
else
    echo -e "${RED}✗ Failed to start Docker services${NC}"
    echo "  Check: docker compose ps"
    exit 1
fi

# Wait for services to be ready
echo -e "\n${BLUE}[4/5] Waiting for services to be healthy...${NC}"

wait_for_service() {
    local name=$1
    local url=$2
    local max_wait=60
    local waited=0
    
    echo -n "  Waiting for $name..."
    
    while [ $waited -lt $max_wait ]; do
        if curl -sf --max-time 2 "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
        echo -n "."
    done
    
    echo -e " ${YELLOW}⚠ (timeout)${NC}"
    return 1
}

wait_for_service "Prometheus" "http://localhost:9090/-/healthy"
wait_for_service "Orchestrator" "http://localhost:9110/health"
wait_for_service "Remediator" "http://localhost:9112/health"
wait_for_service "Grafana" "http://localhost:3001/api/health"

# Run health check
echo -e "\n${BLUE}[5/5] Running health check...${NC}"
if [ -f "scripts/health_check.sh" ]; then
    bash scripts/health_check.sh
else
    echo -e "${YELLOW}⚠ Health check script not found, skipping${NC}"
fi

# Success message
echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Athena is Ready!                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📊 Dashboards:"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana:    http://localhost:3001 (admin/admin)"
echo ""
echo "🔧 Services:"
echo "   • Orchestrator: http://localhost:9110/health"
echo "   • Remediator:   http://localhost:9112/health"
echo "   • Canary:       http://localhost:9111/health"
echo ""
echo "🎯 Next Steps:"
echo "   • Run demo:  ./scripts/remediation_quickstart.sh"
echo "   • Run tests: make auto-remediation-test"
echo "   • View logs: docker compose logs -f agi-remediator"
echo ""
echo "📚 Documentation:"
echo "   • Quick Start:  ./scripts/dgm_quickstart.sh"
echo "   • Auto-Remediation: AUTO_REMEDIATION_GUIDE.md"
echo "   • Architecture: AUTO_REMEDIATION_ARCHITECTURE.md"
echo ""
echo "To stop: docker compose -f docker-compose.athena-governance.yml down"
echo ""

