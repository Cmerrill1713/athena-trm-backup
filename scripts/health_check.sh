#!/bin/bash
# Comprehensive Health Check for Athena System
# Checks all services, endpoints, and critical functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT=5
FAILED=0
TOTAL=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Athena System Health Check                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Helper function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    TOTAL=$((TOTAL + 1))
    
    if response=$(curl -sf --max-time $TIMEOUT -w "%{http_code}" -o /dev/null "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_code" ]; then
            echo -e "${GREEN}✓${NC} $name ($url)"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $name ($url) - returned $response, expected $expected_code"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $name ($url) - not responding"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Helper function to check port
check_port() {
    local name=$1
    local host=$2
    local port=$3
    
    TOTAL=$((TOTAL + 1))
    
    if nc -z -w $TIMEOUT "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name (${host}:${port})"
        return 0
    else
        echo -e "${RED}✗${NC} $name (${host}:${port}) - port not open"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Helper function to check Docker container
check_container() {
    local name=$1
    
    TOTAL=$((TOTAL + 1))
    
    if docker ps --format '{{.Names}}' | grep -q "^${name}$" 2>/dev/null; then
        status=$(docker inspect -f '{{.State.Health.Status}}' "$name" 2>/dev/null || echo "no-healthcheck")
        if [ "$status" = "healthy" ] || [ "$status" = "no-healthcheck" ]; then
            echo -e "${GREEN}✓${NC} $name (container running)"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $name (container unhealthy: $status)"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $name (container not running)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# =============================================================================
# GOVERNANCE SERVICES
# =============================================================================
echo -e "\n${BLUE}[Governance Services]${NC}"
check_endpoint "Orchestrator Health" "http://localhost:9110/health"
check_endpoint "Orchestrator Metrics" "http://localhost:9110/metrics"
check_endpoint "Canary Monitor Health" "http://localhost:9111/health"
check_endpoint "Canary Monitor Metrics" "http://localhost:9111/metrics"
check_endpoint "Remediator Health" "http://localhost:9112/health"
check_endpoint "Remediator Metrics" "http://localhost:9112/metrics"
check_endpoint "Metrics Exporter Health" "http://localhost:9109/health"

# =============================================================================
# MONITORING
# =============================================================================
echo -e "\n${BLUE}[Monitoring]${NC}"
check_endpoint "Prometheus" "http://localhost:9090/-/healthy"
check_endpoint "Grafana" "http://localhost:3001/api/health"

# =============================================================================
# DATABASES
# =============================================================================
echo -e "\n${BLUE}[Databases]${NC}"
check_port "PostgreSQL" "localhost" 5432
check_port "Redis" "localhost" 6379

# =============================================================================
# DOCKER CONTAINERS (if using Docker)
# =============================================================================
if command -v docker &> /dev/null; then
    echo -e "\n${BLUE}[Docker Containers]${NC}"
    check_container "governance-orchestrator" || true
    check_container "governance-canary-monitor" || true
    check_container "agi-remediator" || true
    check_container "athena-prometheus" || true
    check_container "athena-grafana" || true
    check_container "athena-postgres" || true
    check_container "athena-redis" || true
fi

# =============================================================================
# PROMETHEUS TARGETS
# =============================================================================
echo -e "\n${BLUE}[Prometheus Targets]${NC}"
if curl -sf http://localhost:9090/-/healthy &>/dev/null; then
    targets=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | jq -r '.data.activeTargets[] | select(.health=="up") | .labels.instance' 2>/dev/null || echo "")
    
    if [ -n "$targets" ]; then
        TOTAL=$((TOTAL + 1))
        echo -e "${GREEN}✓${NC} Active targets:"
        echo "$targets" | while read -r target; do
            echo "  - $target"
        done
    else
        TOTAL=$((TOTAL + 1))
        echo -e "${YELLOW}⚠${NC} Could not fetch Prometheus targets"
        FAILED=$((FAILED + 1))
    fi
else
    TOTAL=$((TOTAL + 1))
    echo -e "${RED}✗${NC} Prometheus not available - skipping target check"
    FAILED=$((FAILED + 1))
fi

# =============================================================================
# CRITICAL METRICS
# =============================================================================
echo -e "\n${BLUE}[Critical Metrics]${NC}"
if curl -sf http://localhost:9090/-/healthy &>/dev/null; then
    # Check for governance metrics
    TOTAL=$((TOTAL + 1))
    gov_metrics=$(curl -s "http://localhost:9090/api/v1/query?query=governance_remediations_requested_total" 2>/dev/null | jq -r '.data.result[]' 2>/dev/null || echo "")
    if [ -n "$gov_metrics" ]; then
        echo -e "${GREEN}✓${NC} Governance metrics available"
    else
        echo -e "${YELLOW}⚠${NC} Governance metrics not found (may need time to populate)"
    fi
    
    # Check for DGM metrics
    TOTAL=$((TOTAL + 1))
    dgm_metrics=$(curl -s "http://localhost:9090/api/v1/query?query=dgm_generations_total" 2>/dev/null | jq -r '.data.result[]' 2>/dev/null || echo "")
    if [ -n "$dgm_metrics" ]; then
        echo -e "${GREEN}✓${NC} DGM metrics available"
    else
        echo -e "${YELLOW}⚠${NC} DGM metrics not found (will populate after first evolution)"
    fi
fi

# =============================================================================
# STATE FILES
# =============================================================================
echo -e "\n${BLUE}[State Files]${NC}"
TOTAL=$((TOTAL + 1))
if [ -d "state/canary" ]; then
    echo -e "${GREEN}✓${NC} Canary state directory exists"
else
    echo -e "${YELLOW}⚠${NC} Canary state directory not found (will be created on first use)"
fi

TOTAL=$((TOTAL + 1))
if [ -d "sandbox" ]; then
    echo -e "${GREEN}✓${NC} Sandbox directory exists"
else
    echo -e "${YELLOW}⚠${NC} Sandbox directory not found (will be created on first use)"
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                         Summary                                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

PASSED=$((TOTAL - FAILED))
SUCCESS_RATE=$((PASSED * 100 / TOTAL))

echo ""
echo -e "Total Checks: ${TOTAL}"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo -e "Success Rate: ${SUCCESS_RATE}%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All systems operational${NC}"
    echo ""
    exit 0
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${YELLOW}⚠ System partially operational (${SUCCESS_RATE}% healthy)${NC}"
    echo -e "${YELLOW}  Some services may need attention${NC}"
    echo ""
    exit 1
else
    echo -e "${RED}✗ System degraded (${SUCCESS_RATE}% healthy)${NC}"
    echo -e "${RED}  Multiple services down - check logs${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check Docker: docker compose ps"
    echo "  - Check logs: docker logs <service-name>"
    echo "  - Restart services: docker compose restart"
    echo ""
    exit 2
fi

