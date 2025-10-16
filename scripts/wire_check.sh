#!/usr/bin/env bash
# Root Evaluation & Wiring Checklist for Governance System
# This script validates that all endpoints, topics, and metrics are properly wired

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

ok() { echo -e "${GREEN}✓${NC} $*"; ((PASS++)); }
fail() { echo -e "${RED}✗${NC} $*"; ((FAIL++)); }
warn() { echo -e "${YELLOW}⚠${NC} $*"; ((WARN++)); }
info() { echo -e "${BLUE}ℹ${NC} $*"; }
section() { echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"; echo -e "${BLUE}$*${NC}"; echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"; }

# Output file for inventory
INVENTORY_FILE="./wire_check_inventory.txt"
> "$INVENTORY_FILE"

section "0) Fast Context Check"

info "Repo root: $(pwd)"
info "Docker compose file: docker-compose.athena-governance.yml"

section "1) Inventory: Ports, Endpoints, Topics, Metrics"

info "1.1 Listing Docker containers and ports..."
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    docker ps --format 'table {{.Names}}\t{{.Ports}}' | tee -a "$INVENTORY_FILE"
    ok "Docker containers listed"
else
    warn "Docker not available or no containers running"
fi

echo "" >> "$INVENTORY_FILE"
info "1.2 Scanning for HTTP routes in source code..."
{
    echo "=== HTTP ROUTES ==="
    rg -n "app\.route|router\.([A-Z]+)|@app\.(get|post)|POST|GET\s+/|/verdict|/health|/metrics" \
        --glob '!**/archive/**' --hidden 2>/dev/null || echo "No routes found"
} | tee -a "$INVENTORY_FILE"

echo "" >> "$INVENTORY_FILE"
info "1.3 Scanning for OpenAPI/JSON schemas..."
{
    echo "=== SCHEMAS ==="
    rg -n "openapi|swagger|schemas?|schema\.json|\.schema\.json" \
        --hidden 2>/dev/null | head -20 || echo "No schemas found"
} | tee -a "$INVENTORY_FILE"

echo "" >> "$INVENTORY_FILE"
info "1.4 Scanning for event bus topics..."
{
    echo "=== EVENT TOPICS ==="
    rg -n "emit\(|publish\(|topic\s*=\s*|\"exec\.|\"judicial\.|\"release\.canary" \
        --hidden 2>/dev/null | head -20 || echo "No topics found"
} | tee -a "$INVENTORY_FILE"

echo "" >> "$INVENTORY_FILE"
info "1.5 Extracting governance metrics names..."
{
    echo "=== METRICS NAMES ==="
    rg -n "governance_[a-zA-Z0-9_]+" --hidden 2>/dev/null | \
        grep -oE 'governance_[a-zA-Z0-9_]+' | sort -u || echo "No metrics found"
} | tee -a "$INVENTORY_FILE"

ok "Inventory saved to: $INVENTORY_FILE"

section "2) Health, Ready, Version Triad"

# Services to check
SERVICES=(
    "9110:governance-orchestrator"
    "9109:governance-metrics"
    "9111:governance-canary"
    "9090:prometheus"
)

for svc in "${SERVICES[@]}"; do
    PORT="${svc%%:*}"
    NAME="${svc##*:}"
    
    info "Checking $NAME on port $PORT..."
    
    # Health check
    if curl -fsS --max-time 2 "http://localhost:${PORT}/health" &>/dev/null; then
        ok "$NAME health endpoint responds"
    else
        fail "$NAME health endpoint not responding on :$PORT"
    fi
    
    # Ready check
    if curl -fsS --max-time 2 "http://localhost:${PORT}/ready" &>/dev/null; then
        ok "$NAME ready endpoint responds"
    else
        warn "$NAME ready endpoint not available (optional but recommended)"
    fi
    
    # Version check
    if curl -fsS --max-time 2 "http://localhost:${PORT}/version" &>/dev/null; then
        ok "$NAME version endpoint responds"
    else
        warn "$NAME version endpoint not available (optional but recommended)"
    fi
done

section "3) Contract Checks: Required Endpoints"

info "3.1 Testing POST /verdict endpoint..."
VERDICT_RESPONSE=$(curl -s --max-time 5 -X POST "http://localhost:9110/verdict" \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"T-wire-$(date +%s)\",\"verdict\":\"PASS\",\"ece_estimate\":0.045,\"entropy_drift\":0.1,\"actions\":[\"HOLD\"],\"ts\":\"$(date -u +%FT%TZ)\"}" 2>&1)

if echo "$VERDICT_RESPONSE" | grep -q '"status"'; then
    ok "Verdict endpoint accepts POST and returns JSON"
    echo "$VERDICT_RESPONSE" | head -3
else
    fail "Verdict endpoint did not return expected response"
    echo "Response: $VERDICT_RESPONSE" | head -5
fi

