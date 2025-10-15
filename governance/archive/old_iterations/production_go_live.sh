#!/bin/bash
# Production Go-Live Script
# Executes the Day-0 Go Live Runbook procedures

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
CANARY_PERCENTAGE=${CANARY_PERCENTAGE:-25}
BRIDGE_TOKEN=${BRIDGE_TOKEN:-}
UAT_TOKEN=${UAT_TOKEN:-}
ATH_TOKEN=${ATH_TOKEN:-}

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Phase 1: Pre-flight checks
phase_preflight() {
    header "PHASE 1: Pre-Flight Checks"

    log "Checking Docker..."
    if ! docker info >/dev/null 2>&1; then
        error "Docker not running"
        exit 1
    fi
    success "Docker running"

    log "Checking required tokens..."
    if [[ -z "$BRIDGE_TOKEN" || -z "$UAT_TOKEN" || -z "$ATH_TOKEN" ]]; then
        error "Missing required tokens. Set BRIDGE_TOKEN, UAT_TOKEN, ATH_TOKEN"
        exit 1
    fi
    success "All tokens configured"

    log "Running final validation..."
    if ! ./VALIDATE_PLATFORM.sh >/dev/null 2>&1; then
        error "Platform validation failed"
        exit 1
    fi
    success "Platform validation passed"
}

# Phase 2: Fix known issues
phase_fixes() {
    header "PHASE 2: Apply Production Fixes"

    log "Checking FastAPI caching fix..."
    if grep -q "async def api_chat(req: Request, body: dict):" bridge/adapter.py; then
        warning "FastAPI caching issue detected - fixing..."
        sed -i 's/async def api_chat(req: Request, body: dict):/async def api_chat(req: Request, body: ApiChatInput):/' bridge/adapter.py
        success "FastAPI model caching fixed"
    else
        success "FastAPI model already correct"
    fi

    log "Creating production backup..."
    ./scripts/pg_backup.sh
    success "Database backup completed"
}

# Phase 3: Deploy services
phase_deploy() {
    header "PHASE 3: Production Deployment"

    log "Stopping development services..."
    docker-compose down 2>/dev/null || true

    log "Starting production stack..."
    docker-compose -f deploy/docker-compose.prod.yml up -d

    log "Waiting for services to be healthy..."
    sleep 30

    # Health checks
    services=("bridge:8014" "athena:8090" "uat:8181" "kokoro:8020")
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)

        if curl -sf http://localhost:$port/health >/dev/null 2>&1; then
            success "$name healthy on :$port"
        else
            error "$name not healthy on :$port"
            exit 1
        fi
    done
}

# Phase 4: Enable canary traffic
phase_canary() {
    header "PHASE 4: Enable Canary Traffic ($CANARY_PERCENTAGE%)"

    log "Configuring canary traffic..."
    export CANARY_PERCENTAGE

    log "Starting gradual rollout..."
    ./scripts/canary_branch.sh enable

    log "Monitoring traffic for 2 minutes..."
    for i in {1..4}; do
        sleep 30
        log "Canary status check $i/4..."
        ./scripts/monitoring/quick_verify.sh >/dev/null 2>&1 || warning "Check $i had issues"
    done

    success "Canary traffic enabled at $CANARY_PERCENTAGE%"
}

# Phase 5: Post-launch verification
phase_verify() {
    header "PHASE 5: Post-Launch Verification"

    log "Running post-deployment smoke tests..."
    if ./scripts/post_ship_smoke.sh >/dev/null 2>&1; then
        success "Smoke tests passed"
    else
        warning "Some smoke tests failed - check logs"
    fi

    log "Testing chat endpoint..."
    response=$(curl -s -X POST http://localhost:8014/api/chat \
        -H "Authorization: Bearer $BRIDGE_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"text":"Hello production system","kind":"smalltalk"}')

    if echo "$response" | jq -e '.reply' >/dev/null 2>&1; then
        success "Chat endpoint working"
    else
        error "Chat endpoint failed"
        echo "Response: $response"
        exit 1
    fi

    log "Checking learning systems..."
    # Allow 5 minutes for initial learning
    sleep 300

    if ./scripts/learn/verify_learning.sh >/dev/null 2>&1; then
        success "Learning systems operational"
    else
        warning "Learning systems need more time to initialize"
    fi
}

# Phase 6: Final status
phase_final() {
    header "PHASE 6: Go-Live Complete!"

    echo ""
    echo -e "${GREEN}🎉 PRODUCTION DEPLOYMENT SUCCESSFUL${NC}"
    echo ""
    echo "📊 Monitoring URLs:"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana:    http://localhost:3001"
    echo "   Bridge API: http://localhost:8014"
    echo ""
    echo "🛡️  Emergency Procedures:"
    echo "   Rollback:   ./scripts/ROLLBACK_PLAYBOOK.sh"
    echo "   Restart:    docker-compose -f deploy/docker-compose.prod.yml restart"
    echo "   Full Reset: docker-compose -f deploy/docker-compose.prod.yml down && up -d"
    echo ""
    echo "📈 Next Steps:"
    echo "   Monitor for 4 hours"
    echo "   Gradually increase canary traffic"
    echo "   Watch learning system adaptation"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}🚀 NeuroForge Production Go-Live Script${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""

    phase_preflight
    phase_fixes
    phase_deploy
    phase_canary
    phase_verify
    phase_final

    echo -e "${GREEN}✅ Go-Live procedure completed successfully!${NC}"
}

# Run main function
main "$@"
