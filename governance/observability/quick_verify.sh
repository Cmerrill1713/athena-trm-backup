#!/usr/bin/env bash
set -euo pipefail

echo "🔍 TRM Monitoring Quick Verification"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check Docker
echo "Checking Docker..."
if docker info &>/dev/null; then
    check_pass "Docker is running"
else
    check_fail "Docker is not running"
    exit 1
fi

# Check monitoring stack
echo ""
echo "Checking monitoring containers..."
if docker ps | grep -q trm-prometheus; then
    check_pass "Prometheus container running"
else
    check_warn "Prometheus not running (run: make monitoring-up)"
fi

if docker ps | grep -q trm-grafana; then
    check_pass "Grafana container running"
else
    check_warn "Grafana not running (run: make monitoring-up)"
fi

if docker ps | grep -q trm-alertmanager; then
    check_pass "AlertManager container running"
else
    check_warn "AlertManager not running (run: make monitoring-up)"
fi

# Check metrics endpoint
echo ""
echo "Checking metrics endpoint..."
if curl -s http://127.0.0.1:8080/metrics >/dev/null 2>&1; then
    check_pass "Metrics endpoint responding"
    
    # Check for TRM metrics
    if curl -s http://127.0.0.1:8080/metrics | grep -q "routing_decisions_total"; then
        check_pass "TRM metrics present"
    else
        check_warn "TRM metrics not found (integrate src/api/metrics_mount.py)"
    fi
else
    check_warn "Metrics endpoint not responding (start your API)"
fi

# Check Prometheus
echo ""
echo "Checking Prometheus..."
if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
    check_pass "Prometheus is healthy"
else
    check_warn "Prometheus not responding"
fi

# Check Grafana
echo ""
echo "Checking Grafana..."
if curl -s http://localhost:3001/api/health >/dev/null 2>&1; then
    check_pass "Grafana is healthy"
else
    check_warn "Grafana not responding"
fi

# Check database connection
echo ""
echo "Checking database..."
if [ -n "${DATABASE_URL:-}" ]; then
    check_pass "DATABASE_URL is set"
    
    if psql "$DATABASE_URL" -c "SELECT 1" >/dev/null 2>&1; then
        check_pass "Database connection successful"
        
        # Check for routing_outcomes table
        if psql "$DATABASE_URL" -c "\dt routing_outcomes" 2>&1 | grep -q "routing_outcomes"; then
            check_pass "routing_outcomes table exists"
        else
            check_warn "routing_outcomes table not found (run: make init-routing-db)"
        fi
    else
        check_warn "Cannot connect to database"
    fi
else
    check_warn "DATABASE_URL not set"
fi

# Check for required files
echo ""
echo "Checking configuration files..."
if [ -f "dashboards/trm_evolution_overview.json" ]; then
    check_pass "Dashboard JSON exists"
else
    check_fail "Dashboard JSON missing"
fi

if [ -f "prometheus/prometheus.yml" ]; then
    check_pass "Prometheus config exists"
else
    check_fail "Prometheus config missing"
fi

if [ -f "monitoring/alerts/trm.rules.yml" ]; then
    check_pass "Alert rules exist"
else
    check_fail "Alert rules missing"
fi

# Summary
echo ""
echo "===================================="
echo "📊 Quick Links:"
echo "   Grafana:    http://localhost:3001"
echo "   Prometheus: http://localhost:9090"
echo "   Metrics:    http://localhost:8080/metrics"
echo ""
echo "📚 Next Steps:"
echo "   make monitoring-up      # Start stack"
echo "   make init-routing-db    # Initialize database"
echo "   make dash-import        # Import dashboard"
echo "   make check-metrics      # Verify metrics"
echo ""
echo "✅ Verification complete!"