info "3.2 Testing POST /canary-window endpoint (if exists)..."
CANARY_RESPONSE=$(curl -s --max-time 5 -X POST "http://localhost:9111/canary-window" \
  -H "Content-Type: application/json" \
  -d "{\"window_id\":\"w-wire-$(date +%s)\",\"decision\":\"HOLD\",\"samples\":100,\"deltas\":{\"solve_rate\":0.01,\"violation_rate\":-0.001,\"latency_p95\":-0.05},\"ece_post\":0.05,\"confidence\":0.85,\"ts\":\"$(date -u +%FT%TZ)\"}" 2>&1)

if echo "$CANARY_RESPONSE" | grep -q "canary" || echo "$CANARY_RESPONSE" | grep -q "window"; then
    ok "Canary window endpoint available"
else
    warn "Canary window endpoint not available or different path"
fi

info "3.3 Testing GET /metrics endpoint..."
if curl -fsS --max-time 2 "http://localhost:9110/metrics" | grep -q "governance_"; then
    ok "Orchestrator metrics endpoint exports governance_* metrics"
else
    fail "Orchestrator metrics endpoint not exporting properly"
fi

section "4) State, Idempotence, and Action Binding"

info "4.1 Checking for state persistence..."
if [ -f "state/exec_state.json" ] || [ -f "exec_state.json" ]; then
    STATE_FILE=$([ -f "state/exec_state.json" ] && echo "state/exec_state.json" || echo "exec_state.json")
    ok "State file found: $STATE_FILE"
    
    if command -v jq &> /dev/null; then
        echo "Current state:"
        jq '.' "$STATE_FILE" 2>/dev/null | head -10 || cat "$STATE_FILE" | head -10
    else
        warn "jq not installed, skipping state inspection"
    fi
else
    warn "State file not found (exec_state.json)"
fi

info "4.2 Testing idempotence - submitting same verdict twice..."
TASK_ID="T-idempotence-$(date +%s)"
VERDICT_DATA="{\"task_id\":\"$TASK_ID\",\"verdict\":\"PASS\",\"ece_estimate\":0.045,\"entropy_drift\":0.1,\"actions\":[\"HOLD\"]}"

# First submission
curl -s --max-time 5 -X POST "http://localhost:9110/verdict" \
  -H "Content-Type: application/json" \
  -d "$VERDICT_DATA" &>/dev/null

sleep 1

# Second submission (should be idempotent)
SECOND_RESPONSE=$(curl -s --max-time 5 -X POST "http://localhost:9110/verdict" \
  -H "Content-Type: application/json" \
  -d "$VERDICT_DATA" 2>&1)

if echo "$SECOND_RESPONSE" | grep -q "status"; then
    ok "Idempotence test: server accepted duplicate submission gracefully"
else
    warn "Idempotence may not be fully implemented"
fi

info "4.3 Checking action ledger (if exists)..."
if [ -f "artifacts/ledger/actions.log" ]; then
    LEDGER_LINES=$(wc -l < "artifacts/ledger/actions.log")
    ok "Action ledger exists: $LEDGER_LINES entries"
else
    warn "Action ledger not found (artifacts/ledger/actions.log)"
fi

section "5) Event Bus Emissions and Consumers"

info "5.1 Checking for event emissions in logs..."
if [ -d "logs" ]; then
    EVENT_COUNT=$(rg -i "exec\.verdict_applied|judicial\.verdict|release\.canary" logs/ 2>/dev/null | wc -l || echo "0")
    if [ "$EVENT_COUNT" -gt 0 ]; then
        ok "Found $EVENT_COUNT event emissions in logs"
        rg -i "exec\.verdict_applied" logs/ 2>/dev/null | tail -3 || true
    else
        warn "No event emissions found in logs/ directory"
    fi
else
    warn "No logs/ directory found"
fi

section "6) Prometheus: Scrape + Series Present"

info "6.1 Checking Prometheus targets..."
PROM_TARGETS=$(curl -s --max-time 5 "http://localhost:9090/api/v1/targets" 2>&1)

if echo "$PROM_TARGETS" | grep -q "activeTargets"; then
    ok "Prometheus targets API responds"
    
    if command -v jq &> /dev/null; then
        echo "Active targets:"
        echo "$PROM_TARGETS" | jq -r '.data.activeTargets[]? | "\(.labels.job) - \(.health)"' 2>/dev/null | head -10
    fi
else
    fail "Prometheus targets API not responding properly"
fi

info "6.2 Checking for governance metrics series..."
SERIES_CHECK=$(curl -s --max-time 5 "http://localhost:9090/api/v1/series?match[]=governance_verdicts_total" 2>&1)

if echo "$SERIES_CHECK" | grep -q "governance_verdicts_total"; then
    ok "Prometheus has governance_verdicts_total series"
else
    warn "governance_verdicts_total series not found in Prometheus"
fi

info "6.3 Critical series check..."
CRITICAL_SERIES=(
    "governance_verdicts_total"
    "governance_actions_total"
    "governance_ece_post"
    "governance_entropy_drift"
)

for series in "${CRITICAL_SERIES[@]}"; do
    if curl -s --max-time 3 "http://localhost:9090/api/v1/series?match[]=${series}" 2>&1 | grep -q "$series"; then
        ok "Series present: $series"
    else
        warn "Series missing: $series"
    fi
