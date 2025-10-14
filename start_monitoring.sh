#!/bin/bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        NeuroForge Monitoring Stack Setup                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Backup old config and use new one
if [ -f prometheus/prometheus.yml ]; then
    echo -e "${YELLOW}📦 Backing up old Prometheus config...${NC}"
    cp prometheus/prometheus.yml prometheus/prometheus.yml.backup
fi

echo -e "${BLUE}📝 Using updated Prometheus config for your services...${NC}"
cp prometheus/prometheus.updated.yml prometheus/prometheus.yml

# Create alerts directory if it doesn't exist
mkdir -p prometheus/alerts

# Copy alert rules to prometheus/alerts
echo -e "${BLUE}📋 Setting up alert rules...${NC}"
cp monitoring/alerts/*.yml prometheus/alerts/ 2>/dev/null || true

# Stop any existing monitoring containers
echo -e "${YELLOW}🛑 Stopping any existing monitoring containers...${NC}"
docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true

# Start the monitoring stack
echo -e "${GREEN}🚀 Starting monitoring stack...${NC}"
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 5

# Check service health
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Service Health Check                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC} - Running"
        return 0
    else
        echo -e "${RED}❌ $name${NC} - Not responding"
        return 1
    fi
}

check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3001/api/health"
check_service "AlertManager" "http://localhost:9093/-/healthy"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Monitoring URLs                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Prometheus:${NC}    http://localhost:9090"
echo -e "${GREEN}📈 Grafana:${NC}       http://localhost:3001"
echo -e "   ${YELLOW}Login:${NC}         admin / admin"
echo -e "${GREEN}🚨 AlertManager:${NC}  http://localhost:9093"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Next Steps                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. Open Grafana: http://localhost:3001"
echo "2. Login with: admin / admin"
echo "3. Import dashboards from: ./dashboards/"
echo "4. View metrics in Prometheus: http://localhost:9090"
echo ""
echo -e "${GREEN}✅ Monitoring stack is running!${NC}"
echo ""