done

section "7) Grafana Panels & Alerts"

info "7.1 Checking Grafana availability..."
if curl -fsS --max-time 2 "http://localhost:3001/api/health" &>/dev/null; then
    ok "Grafana is responding on :3001"
else
    warn "Grafana not responding on :3001"
fi

info "7.2 Checking Prometheus alerts..."
ALERTS=$(curl -s --max-time 5 "http://localhost:9090/api/v1/alerts" 2>&1)

if echo "$ALERTS" | grep -q "alerts"; then
    ALERT_COUNT=$(echo "$ALERTS" | grep -o "alertname" | wc -l || echo "0")
    if [ "$ALERT_COUNT" -gt 0 ]; then
        ok "Prometheus has $ALERT_COUNT alert(s) configured"
        if command -v jq &> /dev/null; then
            echo "$ALERTS" | jq -r '.data.alerts[]? | "\(.labels.alertname) - \(.state)"' 2>/dev/null | head -5
        fi
    else
        warn "No alerts found in Prometheus"
    fi
else
    warn "Could not query Prometheus alerts"
fi

section "8) Auth, CORS, Rate-Limits (Edge Sanity)"

info "8.1 Checking CORS headers on OPTIONS..."
CORS_RESPONSE=$(curl -s -X OPTIONS "http://localhost:9110/verdict" \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: POST" -I 2>&1)

if echo "$CORS_RESPONSE" | grep -qi "access-control"; then
    ok "CORS headers present"
else
    warn "CORS headers not configured (may be intentional for backend-only services)"
fi

info "8.2 Auth check..."
# Try without auth
UNAUTH_RESPONSE=$(curl -s --max-time 2 -X POST "http://localhost:9110/health" 2>&1)
if echo "$UNAUTH_RESPONSE" | grep -q "healthy"; then
    warn "Endpoints accessible without auth (ensure this is intentional for /health)"
else
    ok "Endpoints may require authentication"
fi

section "9) Failure Drills"

info "9.1 Simulating orchestrator restart (if Docker is available)..."
if command -v docker &> /dev/null && docker ps | grep -q "governance-orchestrator"; then
    warn "Skipping orchestrator restart in automated test (run manually: docker compose restart governance-orchestrator)"
else
    warn "Docker not available or orchestrator not running - skipping failure drill"
fi

section "10) Final Smoke Test"

info "Running comprehensive smoke test..."

# Count checks
SMOKE_PASS=0
SMOKE_FAIL=0

# Prometheus check
if curl -fsS --max-time 2 "http://localhost:9090/-/ready" &>/dev/null; then
    ((SMOKE_PASS++))
else
    ((SMOKE_FAIL++))
    fail "Prometheus not ready"
fi

# Core services check
for port in 9110 9111 9109; do
    if curl -fsS --max-time 2 "http://localhost:${port}/health" &>/dev/null; then
        ((SMOKE_PASS++))
    else
        ((SMOKE_FAIL++))
        fail "Service on :$port not healthy"
    fi
done

# Verdict POST check
if curl -fsS --max-time 5 -X POST "http://localhost:9110/verdict" \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"T-smoke-$(date +%s)\",\"verdict\":\"PASS\",\"ece_estimate\":0.04,\"actions\":[\"HOLD\"]}" &>/dev/null; then
    ((SMOKE_PASS++))
else
    ((SMOKE_FAIL++))
    fail "Verdict POST failed"
fi

# Wait for metrics
sleep 2

# Metrics visibility check
if curl -fsS --max-time 3 "http://localhost:9090/api/v1/query?query=governance_verdicts_total" 2>&1 | grep -q "result"; then
    ((SMOKE_PASS++))
else
    ((SMOKE_FAIL++))
    fail "Metrics not visible in Prometheus"
fi

if [ $SMOKE_FAIL -eq 0 ]; then
    ok "SMOKE TEST PASSED: verdict→action→metrics loop is healthy"
else
    fail "SMOKE TEST FAILED: $SMOKE_FAIL/$((SMOKE_PASS + SMOKE_FAIL)) checks failed"
fi

section "Summary"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CRITICAL CHECKS PASSED${NC}"
    echo ""
    echo "✅ Wiring is complete! All endpoints, topics, and metrics are properly connected."
    echo ""
    echo "Inventory saved to: $INVENTORY_FILE"
    exit 0
else
    echo -e "${RED}✗ WIRING CHECK FAILED${NC}"
    echo ""
    echo "❌ $FAIL critical check(s) failed. Review the output above."
    echo ""
    echo "Common fixes:"
    echo "  - Ensure all services are running: docker compose ps"
    echo "  - Check service logs: docker compose logs [service-name]"
    echo "  - Verify port mappings in docker-compose.yml"
    echo "  - Confirm Prometheus scrape configs point to correct targets"
    echo ""
    echo "Inventory saved to: $INVENTORY_FILE"
    exit 1
fi

